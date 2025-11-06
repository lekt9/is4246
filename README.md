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

These transactions are to mimic real life transactions.

**4. Decisions (8,000 model predictions)**

This is the core simulation - how model predictions are generated:

Model prediction simulation –

Select models and sample transactions – The function retrieves the first three deployed models and their performance metrics (recall and false positive rate) from the database. The transaction set of 10000 transactions is then prepared.

Simulate model predictions – For each sampled transaction:

For each transaction, the system checks whether it’s an actual fraud case (is_fraud = True).

If it is fraud, the model correctly flags it x% of the time, where x is the recall rate (recall = x).

If it is legitimate, the model only incorrectly flags it according to its false positive rate (e.g., 1%).

A confidence score is randomly generated to represent how certain the model is in its prediction.

Explainability generation – Each prediction includes a dictionary of key model features (e.g., transaction amount, velocity, country risk, merchant category). These act like SHAP values, showing which factors influenced the decision and how risky they were.

Human-in-the-loop review – If the model predicts fraud with high confidence (>0.6), a compliance officer reviews the case 90% of the time.

The officer then decides whether to block, approve, or escalate the transaction based on the situation (e.g., true positive or false positive).

About 10% of flagged cases remain pending due to workload.

Audit logging – Finally, each transaction’s details (model prediction, confidence, human decision, and risk features) are stored in a database, along with a cryptographic hash to prevent tampering.

Then after, the validation metrics module will extract all these useful information and present export it into a csv for our review. the data will be savedx under /results/evaluation_xxxxxxx_xxxxx.

### How They Work Together

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

### Performance Evaluation Results

See [FINDINGS.md](docs/FINDINGS.md) for sample validation results and detailed analysis - consisting of a csv file, dahsboard and and findings.md file which showcases the results.
