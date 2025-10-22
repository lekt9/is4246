# AFAAP Database Schema Documentation

## Overview

The AFAAP database schema implements a comprehensive governance framework for AI-powered fraud detection systems, aligned with the Three Lines of Defense (3LOD) model for regulatory compliance.

## Schema Files

1. **[001_initial_schema.sql](001_initial_schema.sql)** - Core tables and relationships
2. **[002_audit_trail_extensions.sql](002_audit_trail_extensions.sql)** - Immutable audit logging
3. **[003_indexes_and_constraints.sql](003_indexes_and_constraints.sql)** - Performance optimization and metrics

## Entity Relationship Diagram

```
┌──────────────┐
│    roles     │
└──────┬───────┘
       │
       │ 1
       │
       │ N
┌──────▼───────┐         ┌─────────────────┐
│    users     │◄────────┤  audit_trails   │
└──────┬───────┘         │  (append-only)  │
       │                 └─────────────────┘
       │                         │
       │                         │ tracks all changes
       │                         │
       │ developed_by            ▼
       │ approved_by      ┌──────────────┐
       │ audited_by       │  governance  │
       │                  │  decisions   │
┌──────▼──────────┐       └──────────────┘
│     models      │
│ ┌─────────────┐ │
│ │ - model_id  │ │
│ │ - name      │ │
│ │ - version   │ │
│ │ - f1_score  │ │ >= 0.85 (threshold)
│ │ - fpr       │ │ <= 0.01 (1%)
│ │ - status    │ │
│ └─────────────┘ │
└────┬────┬───────┘
     │    │
     │    └──────────────────┐
     │                       │
     │ 1                     │ 1
     │                       │
     │ N                     │ N
┌────▼────────────┐   ┌──────▼──────────────────┐
│   decisions     │   │ revalidation_workflows  │
│ ┌─────────────┐ │   │ ┌─────────────────────┐ │
│ │decision_id  │ │   │ │ revalidation_id     │ │
│ │model_id ────┼─┘   │ │ model_id ───────────┼─┘
│ │transaction  │     │ │ trigger_reason      │
│ │  _id ───────┼─┐   │ │ new_fraud_types     │
│ │reviewed_by  │ │   │ │ revalidation_f1     │
│ │officer_     │ │   │ │ revalidation_fpr    │
│ │ decision    │ │   │ │ status              │
│ │audit_trail_ │ │   │ └─────────────────────┘
│ │ complete    │ │   └─────────────────────────┘
│ │audit_trail_ │ │
│ │ hash        │ │
│ └─────────────┘ │   ┌─────────────────────────┐
└─────────────────┘   │  failure_incidents      │
     │                │ ┌─────────────────────┐ │
     │ N              │ │ incident_id         │ │
     │                │ │ model_id ───────────┼─┘
     │ 1              │ │ failure_type        │
     │                │ │ severity            │
┌────▼─────────────┐  │ │ root_cause          │
│  transactions    │  │ │ responsible_party   │
│ ┌──────────────┐ │  │ │ remediation_status  │
│ │transaction_id│ │  │ │ auditor_signoff_by  │
│ │type          │ │  │ └─────────────────────┘
│ │amount        │ │  └─────────────────────────┘
│ │currency      │ │
│ │origin_       │ │
│ │ country      │ │
│ │is_fraud      │ │ (ground truth)
│ │fraud_type    │ │
│ └──────────────┘ │
└──────────────────┘
```

## Core Tables

### 1. Users and Roles

#### `roles`
Implements the Three Lines of Defense (3LOD) model:

- **developer**: First line - model development and testing
- **compliance_officer**: Second line - review and approval
- **auditor**: Third line - independent oversight
- **admin**: System administration

#### `users`
User accounts with role-based access control (RBAC).

**Key Fields:**
- `user_id` (UUID, PK)
- `username`, `email`
- `role_id` (FK to roles)
- `is_active` - for account lifecycle management

**Constraints:**
- Email format validation
- Unique username and email

### 2. Model Metadata

#### `models`
Complete metadata for all AI/ML models used in fraud detection.

**Key Fields:**
- `model_id` (UUID, PK)
- `name`, `version` - unique combination
- `training_data_provenance` - dataset lineage (required)
- `f1_score`, `fpr` - pre-deployment metrics
- `f1_ci_lower`, `f1_ci_upper` - confidence intervals
- `status` - lifecycle: pending_approval, approved, deployed, under_review, retired, rejected
- `developed_by`, `approved_by`, `audited_by` - accountability chain

**Governance Constraints:**
- F1 score must be in [0, 1]
- FPR must be in [0, 1]
- Training end date >= training start date
- Unique (name, version) combination

