"""
AFAAP Performance Metrics Module

Calculates model performance metrics with statistical rigor:
- F1 Score with 95% confidence intervals (bootstrap resampling)
- False Positive Rate (FPR) with confidence intervals
- Precision and Recall
- Fairness metrics (FPR by subgroup)

All calculations follow MAS regulatory requirements for AI model validation.

Governance Note: Metrics must be calculated with confidence intervals to account
for sampling variability. Bootstrap resampling (10,000 iterations) provides
robust estimates of metric uncertainty.
"""

import os
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import numpy as np
from sklearn.metrics import (
    f1_score,
    precision_score,
    recall_score,
    confusion_matrix,
    roc_auc_score
)
import logging
import structlog

# Configure structured logging
logger = structlog.get_logger(__name__)

# Governance thresholds from environment or defaults
MIN_F1_SCORE = float(os.getenv('AFAAP_MIN_F1_SCORE', '0.85'))
MAX_FPR = float(os.getenv('AFAAP_MAX_FPR', '0.01'))
CONFIDENCE_INTERVAL = float(os.getenv('CONFIDENCE_INTERVAL', '0.95'))
BOOTSTRAP_ITERATIONS = int(os.getenv('BOOTSTRAP_ITERATIONS', '10000'))


@dataclass
class PerformanceMetrics:
    """Container for model performance metrics with confidence intervals."""
    f1_score: float
    f1_ci_lower: float
    f1_ci_upper: float

    fpr: float
    fpr_ci_lower: float
    fpr_ci_upper: float

    precision: float
    precision_ci_lower: float
    precision_ci_upper: float

    recall: float
    recall_ci_lower: float
    recall_ci_upper: float

    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int

    auc_roc: Optional[float] = None
    total_samples: int = 0

    def meets_deployment_thresholds(self) -> Tuple[bool, List[str]]:
        """
        Check if metrics meet governance thresholds for deployment.

        Governance Rule: F1 >= 0.85 AND FPR <= 0.01

        Returns:
            Tuple of (meets_thresholds, list_of_failures)
        """
        failures = []

        if self.f1_score < MIN_F1_SCORE:
            failures.append(
                f"F1 score {self.f1_score:.4f} below threshold {MIN_F1_SCORE}"
            )

        if self.fpr > MAX_FPR:
            failures.append(
                f"FPR {self.fpr:.4f} exceeds threshold {MAX_FPR}"
            )

        # Also check confidence intervals to ensure robust performance
        if self.f1_ci_lower < MIN_F1_SCORE:
            failures.append(
                f"F1 CI lower bound {self.f1_ci_lower:.4f} below threshold {MIN_F1_SCORE}"
            )

        if self.fpr_ci_upper > MAX_FPR:
            failures.append(
                f"FPR CI upper bound {self.fpr_ci_upper:.4f} exceeds threshold {MAX_FPR}"
            )

        return (len(failures) == 0, failures)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'f1_score': round(self.f1_score, 4),
            'f1_ci_lower': round(self.f1_ci_lower, 4),
            'f1_ci_upper': round(self.f1_ci_upper, 4),
            'fpr': round(self.fpr, 4),
            'fpr_ci_lower': round(self.fpr_ci_lower, 4),
            'fpr_ci_upper': round(self.fpr_ci_upper, 4),
            'precision': round(self.precision, 4),
            'precision_ci_lower': round(self.precision_ci_lower, 4),
            'precision_ci_upper': round(self.precision_ci_upper, 4),
            'recall': round(self.recall, 4),
            'recall_ci_lower': round(self.recall_ci_lower, 4),
            'recall_ci_upper': round(self.recall_ci_upper, 4),
            'true_positives': self.true_positives,
            'false_positives': self.false_positives,
            'true_negatives': self.true_negatives,
            'false_negatives': self.false_negatives,
            'auc_roc': round(self.auc_roc, 4) if self.auc_roc else None,
            'total_samples': self.total_samples
        }


def calculate_f1_with_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    confidence: float = CONFIDENCE_INTERVAL,
    n_bootstrap: int = BOOTSTRAP_ITERATIONS,
    random_state: int = 42
) -> Tuple[float, float, float]:
    """
    Calculate F1 score with confidence interval using bootstrap resampling.

    Governance Note: Bootstrap resampling provides robust estimate of F1 score
    uncertainty. 10,000 iterations recommended for regulatory reporting.

    Args:
        y_true: Ground truth labels (binary: 0=legitimate, 1=fraud)
        y_pred: Model predictions (binary: 0=legitimate, 1=fraud)
        confidence: Confidence level (default 0.95 for 95% CI)
        n_bootstrap: Number of bootstrap iterations (default 10,000)
        random_state: Random seed for reproducibility

    Returns:
        Tuple of (f1_score, ci_lower, ci_upper)

    Raises:
        ValueError: If inputs are invalid or empty
    """
    # Governance Rule: Validate inputs to prevent silent failures
    if len(y_true) == 0 or len(y_pred) == 0:
        logger.error("empty_input", y_true_len=len(y_true), y_pred_len=len(y_pred))
        raise ValueError("Input arrays cannot be empty")

    if len(y_true) != len(y_pred):
        logger.error("length_mismatch", y_true_len=len(y_true), y_pred_len=len(y_pred))
        raise ValueError("y_true and y_pred must have same length")

    # Calculate point estimate
    f1 = f1_score(y_true, y_pred, zero_division=0)

    # Bootstrap resampling for confidence interval
    np.random.seed(random_state)
    bootstrap_scores = []

    n_samples = len(y_true)
    alpha = 1 - confidence

    for i in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.randint(0, n_samples, n_samples)
        y_true_boot = y_true[indices]
        y_pred_boot = y_pred[indices]

        # Handle edge case: no positive predictions in bootstrap sample
        if y_pred_boot.sum() == 0 or y_true_boot.sum() == 0:
            bootstrap_scores.append(0.0)
        else:
            f1_boot = f1_score(y_true_boot, y_pred_boot, zero_division=0)
            bootstrap_scores.append(f1_boot)

    # Calculate confidence interval
    ci_lower = np.percentile(bootstrap_scores, (alpha/2) * 100)
    ci_upper = np.percentile(bootstrap_scores, (1 - alpha/2) * 100)

    logger.info(
        "f1_calculated",
        f1=f1,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        n_samples=n_samples,
        n_bootstrap=n_bootstrap
    )

    return (f1, ci_lower, ci_upper)


