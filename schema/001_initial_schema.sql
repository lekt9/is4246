-- AI Financial Accountability and Auditability Protocol (AFAAP)
-- Initial Schema - Core Tables
-- Version: 1.0.0
--
-- Governance Note: This schema implements the Three Lines of Defense (3LOD) model
-- for AI fraud detection systems. All tables support immutable audit trails and
-- role-based access control as required by MAS oversight.

-- Enable UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgcrypto for checksum generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- ROLES AND USERS
-- =============================================================================

-- Governance Rule: User roles must align with 3LOD model
-- - developer: First line (model development)
-- - compliance_officer: Second line (review and approval)
-- - auditor: Third line (independent oversight)
CREATE TABLE IF NOT EXISTS roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_role_name CHECK (role_name IN ('developer', 'compliance_officer', 'auditor', 'admin'))
);

-- Insert default roles
INSERT INTO roles (role_name, description) VALUES
    ('developer', 'First line of defense - model development and testing'),
    ('compliance_officer', 'Second line of defense - compliance review and approval'),
    ('auditor', 'Third line of defense - independent oversight and audit'),
    ('admin', 'System administrator with full access')
ON CONFLICT (role_name) DO NOTHING;

-- User accounts with RBAC
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    role_id INTEGER NOT NULL REFERENCES roles(role_id),
    hashed_password VARCHAR(255), -- NULL for SSO/SAML users
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES users(user_id),

    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Create index for authentication lookups
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role_id);

-- =============================================================================
-- MODEL METADATA
-- =============================================================================

-- Governance Rule: All models must have complete metadata before deployment
-- Pre-deployment validation requires F1 ≥ 0.85, FPR ≤ 1%
CREATE TABLE IF NOT EXISTS models (
    model_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,

    -- Training provenance (regulatory requirement)
    training_data_provenance TEXT NOT NULL, -- Dataset name, version, date range
    training_start_date DATE NOT NULL,
    training_end_date DATE NOT NULL,
    training_record_count INTEGER NOT NULL,

    -- Performance metrics (pre-deployment validation)
    f1_score NUMERIC(5, 4) NOT NULL, -- Must be >= 0.85
    fpr NUMERIC(5, 4) NOT NULL, -- Must be <= 0.01 (1%)
    precision_score NUMERIC(5, 4) NOT NULL,
    recall_score NUMERIC(5, 4) NOT NULL,
    auc_roc NUMERIC(5, 4),

    -- Confidence intervals for regulatory reporting
    f1_ci_lower NUMERIC(5, 4),
    f1_ci_upper NUMERIC(5, 4),
    fpr_ci_lower NUMERIC(5, 4),
    fpr_ci_upper NUMERIC(5, 4),

    -- Model lineage
    parent_model_id UUID REFERENCES models(model_id), -- NULL if initial version
    model_type VARCHAR(100), -- e.g., 'random_forest', 'neural_network'
    fraud_types_targeted TEXT[], -- Array of fraud types this model detects

    -- Deployment status
    status VARCHAR(50) NOT NULL DEFAULT 'pending_approval',
    deployment_date TIMESTAMP WITH TIME ZONE,
    retirement_date TIMESTAMP WITH TIME ZONE,

    -- Accountability
    developed_by UUID NOT NULL REFERENCES users(user_id),
    approved_by UUID REFERENCES users(user_id), -- compliance_officer who approved
    audited_by UUID REFERENCES users(user_id), -- auditor who reviewed

    -- Audit metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Governance constraints
    CONSTRAINT valid_status CHECK (status IN ('pending_approval', 'approved', 'deployed', 'under_review', 'retired', 'rejected')),
    CONSTRAINT valid_f1_score CHECK (f1_score >= 0 AND f1_score <= 1),
    CONSTRAINT valid_fpr CHECK (fpr >= 0 AND fpr <= 1),
    CONSTRAINT valid_precision CHECK (precision_score >= 0 AND precision_score <= 1),
    CONSTRAINT valid_recall CHECK (recall_score >= 0 AND recall_score <= 1),
    CONSTRAINT unique_model_version UNIQUE (name, version),
    CONSTRAINT valid_training_dates CHECK (training_end_date >= training_start_date),
    CONSTRAINT positive_record_count CHECK (training_record_count > 0)
);

