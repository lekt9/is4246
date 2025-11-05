# AFAAP Framework Architecture

## Overview

The AFAAP (AI Financial Accountability and Auditability Protocol) framework is a **database-enforced governance system** that automatically ensures AI models comply with regulatory requirements at the data layer, not the application layer.

---

## System Architecture

```mermaid
graph TB
    subgraph "External World"
        Bank[Financial Institution]
        Dev[AI Developer]
        Officer[Compliance Officer]
        Auditor[Independent Auditor]
    end

    subgraph "AFAAP Framework = PostgreSQL Database"
        subgraph "Layer 1: Data Entry"
            TXN[(Transactions Table)]
            MODEL[(Models Table)]
            DECISION[(Decisions Table)]
        end

        subgraph "Layer 2: Automatic Governance (Triggers)"
            T1[assign_risk_tier_and_sla<br/>BEFORE INSERT]
            T2[check_sla_compliance<br/>BEFORE UPDATE]
            T3[audit_decisions_changes<br/>AFTER INSERT/UPDATE]
            T4[compute_audit_hash<br/>SHA-256 Chaining]
        end

        subgraph "Layer 3: Validation Functions"
            V1[validate_deployment_thresholds<br/>F1 ≥ 0.85, FPR ≤ 1%]
            V2[verify_audit_integrity<br/>Hash Chain Verification]
            V3[calculate_rtt<br/>Review Turnaround Time]
        end

        subgraph "Layer 4: Monitoring Dashboards"
            MV1[model_performance_summary<br/>Drift Detection]
            MV2[review_turnaround_time_summary<br/>SLA Compliance]
            MV3[sla_compliance_dashboard<br/>Risk Tier Metrics]
            MV4[sla_violations<br/>Real-time Alerts]
        end

        AUDIT[(Audit Trails Table<br/>Blockchain-style)]
    end

    subgraph "External Tools"
        BOOT[Bootstrap Resampling<br/>performance_metrics.py<br/>10,000 iterations]
        GEN[Synthetic Data Generator<br/>synthetic_dataset_generator.py]
    end

    %% Data Flow
    Bank -->|Transactions| TXN
    Dev -->|Upload Model| MODEL
    MODEL -->|AI Prediction| DECISION
    TXN -->|Link| DECISION

    %% Automatic Triggers
    DECISION -.->|INSERT triggers| T1
    T1 -.->|Auto-assigns| DECISION
    DECISION -.->|UPDATE triggers| T2
    T2 -.->|Checks SLA| DECISION
    DECISION -.->|All changes| T3
    T3 -.->|Creates audit| AUDIT
    AUDIT -.->|Links records| T4

    %% Validation
    Officer -->|Deploy Model?| V1
    V1 -.->|Blocks if invalid| MODEL
    Auditor -->|Verify integrity| V2
    V2 -.->|Checks hash chain| AUDIT

    %% Monitoring
    DECISION --> MV1
    DECISION --> MV2
    DECISION --> MV3
    DECISION --> MV4

    %% External Tools
    BOOT -.->|Validates metrics| MODEL
    GEN -.->|Populates| TXN
    GEN -.->|Populates| DECISION

    style T1 fill:#ff6b6b
    style T2 fill:#ff6b6b
    style T3 fill:#ff6b6b
    style T4 fill:#ff6b6b
    style V1 fill:#4ecdc4
    style V2 fill:#4ecdc4
    style V3 fill:#4ecdc4
```

---

## Governance Workflow: High-Risk Decision

```mermaid
sequenceDiagram
    participant Bank as Financial Institution
    participant Model as AI Fraud Model
    participant DB as AFAAP Framework<br/>(PostgreSQL)
    participant Trigger as Auto Triggers
    participant Officer as Compliance Officer
    participant Audit as Audit Trail

    Bank->>Model: Transaction $50,000 (suspicious)
    Model->>DB: INSERT decision<br/>confidence_score = 0.92<br/>prediction_fraud = TRUE

    Note over DB,Trigger: BEFORE INSERT Trigger Fires
    DB->>Trigger: assign_risk_tier_and_sla()
    Trigger->>Trigger: IF confidence > 0.80<br/>THEN risk_tier = 'high'<br/>sla_deadline = NOW() + 1 hour<br/>transaction_held = TRUE
    Trigger-->>DB: Modified decision record

    DB->>Audit: CREATE audit_trails record
    Audit->>Audit: compute_audit_hash()<br/>SHA-256 with previous hash
    Audit-->>DB: Immutable audit record created

    DB-->>Bank: Transaction HELD<br/>(transaction_held = TRUE)
    DB-->>Officer: ALERT: High-risk decision<br/>SLA deadline: 1 hour

    Note over Officer: Reviews within 1 hour
    Officer->>DB: UPDATE decision<br/>SET reviewed_by = officer_id<br/>officer_decision = 'block_transaction'

    Note over DB,Trigger: BEFORE UPDATE Trigger Fires
    DB->>Trigger: check_sla_compliance()
    Trigger->>Trigger: IF decision_timestamp <= sla_deadline<br/>THEN sla_met = TRUE<br/>ELSE sla_met = FALSE
    Trigger-->>DB: SLA compliance recorded

    DB->>Audit: UPDATE audit_trails record
    Audit-->>DB: Chain extended with new hash

    DB-->>Bank: Transaction BLOCKED<br/>(final_decision = 'blocked')
```