**Pre-Deployment Requirements:**
- F1 >= 0.85
- FPR <= 0.01 (1%)
- Complete training data provenance
- Approval by compliance officer

### 3. Transactions

#### `transactions`
Financial transactions for fraud detection and fairness analysis.

**Key Fields:**
- `transaction_id` (UUID, PK)
- `external_transaction_id` - bank's internal reference
- `transaction_type` - wire_transfer, credit_card, ach, etc.
- `amount`, `currency`
- `origin_country`, `destination_country` - for geographic fairness
- `customer_segment`, `customer_risk_profile`
- `is_fraud` - ground truth (NULL until verified)
- `fraud_type` - classification if fraudulent

**Purpose:**
- Link to fraud detection decisions
- Provide ground truth for validation
- Enable fairness analysis by geography and transaction type

### 4. Fraud Detection Decisions

#### `decisions`
Every model prediction with human-in-the-loop review.

**Key Fields:**
- `decision_id` (UUID, PK)
- `model_id` (FK to models)
- `transaction_id` (FK to transactions)
- `prediction_fraud` - model's prediction
- `confidence_score` - model confidence [0, 1]
- `reviewed_by` (FK to users) - compliance officer
- `officer_decision` - approve_transaction, block_transaction, escalate, false_positive
- `officer_notes` - justification (required for audit trail)
- `final_decision` - pending, approved, blocked, escalated
- `audit_trail_hash` - SHA-256 for tamper detection
- `audit_trail_complete` - TRUE when all required fields populated

**Governance Rules:**
- Every prediction must be logged
- Audit trail completion target: ≥98%
- Review turnaround time target: ≤5 days
- Officer decision requires officer notes for accountability

**Constraints:**
- `review_requires_officer`: If officer_decision is set, reviewed_by must be set

### 5. Re-validation Workflows

#### `revalidation_workflows`
Tracks model re-validation when repurposed or underperforming.

**Key Fields:**
- `revalidation_id` (UUID, PK)
- `model_id` (FK to models)
- `trigger_reason` - new_fraud_type, performance_degradation, data_distribution_shift, regulatory_requirement, scheduled_review
- `trigger_details` - explanation
- `new_fraud_types` - if repurposing
- `revalidation_f1_score`, `revalidation_fpr` - new validation results
- `status` - pending, under_review, approved, rejected, requires_changes
- `reviewed_by`, `approved_by` - compliance officer and auditor

**Governance Rules:**
- Model repurposed to new fraud type → mandatory re-validation
- Performance degradation → re-validation required
- Re-validation must meet same thresholds (F1 >= 0.85, FPR <= 0.01)

### 6. Failure Incidents

#### `failure_incidents`
Complete incident tracking with root cause analysis.

**Key Fields:**
- `incident_id` (UUID, PK)
- `model_id` (FK to models)
- `failure_type` - performance_degradation, false_positive_spike, false_negative_spike, bias_detection, system_error, data_quality_issue, model_drift
- `severity` - critical, high, medium, low
- `detected_by` (FK to users)
- `root_cause` - detailed analysis
- `responsible_party` - developer, financial_institution, vendor, data_issue, external_factor
- `remediation_status` - open, in_progress, resolved, closed, monitoring
- `auditor_signoff_by`, `auditor_signoff_date` - required before closure
- `reported_to_regulator` - regulatory reporting flag

**Governance Rules:**
- Auditor sign-off required before incident can be closed
- All failures must have root cause analysis
- Accountability attribution required

### 7. Audit Trails (Immutable)

#### `audit_trails`
Append-only log of all changes to critical tables.

**Key Fields:**
- `audit_id` (UUID, PK)
- `table_name` - which table was changed
- `record_id` - which record was changed
- `operation` - INSERT, UPDATE, DELETE (soft only)
- `field_changed` - specific field (NULL for INSERT)
- `old_value`, `new_value` - change delta
- `changed_by` (FK to users) - who made the change
- `changed_at` - when the change occurred
- `previous_audit_hash` - blockchain-style chain verification
- `current_audit_hash` - SHA-256 of this record

**Governance Rules:**
- NO UPDATE or DELETE allowed (enforced by RLS policies)
- Append-only for tamper-proof audit
- Every change to decisions, models, revalidation, incidents logged
- Blockchain-style hash chaining for integrity verification

**Row-Level Security:**
- Auditors can view all audit trails
- Users can view their own actions only
- No one can modify audit trails

### 8. Governance Configuration

#### `governance_config`
Configurable thresholds for regulatory compliance.