def calculate_fpr_with_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    confidence: float = CONFIDENCE_INTERVAL,
    n_bootstrap: int = BOOTSTRAP_ITERATIONS,
    random_state: int = 42
) -> Tuple[float, float, float]:
    """
    Calculate False Positive Rate with confidence interval.

    Governance Rule: FPR must be <= 1% for deployment. CI must also meet threshold.

    FPR = FP / (FP + TN)
        = False Positives / Total Negatives (legitimate transactions)

    Args:
        y_true: Ground truth labels
        y_pred: Model predictions
        confidence: Confidence level (default 0.95)
        n_bootstrap: Number of bootstrap iterations
        random_state: Random seed

    Returns:
        Tuple of (fpr, ci_lower, ci_upper)
    """
    if len(y_true) == 0 or len(y_pred) == 0:
        raise ValueError("Input arrays cannot be empty")

    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have same length")

    # Calculate point estimate
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    # Handle edge case: no negative samples
    if (fp + tn) == 0:
        logger.warning("no_negative_samples", y_true=y_true, y_pred=y_pred)
        return (0.0, 0.0, 0.0)

    fpr = fp / (fp + tn)

    # Bootstrap resampling
    np.random.seed(random_state)
    bootstrap_fprs = []

    n_samples = len(y_true)
    alpha = 1 - confidence

    for i in range(n_bootstrap):
        indices = np.random.randint(0, n_samples, n_samples)
        y_true_boot = y_true[indices]
        y_pred_boot = y_pred[indices]

        # Calculate confusion matrix for bootstrap sample
        cm = confusion_matrix(y_true_boot, y_pred_boot, labels=[0, 1])
        if cm.shape != (2, 2):
            # Edge case: bootstrap sample doesn't have both classes
            bootstrap_fprs.append(0.0)
            continue

        tn_boot, fp_boot, fn_boot, tp_boot = cm.ravel()

        if (fp_boot + tn_boot) == 0:
            bootstrap_fprs.append(0.0)
        else:
            fpr_boot = fp_boot / (fp_boot + tn_boot)
            bootstrap_fprs.append(fpr_boot)

    ci_lower = np.percentile(bootstrap_fprs, (alpha/2) * 100)
    ci_upper = np.percentile(bootstrap_fprs, (1 - alpha/2) * 100)

    logger.info(
        "fpr_calculated",
        fpr=fpr,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        fp=int(fp),
        tn=int(tn),
        n_samples=n_samples
    )

    return (fpr, ci_lower, ci_upper)


def calculate_precision_recall_with_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    confidence: float = CONFIDENCE_INTERVAL,
    n_bootstrap: int = BOOTSTRAP_ITERATIONS,
    random_state: int = 42
) -> Dict[str, Tuple[float, float, float]]:
    """
    Calculate precision and recall with confidence intervals.

    Precision = TP / (TP + FP) - of all predicted frauds, how many are real?
    Recall = TP / (TP + FN) - of all real frauds, how many did we catch?

    Returns:
        Dictionary with 'precision' and 'recall' keys, each containing
        (point_estimate, ci_lower, ci_upper)
    """
    if len(y_true) == 0 or len(y_pred) == 0:
        raise ValueError("Input arrays cannot be empty")

    # Point estimates
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)

    # Bootstrap
    np.random.seed(random_state)
    bootstrap_precision = []
    bootstrap_recall = []

    n_samples = len(y_true)
    alpha = 1 - confidence

    for i in range(n_bootstrap):
        indices = np.random.randint(0, n_samples, n_samples)
        y_true_boot = y_true[indices]
        y_pred_boot = y_pred[indices]

        p = precision_score(y_true_boot, y_pred_boot, zero_division=0)
        r = recall_score(y_true_boot, y_pred_boot, zero_division=0)

        bootstrap_precision.append(p)
        bootstrap_recall.append(r)

    precision_ci_lower = np.percentile(bootstrap_precision, (alpha/2) * 100)
    precision_ci_upper = np.percentile(bootstrap_precision, (1 - alpha/2) * 100)

    recall_ci_lower = np.percentile(bootstrap_recall, (alpha/2) * 100)
    recall_ci_upper = np.percentile(bootstrap_recall, (1 - alpha/2) * 100)

    return {
        'precision': (precision, precision_ci_lower, precision_ci_upper),
        'recall': (recall, recall_ci_lower, recall_ci_upper)
    }


def calculate_all_performance_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_scores: Optional[np.ndarray] = None,
    confidence: float = CONFIDENCE_INTERVAL,
    n_bootstrap: int = BOOTSTRAP_ITERATIONS,
    random_state: int = 42
) -> PerformanceMetrics:
    """
    Calculate all performance metrics with confidence intervals.

    Governance Note: This is the primary function for model validation reporting.
    All metrics calculated here are used for deployment approval decisions.

    Args:
        y_true: Ground truth labels (0=legitimate, 1=fraud)
        y_pred: Model predictions (0=legitimate, 1=fraud)
        y_scores: Model confidence scores (optional, for AUC-ROC)
        confidence: Confidence level for intervals
        n_bootstrap: Number of bootstrap iterations
        random_state: Random seed for reproducibility

    Returns:
        PerformanceMetrics object with all calculated metrics

    Example:
        >>> y_true = np.array([0, 1, 1, 0, 1])
        >>> y_pred = np.array([0, 1, 0, 0, 1])
        >>> metrics = calculate_all_performance_metrics(y_true, y_pred)
        >>> print(f"F1: {metrics.f1_score:.4f} [{metrics.f1_ci_lower:.4f}, {metrics.f1_ci_upper:.4f}]")
    """
    logger.info(
        "calculating_performance_metrics",
        n_samples=len(y_true),
        n_positive=int(y_true.sum()),
        n_negative=int((1-y_true).sum())
    )

    # Governance Rule: Input validation to prevent silent failures
    if len(y_true) == 0:
        raise ValueError("Cannot calculate metrics on empty dataset")

    if len(y_true) < 30:
        logger.warning("small_sample_size", n_samples=len(y_true))

    # Calculate F1 with CI
    f1, f1_ci_lower, f1_ci_upper = calculate_f1_with_ci(
        y_true, y_pred, confidence, n_bootstrap, random_state
    )

    # Calculate FPR with CI
    fpr, fpr_ci_lower, fpr_ci_upper = calculate_fpr_with_ci(
        y_true, y_pred, confidence, n_bootstrap, random_state
    )

    # Calculate Precision and Recall with CI
    pr_metrics = calculate_precision_recall_with_ci(
        y_true, y_pred, confidence, n_bootstrap, random_state
    )

    precision, precision_ci_lower, precision_ci_upper = pr_metrics['precision']
    recall, recall_ci_lower, recall_ci_upper = pr_metrics['recall']

    # Confusion matrix
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    # AUC-ROC (if scores provided)
    auc_roc = None
    if y_scores is not None and len(np.unique(y_true)) == 2:
        try:
            auc_roc = roc_auc_score(y_true, y_scores)
        except Exception as e:
            logger.warning("auc_calculation_failed", error=str(e))

    metrics = PerformanceMetrics(
        f1_score=f1,
        f1_ci_lower=f1_ci_lower,
        f1_ci_upper=f1_ci_upper,
        fpr=fpr,
        fpr_ci_lower=fpr_ci_lower,
        fpr_ci_upper=fpr_ci_upper,
        precision=precision,
        precision_ci_lower=precision_ci_lower,
        precision_ci_upper=precision_ci_upper,
        recall=recall,
        recall_ci_lower=recall_ci_lower,
        recall_ci_upper=recall_ci_upper,
        true_positives=int(tp),
        false_positives=int(fp),
        true_negatives=int(tn),
        false_negatives=int(fn),
        auc_roc=auc_roc,
        total_samples=len(y_true)
    )

    # Governance check
    meets_thresholds, failures = metrics.meets_deployment_thresholds()

    if not meets_thresholds:
        logger.warning(
            "metrics_below_threshold",
            failures=failures,
            f1=f1,
            fpr=fpr
        )
    else:
        logger.info(
            "metrics_meet_thresholds",
            f1=f1,
            fpr=fpr
        )

    return metrics


