# AFAAP Setup Guide

Complete installation and configuration instructions for the AI Financial Accountability and Auditability Protocol governance framework.

## Prerequisites

### System Requirements
- Python 3.10 or higher
- PostgreSQL 14 or higher
- 4GB RAM minimum (8GB recommended)
- 10GB disk space

### Development Tools
- Git
- pip (Python package manager)
- psql (PostgreSQL client)
- curl (for API testing)

## Installation Steps

### 1. Clone Repository

```bash
git clone <repository-url>
cd afaap-governance
```

### 2. Python Environment Setup

#### Create Virtual Environment

```bash
# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

#### Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

### 3. PostgreSQL Database Setup

#### Install PostgreSQL

**macOS (using Homebrew):**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql-14 postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download and install from https://www.postgresql.org/download/windows/

#### Create Database and User

```bash
# Connect to PostgreSQL as superuser
psql -U postgres

# Create database
CREATE DATABASE afaap;

# Create user with password
CREATE USER afaap_admin WITH PASSWORD 'your_secure_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE afaap TO afaap_admin;

# Exit psql
\q
```

#### Initialize Schema

```bash
# Run schema migrations in order
psql -U afaap_admin -d afaap -f schema/001_initial_schema.sql
psql -U afaap_admin -d afaap -f schema/002_audit_trail_extensions.sql
psql -U afaap_admin -d afaap -f schema/003_indexes_and_constraints.sql

# Verify tables were created
psql -U afaap_admin -d afaap -c "\dt"
```

Expected output should show tables:
- models
- decisions
- audit_trails
- revalidation_workflows
- failure_incidents
- users
- roles

### 4. Environment Configuration

Create a `.env` file in the project root:

```bash
# Copy example environment file
cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://afaap_admin:your_secure_password@localhost:5432/afaap
DATABASE_ECHO=false

# API Configuration
API_SECRET_KEY=your-secret-key-generate-with-openssl
API_ALGORITHM=HS256
API_ACCESS_TOKEN_EXPIRE_MINUTES=30
API_HOST=0.0.0.0
API_PORT=8000

# Governance Thresholds (configurable per regulatory requirement)
AFAAP_MIN_F1_SCORE=0.85
AFAAP_MAX_FPR=0.01
AFAAP_MIN_AUDIT_COMPLETION=0.98
AFAAP_MAX_REVIEW_TURNAROUND_DAYS=5

# Metrics Configuration
CONFIDENCE_INTERVAL=0.95
BOOTSTRAP_ITERATIONS=10000
FAIRNESS_DISPARITY_THRESHOLD=0.10

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=logs/afaap.log

# Dashboard
DASHBOARD_PORT=8501
DASHBOARD_REFRESH_INTERVAL=5
EOF
```

#### Generate Secret Key

```bash
# Generate a secure secret key
openssl rand -hex 32

# Update API_SECRET_KEY in .env with the generated key
```

### 5. Generate Synthetic Data

```bash
# Create data directory
mkdir -p data/generated

# Run synthetic data generator
python data/synthetic_dataset_generator.py

# Verify data was created
psql -U afaap_admin -d afaap -c "SELECT COUNT(*) FROM decisions;"
```

### 6. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

Expected: All tests pass, coverage >80%

### 7. Start API Server

```bash
# Development mode with auto-reload
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Verify API is running:
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# View API documentation
open http://localhost:8000/docs
```

### 8. Launch Compliance Dashboard

In a new terminal:

```bash
# Activate virtual environment
source venv/bin/activate

# Start Streamlit dashboard
streamlit run dashboard/streamlit_app.py --server.port 8501
```

Dashboard will open automatically at http://localhost:8501

## Verification Checklist

- [ ] PostgreSQL running and accessible
- [ ] Database `afaap` created with all tables
- [ ] Virtual environment activated
- [ ] All dependencies installed without errors
- [ ] `.env` file configured with secure credentials
- [ ] Synthetic data generated successfully
- [ ] All tests passing
- [ ] API server responding at http://localhost:8000
- [ ] API documentation accessible at http://localhost:8000/docs
- [ ] Streamlit dashboard running at http://localhost:8501

## Quick Test of End-to-End Workflow

```bash
# 1. Create a test user (compliance officer)
curl -X POST http://localhost:8000/api/v1/users/create \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_officer",
    "email": "officer@example.com",
    "role": "compliance_officer"
  }'

# 2. Submit a model for pre-deployment approval
curl -X POST http://localhost:8000/api/v1/compliance/approve-deployment \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "fraud_detector_v1",
    "f1_score": 0.87,
    "fpr": 0.008,
    "training_data_provenance": "transactions_2024_q1",
    "safety_case": "Model validated on 100k transactions..."
  }'

# 3. Query metrics
curl http://localhost:8000/api/v1/metrics/dashboard-data?model_id=1

# 4. View audit trail
curl http://localhost:8000/api/v1/audit/trail/1
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
pg_isready

# Check connection with psql
psql -U afaap_admin -d afaap -c "SELECT version();"

# View PostgreSQL logs
tail -f /usr/local/var/log/postgresql@14.log  # macOS
tail -f /var/log/postgresql/postgresql-14-main.log  # Linux
```

### Python Import Errors

```bash
# Verify virtual environment is activated
which python
# Should show path to venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn api.main:app --port 8001
```

### Schema Migration Issues

```bash
# Drop and recreate database (WARNING: deletes all data)
psql -U postgres -c "DROP DATABASE afaap;"
psql -U postgres -c "CREATE DATABASE afaap;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE afaap TO afaap_admin;"

# Re-run migrations
psql -U afaap_admin -d afaap -f schema/001_initial_schema.sql
psql -U afaap_admin -d afaap -f schema/002_audit_trail_extensions.sql
psql -U afaap_admin -d afaap -f schema/003_indexes_and_constraints.sql
```

## Production Deployment Considerations

### Security Hardening

1. **Change default passwords** in `.env`
2. **Enable SSL/TLS** for PostgreSQL connections
3. **Set up firewall rules** to restrict database access
4. **Use environment-specific secrets management** (AWS Secrets Manager, HashiCorp Vault)
5. **Enable audit logging** at database level

### Performance Optimization

1. **Configure connection pooling** (PgBouncer recommended)
2. **Set appropriate `work_mem` and `shared_buffers`** in postgresql.conf
3. **Create additional indexes** based on query patterns
4. **Set up read replicas** for reporting queries
5. **Implement query result caching** for dashboard

### Monitoring

1. **Set up application logging** (ELK stack, CloudWatch)
2. **Configure database monitoring** (pg_stat_statements, pgAdmin)
3. **Set up alerting** for governance threshold violations
4. **Implement health checks** for all services
5. **Monitor disk usage** for audit log growth

### Backup Strategy

```bash
# Daily automated backups
pg_dump -U afaap_admin -d afaap -F c -f backup_$(date +%Y%m%d).dump

# Restore from backup
pg_restore -U afaap_admin -d afaap -c backup_20240101.dump

# Set up automated backup cron job
0 2 * * * /usr/local/bin/pg_dump -U afaap_admin -d afaap -F c -f /backups/afaap_$(date +\%Y\%m\%d).dump
```

## Local Development Workflow

```bash
# 1. Pull latest changes
git pull origin main

# 2. Activate virtual environment
source venv/bin/activate

# 3. Install any new dependencies
pip install -r requirements.txt

# 4. Run migrations if schema changed
psql -U afaap_admin -d afaap -f schema/001_initial_schema.sql

# 5. Run tests before committing
pytest tests/ -v

# 6. Start development server
uvicorn api.main:app --reload
```

## Next Steps

1. Review [governance_workflows.md](docs/governance_workflows.md) to understand the compliance processes
2. Explore the [API documentation](http://localhost:8000/docs) for available endpoints
3. Test the dashboard at http://localhost:8501
4. Review sample audit trails in [data/sample_audit_trails.json](data/sample_audit_trails.json)
5. Run the end-to-end test workflow in [tests/test_end_to_end_workflow.py](tests/test_end_to_end_workflow.py)

## Support

For issues or questions:
- Check [troubleshooting.md](docs/troubleshooting.md)
- Review test files for usage examples
- File an issue on GitHub

## Maintenance

### Weekly Tasks
- Monitor disk usage for audit logs
- Review API access logs for anomalies
- Check compliance threshold violations

### Monthly Tasks
- Backup database
- Review and rotate API keys
- Update dependencies (security patches)

### Quarterly Tasks
- Run full compliance audit
- Review governance thresholds
- Performance optimization review
- Disaster recovery drill