**Default Values:**
- `min_f1_score`: 0.85
- `max_fpr`: 0.01 (1%)
- `min_audit_completion`: 0.98 (98%)
- `max_review_turnaround_days`: 5
- `confidence_interval`: 0.95
- `bootstrap_iterations`: 10000
- `fairness_disparity_threshold`: 0.10 (10%)

## Materialized Views (Performance Optimization)

### `model_performance_summary`
Cached performance metrics for all models (refreshed hourly).

**Metrics:**
- Training vs. production performance (F1, FPR)
- True positives, false positives, false negatives, true negatives
- Audit completion rate
- Average review turnaround time

### `fairness_metrics_by_type`
False positive rate breakdown by transaction type.

**Purpose:** Detect bias in model predictions across different transaction types.

### `fairness_metrics_by_geography`
False positive rate breakdown by origin/destination country.

**Purpose:** Detect geographic bias in model predictions.

### `officer_workload_summary`
Workload summary for compliance officers.

**Metrics:**
- Total assigned decisions
- Pending reviews
- Completed reviews
- Average review hours

## Database Functions

### Audit Functions

#### `compute_audit_hash()`
Computes SHA-256 hash for audit trail integrity.

**Blockchain-style verification:** Each audit record includes hash of previous record, creating an unbreakable chain.

#### `get_decision_audit_trail(p_decision_id UUID)`
Returns complete audit history for a decision.

**Returns:** All changes with timestamps, user attribution, and values.

#### `verify_audit_integrity(p_table_name, p_record_id)`
Verifies audit trail has not been tampered with.

**Validation:**
- Hash recomputation and verification
- Chain integrity check
- Returns boolean + details of any breaks

### Metrics Functions

#### `calculate_f1_score(tp, fp, fn)`
Computes F1 score: 2 * P * R / (P + R)

#### `calculate_fpr(fp, tn)`
Computes false positive rate: FP / (FP + TN)

#### `get_model_production_metrics(p_model_id)`
Real-time production metrics for deployed model.

**Returns:** F1, FPR, precision, recall, audit completion, turnaround time

### Governance Functions

#### `validate_deployment_thresholds(p_model_id)`
Checks if model meets deployment criteria.

**Validation:**
- F1 >= configured threshold (default 0.85)
- FPR <= configured threshold (default 0.01)
- Approved by compliance officer

**Returns:** Boolean + list of failing criteria

#### `refresh_all_metrics_views()`
Refreshes all materialized views for dashboard.

**Schedule:** Run hourly via cron or pg_cron

## Triggers

### Audit Triggers

All triggers fire BEFORE INSERT/UPDATE/DELETE:

1. **`audit_decisions_trigger`** - Logs all decision changes
2. **`audit_models_trigger`** - Logs model lifecycle changes
3. **`audit_revalidation_trigger`** - Logs re-validation workflow changes
4. **`audit_incidents_trigger`** - Logs incident remediation progress

**Key Features:**
- Granular field-level tracking for UPDATE operations
- Physical deletes forbidden (raise exception)
- Automatic hash computation
- User attribution via session variables

### Completeness Trigger

**`check_audit_completeness_trigger`** - Automatically marks decision audit trail as complete when:
- `reviewed_by` populated
- `officer_decision` populated
- `decision_timestamp` populated
- `officer_notes` populated

## Access Control

### Row-Level Security (RLS)

Enabled on `audit_trails`:

- **Auditors**: Full access to all audit records
- **Other users**: Can only view their own actions
- **No one**: Can update or delete audit trails

### Application-Level RBAC

Enforce via session variables:

```sql
-- Set current user before operations
SET app.current_user_id = '<user_uuid>';
SET app.session_id = '<session_id>';
```

All triggers and policies use these settings for attribution.

## Data Integrity

### Checksums and Hashing

- **Decision audit_trail_hash**: SHA-256 of decision record
- **Audit trail current_audit_hash**: SHA-256 of audit record
- **Audit trail previous_audit_hash**: Blockchain-style chaining

### Constraints

- **NOT NULL** on all critical audit fields
- **CHECK constraints** for valid ranges (F1, FPR in [0,1])
- **UNIQUE constraints** for model (name, version)
- **Foreign key** relationships for accountability chains
- **Cascading deletes FORBIDDEN** (prevent accidental data loss)

### Isolation Level

For concurrent writes to decisions:

```sql
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
```

Prevents race conditions in audit trail updates.

## Performance Considerations

### Indexes

**Primary indexes:**
- All primary keys (UUID, B-tree)
- Foreign keys for joins
- Timestamp fields for time-based queries

**Composite indexes:**
- `(model_id, flag_timestamp)` for metrics calculation
- `(transaction_type, origin_country, transaction_date)` for fairness
- `(severity, remediation_status, detected_date)` for incident tracking

**Partial indexes:**
- Decisions pending review
- Active deployed models
- Incidents requiring sign-off

### Query Optimization

- **Materialized views** for expensive aggregations
- **Concurrent refresh** to avoid locking
- **Partitioning** (optional) for tables with millions of rows
- **Connection pooling** recommended (PgBouncer)

### Scaling

**For >1M transactions:**
1. Enable partitioning on `decisions` by month
2. Partition `audit_trails` by month
3. Set up read replicas for reporting queries
4. Archive old data to separate tablespace

## Migration Path

### Initial Setup

```bash
psql -U afaap_admin -d afaap -f 001_initial_schema.sql
psql -U afaap_admin -d afaap -f 002_audit_trail_extensions.sql
psql -U afaap_admin -d afaap -f 003_indexes_and_constraints.sql
```

### Verification

```sql
-- Check all tables exist
\dt

-- Check all functions exist
\df

-- Check materialized views
\dm

-- Verify default roles
SELECT * FROM roles;

-- Verify governance config
SELECT * FROM governance_config;
```

### Sample Queries

```sql
-- Get model performance summary
SELECT * FROM model_performance_summary WHERE status = 'deployed';

-- Get pending compliance officer queue
SELECT * FROM compliance_officer_queue LIMIT 10;

-- Get incidents requiring auditor sign-off
SELECT * FROM auditor_incident_queue WHERE requires_signoff = TRUE;

-- Check audit trail for a decision
SELECT * FROM get_decision_audit_trail('<decision_uuid>');

-- Verify audit integrity
SELECT * FROM verify_audit_integrity('decisions', '<decision_uuid>');

-- Validate model meets deployment thresholds
SELECT * FROM validate_deployment_thresholds('<model_uuid>');
```

## Maintenance

### Hourly

```sql
SELECT refresh_all_metrics_views();
```

### Daily

```sql
-- Vacuum analyze for query performance
VACUUM ANALYZE decisions;
VACUUM ANALYZE audit_trails;
VACUUM ANALYZE transactions;
```

### Weekly

```sql
-- Check audit trail integrity for recent decisions
SELECT d.decision_id, v.*
FROM decisions d
CROSS JOIN LATERAL verify_audit_integrity('decisions', d.decision_id) v
WHERE d.created_at > CURRENT_DATE - INTERVAL '7 days'
  AND v.is_valid = FALSE;
```

### Quarterly

```sql
-- Full governance compliance audit
SELECT
    COUNT(*) AS total_decisions,
    COUNT(CASE WHEN audit_trail_complete THEN 1 END) AS complete_audits,
    ROUND(
        COUNT(CASE WHEN audit_trail_complete THEN 1 END)::NUMERIC / COUNT(*),
        4
    ) AS completion_rate,
    (SELECT config_value::NUMERIC FROM governance_config WHERE config_key = 'min_audit_completion') AS threshold
FROM decisions
WHERE created_at >= CURRENT_DATE - INTERVAL '90 days';
```

## Security Best Practices

1. **Never disable audit triggers** in production
2. **Rotate database credentials** quarterly
3. **Enable SSL/TLS** for all connections
4. **Restrict superuser access** to DBAs only
5. **Monitor failed login attempts** in PostgreSQL logs
6. **Back up audit_trails separately** for disaster recovery
7. **Set up alerts** for audit trail integrity failures
8. **Review access logs** monthly for anomalous queries

## Troubleshooting

### Audit trail not being created

**Check:** Session variables are set correctly
```sql
SHOW app.current_user_id;
SHOW app.session_id;
```

**Fix:** Set variables before operations
```sql
SET app.current_user_id = '<user_uuid>';
```

### Materialized view refresh failing

**Check:** Long-running queries blocking refresh
```sql
SELECT * FROM pg_stat_activity WHERE state != 'idle';
```

**Fix:** Use CONCURRENTLY for non-blocking refresh
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY model_performance_summary;
```

### Slow audit trail queries

**Check:** Number of audit records
```sql
SELECT COUNT(*) FROM audit_trails;
```

**Fix:** Add index on session_id or changed_at if querying by those fields frequently

## Additional Resources

- [PostgreSQL Row-Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Materialized Views Performance](https://www.postgresql.org/docs/current/rules-materializedviews.html)
- [Partitioning for Large Tables](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- [AFAAP Governance Workflows](../docs/governance_workflows.md)