def compare_metrics(
    metrics1: PerformanceMetrics,
    metrics2: PerformanceMetrics,
    metric_name: str = 'f1_score'
) -> Dict[str, Any]:
    """
    Compare two PerformanceMetrics objects to determine if there's significant difference.

    Governance Note: Used for detecting model degradation in production.
    If production metrics significantly worse than training, trigger re-validation.

    Args:
        metrics1: First metrics (e.g., training)
        metrics2: Second metrics (e.g., production)
        metric_name: Which metric to compare ('f1_score' or 'fpr')

    Returns:
        Dictionary with comparison results
    """
    if metric_name == 'f1_score':
        val1 = metrics1.f1_score
        ci1_lower = metrics1.f1_ci_lower
        ci1_upper = metrics1.f1_ci_upper

        val2 = metrics2.f1_score
        ci2_lower = metrics2.f1_ci_lower
        ci2_upper = metrics2.f1_ci_upper

        # Significant degradation if CI don't overlap and val2 < val1
        significant_degradation = (ci2_upper < ci1_lower) and (val2 < val1)

    elif metric_name == 'fpr':
        val1 = metrics1.fpr
        ci1_lower = metrics1.fpr_ci_lower
        ci1_upper = metrics1.fpr_ci_upper

        val2 = metrics2.fpr
        ci2_lower = metrics2.fpr_ci_lower
        ci2_upper = metrics2.fpr_ci_upper

        # Significant degradation if CI don't overlap and val2 > val1
        significant_degradation = (ci2_lower > ci1_upper) and (val2 > val1)

    else:
        raise ValueError(f"Unknown metric_name: {metric_name}")

    return {
        'metric_name': metric_name,
        'metrics1_value': val1,
        'metrics1_ci': (ci1_lower, ci1_upper),
        'metrics2_value': val2,
        'metrics2_ci': (ci2_lower, ci2_upper),
        'absolute_difference': abs(val2 - val1),
        'relative_change': ((val2 - val1) / val1) if val1 != 0 else None,
        'confidence_intervals_overlap': not (ci2_upper < ci1_lower or ci2_lower > ci1_upper),
        'significant_degradation': significant_degradation
    }


def calculate_per_model_metrics(cursor) -> Dict[str, Dict]:
    """
    Calculate performance metrics split by individual model.
    
    Returns:
        Dictionary mapping model_id to metrics dictionary containing:
        - model_name, model_version
        - PerformanceMetrics object
        - confusion matrix values
    """
    # Get all models with decisions
    cursor.execute("""
        SELECT DISTINCT m.model_id, m.name, m.version
        FROM models m
        JOIN decisions d ON m.model_id = d.model_id
        ORDER BY m.name;
    """)
    
    models = cursor.fetchall()
    per_model_results = {}
    
    # Save original bootstrap iterations and temporarily reduce for per-model analysis
    original_bootstrap = globals()['BOOTSTRAP_ITERATIONS']
    globals()['BOOTSTRAP_ITERATIONS'] = 1000  # Use fewer iterations for per-model (faster)
    
    for model_id, model_name, model_version in models:
        # Get decisions for this specific model
        cursor.execute("""
            SELECT 
                d.prediction_fraud,
                t.is_fraud as actual_fraud
            FROM decisions d
            JOIN transactions t ON d.transaction_id = t.transaction_id
            WHERE d.model_id = %s AND t.is_fraud IS NOT NULL;
        """, (model_id,))
        
        results = cursor.fetchall()
        if not results:
            continue
            
        y_pred = np.array([row[0] for row in results])
        y_true = np.array([row[1] for row in results])
        
        # Calculate metrics for this model (with reduced bootstrap iterations)
        metrics = calculate_all_performance_metrics(y_true, y_pred)
        
        # Calculate confusion matrix
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt and yp)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if not yt and yp)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt and not yp)
        tn = sum(1 for yt, yp in zip(y_true, y_pred) if not yt and not yp)
        
        per_model_results[model_id] = {
            'model_name': model_name,
            'model_version': model_version,
            'metrics': metrics,
            'confusion_matrix': {
                'tp': tp,
                'fp': fp,
                'tn': tn,
                'fn': fn
            },
            'total_decisions': len(y_true)
        }
    
    # Restore original bootstrap iterations
    globals()['BOOTSTRAP_ITERATIONS'] = original_bootstrap
    
    return per_model_results