-- Performance indexes
CREATE INDEX idx_models_status ON models(status);
CREATE INDEX idx_models_developed_by ON models(developed_by);
CREATE INDEX idx_models_deployment_date ON models(deployment_date);
CREATE INDEX idx_models_name_version ON models(name, version);

-- =============================================================================
-- TRANSACTIONS (for linking to fraud detection decisions)
-- =============================================================================

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_transaction_id VARCHAR(255) NOT NULL UNIQUE, -- Bank's internal ID

    -- Transaction details
    transaction_type VARCHAR(100) NOT NULL, -- 'wire_transfer', 'credit_card', 'ach', etc.
    amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'SGD',
    transaction_date TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Geographic data (for fairness analysis)
    origin_country VARCHAR(3), -- ISO 3166-1 alpha-3
    destination_country VARCHAR(3),

    -- Customer data (anonymized for privacy)
    customer_segment VARCHAR(50), -- 'retail', 'corporate', 'institutional'
    customer_risk_profile VARCHAR(50), -- 'low', 'medium', 'high'

    -- Ground truth (for validation)
    is_fraud BOOLEAN, -- NULL if not yet verified, TRUE/FALSE once confirmed
    fraud_type VARCHAR(100), -- Type of fraud if is_fraud = TRUE
    verified_at TIMESTAMP WITH TIME ZONE,
    verified_by UUID REFERENCES users(user_id),

    -- Audit metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_amount CHECK (amount >= 0),
    CONSTRAINT valid_currency CHECK (LENGTH(currency) = 3)
);

-- Indexes for query performance
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);
CREATE INDEX idx_transactions_country ON transactions(origin_country, destination_country);
CREATE INDEX idx_transactions_fraud ON transactions(is_fraud) WHERE is_fraud IS NOT NULL;

-- =============================================================================
-- FRAUD DETECTION DECISIONS
-- =============================================================================

-- Governance Rule: Every model prediction must be logged with complete audit trail
-- Audit trail completion rate must be ≥ 98%
CREATE TABLE IF NOT EXISTS decisions (
    decision_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Links to model and transaction
    model_id UUID NOT NULL REFERENCES models(model_id),
    transaction_id UUID NOT NULL REFERENCES transactions(transaction_id),

    -- Model prediction
    prediction_fraud BOOLEAN NOT NULL, -- Model's prediction
    confidence_score NUMERIC(5, 4) NOT NULL, -- Model confidence (0-1)
    model_features JSONB, -- Features used for prediction (for explainability)
    flag_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Human review (compliance officer decision)
    reviewed_by UUID REFERENCES users(user_id), -- compliance_officer
    officer_decision VARCHAR(50), -- 'approve_transaction', 'block_transaction', 'escalate', 'pending'
    officer_notes TEXT, -- Justification for decision
    decision_timestamp TIMESTAMP WITH TIME ZONE,

    -- Final outcome
    final_decision VARCHAR(50) NOT NULL DEFAULT 'pending',
    escalated_to UUID REFERENCES users(user_id), -- Senior officer if escalated
    escalation_reason TEXT,

    -- Audit trail integrity
    audit_trail_hash VARCHAR(64) NOT NULL, -- SHA-256 hash for tamper detection
    audit_trail_complete BOOLEAN NOT NULL DEFAULT FALSE, -- Set TRUE when all fields populated

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Governance constraints
    CONSTRAINT valid_confidence CHECK (confidence_score >= 0 AND confidence_score <= 1),
    CONSTRAINT valid_officer_decision CHECK (
        officer_decision IS NULL OR
        officer_decision IN ('approve_transaction', 'block_transaction', 'escalate', 'pending', 'false_positive')
    ),
    CONSTRAINT valid_final_decision CHECK (
        final_decision IN ('pending', 'approved', 'blocked', 'escalated', 'false_positive')
    ),
    CONSTRAINT review_requires_officer CHECK (
        (officer_decision IS NULL AND reviewed_by IS NULL) OR
        (officer_decision IS NOT NULL AND reviewed_by IS NOT NULL)
    )
);

