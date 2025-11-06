# AFAAP Governance Framework

## AI Financial Accountability and Auditability Protocol

A production-ready governance framework for AI-powered fraud detection systems in financial institutions, designed to operationalize regulatory compliance under Singapore's MAS oversight.

---

## Background & Purpose

### The Problem

Financial institutions deploying AI-driven fraud detection systems face several governance and accountability challenges that threaten both operational integrity and regulatory compliance. Many models are launched without standardized validation processes, leading to inconsistencies in performance and reliability across institutions. The opaque, “black box” nature of these systems further complicates oversight, as flagged transactions often lack clear, explainable audit trails. Over time, undetected model drift can degrade fraud detection accuracy, increasing both false positives and false negatives. Compounding these issues are regulatory gaps — with incomplete documentation and weak traceability making it difficult for institutions to meet MAS compliance requirements. Together, these challenges highlight the urgent need for a robust, auditable framework that enforces accountability, transparency, and continuous monitoring across the AI model lifecycle.

### Our Solution

AFAAP provides a **complete governance framework** that:

1. **Validates models** before deployment (F1 ≥ 0.85, FPR ≤ 1% thresholds)
2. **Logs every AI decision** with immutable audit trails (blockchain-style hashing)
3. **Monitors performance drift** and triggers re-validation workflows
4. **Enforces human oversight** through compliance officer reviews
5. **Demonstrates regulatory compliance** with complete audit documentation

See [FINDINGS.md](docs/FINDINGS.md) for complete validation results.

## Overview

AFAAP implements a comprehensive governance mechanism based on the **Three Lines of Defense (3LOD)** model:

**First Line (Development Team)**

- Model development and initial testing
- Performance metric tracking
- Issue detection and reporting

**Second Line (Compliance Officers)**

- Pre-deployment approval
- Human-in-the-loop review of flagged transactions
- Re-validation oversight

**Third Line (Independent Auditors)**

- Quarterly compliance audits
- Incident investigation
- Regulatory reporting

### Core Governance Metrics Requirements

- **Pre-deployment validation** with F1 ≥ 0.85 and FPR ≤ 1% thresholds
- **Continuous decision logging** with ≥98% audit trail completion
- **Model re-validation protocols** for new use cases
- **Human-in-the-loop workflows** for compliance officer review
- **Immutable audit trails** for regulatory inspection

## Key Features

### 1. Database Schema

- Comprehensive models for ML model metadata, decisions, audit trails, revalidation, and incidents
- Append-only logging for tamper-proof audit trails
- Role-based access control (RBAC) markers
- Foreign key relationships showing accountability chains

### 2. Metrics Pipeline

- F1 Score computation with 95% confidence intervals
- False Positive Rate (FPR) tracking with fairness breakdowns
- Audit Trail Completion Rate monitoring
- Review Turnaround Time analysis
- Fairness audits by transaction type and geography

### 3. Governance Decision Engine

- Automated model performance evaluation against thresholds
- Re-validation workflow triggers for repurposed models
- Failure escalation to independent auditor roles
- Compliance checklist generation for pre-deployment approval

---

## Running this on own local machine

## The fastest way to run this project is using **Docker** (avoids Python 3.13 compatibility issues):

## Installation

### Prerequisites

- **Python 3.10-3.12** (⚠️ Python 3.13 not supported due to numpy compatibility)
- **PostgreSQL 14+**
- **Docker & Docker Compose** (recommended)

### Step-by-Step Setup

See [setup.md](setup.md) for comprehensive instructions. Here's a summary:

#### Option 1: Docker (Recommended)

```bash
# 1. Start services
docker-compose up -d

# 2. Apply migrations and generate data
docker exec -i afaap-app psql postgresql://afaap_admin:afaap_password@postgres:5432/afaap < schema/001_initial_schema.sql
docker exec afaap-app python data/synthetic_dataset_generator.py

# 3. View results
docker exec afaap-app python metrics/performance_metrics.py
```

#### Option 2: Local Installation