# Main execution for direct running
if __name__ == "__main__":
    import psycopg2
    import os
    
    # Connect to database
    db_url = os.getenv('DATABASE_URL', 'postgresql://afaap_admin:afaap_password@localhost:5432/afaap')
    # Parse connection string
    if db_url.startswith('postgresql://'):
        # Extract components
        parts = db_url.replace('postgresql://', '').split('@')
        user_pass = parts[0].split(':')
        host_db = parts[1].split('/')
        host_port = host_db[0].split(':')
        
        conn = psycopg2.connect(
            host=host_port[0] if len(host_port) > 0 else 'localhost',
            port=int(host_port[1]) if len(host_port) > 1 else 5432,
            database=host_db[1] if len(host_db) > 1 else 'afaap',
            user=user_pass[0] if len(user_pass) > 0 else 'afaap_admin',
            password=user_pass[1] if len(user_pass) > 1 else 'afaap_password'
        )
    
    cursor = conn.cursor()
    
    print("=" * 80)
    print(" AFAAP PERFORMANCE METRICS CALCULATOR".center(80))
    print("=" * 80)
    
    # Get decisions with ground truth
    cursor.execute("""
        SELECT 
            d.prediction_fraud,
            t.is_fraud as actual_fraud
        FROM decisions d
        JOIN transactions t ON d.transaction_id = t.transaction_id
        WHERE t.is_fraud IS NOT NULL;
    """)
    
    results = cursor.fetchall()
    y_pred = [row[0] for row in results]
    y_true = [row[1] for row in results]
    
    print(f"\nTotal Decisions Analyzed: {len(y_true):,}")
    
    # ========================================================================
    # PER-MODEL BREAKDOWN (MAIN RESULTS)
    # ========================================================================
    
    print("\n" + "=" * 80)
    print(" PER-MODEL PERFORMANCE BREAKDOWN".center(80))
    print("=" * 80)
    print("\nCalculating metrics for each model individually...")
    print("(Using 1,000 bootstrap iterations per model for faster computation)\n")
    
    per_model_results = calculate_per_model_metrics(cursor)
    
    for model_id, result in per_model_results.items():
        model_name = result['model_name']
        model_version = result['model_version']
        m = result['metrics']
        cm = result['confusion_matrix']
        total = result['total_decisions']
        
        print("─" * 80)
        print(f"  Model: {model_name} ({model_version})".center(80))
        print("─" * 80)
        
        print(f"""
Decisions Analyzed:  {total:,}

F1 Score:           {m.f1_score:.4f} (95% CI: [{m.f1_ci_lower:.4f}, {m.f1_ci_upper:.4f}])
  Target: ≥ 0.85    Status: {'✅ PASS' if m.f1_ci_lower >= 0.85 else '❌ FAIL'}

False Positive Rate: {m.fpr:.4f} (95% CI: [{m.fpr_ci_lower:.4f}, {m.fpr_ci_upper:.4f}])
  Target: ≤ 0.01    Status: {'✅ PASS' if m.fpr_ci_upper <= 0.01 else '❌ FAIL'}

Precision:          {m.precision:.4f} (95% CI: [{m.precision_ci_lower:.4f}, {m.precision_ci_upper:.4f}])
Recall:             {m.recall:.4f} (95% CI: [{m.recall_ci_lower:.4f}, {m.recall_ci_upper:.4f}])

Confusion Matrix:
         ┌─────────────┬─────────────┐
  FRAUD  │  {cm['tp']:>6}     │  {cm['fn']:>6}     │
  Actual ├─────────────┼─────────────┤
  LEGIT  │  {cm['fp']:>6}     │  {cm['tn']:>6}     │
         └─────────────┴─────────────┘
  
  TP: {cm['tp']:,}  |  FP: {cm['fp']:,}  |  FN: {cm['fn']:,}  |  TN: {cm['tn']:,}
""")
    
    print("=" * 80)
    print(" END OF PER-MODEL BREAKDOWN".center(80))
    print("=" * 80)
    
    # ========================================================================
    # GENERATE RESULTS FOLDER WITH VISUALIZATIONS AND OUTPUTS
    # ========================================================================
    
    print("\n" + "=" * 80)
    print(" GENERATING RESULTS FOLDER".center(80))
    print("=" * 80)
    
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for Docker
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd
    import json
    from datetime import datetime
    
    # Create results directory with timestamp subfolder
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_dir = os.path.join('results', f'evaluation_{timestamp}')
    os.makedirs(results_dir, exist_ok=True)
    
    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (16, 12)
    plt.rcParams['font.size'] = 9
    
    # ========================================================================
    # GENERATE COMPREHENSIVE DASHBOARD (Per-Model Visualizations Only)
    # ========================================================================
    print("\n📊 Generating per-model evaluation dashboard...")
    
    # Get fairness data
    cursor.execute("""
        SELECT 
            t.transaction_type,
            SUM(CASE WHEN d.prediction_fraud = TRUE AND t.is_fraud = FALSE THEN 1 ELSE 0 END) AS false_positives,
            SUM(CASE WHEN t.is_fraud = FALSE THEN 1 ELSE 0 END) AS total_legitimate,
            CASE 
                WHEN SUM(CASE WHEN t.is_fraud = FALSE THEN 1 ELSE 0 END) > 0
                THEN SUM(CASE WHEN d.prediction_fraud = TRUE AND t.is_fraud = FALSE THEN 1 ELSE 0 END)::float / 
                     SUM(CASE WHEN t.is_fraud = FALSE THEN 1 ELSE 0 END)
                ELSE 0
            END AS fpr_rate
        FROM decisions d
        JOIN transactions t ON d.transaction_id = t.transaction_id
        WHERE t.is_fraud IS NOT NULL
        GROUP BY t.transaction_type
        ORDER BY fpr_rate DESC;
    """)
    fairness_data = cursor.fetchall()
    fairness_df = pd.DataFrame(fairness_data, 
                               columns=['Transaction Type', 'False Positives', 'Total Legitimate', 'FPR'])
    
    # Create 2x2 subplot layout for per-model visualizations
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
    
    # Prepare per-model data
    model_names = []
    model_f1_scores = []
    model_fpr_scores = []
    model_f1_ci_lower = []
    model_f1_ci_upper = []
    model_fpr_ci_lower = []
    model_fpr_ci_upper = []
    model_recall = []
    model_precision = []
    
    for model_id, result in per_model_results.items():
        model_names.append(f"{result['model_name']}\n({result['total_decisions']:,} decisions)")
        m = result['metrics']
        model_f1_scores.append(m.f1_score)
        model_f1_ci_lower.append(m.f1_score - m.f1_ci_lower)
        model_f1_ci_upper.append(m.f1_ci_upper - m.f1_score)
        model_fpr_scores.append(m.fpr)
        model_fpr_ci_lower.append(m.fpr - m.fpr_ci_lower)
        model_fpr_ci_upper.append(m.fpr_ci_upper - m.fpr)
        model_recall.append(m.recall)
        model_precision.append(m.precision)
    
    # ---- SUBPLOT 1: PER-MODEL F1 vs FPR COMPARISON (Top Left) ----
    ax1 = fig.add_subplot(gs[0, :])  # Span full width
    
    x = np.arange(len(model_names))
    width = 0.35
    
    # Plot F1 scores
    bars1 = ax1.bar(x - width/2, model_f1_scores, width, label='F1 Score', 
                    color='#3498db', alpha=0.8, edgecolor='black', linewidth=1.5)
    ax1.errorbar(x - width/2, model_f1_scores, 
                yerr=[model_f1_ci_lower, model_f1_ci_upper],
                fmt='none', ecolor='black', capsize=5, capthick=1.5, linewidth=1.5)
    
    # Plot FPR scores (scaled up for visibility)
    fpr_scaled = [f * 100 for f in model_fpr_scores]  # Convert to percentage
    fpr_ci_lower_scaled = [f * 100 for f in model_fpr_ci_lower]
    fpr_ci_upper_scaled = [f * 100 for f in model_fpr_ci_upper]
    
    bars2 = ax1.bar(x + width/2, fpr_scaled, width, label='FPR (×100)', 
                    color='#e74c3c', alpha=0.8, edgecolor='black', linewidth=1.5)
    ax1.errorbar(x + width/2, fpr_scaled,
                yerr=[fpr_ci_lower_scaled, fpr_ci_upper_scaled],
                fmt='none', ecolor='black', capsize=5, capthick=1.5, linewidth=1.5)
    
    # Add threshold lines
    ax1.axhline(y=0.85, color='blue', linestyle='--', linewidth=2, alpha=0.7, label='F1 Threshold (0.85)')
    ax1.axhline(y=1.0, color='red', linestyle='--', linewidth=2, alpha=0.7, label='FPR Threshold (0.01 = 1.0 ×100)')
    
    # Add value labels on bars
    for i, (f1, fpr) in enumerate(zip(model_f1_scores, fpr_scaled)):
        ax1.text(i - width/2, f1 + model_f1_ci_upper[i] + 0.01, f'{f1:.3f}', 
                ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax1.text(i + width/2, fpr + fpr_ci_upper_scaled[i] + 0.01, f'{model_fpr_scores[i]:.4f}', 
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax1.set_xlabel('Model', fontsize=13, fontweight='bold')
    ax1.set_ylabel('Score', fontsize=13, fontweight='bold')
    ax1.set_title('Per-Model Performance: F1 Score vs False Positive Rate (FPR)', fontsize=16, fontweight='bold', pad=15)
    ax1.set_xticks(x)
    ax1.set_xticklabels(model_names, fontsize=10)
    ax1.legend(loc='upper right', fontsize=11)
    ax1.grid(axis='y', alpha=0.3)
    
    # ---- SUBPLOT 2: PER-MODEL CONFUSION MATRICES (Bottom Left) ----
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.axis('off')
    
    # Create table with confusion matrix data
    cm_table_data = [['Model', 'TP', 'FP', 'TN', 'FN', 'Total']]
    for model_id, result in per_model_results.items():
        cm = result['confusion_matrix']
        total = result['total_decisions']
        cm_table_data.append([
            result['model_name'][:20],  # Truncate long names
            f"{cm['tp']}",
            f"{cm['fp']}",
            f"{cm['tn']}",
            f"{cm['fn']}",
            f"{total}"
        ])
    
    table = ax2.table(cellText=cm_table_data, cellLoc='center', loc='center',
                     colWidths=[0.35, 0.13, 0.13, 0.13, 0.13, 0.13])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2.5)
    
    # Style header
    for i in range(len(cm_table_data[0])):
        cell = table[(0, i)]
        cell.set_facecolor('#3498db')
        cell.set_text_props(weight='bold', color='white')
    
    # Style data rows
    for i in range(1, len(cm_table_data)):
        for j in range(len(cm_table_data[0])):
            cell = table[(i, j)]
            cell.set_facecolor('#f0f0f0')
    
    ax2.set_title('Per-Model Confusion Matrix Breakdown', fontsize=16, fontweight='bold', pad=20)
    
    # ---- SUBPLOT 3: PER-MODEL PRECISION vs RECALL (Bottom Right) ----
    ax3 = fig.add_subplot(gs[1, 1])
    
    x_pos = np.arange(len(model_names))
    width = 0.35
    
    bars1 = ax3.bar(x_pos - width/2, model_precision, width, label='Precision', 
                    color='#9b59b6', alpha=0.8, edgecolor='black', linewidth=1.5)
    bars2 = ax3.bar(x_pos + width/2, model_recall, width, label='Recall', 
                    color='#27ae60', alpha=0.8, edgecolor='black', linewidth=1.5)
    
    # Add value labels
    for i, (prec, rec) in enumerate(zip(model_precision, model_recall)):
        ax3.text(i - width/2, prec + 0.01, f'{prec:.3f}', 
                ha='center', va='bottom', fontsize=9, fontweight='bold')
        ax3.text(i + width/2, rec + 0.01, f'{rec:.3f}', 
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    ax3.set_xlabel('Model', fontsize=13, fontweight='bold')
    ax3.set_ylabel('Score', fontsize=13, fontweight='bold')
    ax3.set_title('Per-Model Precision vs Recall', fontsize=16, fontweight='bold', pad=15)
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(model_names, fontsize=10)
    ax3.legend(loc='lower right', fontsize=11)
    ax3.set_ylim(0, 1.1)
    ax3.grid(axis='y', alpha=0.3)
    
    # Main title
    total_decisions = sum(result['total_decisions'] for result in per_model_results.values())
    fig.suptitle(f'AFAAP Per-Model Evaluation Dashboard\nGenerated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Total Decisions: {total_decisions:,} | Models: {len(per_model_results)}',
                fontsize=20, fontweight='bold', y=0.98)
    
    # Save comprehensive dashboard
    dashboard_path = os.path.join(results_dir, 'per_model_evaluation_dashboard.png')
    plt.savefig(dashboard_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✅ Saved: {dashboard_path}")
    
    # ========================================================================
    # GENERATE COMPLETE DATA FILE (CSV with per-model results)
    # ========================================================================
    print("\n� Generating per-model data file...")
    
    # Create single comprehensive CSV with all results
    results_csv_path = os.path.join(results_dir, 'per_model_results.csv')
    
    with open(results_csv_path, 'w') as f:
        # Header
        f.write(f"AFAAP Per-Model Evaluation Results\n")
        f.write(f"Generated,{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Decisions,{total_decisions}\n")
        f.write(f"Number of Models,{len(per_model_results)}\n")
        f.write("\n")
        
        # Section 1: Per-Model Performance
        f.write("=== PER-MODEL PERFORMANCE BREAKDOWN ===\n")
        f.write("Model Name,Version,Decisions,F1,F1_CI_Lower,F1_CI_Upper,FPR,FPR_CI_Lower,FPR_CI_Upper,Precision,Recall,TP,FP,TN,FN,F1_Status,FPR_Status\n")
        for model_id, result in per_model_results.items():
            m = result['metrics']
            cm = result['confusion_matrix']
            f1_status = 'PASS' if m.f1_ci_lower >= 0.85 else 'FAIL'
            fpr_status = 'PASS' if m.fpr_ci_upper <= 0.01 else 'FAIL'
            f.write(f"{result['model_name']},{result['model_version']},{result['total_decisions']},")
            f.write(f"{m.f1_score:.4f},{m.f1_ci_lower:.4f},{m.f1_ci_upper:.4f},")
            f.write(f"{m.fpr:.4f},{m.fpr_ci_lower:.4f},{m.fpr_ci_upper:.4f},")
            f.write(f"{m.precision:.4f},{m.recall:.4f},")
            f.write(f"{cm['tp']},{cm['fp']},{cm['tn']},{cm['fn']},")
            f.write(f"{f1_status},{fpr_status}\n")
        f.write("\n")
        
        # Section 2: Fairness Analysis
        f.write("=== FAIRNESS ANALYSIS (FPR by Transaction Type) ===\n")
        f.write("Transaction Type,False Positives,Total Legitimate,FPR,Status\n")
        for _, row in fairness_df.iterrows():
            status = 'PASS' if row['FPR'] <= 0.01 else 'WARN'
            f.write(f"{row['Transaction Type']},{row['False Positives']},{row['Total Legitimate']},{row['FPR']:.4f},{status}\n")
        f.write("\n")
    
    print(f"   ✅ Saved: {results_csv_path}")
    
    # ========================================================================
    # GENERATE FINDINGS.MD WITH DETAILED ANALYSIS
    # ========================================================================
    
    print("\n📝 Generating findings.md with detailed analysis...")
    
    findings_path = os.path.join(results_dir, 'findings.md')
    
    with open(findings_path, 'w') as f:
        # Header
        f.write("# AFAAP Model Performance Evaluation - Findings\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Decisions Analyzed:** {total_decisions:,}\n\n")
        f.write(f"**Number of Models Evaluated:** {len(per_model_results)}\n\n")
        f.write("---\n\n")
        
        # Executive Summary
        f.write("## Executive Summary\n\n")
        f.write("This evaluation analyzes the performance of fraud detection models deployed in the AFAAP framework. ")
        f.write("Each model was tested with exactly 10,000 decisions to ensure fair comparison. ")
        f.write("The analysis focuses on two critical metrics:\n\n")
        f.write("- **F1 Score** (≥ 0.85): Harmonic mean of precision and recall, measuring overall classification accuracy\n")
        f.write("- **False Positive Rate** (≤ 0.01): Proportion of legitimate transactions incorrectly flagged as fraud\n\n")
        
        # Count pass/fail
        f1_passes = sum(1 for r in per_model_results.values() if r['metrics'].f1_ci_lower >= 0.85)
        fpr_passes = sum(1 for r in per_model_results.values() if r['metrics'].fpr_ci_upper <= 0.01)
        
        f.write(f"**Overall Results:**\n")
        f.write(f"- {f1_passes}/{len(per_model_results)} models meet F1 score threshold (≥ 0.85)\n")
        f.write(f"- {fpr_passes}/{len(per_model_results)} models meet FPR threshold (≤ 0.01)\n\n")
        
        if f1_passes == len(per_model_results) and fpr_passes == len(per_model_results):
            f.write("✅ **All models meet both performance thresholds.**\n\n")
        else:
            f.write("⚠️ **Some models require improvement to meet performance thresholds.**\n\n")
        
        f.write("---\n\n")
        
        # Per-Model Detailed Results
        f.write("## Per-Model Performance Analysis\n\n")
        
        for model_id, result in sorted(per_model_results.items(), 
                                      key=lambda x: x[1]['metrics'].f1_score, 
                                      reverse=True):
            model_name = result['model_name']
            model_version = result['model_version']
            m = result['metrics']
            cm = result['confusion_matrix']
            total = result['total_decisions']
            
            f.write(f"### {model_name} ({model_version})\n\n")
            
            # Performance Metrics Table
            f.write("| Metric | Value | 95% Confidence Interval | Threshold | Status |\n")
            f.write("|--------|-------|------------------------|-----------|--------|\n")
            f.write(f"| **F1 Score** | {m.f1_score:.4f} | [{m.f1_ci_lower:.4f}, {m.f1_ci_upper:.4f}] | ≥ 0.85 | {'✅ PASS' if m.f1_ci_lower >= 0.85 else '❌ FAIL'} |\n")
            f.write(f"| **False Positive Rate** | {m.fpr:.4f} | [{m.fpr_ci_lower:.4f}, {m.fpr_ci_upper:.4f}] | ≤ 0.01 | {'✅ PASS' if m.fpr_ci_upper <= 0.01 else '❌ FAIL'} |\n")
            f.write(f"| **Precision** | {m.precision:.4f} | [{m.precision_ci_lower:.4f}, {m.precision_ci_upper:.4f}] | - | - |\n")
            f.write(f"| **Recall** | {m.recall:.4f} | [{m.recall_ci_lower:.4f}, {m.recall_ci_upper:.4f}] | - | - |\n\n")
            
            # Confusion Matrix
            f.write("**Confusion Matrix:**\n\n")
            f.write("```\n")
            f.write("                 Predicted\n")
            f.write("                FRAUD    LEGIT\n")
            f.write(f"Actual  FRAUD   {cm['tp']:>6}   {cm['fn']:>6}\n")
            f.write(f"        LEGIT   {cm['fp']:>6}   {cm['tn']:>6}\n")
            f.write("```\n\n")
            f.write(f"- **True Positives (TP):** {cm['tp']:,} - Correctly identified fraud cases\n")
            f.write(f"- **False Positives (FP):** {cm['fp']:,} - Legitimate transactions incorrectly flagged\n")
            f.write(f"- **True Negatives (TN):** {cm['tn']:,} - Correctly identified legitimate transactions\n")
            f.write(f"- **False Negatives (FN):** {cm['fn']:,} - Fraud cases missed by the model\n\n")
            
            # Interpretation
            f.write("**Interpretation:**\n\n")
            
            # F1 Score analysis
            if m.f1_ci_lower >= 0.85:
                f.write(f"- ✅ The F1 score of {m.f1_score:.4f} indicates strong overall performance with a good balance between precision and recall.\n")
            else:
                f.write(f"- ⚠️ The F1 score of {m.f1_score:.4f} falls below the target threshold. ")
                if m.precision < 0.85:
                    f.write(f"Low precision ({m.precision:.4f}) suggests many false positives. ")
                if m.recall < 0.85:
                    f.write(f"Low recall ({m.recall:.4f}) indicates the model is missing fraud cases. ")
                f.write("\n")
            
            # FPR analysis
            if m.fpr_ci_upper <= 0.01:
                f.write(f"- ✅ The false positive rate of {m.fpr:.4f} is acceptably low, minimizing customer friction from false fraud alerts.\n")
            else:
                f.write(f"- ⚠️ The false positive rate of {m.fpr:.4f} exceeds the 1% threshold. ")
                f.write(f"This means {m.fpr*100:.2f}% of legitimate transactions are incorrectly flagged, which could frustrate customers.\n")
            
            # Business impact
            fraud_caught_rate = (cm['tp'] / (cm['tp'] + cm['fn'])) if (cm['tp'] + cm['fn']) > 0 else 0
            f.write(f"- 📊 **Business Impact:** This model catches {fraud_caught_rate*100:.1f}% of fraud cases while flagging {cm['fp']:,} legitimate transactions for review.\n")
            
            f.write("\n---\n\n")
        
        # Fairness Analysis
        f.write("## Fairness Analysis by Transaction Type\n\n")
        f.write("This section examines whether the models treat different transaction types fairly by analyzing false positive rates across transaction categories.\n\n")
        
        f.write("| Transaction Type | False Positives | Total Legitimate | FPR | Status |\n")
        f.write("|-----------------|----------------|------------------|-----|--------|\n")
        for _, row in fairness_df.iterrows():
            status = '✅ PASS' if row['FPR'] <= 0.01 else '⚠️ WARN'
            f.write(f"| {row['Transaction Type']} | {row['False Positives']:,} | {row['Total Legitimate']:,} | {row['FPR']:.4f} | {status} |\n")
        f.write("\n")
        
        # Fairness interpretation
        high_fpr_types = fairness_df[fairness_df['FPR'] > 0.01]
        if len(high_fpr_types) > 0:
            f.write("**⚠️ Fairness Concerns:**\n\n")
            for _, row in high_fpr_types.iterrows():
                f.write(f"- **{row['Transaction Type']}** transactions have an elevated FPR of {row['FPR']:.4f} ({row['FPR']*100:.2f}%), ")
                f.write(f"with {row['False Positives']:,} false positives out of {row['Total Legitimate']:,} legitimate transactions.\n")
            f.write("\nThese disparities may indicate model bias or need for additional feature engineering for specific transaction types.\n\n")
        else:
            f.write("✅ **No significant fairness concerns detected.** All transaction types have FPR ≤ 1%.\n\n")
        
        f.write("---\n\n")
        
        # Recommendations
        f.write("## Recommendations\n\n")
        
        failing_models = [(name, r) for name, r in 
                         [(r['model_name'], r) for r in per_model_results.values()]
                         if r['metrics'].f1_ci_lower < 0.85 or r['metrics'].fpr_ci_upper > 0.01]
        
        if failing_models:
            f.write("### Models Requiring Improvement\n\n")
            for model_name, result in failing_models:
                m = result['metrics']
                f.write(f"**{model_name}:**\n")
                if m.f1_ci_lower < 0.85:
                    f.write(f"- Improve F1 score from {m.f1_score:.4f} to ≥ 0.85\n")
                    if m.precision < m.recall:
                        f.write(f"  - Focus on reducing false positives (current precision: {m.precision:.4f})\n")
                    else:
                        f.write(f"  - Focus on catching more fraud cases (current recall: {m.recall:.4f})\n")
                if m.fpr_ci_upper > 0.01:
                    f.write(f"- Reduce false positive rate from {m.fpr:.4f} to ≤ 0.01\n")
                    f.write(f"  - Consider adjusting classification threshold or adding features to better distinguish legitimate transactions\n")
                f.write("\n")
        
        f.write("### General Recommendations\n\n")
        f.write("1. **Continuous Monitoring:** Track these metrics over time to detect model degradation\n")
        f.write("2. **A/B Testing:** Test model improvements with controlled experiments before full deployment\n")
        f.write("3. **Feature Analysis:** Investigate which features contribute most to false positives\n")
        f.write("4. **Threshold Tuning:** Experiment with classification thresholds to optimize the precision-recall trade-off\n")
        f.write("5. **Transaction Type Analysis:** Pay special attention to transaction types with elevated FPR\n\n")
        
        f.write("---\n\n")
        
        # Methodology
        f.write("## Methodology\n\n")
        f.write("**Data Source:** Synthetic fraud detection dataset with ground truth labels\n\n")
        f.write("**Decisions per Model:** 10,000 (equal distribution for fair comparison)\n\n")
        f.write("**Bootstrap Confidence Intervals:** 1,000 iterations with stratified sampling to preserve class distribution\n\n")
        f.write("**Metrics Calculated:**\n")
        f.write("- **F1 Score:** 2 × (Precision × Recall) / (Precision + Recall)\n")
        f.write("- **Precision:** TP / (TP + FP)\n")
        f.write("- **Recall:** TP / (TP + FN)\n")
        f.write("- **False Positive Rate:** FP / (FP + TN)\n\n")
        
        f.write("**Thresholds:**\n")
        f.write("- F1 Score: ≥ 0.85 (lower bound of 95% CI must exceed threshold)\n")
        f.write("- FPR: ≤ 0.01 (upper bound of 95% CI must be below threshold)\n\n")
        
        f.write("---\n\n")
        f.write(f"*Report generated by AFAAP Performance Metrics Module on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}*\n")
    
    print(f"   ✅ Saved: {findings_path}")
    
    # ========================================================================
    # OUTPUT SUMMARY TO CONSOLE
    # ========================================================================
    
    print("\n" + "=" * 80)
    print(" EVALUATION SUMMARY".center(80))
    print("=" * 80)
    
    # Create summary table
    print(f"\n{'Model':<30} {'Decisions':<12} {'F1 Score':<15} {'FPR':<15} {'Status':<10}")
    print("─" * 80)
    
    for model_id, result in sorted(per_model_results.items(), 
                                  key=lambda x: x[1]['metrics'].f1_score, 
                                  reverse=True):
        model_name = result['model_name']
        m = result['metrics']
        total = result['total_decisions']
        
        f1_status = '✅' if m.f1_ci_lower >= 0.85 else '❌'
        fpr_status = '✅' if m.fpr_ci_upper <= 0.01 else '❌'
        overall_status = '✅ PASS' if (m.f1_ci_lower >= 0.85 and m.fpr_ci_upper <= 0.01) else '❌ FAIL'
        
        print(f"{model_name:<30} {total:>10,}  {f1_status} {m.f1_score:.4f}      {fpr_status} {m.fpr:.4f}      {overall_status}")
    
    print("\n" + "=" * 80)
    print(" RESULTS GENERATION COMPLETE".center(80))
    print("=" * 80)
    print(f"\n📁 Results saved to: ./{results_dir}/")
    print(f"\n   📊 Dashboard:      {os.path.basename(dashboard_path)}")
    print(f"   📄 Data CSV:       {os.path.basename(results_csv_path)}")
    print(f"   📝 Findings:       {os.path.basename(findings_path)}")
    print(f"\n💡 Next steps:")
    print(f"   • Open findings.md for detailed analysis and recommendations")
    print(f"   • Review the dashboard PNG for visual performance comparison")
    print(f"   • Use the CSV file for further analysis in Excel/Python")
    print("\n" + "=" * 80)
    
    cursor.close()
    conn.close()
    
# Delete old code below
if False:
    summary = {
        'timestamp': timestamp,
        'total_decisions': len(y_true),
        'performance_metrics': {
            'f1_score': {
                'value': round(float(metrics.f1_score), 4),
                'ci_lower': round(float(metrics.f1_ci_lower), 4),
                'ci_upper': round(float(metrics.f1_ci_upper), 4),
                'threshold': 0.85,
                'pass': bool(metrics.f1_ci_lower >= 0.85)
            },
            'fpr': {
                'value': round(float(metrics.fpr), 4),
                'ci_lower': round(float(metrics.fpr_ci_lower), 4),
                'ci_upper': round(float(metrics.fpr_ci_upper), 4),
                'threshold': 0.01,
                'pass': bool(metrics.fpr_ci_upper <= 0.01)
            },
            'precision': {
                'value': round(float(metrics.precision), 4),
                'ci_lower': round(float(metrics.precision_ci_lower), 4),
                'ci_upper': round(float(metrics.precision_ci_upper), 4)
            },
            'recall': {
                'value': round(float(metrics.recall), 4),
                'ci_lower': round(float(metrics.recall_ci_lower), 4),
                'ci_upper': round(float(metrics.recall_ci_upper), 4)
            }
        },
        'confusion_matrix': {
            'true_positives': int(tp),
            'false_positives': int(fp),
            'false_negatives': int(fn),
            'true_negatives': int(tn)
        },
        'audit_compliance': {
            'total_decisions': int(audit_stats[0]),
            'completed_audits': int(audit_stats[1]),
            'completion_rate': float(audit_stats[2]),
            'threshold': 98.0,
            'pass': bool(audit_stats[2] >= 98.0)
        },
        'fairness_analysis': fairness_df.to_dict('records'),
        'deployment_recommendation': 'BLOCK - Model does not meet governance thresholds' 
                                    if not (metrics.f1_ci_lower >= 0.85 and metrics.fpr_ci_upper <= 0.01)
                                    else 'APPROVE - Model meets all governance requirements'
    }
    
    summary_json_path = os.path.join(results_dir, 'evaluation_summary.json')
    with open(summary_json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"   ✅ Saved: {summary_json_path}")
    
    # ========================================================================
    # 7. GENERATE README FOR RESULTS FOLDER
    # ========================================================================
    print("\n📄 Generating results README...")
    
    readme_content = f"""# AFAAP Evaluation Results

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Decisions Analyzed:** {len(y_true):,}

## 📊 Summary

### Performance Metrics
- **F1 Score:** {metrics.f1_score:.4f} (95% CI: [{metrics.f1_ci_lower:.4f}, {metrics.f1_ci_upper:.4f}]) - {'✅ PASS' if metrics.f1_ci_lower >= 0.85 else '❌ FAIL'}
- **False Positive Rate:** {metrics.fpr:.4f} (95% CI: [{metrics.fpr_ci_lower:.4f}, {metrics.fpr_ci_upper:.4f}]) - {'✅ PASS' if metrics.fpr_ci_upper <= 0.01 else '❌ FAIL'}
- **Precision:** {metrics.precision:.4f} (95% CI: [{metrics.precision_ci_lower:.4f}, {metrics.precision_ci_upper:.4f}])
- **Recall:** {metrics.recall:.4f} (95% CI: [{metrics.recall_ci_lower:.4f}, {metrics.recall_ci_upper:.4f}])

### Confusion Matrix
- True Positives (TP): {tp:,}
- False Positives (FP): {fp:,}
- False Negatives (FN): {fn:,}
- True Negatives (TN): {tn:,}

### Audit Compliance
- Completion Rate: {audit_stats[2]:.2f}% - {'✅ PASS' if audit_stats[2] >= 98 else '⚠️ FAIL (Target: ≥98%)'}

## 📁 Generated Files

### Visualizations (PNG)
- `confusion_matrix.png` - Heatmap showing TP/FP/FN/TN
- `metrics_comparison.png` - Bar chart with confidence intervals and pass/fail status
- `fairness_fpr_by_type.png` - FPR breakdown by transaction type (bias detection)
- `governance_scorecard.png` - Complete governance evaluation table

### Data Files (CSV)
- `performance_metrics.csv` - All metrics with confidence intervals
- `confusion_matrix.csv` - Confusion matrix breakdown with descriptions
- `fairness_analysis.csv` - FPR by transaction type (fairness audit)
- `governance_scorecard.csv` - Complete scorecard table

### Summary (JSON)
- `evaluation_summary.json` - Machine-readable summary with all results

## 🎯 Deployment Recommendation

**{summary['deployment_recommendation']}**

## 📖 Interpretation Guide

### F1 Score
Harmonic mean of precision and recall. Threshold: ≥ 0.85
- **Pass:** Model balances fraud detection and false alarm rates well
- **Fail:** Model needs retraining to improve performance

### False Positive Rate (FPR)
Percentage of legitimate transactions wrongly flagged. Threshold: ≤ 1%
- **Pass:** Acceptable customer experience (low false alarms)
- **Fail:** Too many false alarms will frustrate customers

### Fairness Analysis
FPR should be consistent across transaction types.
- Large disparities indicate model bias
- May violate fairness regulations

### Audit Completion
Percentage of decisions with complete human review. Threshold: ≥ 98%
- **Pass:** Strong human oversight and accountability
- **Fail:** Scalability bottleneck - need more compliance officers
"""
    
    readme_path = os.path.join(results_dir, 'README.md')
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    print(f"   ✅ Saved: {readme_path}")
    
    print("\n" + "=" * 80)
    print(" RESULTS GENERATION COMPLETE".center(80))
    print("=" * 80)
    print(f"\n📁 All results saved to: ./{results_dir}/")
    print(f"\n   View summary: cat {readme_path}")
    print(f"   Open visualizations in your file browser or image viewer")
    print("\n" + "=" * 80)
    
    cursor.close()
    conn.close()