-- Performance indexes
CREATE INDEX idx_decisions_model ON decisions(model_id);
CREATE INDEX idx_decisions_transaction ON decisions(transaction_id);
CREATE INDEX idx_decisions_flag_timestamp ON decisions(flag_timestamp);
CREATE INDEX idx_decisions_reviewed_by ON decisions(reviewed_by);
CREATE INDEX idx_decisions_audit_complete ON decisions(audit_trail_complete);
CREATE INDEX idx_decisions_final_decision ON decisions(final_decision);

-- =============================================================================
-- RE-VALIDATION WORKFLOWS
-- =============================================================================

-- Governance Rule: Models must be re-validated when repurposed for new fraud types
-- or when performance degrades below thresholds
CREATE TABLE IF NOT EXISTS revalidation_workflows (
    revalidation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Model being revalidated
    model_id UUID NOT NULL REFERENCES models(model_id),

    -- Trigger reason
    trigger_reason VARCHAR(100) NOT NULL,
    trigger_details TEXT NOT NULL,
    triggered_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    triggered_by UUID NOT NULL REFERENCES users(user_id),

    -- New use case (if repurposed)
    new_fraud_types TEXT[], -- New fraud types being targeted
    new_data_provenance TEXT, -- New dataset used for validation

    -- Re-validation results
    revalidation_f1_score NUMERIC(5, 4),
    revalidation_fpr NUMERIC(5, 4),
    revalidation_test_set_size INTEGER,
    revalidation_report_url TEXT, -- Link to detailed validation report

    -- Approval workflow
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    reviewed_by UUID REFERENCES users(user_id), -- compliance_officer
    review_notes TEXT,
    review_date TIMESTAMP WITH TIME ZONE,

    -- Final approval
    approved_by UUID REFERENCES users(user_id), -- auditor
    approval_date TIMESTAMP WITH TIME ZONE,
    approval_notes TEXT,

    -- Audit metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Governance constraints
    CONSTRAINT valid_trigger_reason CHECK (
        trigger_reason IN (
            'new_fraud_type',
            'performance_degradation',
            'data_distribution_shift',
            'regulatory_requirement',
            'scheduled_review'
        )
    ),
    CONSTRAINT valid_revalidation_status CHECK (
        status IN ('pending', 'under_review', 'approved', 'rejected', 'requires_changes')
    ),
    CONSTRAINT revalidation_f1_range CHECK (
        revalidation_f1_score IS NULL OR
        (revalidation_f1_score >= 0 AND revalidation_f1_score <= 1)
    ),
    CONSTRAINT revalidation_fpr_range CHECK (
        revalidation_fpr IS NULL OR
        (revalidation_fpr >= 0 AND revalidation_fpr <= 1)
    )
);

-- Indexes
CREATE INDEX idx_revalidation_model ON revalidation_workflows(model_id);
CREATE INDEX idx_revalidation_status ON revalidation_workflows(status);
CREATE INDEX idx_revalidation_triggered_date ON revalidation_workflows(triggered_date);

-- =============================================================================
-- FAILURE INCIDENTS
-- =============================================================================

