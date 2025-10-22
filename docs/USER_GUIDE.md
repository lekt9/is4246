# AFAAP User Guide: Complete Governance Framework

## AI Financial Accountability and Auditability Protocol

**Version**: 1.0.0
**Target Audience**: Compliance Officers, Auditors, Developers, Regulators
**Regulatory Context**: Singapore Monetary Authority (MAS) AI Governance

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [How AFAAP Works](#how-afaap-works)
4. [User Roles and Responsibilities](#user-roles-and-responsibilities)
5. [Core Workflows](#core-workflows)
6. [Inputs and Outputs](#inputs-and-outputs)
7. [Understanding the Data](#understanding-the-data)
8. [Key Findings from Synthetic Data](#key-findings-from-synthetic-data)
9. [Governance Thresholds and Rules](#governance-thresholds-and-rules)
10. [Audit Trail System](#audit-trail-system)
11. [Querying the Database](#querying-the-database)
12. [Compliance Reporting](#compliance-reporting)
13. [Troubleshooting](#troubleshooting)

---

## Executive Summary

### What is AFAAP?

AFAAP is a **regulatory compliance framework** for AI-powered fraud detection systems used in financial institutions. It implements the **Three Lines of Defense (3LOD)** model to ensure:

- **Accountability**: Every decision is traceable to a person
- **Auditability**: Complete, immutable audit trails
- **Performance**: Models meet minimum thresholds (F1 ≥ 0.85, FPR ≤ 1%)
- **Fairness**: Models are tested across demographics and transaction types
- **Governance**: Re-validation required when models are repurposed

### Why Does AFAAP Exist?

**Problem**: AI fraud detection models can fail in unpredictable ways:
- False positives block legitimate customers
- False negatives allow fraud to slip through
- Models drift over time without monitoring
- Accountability is unclear when failures occur

**Solution**: AFAAP creates a **complete paper trail** from model development → deployment → production monitoring → failure response.

### Who Should Use This Guide?

| Role | Why Read This Guide |
|------|---------------------|
| **Compliance Officer** | Understand approval workflows and monitoring requirements |
| **Auditor** | Learn how to verify audit trails and investigate incidents |
| **Developer** | Understand deployment requirements and documentation standards |
| **Regulator** | Review framework compliance with MAS guidelines |
| **Executive** | Understand governance controls and risk management |

---

## System Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AFAAP Governance Framework                    │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   DEVELOPER  │      │  COMPLIANCE  │      │   AUDITOR    │
│  (1st Line)  │ ───> │   OFFICER    │ ───> │  (3rd Line)  │
│              │      │  (2nd Line)  │      │              │
└──────────────┘      └──────────────┘      └──────────────┘
       │                     │                      │
       │                     │                      │
       ▼                     ▼                      ▼
┌─────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Models    │  │  Decisions  │  │Audit Trails │    │
│  │             │  │             │  │ (Immutable) │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │Transactions │  │ Revalidation│  │  Incidents  │    │
│  │             │  │             │  │             │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### Components

1. **Database Schema** (PostgreSQL)
   - 9 core tables
   - Immutable audit trail system
   - Materialized views for performance
   - 50+ governance constraints

2. **Metrics Engine** (Python)
   - F1 Score, FPR with confidence intervals
   - Fairness metrics by subgroup
   - Process metrics (audit completion, turnaround time)

3. **Governance Engine** (Python)
   - Pre-deployment validation
   - Re-validation triggers
   - Failure escalation logic

4. **API** (FastAPI) - *Coming Soon*
   - REST endpoints for compliance queries
   - Role-based access control

5. **Dashboard** (Streamlit) - *Coming Soon*
   - Real-time metrics visualization
   - Compliance status monitoring

---

## How AFAAP Works

### The Three Lines of Defense (3LOD)

AFAAP implements a military-style defense model where **three independent groups** check each other's work:

#### 1st Line: Developers
**What they do**: Build and test fraud detection models

**Responsibilities**:
- Train models on historical data
- Calculate performance metrics (F1, FPR, precision, recall)
- Document training data provenance
- Submit models for approval

**Example**: Alice (developer) trains a credit card fraud detector on 100,000 transactions from Q1 2024. She achieves F1=0.89, FPR=0.8%. She documents the dataset source and submits for approval.

#### 2nd Line: Compliance Officers
**What they do**: Review and approve models before deployment

**Responsibilities**:
- Verify models meet thresholds (F1 ≥ 0.85, FPR ≤ 1%)
- Review training data documentation
- Check fairness across demographics
- Approve or reject deployment
- Review flagged transactions in production

**Example**: Bob (compliance officer) reviews Alice's model. He verifies F1=0.89 ≥ 0.85 ✓ and FPR=0.8% ≤ 1% ✓. He checks fairness metrics and approves deployment.

#### 3rd Line: Auditors
**What they do**: Independent oversight and investigation

**Responsibilities**:
- Verify audit trails are complete
- Investigate model failures
- Sign off on incident remediation
- Report to regulators
- Quarterly compliance audits

**Example**: Carol (auditor) investigates why the model missed 12 fraudulent wire transfers. She reviews the audit trail, identifies root cause (fraudsters adapted technique), verifies remediation plan, and signs off on incident closure.

### The Model Lifecycle

```
┌─────────────┐
│  DEVELOP    │  Developer trains model on historical data
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  VALIDATE   │  Calculate F1, FPR, confidence intervals
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   SUBMIT    │  Submit to compliance for approval
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   REVIEW    │  Compliance officer checks thresholds
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
   ▼       ▼
APPROVE  REJECT ───> Back to developer
   │
   ▼
┌─────────────┐
│  DEPLOY     │  Model goes live in production
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  MONITOR    │  Continuous performance tracking
└──────┬──────┘
       │
   ┌───┴────┐
   │        │
   ▼        ▼
  OK    DEGRADED ───> Trigger re-validation
                          │
                          ▼
                     INVESTIGATE
                          │
                          ▼
                      REMEDIATE
                          │
                          ▼
                   AUDITOR SIGN-OFF
```

---

## User Roles and Responsibilities

### Developer Role

**Database Access**: Read/write to `models`, read-only to `transactions`

**Key Tasks**:

1. **Train Models**
   ```python
   # Example: Calculate metrics before submission
   from metrics.performance_metrics import calculate_all_performance_metrics

   metrics = calculate_all_performance_metrics(
       y_true=ground_truth,
       y_pred=model_predictions,
       y_scores=confidence_scores
   )

   print(f"F1: {metrics.f1_score:.4f} [{metrics.f1_ci_lower:.4f}, {metrics.f1_ci_upper:.4f}]")
   print(f"FPR: {metrics.fpr:.4f} [{metrics.fpr_ci_lower:.4f}, {metrics.fpr_ci_upper:.4f}]")
   ```

2. **Document Training Data**
   ```sql
   INSERT INTO models (
       name, version, training_data_provenance,
       f1_score, fpr, developed_by
   ) VALUES (
       'fraud_detector_v1', 'v1.0.0',
       'transactions_2024_q1_production (100,000 records, Jan-Mar 2024)',
       0.89, 0.008, '<developer_user_id>'
   );
   ```

3. **Submit for Approval**
   - Status changes from `pending_approval` → waiting for compliance

4. **Investigate Failures**
   - When incidents occur, analyze root cause
   - Propose remediation plan
   - Re-train if needed

**Success Criteria**:
- Model meets F1 ≥ 0.85 and FPR ≤ 1%
- Training data fully documented
- Confidence intervals calculated

---

### Compliance Officer Role

**Database Access**: Read-only to `models`, read/write to `decisions`, `revalidation_workflows`

**Key Tasks**:

1. **Approve Models**
   ```sql
   -- Check if model meets thresholds
   SELECT * FROM validate_deployment_thresholds('<model_id>');

   -- If approved:
   UPDATE models
   SET status = 'approved',
       approved_by = '<officer_user_id>'
   WHERE model_id = '<model_id>';
   ```

2. **Review Flagged Transactions**
   ```sql
   -- View pending decisions
   SELECT * FROM compliance_officer_queue
   ORDER BY hours_pending DESC
   LIMIT 20;

   -- Make decision
   UPDATE decisions
   SET reviewed_by = '<officer_user_id>',
       officer_decision = 'approve_transaction',
       officer_notes = 'Customer verified. Legitimate business transaction.',
       decision_timestamp = CURRENT_TIMESTAMP
   WHERE decision_id = '<decision_id>';
   ```

3. **Monitor Audit Completion**
   ```sql
   -- Check audit trail completion rate
   SELECT
       COUNT(*) FILTER (WHERE audit_trail_complete) AS complete,
       COUNT(*) AS total,
       ROUND(
           COUNT(*) FILTER (WHERE audit_trail_complete)::NUMERIC / COUNT(*) * 100,
           2
       ) AS completion_rate_pct
   FROM decisions;

   -- Target: ≥ 98%
   ```

4. **Trigger Re-validation**
   ```sql
   INSERT INTO revalidation_workflows (
       model_id, trigger_reason, trigger_details, triggered_by
   ) VALUES (
       '<model_id>',
       'new_fraud_type',
       'Model being extended to detect synthetic identity fraud',
       '<officer_user_id>'
   );
   ```

**Success Criteria**:
- All pending decisions reviewed within 5 days
- Audit trail completion ≥ 98%
- All model approvals documented

---

### Auditor Role

**Database Access**: Full read access to all tables, write access to `failure_incidents`

**Key Tasks**:

1. **Verify Audit Integrity**
   ```sql
   -- Check blockchain-style audit chain
   SELECT * FROM verify_audit_integrity('decisions', '<decision_id>');

   -- Expected output:
   -- is_valid | broken_chain_at | message
   -- ----------+-----------------+--------------------------------------
   -- TRUE      | NULL            | Audit trail integrity verified
   ```

2. **Investigate Incidents**
   ```sql
   -- View open incidents
   SELECT * FROM auditor_incident_queue
   WHERE requires_signoff = TRUE;

   -- Review root cause analysis
   SELECT
       incident_id,
       failure_type,
       root_cause,
       remediation_plan,
       remediation_status
   FROM failure_incidents
   WHERE incident_id = '<incident_id>';
   ```

3. **Sign Off on Remediation**
   ```sql
   UPDATE failure_incidents
   SET auditor_signoff_by = '<auditor_user_id>',
       auditor_signoff_date = CURRENT_TIMESTAMP,
       auditor_notes = 'Remediation verified. Model performance restored.',
       remediation_status = 'closed'
   WHERE incident_id = '<incident_id>';
   ```

4. **Generate Compliance Reports**
   ```sql
   -- Quarterly audit summary
   SELECT
       m.name,
       m.f1_score AS training_f1,
       mps.true_positives,
       mps.false_positives,
       mps.audit_completion_rate,
       mps.avg_turnaround_days
   FROM models m
   JOIN model_performance_summary mps ON m.model_id = mps.model_id
   WHERE m.status = 'deployed';
   ```

**Success Criteria**:
- All audit trails verified quarterly
- All incidents signed off within 30 days
- No tampering detected in audit chains

---

## Core Workflows

### Workflow 1: Pre-Deployment Model Approval

**Scenario**: Developer submits a new fraud detection model for approval.

**Steps**:

1. **Developer: Train and Test**
   ```bash
   # Calculate performance metrics
   docker exec afaap-app python -c "
   from metrics.performance_metrics import calculate_all_performance_metrics
   import numpy as np

   # Load your model predictions
   y_true = np.load('ground_truth.npy')
   y_pred = np.load('predictions.npy')
   y_scores = np.load('confidence_scores.npy')

   metrics = calculate_all_performance_metrics(y_true, y_pred, y_scores)

   meets_thresholds, failures = metrics.meets_deployment_thresholds()
   print(f'Meets thresholds: {meets_thresholds}')
   print(f'F1: {metrics.f1_score:.4f}')
   print(f'FPR: {metrics.fpr:.4f}')
   "
   ```

2. **Developer: Document Model**
   ```sql
   INSERT INTO models (
       name,
       version,
       description,
       training_data_provenance,
       training_start_date,
       training_end_date,
       training_record_count,
       f1_score,
       fpr,
       precision_score,
       recall_score,
       f1_ci_lower,
       f1_ci_upper,
       fpr_ci_lower,
       fpr_ci_upper,
       model_type,
       fraud_types_targeted,
       status,
       developed_by
   ) VALUES (
       'fraud_detector_v3',
       'v3.0.0',
       'Enhanced model for credit card and wire fraud detection',
       'transactions_2024_q2_production: 150,000 records from Apr-Jun 2024',
       '2024-04-01',
       '2024-06-30',
       150000,
       0.89,  -- F1
       0.008, -- FPR
       0.91,  -- Precision
       0.87,  -- Recall
       0.86,  -- F1 CI lower
       0.92,  -- F1 CI upper
       0.006, -- FPR CI lower
       0.010, -- FPR CI upper
       'gradient_boosting',
       ARRAY['credit_card_fraud', 'wire_fraud'],
       'pending_approval',
       '<developer_user_id>'
   );
   ```

3. **Compliance Officer: Validate Thresholds**
   ```sql
   -- Run automated validation
   SELECT * FROM validate_deployment_thresholds('<model_id>');

   -- Output example:
   -- is_valid | failing_criteria | message
   -- ---------+------------------+-----------------------------------
   -- TRUE     | NULL             | Model meets all deployment thresholds
   ```

4. **Compliance Officer: Review Fairness**
   ```sql
   -- Check fairness by transaction type (once model has test predictions)
   SELECT
       transaction_type,
       fpr,
       false_positives,
       true_negatives
   FROM fairness_metrics_by_type
   WHERE model_id = '<model_id>'
   ORDER BY fpr DESC;

   -- Flag if FPR disparity > 10%
   ```

5. **Compliance Officer: Approve**
   ```sql
   UPDATE models
   SET status = 'approved',
       approved_by = '<officer_user_id>'
   WHERE model_id = '<model_id>';
   ```

6. **Auditor: Review Approval**
   ```sql
   -- Verify approval workflow was followed
   SELECT * FROM get_decision_audit_trail('<model_id>');

   -- Check: developer → officer → auditor chain
   ```

7. **Auditor: Sign Off**
   ```sql
   UPDATE models
   SET audited_by = '<auditor_user_id>'
   WHERE model_id = '<model_id>';
   ```

8. **Developer: Deploy**
   ```sql
   UPDATE models
   SET status = 'deployed',
       deployment_date = CURRENT_TIMESTAMP
   WHERE model_id = '<model_id>';
   ```

**Audit Trail Generated**:
```
┌──────────────────┬────────────────┬──────────────┬─────────────────┐
│   Timestamp      │     Actor      │   Action     │    Details      │
├──────────────────┼────────────────┼──────────────┼─────────────────┤
│ 2024-10-01 09:00 │ dev_alice      │ model_created│ F1=0.89 FPR=0.8%│
│ 2024-10-01 14:30 │ officer_bob    │ approved     │ Meets thresholds│
│ 2024-10-02 10:00 │ auditor_carol  │ audited      │ Documentation OK│
│ 2024-10-03 08:00 │ dev_alice      │ deployed     │ Production      │
└──────────────────┴────────────────┴──────────────┴─────────────────┘
```

**Success Indicators**:
- ✅ F1 ≥ 0.85
- ✅ FPR ≤ 1%
- ✅ Complete documentation
- ✅ Three lines of defense all signed off
- ✅ Immutable audit trail created

---

### Workflow 2: Human-in-the-Loop Transaction Review

**Scenario**: Fraud detection model flags a high-value wire transfer as suspicious.

**Steps**:

1. **Model: Flag Transaction**
   ```sql
   INSERT INTO decisions (
       model_id,
       transaction_id,
       prediction_fraud,
       confidence_score,
       model_features,
       flag_timestamp
   ) VALUES (
       '<model_id>',
       '<transaction_id>',
       TRUE,  -- Flagged as fraud
       0.78,  -- 78% confidence
       '{"amount_zscore": 3.2, "velocity_24h": 1, "new_beneficiary": true}',
       CURRENT_TIMESTAMP
   );
   ```

2. **Compliance Officer: Review Queue**
   ```sql
   SELECT
       decision_id,
       transaction_id,
       external_transaction_id,
       amount,
       currency,
       prediction_fraud,
       confidence_score,
       hours_pending
   FROM compliance_officer_queue
   WHERE hours_pending > 24  -- Priority: pending > 24 hours
   ORDER BY hours_pending DESC;
   ```

3. **Compliance Officer: Investigate**
   - Contact customer
   - Request documentation
   - Verify beneficiary
   - Check transaction history

4. **Compliance Officer: Make Decision**
   ```sql
   UPDATE decisions
   SET reviewed_by = '<officer_user_id>',
       officer_decision = 'false_positive',  -- or 'block_transaction'
       officer_notes = 'Customer contacted and verified. Legitimate corporate real estate purchase. Documentation: purchase agreement, board approval, KYC for beneficiary.',
       decision_timestamp = CURRENT_TIMESTAMP,
       final_decision = 'approved'
   WHERE decision_id = '<decision_id>';
   ```

5. **System: Mark Audit Trail Complete**
   ```
   -- Automatic trigger fires
   -- Sets audit_trail_complete = TRUE
   -- Computes audit_trail_hash
   ```

**Key Metrics Tracked**:
- **Review Turnaround Time**: 2.86 hours (target: < 5 days)
- **Audit Trail Completion**: TRUE
- **Officer Accountability**: Fully documented

**Why This Matters**:
- **Customer Experience**: Legitimate transaction approved quickly
- **False Positive Feedback**: Model learns this pattern is OK
- **Accountability**: If this was actually fraud, we know who approved it
- **Auditability**: Complete record for regulatory inspection

---

### Workflow 3: Model Failure Investigation

**Scenario**: Production monitoring detects F1 score dropped from 0.87 to 0.79.

**Steps**:

1. **System: Detect Degradation**
   ```sql
   -- Automated monitoring query
   SELECT
       model_id,
       name,
       training_f1,
       calculate_f1_score(
           SUM(CASE WHEN prediction_fraud = TRUE AND is_fraud = TRUE THEN 1 ELSE 0 END)::INTEGER,
           SUM(CASE WHEN prediction_fraud = TRUE AND is_fraud = FALSE THEN 1 ELSE 0 END)::INTEGER,
           SUM(CASE WHEN prediction_fraud = FALSE AND is_fraud = TRUE THEN 1 ELSE 0 END)::INTEGER
       ) AS production_f1
   FROM model_performance_summary
   WHERE status = 'deployed';

   -- Alert if production_f1 < 0.85
   ```

2. **Developer: Create Incident**
   ```sql
   INSERT INTO failure_incidents (
       model_id,
       failure_type,
       severity,
       description,
       detected_date,
       detected_by
   ) VALUES (
       '<model_id>',
       'performance_degradation',
       'high',
       'F1 score dropped from 0.87 to 0.79 in production over 5 days. 23 false negatives detected (missed frauds).',
       CURRENT_TIMESTAMP,
       '<developer_user_id>'
   );
   ```

3. **Developer: Root Cause Analysis**
   ```sql
   -- Analyze false negatives
   SELECT
       t.transaction_type,
       t.amount,
       t.fraud_type,
       d.model_features
   FROM decisions d
   JOIN transactions t ON d.transaction_id = t.transaction_id
   WHERE d.model_id = '<model_id>'
     AND d.prediction_fraud = FALSE
     AND t.is_fraud = TRUE
   ORDER BY t.transaction_date DESC
   LIMIT 50;
   ```

4. **Developer: Document Root Cause**
   ```sql
   UPDATE failure_incidents
   SET root_cause = 'New fraud pattern (account takeover via SIM swap) not represented in training data. Fraudsters adapted technique: small test transactions followed by large transfers. Model trained on older takeover patterns.',
       root_cause_category = 'model_drift',
       contributing_factors = ARRAY['training_data_gap', 'adversarial_adaptation', 'insufficient_retraining_frequency'],
       responsible_party = 'developer'
   WHERE incident_id = '<incident_id>';
   ```

5. **Developer: Remediation Plan**
   ```sql
   UPDATE failure_incidents
   SET remediation_plan = '
   1. Collect labeled data for new fraud pattern (SIM swap takeovers)
   2. Retrain model with augmented dataset including 500+ SIM swap cases
   3. Validate on held-out test set with new fraud pattern
   4. Deploy hotfix if F1 >= 0.85
   5. Implement monthly retraining schedule going forward
   ',
       remediation_status = 'in_progress',
       assigned_to = '<developer_user_id>'
   WHERE incident_id = '<incident_id>';
   ```

6. **Developer: Execute Remediation**
   - Collect new training data
   - Retrain model → `fraud_detector_v3.1`
   - Validate: F1 = 0.88, FPR = 0.009
   - Deploy to production

7. **Developer: Mark Resolved**
   ```sql
   UPDATE failure_incidents
   SET remediation_status = 'resolved',
       remediation_completed_date = CURRENT_TIMESTAMP,
       remediation_verified_by = '<developer_user_id>'
   WHERE incident_id = '<incident_id>';
   ```

8. **Auditor: Review and Sign Off**
   ```sql
   -- Review complete incident record
   SELECT * FROM failure_incidents WHERE incident_id = '<incident_id>';

   -- Verify new model performance
   SELECT * FROM models WHERE name = 'fraud_detector_v3.1';

   -- Sign off
   UPDATE failure_incidents
   SET auditor_signoff_by = '<auditor_user_id>',
       auditor_signoff_date = CURRENT_TIMESTAMP,
       auditor_notes = 'Reviewed root cause analysis, remediation plan, and validation results. New model demonstrates improved performance on SIM swap fraud pattern (recall=0.91). Monthly retraining schedule approved. Incident closed.',
       remediation_status = 'closed'
   WHERE incident_id = '<incident_id>';
   ```

**Lifecycle**: 15 days from detection → remediation → sign-off

**Accountability**:
- **Who found it?** Developer (monitoring)
- **Who caused it?** Developer (training data gap)
- **Who fixed it?** Developer (retraining)
- **Who verified it?** Auditor (independent review)

---

## Inputs and Outputs

### Inputs to AFAAP

#### 1. Training Data
**What**: Historical financial transactions with labels

**Format**:
```csv
transaction_id,amount,currency,type,origin_country,destination_country,is_fraud,fraud_type
TXN-001,50000.00,SGD,wire_transfer,SGP,USA,FALSE,
TXN-002,1200.50,SGD,credit_card,SGP,SGP,FALSE,
TXN-003,85000.00,SGD,wire_transfer,SGP,XXX,TRUE,wire_fraud
```

**Requirements**:
- Minimum 10,000 transactions
- Fraud rate: 1-10% (realistic distribution)
- Labels verified by investigators
- Date range documented
- Provenance tracked

**How to Load**:
```sql
COPY transactions (
    external_transaction_id, amount, currency, transaction_type,
    origin_country, destination_country, is_fraud, fraud_type
)
FROM '/path/to/training_data.csv'
CSV HEADER;
```

---

#### 2. Model Predictions
**What**: AI model's output for each transaction

**Format**:
```python
{
    "transaction_id": "TXN-004",
    "prediction_fraud": True,
    "confidence_score": 0.87,
    "model_features": {
        "amount_zscore": 2.5,
        "velocity_24h": 3,
        "new_beneficiary": True,
        "country_risk_score": 0.8
    }
}
```

**Requirements**:
- Confidence score: 0.0 to 1.0
- Explainable features included
- Model version tracked

**How to Load**:
```sql
INSERT INTO decisions (model_id, transaction_id, prediction_fraud, confidence_score, model_features)
VALUES ('<model_id>', '<transaction_id>', TRUE, 0.87, '{"amount_zscore": 2.5}');
```

---

#### 3. Ground Truth (for validation)
**What**: Verified outcome (was it actually fraud?)

**When Available**: After investigation completes (days to weeks later)

**How to Update**:
```sql
UPDATE transactions
SET is_fraud = TRUE,
    fraud_type = 'account_takeover',
    verified_at = CURRENT_TIMESTAMP,
    verified_by = '<officer_user_id>'
WHERE transaction_id = '<transaction_id>';
```

**Why Important**: Ground truth enables:
- Model performance calculation (true F1, FPR)
- False positive/negative analysis
- Model drift detection

---

#### 4. Human Review Decisions
**What**: Compliance officer's decision on flagged transactions

**Format**:
```sql
{
    "reviewed_by": "<officer_user_id>",
    "officer_decision": "approve_transaction",
    "officer_notes": "Customer verified via phone. Transaction legitimate.",
    "decision_timestamp": "2024-10-22T14:30:00Z"
}
```

**Options for `officer_decision`**:
- `approve_transaction`: Let it through
- `block_transaction`: Stop it
- `escalate`: Send to senior officer
- `false_positive`: Model wrong, transaction OK

**Why Important**:
- Creates human accountability
- Completes audit trail
- Provides feedback for model improvement

---

### Outputs from AFAAP

#### 1. Performance Metrics

**Format**:
```json
{
    "model_id": "029c692b-21a2-46f1-845a-a3216aa1e2e8",
    "model_name": "fraud_detector_v1",
    "f1_score": 0.8900,
    "f1_ci_lower": 0.8600,
    "f1_ci_upper": 0.9100,
    "fpr": 0.0080,
    "fpr_ci_lower": 0.0060,
    "fpr_ci_upper": 0.0110,
    "precision": 0.9100,
    "recall": 0.8700,
    "true_positives": 404,
    "false_positives": 102,
    "false_negatives": 80,
    "true_negatives": 8990,
    "total_samples": 9576
}
```

**How to Query**:
```sql
SELECT * FROM get_model_production_metrics('<model_id>');
```

**Interpretation**:
- **F1 = 0.89**: Good balance of precision and recall
- **FPR = 0.8%**: 0.8% of legitimate transactions flagged (80 out of 10,000)
- **Confidence Interval**: [0.86, 0.91] means we're 95% confident true F1 is in this range

**Meets Deployment Threshold?** ✅ YES (F1 ≥ 0.85, FPR ≤ 1%)

---

#### 2. Fairness Metrics

**Output Example**:
```
┌──────────────────┬─────────┬──────────────────┬──────────────────┐
│ Transaction Type │   FPR   │ False Positives  │ True Negatives   │
├──────────────────┼─────────┼──────────────────┼──────────────────┤
│ wire_transfer    │ 0.0120  │        45        │      3,700       │
│ credit_card      │ 0.0080  │        32        │      3,968       │
│ ach              │ 0.0070  │        15        │      2,128       │
│ mobile_payment   │ 0.0065  │        10        │      1,530       │
└──────────────────┴─────────┴──────────────────┴──────────────────┘

Disparity Detection:
- Wire transfers have 1.7x higher FPR than mobile payments
- Investigate: Are wire transfers inherently riskier or is model biased?
```

**How to Query**:
```sql
SELECT * FROM fairness_metrics_by_type
WHERE model_id = '<model_id>'
ORDER BY fpr DESC;
```

**Red Flag**: FPR disparity > 10% (governance threshold)

---

#### 3. Process Metrics

**Output Example**:
```
Audit Trail Completion Rate: 3.79%
Target: 98%
Status: 🔴 BELOW THRESHOLD

Review Turnaround Time: 2.5 days (average)
Target: < 5 days
Status: ✅ MEETS TARGET

Pending Reviews: 15,394
Reviewed: 606
Total Decisions: 16,000
```

**How to Query**:
```sql
SELECT
    COUNT(*) FILTER (WHERE audit_trail_complete) AS complete,
    COUNT(*) AS total,
    ROUND(
        COUNT(*) FILTER (WHERE audit_trail_complete)::NUMERIC / COUNT(*) * 100,
        2
    ) AS completion_rate_pct
FROM decisions;
```

**Why 3.79% is Low**: Most decisions are still pending review (realistic in production system with high transaction volume)

**Action Required**: Hire more compliance officers or automate low-risk reviews

---

#### 4. Audit Trails

**Output Example**:
```sql
SELECT * FROM get_decision_audit_trail('<decision_id>');
```

**Result**:
```
┌────────────────────────────┬───────────────┬─────────────────┬─────────────┬──────────────┬─────────────────────┬────────────────────────┐
│         audit_id           │  operation    │  field_changed  │  old_value  │  new_value   │  changed_by         │      changed_at        │
├────────────────────────────┼───────────────┼─────────────────┼─────────────┼──────────────┼─────────────────────┼────────────────────────┤
│ a1b2c3d4-...               │ INSERT        │ NULL            │ NULL        │ {entire row} │ system              │ 2024-10-22 11:23:45    │
│ e5f6g7h8-...               │ UPDATE        │ reviewed_by     │ NULL        │ officer_123  │ officer_bob         │ 2024-10-22 14:15:30    │
│ i9j0k1l2-...               │ UPDATE        │ officer_decision│ NULL        │ approve...   │ officer_bob         │ 2024-10-22 14:15:30    │
│ m3n4o5p6-...               │ UPDATE        │ officer_notes   │ NULL        │ Customer...  │ officer_bob         │ 2024-10-22 14:15:30    │
│ q7r8s9t0-...               │ UPDATE        │ audit_trail...  │ FALSE       │ TRUE         │ system (trigger)    │ 2024-10-22 14:15:31    │
└────────────────────────────┴───────────────┴─────────────────┴─────────────┴──────────────┴─────────────────────┴────────────────────────┘
```

**Interpretation**:
1. System created decision when model flagged transaction
2. Officer Bob reviewed it 2 hours 52 minutes later
3. Officer Bob made decision (approve), added notes
4. System automatically marked audit trail as complete

**Integrity Verification**:
```sql
SELECT * FROM verify_audit_integrity('decisions', '<decision_id>');
-- Result: is_valid = TRUE (no tampering detected)
```

---

#### 5. Compliance Reports

**Quarterly Audit Summary**:
```sql
-- Generate report
SELECT
    m.name AS model_name,
    m.status,
    m.f1_score AS training_f1,
    mps.true_positives,
    mps.false_positives,
    mps.false_negatives,
    mps.true_negatives,
    calculate_f1_score(
        mps.true_positives,
        mps.false_positives,
        mps.false_negatives
    ) AS production_f1,
    calculate_fpr(
        mps.false_positives,
        mps.true_negatives
    ) AS production_fpr,
    mps.audit_completion_rate,
    mps.avg_turnaround_days,
    COUNT(DISTINCT fi.incident_id) AS failure_incidents
FROM models m
LEFT JOIN model_performance_summary mps ON m.model_id = mps.model_id
LEFT JOIN failure_incidents fi ON m.model_id = fi.model_id
WHERE m.created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY m.model_id, m.name, m.status, m.f1_score, mps.*;
```

**Output for Regulator**:
```markdown
# Q3 2024 AI Governance Compliance Report

## Model Performance
- fraud_detector_v1: F1=0.89 (production=0.87) ✅
- fraud_detector_v2: F1=0.85 (production=0.84) ⚠️  (borderline)
- fraud_detector_beta: F1=0.82 (under review) 🔴

## Audit Trail Compliance
- Completion Rate: 3.79% (target: 98%) 🔴
- Average Review Time: 2.5 days (target: <5 days) ✅

## Incidents
- Total: 10
- Critical: 2
- All signed off by auditors: ✅

## Actions Taken
1. fraud_detector_v2 flagged for re-validation (borderline performance)
2. Hired 5 additional compliance officers to improve audit completion
3. Implemented automated review for low-risk transactions (<$1000)
```

---

## Understanding the Data

### Current Database State

Run this query to see overview:
```sql
SELECT
    'Users' AS table_name,
    COUNT(*) AS count
FROM users
UNION ALL
SELECT 'Models', COUNT(*) FROM models
UNION ALL
SELECT 'Transactions', COUNT(*) FROM transactions
UNION ALL
SELECT 'Decisions', COUNT(*) FROM decisions
UNION ALL
SELECT 'Revalidation Workflows', COUNT(*) FROM revalidation_workflows
UNION ALL
SELECT 'Failure Incidents', COUNT(*) FROM failure_incidents
UNION ALL
SELECT 'Audit Trails', COUNT(*) FROM audit_trails;
```

**Expected Output**:
```
┌────────────────────────┬────────┐
│      table_name        │ count  │
├────────────────────────┼────────┤
│ Users                  │     20 │
│ Models                 │      5 │
│ Transactions           │ 10,000 │
│ Decisions              │ 16,000 │
│ Revalidation Workflows │      6 │
│ Failure Incidents      │     10 │
│ Audit Trails           │ 16,036 │
└────────────────────────┴────────┘
```

### Synthetic Data Characteristics

#### Transactions (10,000 total)
- **Fraud Rate**: 5% (500 fraudulent, 9,500 legitimate)
- **Edge Cases Included**:
  - High-value (>$1M): ~5%
  - Micro-transactions (<$10): ~10%
  - Cross-border: ~40%
  - High-risk jurisdictions: ~15%

#### Models (5 total)
```sql
SELECT name, version, status, f1_score, fpr
FROM models
ORDER BY created_at;
```

**Output**:
```
┌──────────────────────────┬─────────┬──────────────────┬──────────┬────────┐
│           name           │ version │     status       │ f1_score │  fpr   │
├──────────────────────────┼─────────┼──────────────────┼──────────┼────────┤
│ fraud_detector_v1        │ v1.0.0  │ deployed         │  0.8900  │ 0.0080 │
│ fraud_detector_v2        │ v2.0.0  │ deployed         │  0.8500  │ 0.0100 │
│ fraud_detector_beta      │ v3.0.0  │ under_review     │  0.8200  │ 0.0150 │
│ high_value_wire_detector │ v4.0.0  │ deployed         │  0.8700  │ 0.0050 │
│ ml_ensemble_v1           │ v5.0.0  │ pending_approval │  0.9100  │ 0.0090 │
└──────────────────────────┴─────────┴──────────────────┴──────────┴────────┘
```

**Insights**:
- **3 deployed** models actively flagging transactions
- **1 under review** (below F1 threshold)
- **1 pending approval** (awaiting compliance officer review)

#### Decisions (16,000 total)
- **Coverage**: 80% of transactions have been scored
- **Audit Complete**: 3.79% (606 out of 16,000)
- **Why Low**: Most decisions are still pending compliance officer review

---

## Key Findings from Synthetic Data

### Finding 1: Audit Completion Challenge

**Observation**:
```sql
SELECT
    final_decision,
    COUNT(*) AS count,
    COUNT(*) FILTER (WHERE audit_trail_complete) AS complete
FROM decisions
GROUP BY final_decision;
```

**Result**:
```
┌────────────────┬───────┬──────────┐
│ final_decision │ count │ complete │
├────────────────┼───────┼──────────┤
│ pending        │ 15394 │        0 │
│ approved       │   314 │      314 │
│ blocked        │   212 │      212 │
│ escalated      │    80 │       80 │
└────────────────┴───────┴──────────┘
```

**Finding**: Only reviewed decisions have complete audit trails (by design).

**Implication**:
- 96.2% of decisions still pending review
- This is realistic for high-throughput fraud detection
- Need to prioritize high-risk reviews

**Action**:
```sql
-- Focus on high-confidence fraud predictions first
SELECT * FROM compliance_officer_queue
WHERE confidence_score > 0.7
ORDER BY hours_pending DESC
LIMIT 100;
```

---

### Finding 2: Model Performance Variance

**Observation**:
```sql
SELECT
    name,
    training_f1,
    calculate_f1_score(
        SUM(true_positives)::INTEGER,
        SUM(false_positives)::INTEGER,
        SUM(false_negatives)::INTEGER
    ) AS production_f1
FROM model_performance_summary
WHERE status = 'deployed'
GROUP BY model_id, name, training_f1;
```

**Result**:
```
┌──────────────────┬──────────────┬───────────────┐
│       name       │ training_f1  │ production_f1 │
├──────────────────┼──────────────┼───────────────┤
│ detector_v1      │    0.8900    │    0.8345     │
│ detector_v2      │    0.8500    │    0.8213     │
│ wire_detector    │    0.8700    │      N/A      │
└──────────────────┴──────────────┴───────────────┘
```

**Finding**: Production F1 is 4-6% lower than training.

**Why**:
1. **Distribution shift**: Production data differs from training
2. **Adversarial adaptation**: Fraudsters evolve tactics
3. **Labeling delay**: Ground truth not yet available for recent transactions

**Action**: Trigger re-validation if production F1 < training F1 - 0.05

---

### Finding 3: False Positive Impact

**Observation**:
```sql
SELECT
    SUM(false_positives) AS total_fp,
    AVG(avg_turnaround_days) AS avg_review_time,
    SUM(false_positives) * AVG(avg_turnaround_days) AS customer_friction_days
FROM model_performance_summary
WHERE status = 'deployed';
```

**Result**:
```
┌───────────┬──────────────────┬───────────────────────┐
│ total_fp  │ avg_review_time  │ customer_friction_days│
├───────────┼──────────────────┼───────────────────────┤
│    170    │    2.5 days      │       425 days        │
└───────────┴──────────────────┴───────────────────────┘
```

**Finding**: 170 legitimate customers experienced 2.5-day delays.

**Business Impact**:
- Customer satisfaction risk
- Potential revenue loss if customers abandon
- Each false positive costs ~$500 in manual review time

**Cost**: 170 FP × $500 = $85,000 in review costs

**Trade-off**: Lowering FPR might increase false negatives (missed fraud)

---

### Finding 4: Review Turnaround Performance

**Observation**:
```sql
SELECT
    username,
    total_assigned,
    pending_review,
    completed_review,
    avg_review_hours
FROM officer_workload_summary
ORDER BY pending_review DESC;
```

**Result**:
```
┌──────────────────┬───────────────┬────────────────┬──────────────────┬──────────────────┐
│    username      │total_assigned │ pending_review │ completed_review │ avg_review_hours │
├──────────────────┼───────────────┼────────────────┼──────────────────┼──────────────────┤
│ officer_yherrera │     1,847     │     1,785      │        62        │      58.3        │
│ officer_barbara10│     1,623     │     1,561      │        62        │      61.2        │
│ officer_james... │     1,518     │     1,458      │        60        │      55.7        │
└──────────────────┴───────────────┴────────────────┴──────────────────┴──────────────────┘
```

**Finding**: Officers reviewing ~3% of assigned cases, average 58 hours per review.

**Problem**: Workload unsustainable (1,500+ pending per officer).

**Solution**:
1. **Automate low-risk reviews**: Auto-approve predictions with confidence < 0.3
2. **Hire more officers**: Target 200 pending per officer
3. **Prioritize high-value**: Review $10k+ transactions first

---

### Finding 5: Fairness Concerns

**Observation**:
```sql
SELECT
    transaction_type,
    fpr,
    ROUND(fpr * 100, 2) AS fpr_pct
FROM fairness_metrics_by_type
WHERE model_id = '<deployed_model_id>'
ORDER BY fpr DESC;
```

**Result**:
```
┌──────────────────┬─────────┬─────────┐
│ transaction_type │   fpr   │ fpr_pct │
├──────────────────┼─────────┼─────────┤
│ wire_transfer    │ 0.0120  │  1.20%  │
│ cryptocurrency   │ 0.0110  │  1.10%  │
│ credit_card      │ 0.0080  │  0.80%  │
│ ach              │ 0.0070  │  0.70%  │
│ mobile_payment   │ 0.0065  │  0.65%  │
└──────────────────┴─────────┴─────────┘
```

**Finding**: Wire transfers have 1.85x higher FPR than mobile payments.

**Disparity Threshold**: 10% (governance rule)

**Status**: 🔴 **VIOLATION** (85% disparity > 10% threshold)

**Root Cause**:
- Wire transfers are legitimately higher risk
- BUT: Model may be over-penalizing them

**Action**:
1. Collect more wire transfer training data
2. Re-balance training set
3. Implement separate models for high/low risk types

---

## Governance Thresholds and Rules

### Performance Thresholds

| Metric | Threshold | Why This Value? |
|--------|-----------|-----------------|
| **F1 Score** | ≥ 0.85 | Balance precision/recall. Below 0.85 means missing >15% of fraud OR blocking >15% of legitimate. |
| **False Positive Rate (FPR)** | ≤ 1% | Customer experience. 1% FPR = 100 legitimate customers blocked per 10,000 transactions. Higher causes churn. |
| **Confidence Interval** | 95% | Statistical rigor. 95% CI means we're confident metric will hold in production. |

### Process Thresholds

| Metric | Threshold | Why This Value? |
|--------|-----------|-----------------|
| **Audit Trail Completion** | ≥ 98% | Regulatory requirement. 98% allows for 2% system errors but ensures near-complete accountability. |
| **Review Turnaround Time** | ≤ 5 days | Customer experience + fraud window. Longer delays = customer churn + fraud opportunity. |
| **Fairness Disparity** | ≤ 10% | Prevent discrimination. FPR shouldn't vary >10% across demographics/transaction types. |

### Re-validation Triggers

**Rule 1: New Use Case**
```
IF model is being used for a fraud type not in original training
THEN trigger re-validation
```

**Example**:
- Original: credit card fraud only
- New: extending to wire fraud
- **Action**: Re-validate on wire fraud dataset

**Rule 2: Performance Degradation**
```
IF production_f1 < training_f1 - 0.05
OR production_fpr > training_fpr + 0.02
THEN trigger re-validation
```

**Example**:
- Training F1: 0.89
- Production F1: 0.83 (difference = 0.06 > 0.05 threshold)
- **Action**: Investigate and re-validate

**Rule 3: Distribution Shift**
```
IF fraud_rate changes by >50%
OR transaction_volume changes by >100%
THEN trigger re-validation
```

**Example**:
- Training fraud rate: 2%
- Production fraud rate: 4% (100% increase)
- **Action**: Re-validate with new distribution

### Escalation Rules

**Rule 1: High-Value Transactions**
```
IF transaction_amount > $500,000
AND prediction_fraud = TRUE
THEN escalate to senior compliance officer
```

**Rule 2: Repeat Offenders**
```
IF customer has >3 blocked transactions in 30 days
THEN escalate to fraud investigation team
```

**Rule 3: Audit Trail Gaps**
```
IF audit_completion_rate < 98% for 2 consecutive weeks
THEN escalate to compliance director
```

---

## Audit Trail System

### How Audit Trails Work

**Every change creates a record**:
```sql
-- When you update a decision
UPDATE decisions
SET officer_decision = 'approve_transaction'
WHERE decision_id = '<id>';

-- Automatic trigger fires and logs:
INSERT INTO audit_trails (
    table_name,
    record_id,
    operation,
    field_changed,
    old_value,
    new_value,
    changed_by,
    changed_at,
    previous_audit_hash,
    current_audit_hash
) VALUES (
    'decisions',
    '<id>',
    'UPDATE',
    'officer_decision',
    NULL,
    'approve_transaction',
    '<officer_user_id>',
    '2024-10-22 14:15:30',
    'a1b2c3...',  -- Hash of previous audit record
    'd4e5f6...'   -- Hash of this audit record
);
```

### Blockchain-Style Hash Chaining

Each audit record includes:
1. **Current hash**: SHA-256 of this record
2. **Previous hash**: Links to previous audit record

```
Audit Record 1:
├── previous_hash: NULL (first record)
└── current_hash: a1b2c3...

Audit Record 2:
├── previous_hash: a1b2c3... (matches Record 1)
└── current_hash: d4e5f6...

Audit Record 3:
├── previous_hash: d4e5f6... (matches Record 2)
└── current_hash: g7h8i9...
```

**If someone tries to tamper**:
- Change old_value in Record 2
- Hash no longer matches
- Verification function detects break in chain

### Verifying Integrity

```sql
SELECT * FROM verify_audit_integrity('decisions', '<decision_id>');
```

**Output if valid**:
```
┌──────────┬─────────────────┬────────────────────────────────────┐
│ is_valid │ broken_chain_at │             message                │
├──────────┼─────────────────┼────────────────────────────────────┤
│   TRUE   │      NULL       │ Audit trail integrity verified     │
└──────────┴─────────────────┴────────────────────────────────────┘
```

**Output if tampered**:
```
┌──────────┬─────────────────────────┬─────────────────────────────┐
│ is_valid │   broken_chain_at       │          message            │
├──────────┼─────────────────────────┼─────────────────────────────┤
│  FALSE   │ 2024-10-22 14:16:00     │ Hash mismatch detected -    │
│          │                         │ possible tampering          │
└──────────┴─────────────────────────┴─────────────────────────────┘
```

### What Gets Audited?

**Tables with full audit trails**:
- ✅ `models` - Every status change, approval, deployment
- ✅ `decisions` - Every review, decision, escalation
- ✅ `revalidation_workflows` - Every trigger, review, approval
- ✅ `failure_incidents` - Every update, remediation, sign-off

**What's NOT audited**:
- ❌ `transactions` - Raw data (performance reasons)
- ❌ `users` - Privacy (only creation audited)

---

## Querying the Database

### Basic Queries

#### View All Models
```sql
SELECT
    name,
    version,
    status,
    f1_score,
    fpr,
    deployment_date
FROM models
ORDER BY deployment_date DESC;
```

#### View Pending Reviews
```sql
SELECT
    decision_id,
    transaction_id,
    confidence_score,
    flag_timestamp,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - flag_timestamp)) / 3600 AS hours_pending
FROM decisions
WHERE final_decision = 'pending'
ORDER BY hours_pending DESC
LIMIT 20;
```

#### Check Audit Completion
```sql
SELECT
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE audit_trail_complete) AS complete,
    ROUND(
        COUNT(*) FILTER (WHERE audit_trail_complete)::NUMERIC / COUNT(*) * 100,
        2
    ) AS completion_pct
FROM decisions;
```

### Advanced Queries

#### Calculate Production Metrics
```sql
SELECT * FROM get_model_production_metrics('<model_id>');
```

#### Compare Training vs Production Performance
```sql
WITH production_metrics AS (
    SELECT
        model_id,
        calculate_f1_score(
            SUM(CASE WHEN prediction_fraud = TRUE AND is_fraud = TRUE THEN 1 ELSE 0 END)::INTEGER,
            SUM(CASE WHEN prediction_fraud = TRUE AND is_fraud = FALSE THEN 1 ELSE 0 END)::INTEGER,
            SUM(CASE WHEN prediction_fraud = FALSE AND is_fraud = TRUE THEN 1 ELSE 0 END)::INTEGER
        ) AS production_f1,
        calculate_fpr(
            SUM(CASE WHEN prediction_fraud = TRUE AND is_fraud = FALSE THEN 1 ELSE 0 END)::INTEGER,
            SUM(CASE WHEN prediction_fraud = FALSE AND is_fraud = FALSE THEN 1 ELSE 0 END)::INTEGER
        ) AS production_fpr
    FROM decisions d
    JOIN transactions t ON d.transaction_id = t.transaction_id
    WHERE t.is_fraud IS NOT NULL
    GROUP BY model_id
)
SELECT
    m.name,
    m.f1_score AS training_f1,
    pm.production_f1,
    m.f1_score - pm.production_f1 AS f1_degradation,
    m.fpr AS training_fpr,
    pm.production_fpr,
    pm.production_fpr - m.fpr AS fpr_increase
FROM models m
JOIN production_metrics pm ON m.model_id = pm.model_id
WHERE m.status = 'deployed';
```

#### Find High-Risk Pending Decisions
```sql
SELECT
    d.decision_id,
    t.external_transaction_id,
    t.amount,
    t.currency,
    d.confidence_score,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - d.flag_timestamp)) / 3600 AS hours_pending
FROM decisions d
JOIN transactions t ON d.transaction_id = t.transaction_id
WHERE d.final_decision = 'pending'
  AND d.confidence_score > 0.8  -- High confidence fraud
  AND t.amount > 50000          -- High value
ORDER BY t.amount DESC, d.confidence_score DESC
LIMIT 50;
```

#### Analyze False Positives by Customer Segment
```sql
SELECT
    t.customer_segment,
    COUNT(*) FILTER (WHERE d.prediction_fraud = TRUE AND t.is_fraud = FALSE) AS false_positives,
    COUNT(*) FILTER (WHERE t.is_fraud = FALSE) AS total_legitimate,
    ROUND(
        COUNT(*) FILTER (WHERE d.prediction_fraud = TRUE AND t.is_fraud = FALSE)::NUMERIC /
        NULLIF(COUNT(*) FILTER (WHERE t.is_fraud = FALSE), 0) * 100,
        2
    ) AS fpr_pct
FROM decisions d
JOIN transactions t ON d.transaction_id = t.transaction_id
WHERE d.model_id = '<model_id>'
  AND t.is_fraud IS NOT NULL
GROUP BY t.customer_segment
ORDER BY fpr_pct DESC;
```

---

## Compliance Reporting

### Monthly Report Template

```sql
-- Month-End Compliance Report
WITH reporting_period AS (
    SELECT
        DATE_TRUNC('month', CURRENT_DATE) AS period_start,
        CURRENT_DATE AS period_end
),
model_stats AS (
    SELECT
        m.model_id,
        m.name,
        m.status,
        COUNT(d.decision_id) AS total_decisions,
        COUNT(*) FILTER (WHERE d.final_decision != 'pending') AS reviewed,
        COUNT(*) FILTER (WHERE d.audit_trail_complete) AS audit_complete,
        ROUND(
            COUNT(*) FILTER (WHERE d.audit_trail_complete)::NUMERIC /
            NULLIF(COUNT(d.decision_id), 0) * 100,
            2
        ) AS audit_completion_pct,
        AVG(
            EXTRACT(EPOCH FROM (d.decision_timestamp - d.flag_timestamp)) / 86400
        ) AS avg_turnaround_days
    FROM models m
    LEFT JOIN decisions d ON m.model_id = d.model_id
    WHERE d.created_at >= (SELECT period_start FROM reporting_period)
      AND d.created_at <= (SELECT period_end FROM reporting_period)
    GROUP BY m.model_id, m.name, m.status
)
SELECT
    period_start::DATE AS report_period_start,
    period_end::DATE AS report_period_end,
    name AS model_name,
    status,
    total_decisions,
    reviewed,
    audit_complete,
    audit_completion_pct,
    CASE
        WHEN audit_completion_pct >= 98 THEN 'MEETS TARGET'
        ELSE 'BELOW TARGET'
    END AS audit_status,
    ROUND(avg_turnaround_days, 2) AS avg_turnaround_days,
    CASE
        WHEN avg_turnaround_days <= 5 THEN 'MEETS TARGET'
        ELSE 'EXCEEDS TARGET'
    END AS turnaround_status
FROM reporting_period, model_stats
ORDER BY total_decisions DESC;
```

### Quarterly Audit Checklist

```sql
-- Q3 2024 Audit Checklist
SELECT
    'Deployed Models' AS check_item,
    COUNT(*) AS count,
    CASE WHEN COUNT(*) > 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM models WHERE status = 'deployed'

UNION ALL

SELECT
    'Models Meet F1 Threshold',
    COUNT(*),
    CASE WHEN COUNT(*) = (SELECT COUNT(*) FROM models WHERE status = 'deployed') THEN 'PASS' ELSE 'FAIL' END
FROM models
WHERE status = 'deployed' AND f1_score >= 0.85

UNION ALL

SELECT
    'Models Meet FPR Threshold',
    COUNT(*),
    CASE WHEN COUNT(*) = (SELECT COUNT(*) FROM models WHERE status = 'deployed') THEN 'PASS' ELSE 'FAIL' END
FROM models
WHERE status = 'deployed' AND fpr <= 0.01

UNION ALL

SELECT
    'Audit Trail Integrity',
    COUNT(*),
    CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM (
    SELECT verify_audit_integrity('decisions', decision_id)
    FROM decisions
    WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
    LIMIT 100
) AS integrity_checks
WHERE (integrity_checks.verify_audit_integrity).is_valid = FALSE

UNION ALL

SELECT
    'Incidents Signed Off',
    COUNT(*),
    CASE WHEN COUNT(*) = (SELECT COUNT(*) FROM failure_incidents WHERE remediation_status = 'closed') THEN 'PASS' ELSE 'FAIL' END
FROM failure_incidents
WHERE auditor_signoff_by IS NOT NULL AND remediation_status = 'closed';
```

---

## Troubleshooting

### Issue 1: Audit Completion Rate Low

**Symptom**:
```sql
SELECT ROUND(
    COUNT(*) FILTER (WHERE audit_trail_complete)::NUMERIC / COUNT(*) * 100, 2
) FROM decisions;
-- Result: 3.79% (target: 98%)
```

**Diagnosis**:
```sql
SELECT
    final_decision,
    COUNT(*),
    COUNT(*) FILTER (WHERE audit_trail_complete) AS complete
FROM decisions
GROUP BY final_decision;
```

**Root Cause**: Most decisions still pending review.

**Solutions**:
1. **Hire more compliance officers**
2. **Automate low-risk approvals**:
   ```sql
   -- Auto-approve low confidence, low value
   UPDATE decisions
   SET reviewed_by = '<system_user_id>',
       officer_decision = 'approve_transaction',
       officer_notes = 'Auto-approved: low risk (confidence < 0.3, amount < $1000)',
       decision_timestamp = CURRENT_TIMESTAMP,
       final_decision = 'approved'
   WHERE confidence_score < 0.3
     AND transaction_id IN (
         SELECT transaction_id FROM transactions WHERE amount < 1000
     )
     AND final_decision = 'pending';
   ```

---

### Issue 2: Model Performance Degradation

**Symptom**:
```sql
SELECT
    training_f1,
    production_f1
FROM (
    SELECT
        m.f1_score AS training_f1,
        calculate_f1_score(
            SUM(CASE WHEN d.prediction_fraud = TRUE AND t.is_fraud = TRUE THEN 1 ELSE 0 END)::INTEGER,
            SUM(CASE WHEN d.prediction_fraud = TRUE AND t.is_fraud = FALSE THEN 1 ELSE 0 END)::INTEGER,
            SUM(CASE WHEN d.prediction_fraud = FALSE AND t.is_fraud = TRUE THEN 1 ELSE 0 END)::INTEGER
        ) AS production_f1
    FROM models m
    JOIN decisions d ON m.model_id = d.model_id
    JOIN transactions t ON d.transaction_id = t.transaction_id
    WHERE m.model_id = '<model_id>'
      AND t.is_fraud IS NOT NULL
    GROUP BY m.f1_score
) AS metrics;
-- Result: training_f1=0.89, production_f1=0.83 (6% degradation)
```

**Root Cause Investigation**:
```sql
-- When did degradation start?
SELECT
    DATE_TRUNC('week', d.created_at) AS week,
    COUNT(*) FILTER (WHERE d.prediction_fraud = FALSE AND t.is_fraud = TRUE) AS false_negatives,
    COUNT(*) FILTER (WHERE t.is_fraud = TRUE) AS total_fraud
FROM decisions d
JOIN transactions t ON d.transaction_id = t.transaction_id
WHERE d.model_id = '<model_id>'
  AND t.is_fraud IS NOT NULL
GROUP BY week
ORDER BY week;
```

**Solution**: Trigger re-validation workflow

---

### Issue 3: Fairness Disparity Detected

**Symptom**:
```sql
SELECT
    transaction_type,
    fpr
FROM fairness_metrics_by_type
WHERE model_id = '<model_id>'
ORDER BY fpr DESC;
-- Result: wire_transfer FPR=1.2%, mobile_payment FPR=0.65% (85% disparity)
```

**Root Cause**:
```sql
-- Check training data distribution
SELECT
    transaction_type,
    COUNT(*) AS count,
    ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER () * 100, 2) AS pct
FROM transactions
WHERE created_at >= '2024-01-01' AND created_at < '2024-04-01'  -- Training period
GROUP BY transaction_type
ORDER BY count DESC;
```

**Solution**: Re-balance training data or create specialized models

---

## Conclusion

AFAAP provides **complete accountability** for AI fraud detection through:

1. **Three Lines of Defense**: Developer → Officer → Auditor
2. **Performance Thresholds**: F1 ≥ 0.85, FPR ≤ 1%
3. **Immutable Audit Trails**: Blockchain-style verification
4. **Fairness Monitoring**: Detect bias across demographics
5. **Failure Response**: Root cause → remediation → sign-off

### Quick Reference

**Start Docker Services**:
```bash
docker-compose up -d
```

**Query Database**:
```bash
docker exec afaap-postgres psql -U afaap_admin -d afaap
```

**Run Metrics**:
```bash
docker exec afaap-app python -m metrics.performance_metrics
```

**Generate Report**:
```sql
SELECT * FROM model_performance_summary;
```

### Next Steps

1. **Explore the Data**: Run sample queries in this guide
2. **Test Workflows**: Try approving a decision, triggering re-validation
3. **Build Dashboard**: Visualize metrics in real-time
4. **Integrate Your Model**: Replace synthetic data with real predictions
5. **Customize Thresholds**: Adjust governance rules for your use case

---

**For Support**: See [troubleshooting.md](troubleshooting.md)
**For API Reference**: See [api_spec.md](api_spec.md)
**For Schema Details**: See [schema/README.md](../schema/README.md)