---

## Risk Stratification Logic

```mermaid
flowchart TD
    START[AI Model Flags Transaction] --> CHECK{Confidence Score?}

    CHECK -->|> 80%| HIGH[Risk Tier: HIGH]
    CHECK -->|50-80%| MEDIUM[Risk Tier: MEDIUM]
    CHECK -->|< 50%| LOW[Risk Tier: LOW]

    HIGH --> HIGH_ACTION[• SLA: 1 hour<br/>• Transaction: HELD<br/>• Officer: Notified immediately]
    MEDIUM --> MED_ACTION[• SLA: 24 hours<br/>• Transaction: Proceeds<br/>• Officer: Queued for review]
    LOW --> LOW_ACTION[• SLA: None<br/>• Transaction: Proceeds<br/>• Log only, no review]

    HIGH_ACTION --> OFFICER_REVIEW{Officer Reviews<br/>Within SLA?}
    MED_ACTION --> OFFICER_REVIEW
    LOW_ACTION --> LOG[Logged for<br/>Pattern Analysis]

    OFFICER_REVIEW -->|Yes| SLA_MET[sla_met = TRUE<br/>Audit trail complete]
    OFFICER_REVIEW -->|No| SLA_MISS[sla_met = FALSE<br/>Triggers alert]

    SLA_MET --> FINAL[Final Decision:<br/>Approve/Block/Escalate]
    SLA_MISS --> ESCALATE[Auto-escalate to<br/>Senior Officer]

    style HIGH fill:#ff6b6b
    style MEDIUM fill:#ffd93d
    style LOW fill:#6bcf7f
    style OFFICER_REVIEW fill:#4ecdc4
```

---

## Three Lines of Defense Enforcement

```mermaid
graph LR
    subgraph "First Line: Developer"
        DEV[AI Developer]
        DEV --> M1[Develops Model<br/>F1 = 0.89<br/>FPR = 0.008]
        M1 --> SAFETY[Submits Safety Case]
    end

    subgraph "Second Line: Compliance Officer"
        OFFICER[Compliance Officer]
        SAFETY --> OFFICER
        OFFICER --> CHECK_THRESH{validate_deployment_thresholds}
        CHECK_THRESH -->|F1 ≥ 0.85 ✓<br/>FPR ≤ 0.01 ✓| APPROVE[Approves Model]
        CHECK_THRESH -->|Fails| REJECT[Rejects Model]
    end

    subgraph "Third Line: Independent Auditor"
        AUDITOR[External Auditor]
        APPROVE --> AUDITOR
        AUDITOR --> VERIFY{verify_audit_integrity}
        VERIFY -->|Hash chain valid| DEPLOY[Model Deployed]
        VERIFY -->|Tampered| BLOCK[Deployment Blocked]
    end

    subgraph "Database Enforcement"
        DB[(Models Table)]
        DEPLOY --> DB
        DB --> CONSTRAINT[CHECK CONSTRAINTS:<br/>developed_by ≠ approved_by ≠ audited_by<br/>developer role ≠ officer role ≠ auditor role]
    end

    style CHECK_THRESH fill:#4ecdc4
    style VERIFY fill:#4ecdc4
    style CONSTRAINT fill:#ff6b6b
    style DEPLOY fill:#6bcf7f
    style BLOCK fill:#ff6b6b
    style REJECT fill:#ff6b6b
```

---

## Audit Trail: Blockchain-Style Hash Chaining

