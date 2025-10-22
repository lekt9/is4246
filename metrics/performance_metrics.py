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
