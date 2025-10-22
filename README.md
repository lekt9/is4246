# AFAAP Governance Framework

## AI Financial Accountability and Auditability Protocol

A production-ready governance framework for AI-powered fraud detection systems in financial institutions, designed to operationalize regulatory compliance under Singapore's MAS oversight.

## Overview

AFAAP implements a comprehensive governance mechanism based on the Three Lines of Defense (3LOD) model, ensuring:

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

### 4. API Layer
- RESTful endpoints for compliance operations
- Role-based access control enforcement
- Real-time metrics querying
- Incident reporting and tracking

### 5. Compliance Dashboard
- Real-time metrics visualization
- Model deployment status tracking
- Incident monitoring and remediation tracking
- Compliance health alerts

## Project Structure

```
afaap-governance/
├── schema/              # PostgreSQL database schemas
├── metrics/             # Performance and process metrics
├── governance/          # Decision engine and workflows
├── api/                 # FastAPI application
├── dashboard/           # Streamlit compliance dashboard
├── data/                # Synthetic data generation
├── tests/               # Comprehensive test suite
└── docs/                # Documentation
```

## Quick Start

See [setup.md](setup.md) for detailed installation instructions.

```bash
# 1. Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up PostgreSQL database
# See setup.md for database initialization

# 4. Run database migrations
psql -U postgres -f schema/001_initial_schema.sql
psql -U postgres -f schema/002_audit_trail_extensions.sql
psql -U postgres -f schema/003_indexes_and_constraints.sql

# 5. Generate synthetic data
python data/synthetic_dataset_generator.py

# 6. Run tests
pytest tests/ -v

# 7. Start API server
uvicorn api.main:app --reload

# 8. Launch compliance dashboard
streamlit run dashboard/streamlit_app.py
```

## Architecture

### Three Lines of Defense (3LOD)

1. **First Line (Development Team)**
   - Model development and initial testing
   - Performance metric tracking
   - Issue detection and reporting

2. **Second Line (Compliance Officers)**
   - Pre-deployment approval
   - Human-in-the-loop review of flagged transactions
   - Re-validation oversight
   - Process compliance monitoring

3. **Third Line (Independent Auditors)**
   - Quarterly compliance audits
   - Incident investigation
   - Governance framework validation
   - Regulatory reporting

### Data Flow

```
Transaction → Model Prediction → Decision Logging → Audit Trail
                                        ↓
                            Compliance Officer Review
                                        ↓
                            Decision + Officer Annotation
                                        ↓
                            Immutable Audit Record
```

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
```

## Security & Compliance

### Data Integrity
- Checksums on decision logs to prevent tampering
- Cascading deletes forbidden (no accidental data loss)
- Serializable isolation for concurrent writes
- Quarterly audit trail completeness validation

### Access Control
- Role-based access: developer, compliance_officer, auditor
- Audit logs queryable by auditors only
- All database operations logged with role information
- Failed access attempts logged and alerted

### Error Handling
- Structured logging in JSON format
- Compliance violations generate alerts (not silent failures)
- Every error traces back to responsible role
- Audit trail of all system errors

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test suites
pytest tests/test_schema_integrity.py -v
pytest tests/test_metrics.py -v
pytest tests/test_governance.py -v
pytest tests/test_end_to_end_workflow.py -v
```

Target: >80% code coverage

## Documentation

- [Setup Guide](setup.md) - Installation and environment setup
- [Schema Documentation](schema/README.md) - Database design with ER diagrams
- [Governance Workflows](docs/governance_workflows.md) - Step-by-step process guides
- [API Specification](docs/api_spec.md) - REST API documentation
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

## Performance Targets

- Database: Support 1M+ rows without query degradation
- Metrics: Calculate F1/FPR for 100k transactions in <5 seconds
- API: Response times <500ms under normal load
- Dashboard: Real-time updates with <2 second refresh

## Contributing

This is an open-source governance framework for regulatory pilot programs. Contributions should maintain:

- Production-ready code quality (error handling, logging, type hints)
- Governance-conscious design (every decision path documented)
- Defensive programming (validate all inputs, assume adversarial actors)
- Transparent audit trails (primary output, not afterthought)

## License

MIT License - See LICENSE file for details

## Contact

For questions about MAS regulatory compliance or framework customization, see documentation or file an issue.

## Acknowledgments

Designed for Singapore's Monetary Authority (MAS) oversight framework, based on the Three Lines of Defense model for AI governance in financial institutions.