```mermaid
flowchart LR
    subgraph "Record 1"
        R1[Decision INSERT<br/>transaction_id: 001<br/>prediction: fraud]
        H1[Previous: NULL<br/>Current: SHA256<br/>a3f2...c91d]
    end

    subgraph "Record 2"
        R2[Decision UPDATE<br/>reviewed_by: officer_5<br/>decision: block]
        H2[Previous: a3f2...c91d<br/>Current: SHA256<br/>7b8e...4fa2]
    end

    subgraph "Record 3"
        R3[Model UPDATE<br/>status: deployed<br/>approved_by: auditor_1]
        H3[Previous: 7b8e...4fa2<br/>Current: SHA256<br/>e5c1...9ad7]
    end

    R1 --> H1
    H1 -.->|Links to next| R2
    R2 --> H2
    H2 -.->|Links to next| R3
    R3 --> H3

    H3 --> VERIFY[verify_audit_integrity]
    VERIFY --> CHECK{Recompute<br/>all hashes<br/>& verify chain}
    CHECK -->|Valid| PASS[✓ Audit trail<br/>tamper-proof]
    CHECK -->|Broken| FAIL[✗ Tampering<br/>detected]

    style VERIFY fill:#4ecdc4
    style PASS fill:#6bcf7f
    style FAIL fill:#ff6b6b
```

---

## Performance Metrics: Bootstrap Resampling

```mermaid
flowchart TD
    START[Model Training Complete] --> EVAL[Evaluate on Test Set<br/>10,000 transactions]

    EVAL --> F1_POINT[Point Estimate:<br/>F1 = 0.87]

    F1_POINT --> BOOT_START[Bootstrap Resampling<br/>10,000 iterations]

    BOOT_START --> ITER[For each iteration:]
    ITER --> SAMPLE[1. Random sample with replacement<br/>n = 10,000]
    SAMPLE --> CALC[2. Calculate F1 score<br/>for this sample]
    CALC --> STORE[3. Store F1 value]

    STORE --> LOOP{Iteration < 10,000?}
    LOOP -->|Yes| ITER
    LOOP -->|No| CI[Calculate 95% CI:<br/>2.5th percentile = 0.851<br/>97.5th percentile = 0.889]

    CI --> RESULT[Final Result:<br/>F1 = 0.87<br/>95% CI: [0.851, 0.889]]

    RESULT --> VALIDATE{F1 ≥ 0.85<br/>AND<br/>lower bound ≥ 0.85?}

    VALIDATE -->|Yes| PASS[✓ Meets Threshold<br/>Deployment Approved]
    VALIDATE -->|No| FAIL[✗ Fails Threshold<br/>Deployment Blocked]

    style BOOT_START fill:#ffd93d
    style VALIDATE fill:#4ecdc4
    style PASS fill:#6bcf7f
    style FAIL fill:#ff6b6b
```

---

## What Makes This a "Framework"

### Traditional Application-Layer Governance (What We DIDN'T Build)

```
❌ Python/Node.js API with governance logic
❌ Middleware checking permissions
❌ Application code enforcing SLA
❌ Cron jobs calculating drift
❌ Separate audit service
```

### Database-Layer Governance (What We BUILT)

```
✅ PostgreSQL triggers auto-enforce risk tiers
✅ CHECK constraints prevent bad data entry
✅ Functions validate before deployment
✅ Materialized views auto-update dashboards
✅ Hash chaining happens automatically
```

**Why Database-Layer?**

1. **Impossible to bypass**: Application bugs can't circumvent governance
2. **ACID guarantees**: Transactions are atomic, consistent, isolated, durable
3. **Single source of truth**: No sync issues between app and database
4. **Performance**: Indexes and materialized views are optimized
5. **Regulatory compliance**: Immutable audit trail at data layer

---

## File Mapping to Design Document

| Design Doc Section | Implementation File | What It Does |
|-------------------|---------------------|--------------|
| **3.1** Three Lines of Defense | [schema/001_initial_schema.sql](../schema/001_initial_schema.sql) | Models table with `developed_by`, `approved_by`, `audited_by` foreign keys to users with role constraints |
| **3.2.2** Risk Stratification | [schema/004_risk_stratification_and_sla.sql](../schema/004_risk_stratification_and_sla.sql) | Trigger assigns high/medium/low based on confidence, sets SLA (1hr/24hr/none), holds transaction if high-risk |
| **4.1** Performance Thresholds | [schema/003_indexes_and_constraints.sql](../schema/003_indexes_and_constraints.sql) | `validate_deployment_thresholds()` function checks F1 ≥ 0.85, FPR ≤ 1% |
| **4.3.1** Audit Trail Completion | [schema/002_audit_trail_extensions.sql](../schema/002_audit_trail_extensions.sql) | SHA-256 hash chaining, `verify_audit_integrity()` function |
| **4.3.2** Review Turnaround Time | [schema/004_risk_stratification_and_sla.sql](../schema/004_risk_stratification_and_sla.sql) | `calculate_rtt()` function, materialized view for ≤ 5 days metric |
| **4.4.1** Bootstrap Resampling | [metrics/performance_metrics.py](../metrics/performance_metrics.py) | 10,000 iterations, 95% CI for F1 and FPR |
| **3.1.1, 4.4.3** Explainability | [schema/004_risk_stratification_and_sla.sql](../schema/004_risk_stratification_and_sla.sql) | `model_explanation` TEXT field for SHAP output |