```bash
# 1. Create virtual environment (use Python 3.10-3.12)
python3.12 -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up PostgreSQL (example for macOS with Homebrew)
brew install postgresql@14
brew services start postgresql@14
createdb afaap
psql afaap -c "CREATE USER afaap_admin WITH PASSWORD 'afaap_password';"
psql afaap -c "GRANT ALL PRIVILEGES ON DATABASE afaap TO afaap_admin;"

# 4. Create .env file
cat > .env << 'EOF'
DATABASE_URL=postgresql://afaap_admin:afaap_password@localhost:5432/afaap
API_SECRET_KEY=your-secret-key-here
GOVERNANCE_F1_THRESHOLD=0.85
GOVERNANCE_FPR_THRESHOLD=0.01
GOVERNANCE_AUDIT_COMPLETION_THRESHOLD=98
EOF

# 5. Run database migrations
psql postgresql://afaap_admin:afaap_password@localhost:5432/afaap -f schema/001_initial_schema.sql
psql postgresql://afaap_admin:afaap_password@localhost:5432/afaap -f schema/002_audit_trail_extensions.sql
psql postgresql://afaap_admin:afaap_password@localhost:5432/afaap -f schema/003_indexes_and_constraints.sql

# 6. Generate synthetic data and run simulation
python data/synthetic_dataset_generator.py


# 7. Calculate performance metrics (use Docker if on Python 3.13)
docker exec afaap-app python metrics/performance_metrics.py
```

## Validation Plan

### Overview: Two-Stage Process

The validation uses **two separate tools** that work in sequence:

```
Step 1: synthetic_dataset_generator.py → Creates test data and runs simualtion with 2 simulated AI fraud test models.
                    ↓
            PostgreSQL Database
                    ↓
Step 2: performance_metrics.py → Analyzes performance metrics based on such results.
```

---

### Stage 1: Synthetic Data Generation

**File:** `data/synthetic_dataset_generator.py`  
**Purpose:** Creates realistic fake data to simulate 6 months of fraud detection in production

#### What Gets Created:

**1. Users (20 total)**

- 5 Developers (First Line of Defense)
- 10 Compliance Officers (Second Line of Defense)
- 5 Independent Auditors (Third Line of Defense)

**2. Models (5 AI fraud detection models)**

```python
# 3 deployed models currently in use
fraud_detector_v1: hardcoded_fpr=0.0095, deployed=True
fraud_detector_v2: hardcoded_fpr=0.0120, deployed=True
fraud_detector_v3: hardcoded_fpr=0.0085, deployed=True

# 2 experimental models in testing
experimental_ml_model_v1: hardcoded_fpr=0.0200, deployed=False
experimental_ml_model_v2: hardcoded_fpr=0.0150, deployed=False
```

**3. Transactions (10,000 total)**

```python
# Realistic distribution
500 fraudulent (5% fraud rate - typical for banking)
9,500 legitimate (95% legitimate transactions)

# Types generated:
- Wire transfers ($1,000 - $500,000)
- Credit card purchases ($10 - $10,000)
- ACH transfers ($100 - $50,000)
- Mobile payments ($5 - $5,000)
- Cryptocurrency ($50 - $1,000,000)
- ATM withdrawals ($20 - $2,000)

# Edge cases included:
- High-value transactions (>$1M)
- Micro-transactions (<$10)
- Cross-border high-risk corridors
- Same-day reversals (fraud pattern)
```

**4. Decisions (8,000 model predictions)**

This is the **core simulation** - how model predictions are generated:

```python
# For each transaction, model makes a prediction
for transaction in transactions:
    # Get ground truth
    actual_fraud = transaction.is_fraud  # TRUE or FALSE

    # SIMULATE MODEL PREDICTION using probability rules
    if actual_fraud == True:
        # Real fraud: Model catches it 85% of the time (RECALL = 0.85)
        prediction_fraud = random.random() < 0.85
        confidence = random.uniform(0.7, 0.95) if caught else random.uniform(0.3, 0.6)

    elif actual_fraud == False:
        # Legitimate: Model correctly identifies 99% (FPR = 1%)
        prediction_fraud = random.random() < 0.01  # Only 1% false alarms
        confidence = random.uniform(0.1, 0.4) if flagged else random.uniform(0.05, 0.3)

    # Generate explainability (SHAP-like feature importance)
    model_features = {
        'amount_zscore': 0.45,        # How unusual is the amount?
        'velocity_24h': 7,            # Transactions in last 24 hours
        'country_risk_score': 0.8,   # Destination country risk
        'merchant_category_risk': 0.6 # Merchant type risk
    }

    # Human review (Compliance Officer)
    if prediction_fraud and confidence > 0.6:
        # 90% of flagged transactions get reviewed
        if random.random() < 0.9:
            officer = select_random_officer()

            # Officer decides based on situation:
            if actual_fraud and prediction_fraud:
                # TRUE POSITIVE: Model correct
                officer_decision = 'block_transaction' (80%) or 'escalate' (20%)

            elif not actual_fraud and prediction_fraud:
                # FALSE POSITIVE: Model wrong
                officer_decision = 'approve_transaction' (60%) or 'false_positive' (30%) or 'escalate' (10%)

            final_decision = 'blocked' or 'approved' or 'escalated'
        else:
            # 10% not reviewed yet (workload bottleneck)
            final_decision = 'pending'

    # Store complete decision record
    INSERT INTO decisions (
        prediction_fraud,      # Model's verdict
        confidence_score,      # Model's confidence
        model_features,        # Risk factors (JSON)
        reviewed_by,           # Officer user_id
        officer_decision,      # Human decision
        officer_notes,         # Explanation
        final_decision,        # Outcome: approved/blocked/escalated/pending
        audit_trail_hash      # SHA256 tamper-proof hash
    )
```

**Expected Confusion Matrix from Generator:**

```
                Actual Fraud    Actual Legitimate
Predicted Fraud    ~333 (TP)         ~77 (FP)
Predicted Safe     ~66 (FN)        ~7,524 (TN)

TP (True Positive):  85% of 500 frauds × 0.8 coverage = 333 caught
FP (False Positive): 1% of 9,500 legit × 0.8 coverage = 77 false alarms
FN (False Negative): 15% of 500 frauds × 0.8 coverage = 66 missed
TN (True Negative):  99% of 9,500 legit × 0.8 coverage = 7,524 correct
```

**Data Integrity Features:**

- **Audit trail hash:** SHA256 hash prevents tampering
- **Foreign key constraints:** All decisions link to valid transactions/models/users
- **Timestamps:** Flag time, review time (1-120 hours turnaround)
- **Explainability:** Every decision has feature importance values

---

### 📊 Stage 2: Performance Metrics Analysis

**File:** `metrics/performance_metrics.py`  
**Purpose:** Reads the generated decisions and calculates statistical performance metrics

#### How It Works:

**1. Data Extraction**

```python
# Connect to database
conn = psycopg2.connect(DATABASE_URL)

# Query decisions with ground truth
query = """
    SELECT
        d.prediction_fraud,    -- What did model predict?
        t.is_fraud            -- What was actual truth?
    FROM decisions d
    JOIN transactions t ON d.transaction_id = t.transaction_id
    WHERE d.model_id = %s
"""

results = cursor.execute(query, (model_id,))

# Convert to numpy arrays for analysis
y_pred = np.array([row[0] for row in results])  # [True, False, True, ...]
y_true = np.array([row[1] for row in results])  # [True, False, False, ...]
```

**2. F1 Score Calculation**

F1 combines Precision and Recall into a single metric:

```python
# Calculate confusion matrix
TP = sum((y_pred == True) & (y_true == True))   # 333 frauds caught
FP = sum((y_pred == True) & (y_true == False))  # 77 false alarms
FN = sum((y_pred == False) & (y_true == True))  # 66 frauds missed
TN = sum((y_pred == False) & (y_true == False)) # 7,524 correct approvals

# Calculate metrics
Precision = TP / (TP + FP) = 333 / (333 + 77) = 0.8122
           "Of flagged transactions, how many are actually fraud?"

Recall = TP / (TP + FN) = 333 / (333 + 66) = 0.8346
        "Of actual frauds, how many did we catch?"

F1 Score = 2 × (Precision × Recall) / (Precision + Recall)
         = 2 × (0.8122 × 0.8346) / (0.8122 + 0.8346)
         = 0.8232
```

**3. False Positive Rate Calculation**

```python
FPR = FP / (FP + TN) = 77 / (77 + 7524) = 0.0101 = 1.01%
     "Of legitimate transactions, how many did we wrongly flag?"
```

**4. Bootstrap Confidence Intervals**

The **±0.0246** in F1=0.8232±0.0246 comes from statistical resampling:

```python
# 10,000 iterations for statistical rigor
bootstrap_scores = []
for i in range(10000):
    # Randomly resample predictions WITH REPLACEMENT
    indices = np.random.randint(0, len(y_pred), len(y_pred))
    y_pred_sample = y_pred[indices]
    y_true_sample = y_true[indices]

    # Calculate F1 for this sample
    f1_sample = f1_score(y_true_sample, y_pred_sample)
    bootstrap_scores.append(f1_sample)

# 95% confidence interval (2.5th to 97.5th percentile)
ci_lower = np.percentile(bootstrap_scores, 2.5)   # 0.7986
ci_upper = np.percentile(bootstrap_scores, 97.5)  # 0.8478

# Result: F1 = 0.8232 with 95% CI [0.7986, 0.8478]
# Meaning: We're 95% confident true F1 is between 0.7986 and 0.8478
```

**Why Bootstrap?**

- Accounts for **sampling variability**
- Provides **statistical rigor** required by MAS regulations
- Ensures metrics are **robust**, not just lucky

**5. Threshold Validation**

```python
# Governance rules from environment
MIN_F1_SCORE = 0.85
MAX_FPR = 0.01

# Check thresholds
if f1_score < MIN_F1_SCORE:
    status = "❌ FAIL"
    action = "Model deployment BLOCKED - requires retraining"

if fpr > MAX_FPR:
    status = "❌ FAIL"
    action = "Model deployment BLOCKED - too many false alarms"

# Also check confidence intervals
if f1_ci_lower < MIN_F1_SCORE:
    status = "❌ FAIL"
    reason = "Even in best case, F1 might drop below threshold"
```

**6. Fairness Analysis**

```python
# Break down FPR by transaction type
SELECT
    transaction_type,
    SUM(CASE WHEN prediction_fraud AND NOT is_fraud THEN 1 ELSE 0 END) AS false_positives,
    SUM(CASE WHEN NOT is_fraud THEN 1 ELSE 0 END) AS total_legitimate,
    (false_positives::float / total_legitimate) AS fpr_rate
FROM decisions d
JOIN transactions t ON d.transaction_id = t.transaction_id
GROUP BY transaction_type

# Results show bias:
wire_transfer:  FPR = 0.0182 (1.82% false alarm rate)
credit_card:    FPR = 0.0028 (0.28% false alarm rate)
# Disparity: wire transfers flagged 6.5x more often!
```

**7. Performance Drift Detection**

```python
# Compare model's claimed FPR vs actual FPR
hardcoded_fpr = 0.0095  # From models table (what model claims)
calculated_fpr = 0.0101 # From actual predictions (what model does)

drift_percentage = (calculated_fpr - hardcoded_fpr) / hardcoded_fpr × 100
                 = (0.0101 - 0.0095) / 0.0095 × 100
                 = 6.2% degradation

if drift_percentage > 5%:
    alert = "⚠️ Model performance has degraded - re-validation required"
```

---