-- Governance Rule: All model failures must be documented with root cause analysis
-- and accountability attribution. Independent auditor must sign off on remediation.
CREATE TABLE IF NOT EXISTS failure_incidents (
    incident_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Related model
    model_id UUID NOT NULL REFERENCES models(model_id),

    -- Incident details
    failure_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    detected_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    detected_by UUID NOT NULL REFERENCES users(user_id),

    -- Impact assessment
    affected_transaction_count INTEGER,
    false_positive_count INTEGER,
    false_negative_count INTEGER,
    financial_impact NUMERIC(15, 2), -- In SGD

    -- Root cause analysis
    root_cause TEXT,
    root_cause_category VARCHAR(100),
    contributing_factors TEXT[],

    -- Accountability attribution
    responsible_party VARCHAR(100) NOT NULL, -- 'developer', 'financial_institution', 'vendor', 'data_issue'
    assigned_to UUID REFERENCES users(user_id), -- Person responsible for remediation

    -- Remediation
    remediation_plan TEXT,
    remediation_status VARCHAR(50) NOT NULL DEFAULT 'open',
    remediation_completed_date TIMESTAMP WITH TIME ZONE,
    remediation_verified_by UUID REFERENCES users(user_id),

    -- Auditor sign-off (required for closure)
    auditor_signoff_date TIMESTAMP WITH TIME ZONE,
    auditor_signoff_by UUID REFERENCES users(user_id),
    auditor_notes TEXT,

    -- Regulatory reporting
    reported_to_regulator BOOLEAN NOT NULL DEFAULT FALSE,
    regulator_report_date TIMESTAMP WITH TIME ZONE,
    regulator_case_id VARCHAR(255),

    -- Audit metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Governance constraints
    CONSTRAINT valid_failure_type CHECK (
        failure_type IN (
            'performance_degradation',
            'false_positive_spike',
            'false_negative_spike',
            'bias_detection',
            'system_error',
            'data_quality_issue',
            'model_drift'
        )
    ),
    CONSTRAINT valid_severity CHECK (
        severity IN ('critical', 'high', 'medium', 'low')
    ),
    CONSTRAINT valid_responsible_party CHECK (
        responsible_party IN ('developer', 'financial_institution', 'vendor', 'data_issue', 'external_factor')
    ),
    CONSTRAINT valid_remediation_status CHECK (
        remediation_status IN ('open', 'in_progress', 'resolved', 'closed', 'monitoring')
    ),
    CONSTRAINT closure_requires_signoff CHECK (
        remediation_status != 'closed' OR
        (auditor_signoff_date IS NOT NULL AND auditor_signoff_by IS NOT NULL)
    )
);

-- Indexes
CREATE INDEX idx_incidents_model ON failure_incidents(model_id);
CREATE INDEX idx_incidents_severity ON failure_incidents(severity);
CREATE INDEX idx_incidents_status ON failure_incidents(remediation_status);
CREATE INDEX idx_incidents_detected_date ON failure_incidents(detected_date);
CREATE INDEX idx_incidents_responsible ON failure_incidents(responsible_party);

-- =============================================================================
-- CONFIGURATION
-- =============================================================================

-- Governance thresholds (configurable per regulatory requirement)
CREATE TABLE IF NOT EXISTS governance_config (
    config_id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value VARCHAR(255) NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(user_id)
);

-- Insert default thresholds
INSERT INTO governance_config (config_key, config_value, description) VALUES
    ('min_f1_score', '0.85', 'Minimum F1 score for model deployment'),
    ('max_fpr', '0.01', 'Maximum false positive rate (1%)'),
    ('min_audit_completion', '0.98', 'Minimum audit trail completion rate (98%)'),
    ('max_review_turnaround_days', '5', 'Maximum days for compliance officer review'),
    ('confidence_interval', '0.95', 'Confidence interval for statistical metrics'),
    ('bootstrap_iterations', '10000', 'Bootstrap iterations for CI calculation'),
    ('fairness_disparity_threshold', '0.10', 'Maximum acceptable FPR disparity across groups (10%)')
ON CONFLICT (config_key) DO NOTHING;

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE roles IS 'User roles aligned with Three Lines of Defense (3LOD) model';
COMMENT ON TABLE users IS 'User accounts with role-based access control';
COMMENT ON TABLE models IS 'AI/ML model metadata including performance metrics and lineage';
COMMENT ON TABLE transactions IS 'Financial transactions for fraud detection';
COMMENT ON TABLE decisions IS 'Fraud detection decisions with human-in-the-loop review';
COMMENT ON TABLE revalidation_workflows IS 'Model re-validation workflows for new use cases';
COMMENT ON TABLE failure_incidents IS 'Model failure tracking with root cause and remediation';
COMMENT ON TABLE governance_config IS 'Configurable governance thresholds';

COMMENT ON COLUMN models.f1_score IS 'Pre-deployment requirement: F1 >= 0.85';
COMMENT ON COLUMN models.fpr IS 'Pre-deployment requirement: FPR <= 0.01 (1%)';
COMMENT ON COLUMN decisions.audit_trail_hash IS 'SHA-256 hash for tamper detection';
COMMENT ON COLUMN decisions.audit_trail_complete IS 'Target: 98% completion rate';
COMMENT ON COLUMN failure_incidents.auditor_signoff_date IS 'Required before incident closure';