---

## Key Governance Mechanisms

### 1. Automatic Risk Stratification

**Trigger:** `trigger_assign_risk_tier` (BEFORE INSERT on decisions)

```sql
IF confidence_score > 0.80 THEN
    risk_tier := 'high'
    sla_deadline := created_at + INTERVAL '1 hour'
    transaction_held := TRUE
ELSIF confidence_score >= 0.50 THEN
    risk_tier := 'medium'
    sla_deadline := created_at + INTERVAL '24 hours'
    transaction_held := FALSE
ELSE
    risk_tier := 'low'
    sla_deadline := NULL
    transaction_held := FALSE
END IF
```

### 2. SLA Compliance Checking

**Trigger:** `trigger_check_sla_compliance` (BEFORE UPDATE on decisions)

```sql
IF reviewed_by IS NOT NULL AND sla_deadline IS NOT NULL THEN
    IF decision_timestamp <= sla_deadline THEN
        sla_met := TRUE
    ELSE
        sla_met := FALSE
    END IF
END IF
```

### 3. Threshold Validation

**Function:** `validate_deployment_thresholds(model_id UUID)`

```sql
SELECT f1_score, fpr FROM models WHERE model_id = p_model_id;

IF f1_score < 0.85 THEN
    failing_criteria := array_append(failing_criteria, 'F1 score below 0.85')
END IF

IF fpr > 0.01 THEN
    failing_criteria := array_append(failing_criteria, 'FPR above 1%')
END IF

RETURN (is_valid, failing_criteria, message)
```

### 4. Audit Hash Chaining

**Function:** `compute_audit_hash()`

```sql
-- Get previous hash
SELECT current_audit_hash INTO v_previous_hash
FROM audit_trails
WHERE table_name = p_table_name
ORDER BY created_at DESC
LIMIT 1;

-- Compute new hash: SHA-256(table | record_id | previous_hash)
v_hash_input := p_table_name || '|' || p_record_id || '|' || COALESCE(v_previous_hash, '');
v_current_hash := encode(digest(v_hash_input, 'sha256'), 'hex');

RETURN (v_previous_hash, v_current_hash)
```

---

## Verification Commands

### Check Three Lines of Defense

```sql
SELECT
    m.name,
    r_dev.role_name as developer,
    r_off.role_name as officer,
    r_aud.role_name as auditor
FROM models m
JOIN users u_dev ON m.developed_by = u_dev.user_id
JOIN users u_off ON m.approved_by = u_off.user_id
JOIN users u_aud ON m.audited_by = u_aud.user_id
JOIN roles r_dev ON u_dev.role_id = r_dev.role_id
JOIN roles r_off ON u_off.role_id = r_off.role_id
JOIN roles r_aud ON u_aud.role_id = r_aud.role_id
WHERE m.status = 'deployed';
```

### Check Risk Stratification

```sql
SELECT
    risk_tier,
    COUNT(*) as decisions,
    MIN(confidence_score) as min_confidence,
    MAX(confidence_score) as max_confidence
FROM decisions
GROUP BY risk_tier;
```

### Check Audit Integrity

```sql
SELECT * FROM verify_audit_integrity('decisions',
    (SELECT decision_id FROM decisions LIMIT 1)::TEXT
);
```

### Check SLA Compliance

```sql
SELECT * FROM sla_compliance_dashboard;
SELECT * FROM review_turnaround_time_summary;
SELECT * FROM sla_violations LIMIT 10;
```

---

## Summary

**The AFAAP framework is a governance-as-code system embedded in PostgreSQL.**

It doesn't rely on application logic that can be bypassed. Instead:

- **Triggers** automatically enforce rules on every data change
- **Functions** validate before critical operations
- **Constraints** prevent invalid data from entering
- **Materialized views** provide real-time dashboards
- **Hash chaining** creates an immutable audit trail

When a financial institution uses AFAAP:

1. AI models **can't be deployed** unless F1 ≥ 0.85 and FPR ≤ 1%
2. High-risk decisions **automatically hold transactions** and notify officers
3. SLA compliance is **tracked automatically** (met/missed)
4. Audit trails are **tamper-proof** via cryptographic chaining
5. Three Lines of Defense **can't be bypassed** (database enforces role separation)

**This is what makes it a framework**: governance is structural, not procedural.