### 🎯 How They Work Together

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. SYNTHETIC DATA GENERATOR (Data Creation)                        │
├─────────────────────────────────────────────────────────────────────┤
│ Input:  None (generates from scratch)                              │
│ Process:                                                            │
│   - Create 10,000 transactions (500 fraud, 9,500 legit)           │
│   - Simulate 8,000 predictions (85% recall, 1% FPR)               │
│   - Generate officer reviews (approve/block/escalate)              │
│   - Insert into PostgreSQL with audit trails                       │
│ Output: Populated database with realistic governance data          │
├─────────────────────────────────────────────────────────────────────┤
│                              ↓                                      │
│                    PostgreSQL Database                              │
│         Tables: transactions, decisions, models, users              │
│                              ↓                                      │
├─────────────────────────────────────────────────────────────────────┤
│ 2. PERFORMANCE METRICS (Data Analysis)                             │
├─────────────────────────────────────────────────────────────────────┤
│ Input:  Decisions from database                                    │
│ Process:                                                            │
│   - Extract predictions (y_pred) and ground truth (y_true)         │
│   - Calculate F1 = 0.8232, FPR = 0.0101                           │
│   - Bootstrap 10,000 samples → CI = ±0.0246                       │
│   - Compare against thresholds (F1≥0.85, FPR≤0.01)                │
│   - Detect drift (6.2% degradation)                                │
│   - Analyze fairness (84.6% FPR disparity)                         │
│ Output: Statistical dashboard with pass/fail status                │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Insight:**

- Generator uses **probability rules** to simulate predictions (85% catch rate)
- Metrics tool uses **actual math** to calculate if we achieved 85%
- Result: F1=0.8232 (close to 0.85 target, but slightly below due to randomness)
- This proves the framework **correctly detects underperforming models**

---

### 📈 What Makes This Validation Rigorous?

**1. Realistic Data Distribution**

- 5% fraud rate (matches real banking data)
- Edge cases: high-value, micro-transactions, cross-border
- Human review workflows with realistic turnaround times

**2. Statistical Rigor**

- Bootstrap confidence intervals (10,000 iterations)
- Not just point estimates - accounts for uncertainty
- Both point estimate AND confidence bounds must meet thresholds

**3. Complete Audit Trail**

- Every decision has SHA256 hash (tamper-proof)
- All foreign keys enforced (no orphaned records)
- Timestamps track full workflow (flag → review → decision)

**4. Three Lines of Defense**

- Model predictions (First Line)
- Officer reviews (Second Line)
- Auditor escalations (Third Line)
- All roles tracked with user_id accountability

**5. Multi-Dimensional Analysis**

- Performance: F1, FPR, Precision, Recall
- Fairness: FPR by transaction type
- Drift: Hardcoded vs calculated FPR comparison
- Process: Audit completion rate, review turnaround time

---

````

## Governance Rules

### Pre-Deployment Validation
- F1 Score ≥ 0.85 (with 95% confidence interval)
- False Positive Rate ≤ 1%
- Audit trail completion ≥ 98%
- Safety case documentation required

### Re-Validation Triggers
- Model repurposed to new fraud type
- Performance degradation below thresholds
- Significant data distribution shift
- Regulatory requirement changes

### Failure Escalation
- F1 < 0.85 OR FPR > 1% → Alert + Escalation
- Audit trail completion < 98% → Compliance gap flag
- Review Turnaround Time > 5 days → Workflow investigation
- Model failure → Incident log + Auditor sign-off required

## Configuration

Key governance thresholds are configurable via environment variables:

```bash
# Governance thresholds
AFAAP_MIN_F1_SCORE=0.85
AFAAP_MAX_FPR=0.01
AFAAP_MIN_AUDIT_COMPLETION=0.98
AFAAP_MAX_REVIEW_TURNAROUND_DAYS=5

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/afaap

# API
API_SECRET_KEY=your-secret-key
API_ACCESS_TOKEN_EXPIRE_MINUTES=30
````

## Documentation

- [Setup Guide](setup.md) - Installation and environment setup
- [Schema Documentation](schema/README.md) - Database design with ER diagrams
- [Governance Workflows](docs/governance_workflows.md) - Step-by-step process guides
- [API Specification](docs/api_spec.md) - REST API documentation
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions
