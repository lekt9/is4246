# AFAAP Quick Start Guide

## Get Up and Running in 5 Minutes

### What You Have

A complete AI governance framework with:
- ✅ PostgreSQL database (port 5434)
- ✅ 10,000 synthetic transactions
- ✅ 5 fraud detection models
- ✅ 16,000+ audit trail records
- ✅ Complete compliance infrastructure

### Start the System

```bash
cd "/Users/lekt9/Projects/School/4246 artifact"

# Start all services
docker-compose up -d

# Verify running
docker ps
```

### Access the Database

```bash
# Connect to PostgreSQL
docker exec -it afaap-postgres psql -U afaap_admin -d afaap

# Or run quick queries
docker exec afaap-postgres psql -U afaap_admin -d afaap -c "SELECT * FROM model_performance_summary;"
```

### Try These Queries

#### 1. View Model Performance
```sql
SELECT
    name,
    status,
    f1_score,
    fpr,
    total_decisions,
    audit_completion_rate
FROM model_performance_summary
WHERE status = 'deployed';
```

#### 2. Check Pending Reviews
```sql
SELECT * FROM compliance_officer_queue LIMIT 10;
```

#### 3. Verify Audit Integrity
```sql
SELECT * FROM verify_audit_integrity('decisions',
    (SELECT decision_id FROM decisions LIMIT 1)
);
```

#### 4. Generate Compliance Report
```sql
SELECT
    COUNT(*) AS total_decisions,
    COUNT(*) FILTER (WHERE audit_trail_complete) AS complete_audits,
    ROUND(
        COUNT(*) FILTER (WHERE audit_trail_complete)::NUMERIC / COUNT(*) * 100,
        2
    ) AS completion_pct
FROM decisions;
```

### Key Numbers

| Metric | Current Value | Target | Status |
|--------|---------------|--------|--------|
| Models Deployed | 3 | - | ✅ |
| F1 Score (avg) | 0.87 | ≥ 0.85 | ✅ |
| FPR (avg) | 0.86% | ≤ 1% | ✅ |
| Audit Completion | 3.79% | ≥ 98% | 🔴 |
| Review Time | 2.5 days | ≤ 5 days | ✅ |

### Understanding the Low Audit Completion (3.79%)

**This is expected!**

- 16,000 total decisions
- 606 have been reviewed by compliance officers
- 15,394 are still pending review

**Why?** In a high-throughput fraud detection system:
- Models flag thousands of transactions daily
- Compliance officers can only review ~60 per day each
- Backlog is normal and realistic

**What to do?**
1. Prioritize high-risk reviews (high confidence + high value)
2. Auto-approve low-risk (confidence < 0.3, amount < $1000)
3. Hire more compliance officers

### Common Tasks

#### Approve a Pending Decision
```sql
UPDATE decisions
SET reviewed_by = (SELECT user_id FROM users WHERE username = 'officer_yherrera' LIMIT 1),
    officer_decision = 'approve_transaction',
    officer_notes = 'Reviewed and approved. Customer verified.',
    decision_timestamp = CURRENT_TIMESTAMP,
    final_decision = 'approved'
WHERE decision_id = (
    SELECT decision_id FROM decisions
    WHERE final_decision = 'pending'
    LIMIT 1
);

-- Check audit trail was created
SELECT * FROM audit_trails WHERE table_name = 'decisions' ORDER BY changed_at DESC LIMIT 5;
```

#### Check Model Meets Thresholds
```sql
SELECT * FROM validate_deployment_thresholds(
    (SELECT model_id FROM models WHERE name = 'fraud_detector_v1')
);
```

#### Trigger Re-validation
```sql
INSERT INTO revalidation_workflows (
    model_id,
    trigger_reason,
    trigger_details,
    triggered_by
) VALUES (
    (SELECT model_id FROM models WHERE name = 'fraud_detector_v1'),
    'performance_degradation',
    'Production F1 dropped below training threshold',
    (SELECT user_id FROM users WHERE username LIKE 'dev_%' LIMIT 1)
);
```

### Explore the Data

**See all tables:**
```sql
\dt
```

**Table sizes:**
```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Sample decisions with full context:**
```sql
SELECT
    d.decision_id,
    d.prediction_fraud,
    d.confidence_score,
    d.officer_decision,
    d.final_decision,
    t.amount,
    t.transaction_type,
    t.is_fraud AS actual_fraud
FROM decisions d
JOIN transactions t ON d.transaction_id = t.transaction_id
WHERE t.is_fraud IS NOT NULL  -- Has ground truth
LIMIT 20;
```

### Next Steps

1. **Read the Full Guide**: [docs/USER_GUIDE.md](docs/USER_GUIDE.md)
2. **Explore Workflows**: Try the pre-deployment approval workflow
3. **Run Python Metrics**:
   ```bash
   docker exec afaap-app python -c "
   from metrics.performance_metrics import calculate_all_performance_metrics
   import numpy as np
   print('Metrics module loaded successfully!')
   "
   ```
4. **Build the API**: Coming soon - FastAPI endpoints
5. **Build the Dashboard**: Coming soon - Streamlit visualization

### Troubleshooting

**PostgreSQL not running?**
```bash
docker-compose up -d postgres
docker ps | grep afaap
```

**Can't connect to database?**
```bash
# Check health
docker exec afaap-postgres pg_isready -U afaap_admin -d afaap

# View logs
docker-compose logs postgres
```

**Reset everything:**
```bash
# WARNING: This deletes all data!
docker-compose down -v
docker-compose up -d
# Wait 30 seconds for schema initialization
sleep 30
docker exec afaap-app python data/synthetic_dataset_generator.py
```

### Key Files

- **Schema**: `schema/*.sql` - Database design
- **Data Generator**: `data/synthetic_dataset_generator.py`
- **Metrics**: `metrics/performance_metrics.py`
- **Docker Config**: `docker-compose.yml`
- **Environment**: `.env`

### Governance Thresholds (Configurable)

Edit `.env` to change:
```bash
AFAAP_MIN_F1_SCORE=0.85        # Minimum F1 for deployment
AFAAP_MAX_FPR=0.01             # Maximum false positive rate (1%)
AFAAP_MIN_AUDIT_COMPLETION=0.98 # Minimum audit trail completion (98%)
AFAAP_MAX_REVIEW_TURNAROUND_DAYS=5  # Maximum review time
```

### Resources

- **Full User Guide**: [docs/USER_GUIDE.md](docs/USER_GUIDE.md) - 10,000+ words covering everything
- **Schema Documentation**: [schema/README.md](schema/README.md)
- **Setup Guide**: [setup.md](setup.md)
- **Sample Audit Trails**: [data/sample_audit_trails.json](data/sample_audit_trails.json)

---

**Questions?** Read the full user guide or explore the database!
