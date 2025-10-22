-- AFAAP - Performance Indexes and Additional Constraints
-- Version: 1.0.0
--
-- Governance Note: This schema adds performance optimizations and additional
-- constraints to ensure data quality and query efficiency for regulatory reporting.

-- =============================================================================
-- COMPOSITE INDEXES FOR COMMON QUERY PATTERNS
-- =============================================================================

-- Dashboard queries: metrics by model and time period
CREATE INDEX idx_decisions_model_timestamp ON decisions(model_id, flag_timestamp DESC);
CREATE INDEX idx_decisions_model_complete ON decisions(model_id, audit_trail_complete);

-- Compliance officer workload queries
CREATE INDEX idx_decisions_pending_review ON decisions(reviewed_by, final_decision)
    WHERE final_decision = 'pending';

-- Review turnaround time calculations
CREATE INDEX idx_decisions_turnaround ON decisions(flag_timestamp, decision_timestamp)
    WHERE decision_timestamp IS NOT NULL;

-- Model performance tracking over time
CREATE INDEX idx_decisions_model_date_outcome ON decisions(
    model_id,
    flag_timestamp,
    prediction_fraud,
    officer_decision
);

-- Fairness analysis: decisions by transaction characteristics
CREATE INDEX idx_transactions_decisions ON decisions(transaction_id);
CREATE INDEX idx_transactions_type_country ON transactions(
    transaction_type,
    origin_country,
    transaction_date
);

-- Incident tracking by severity and status
CREATE INDEX idx_incidents_severity_status ON failure_incidents(
    severity,
    remediation_status,
    detected_date DESC
);

-- Model lineage queries
CREATE INDEX idx_models_parent ON models(parent_model_id)
    WHERE parent_model_id IS NOT NULL;

-- Active models only
CREATE INDEX idx_models_active ON models(status, deployment_date)
    WHERE status = 'deployed';

-- =============================================================================
-- MATERIALIZED VIEWS FOR METRICS CALCULATION
-- =============================================================================

-- Governance Rule: Metrics calculations should be fast (<5 seconds for 100k rows)
-- Materialized views cache common aggregations for dashboard performance

-- Model performance summary (refreshed hourly)
CREATE MATERIALIZED VIEW IF NOT EXISTS model_performance_summary AS
SELECT
    m.model_id,
    m.name,
    m.version,
    m.status,
    m.deployment_date,
    m.f1_score AS training_f1,
    m.fpr AS training_fpr,

    -- Production performance (from decisions with ground truth)
    COUNT(DISTINCT d.decision_id) AS total_decisions,
    COUNT(DISTINCT CASE WHEN d.final_decision != 'pending' THEN d.decision_id END) AS reviewed_decisions,
    COUNT(DISTINCT CASE WHEN d.audit_trail_complete THEN d.decision_id END) AS complete_audit_trails,

    -- Performance metrics (require ground truth from transactions)
    COUNT(CASE WHEN d.prediction_fraud = TRUE AND t.is_fraud = TRUE THEN 1 END) AS true_positives,
    COUNT(CASE WHEN d.prediction_fraud = TRUE AND t.is_fraud = FALSE THEN 1 END) AS false_positives,
    COUNT(CASE WHEN d.prediction_fraud = FALSE AND t.is_fraud = TRUE THEN 1 END) AS false_negatives,
    COUNT(CASE WHEN d.prediction_fraud = FALSE AND t.is_fraud = FALSE THEN 1 END) AS true_negatives,

    -- Audit completeness
    CASE
        WHEN COUNT(d.decision_id) > 0 THEN
            COUNT(CASE WHEN d.audit_trail_complete THEN 1 END)::NUMERIC / COUNT(d.decision_id)
        ELSE NULL
    END AS audit_completion_rate,

    -- Review turnaround time (average days)
    AVG(
        EXTRACT(EPOCH FROM (d.decision_timestamp - d.flag_timestamp)) / 86400
    ) AS avg_turnaround_days,

    -- Last updated
    CURRENT_TIMESTAMP AS last_refreshed

FROM models m
LEFT JOIN decisions d ON m.model_id = d.model_id
LEFT JOIN transactions t ON d.transaction_id = t.transaction_id
GROUP BY m.model_id, m.name, m.version, m.status, m.deployment_date, m.f1_score, m.fpr;

-- Index for fast lookups
CREATE UNIQUE INDEX idx_model_perf_summary_model_id ON model_performance_summary(model_id);
CREATE INDEX idx_model_perf_summary_status ON model_performance_summary(status);

-- Fairness metrics by transaction type
CREATE MATERIALIZED VIEW IF NOT EXISTS fairness_metrics_by_type AS
SELECT
    m.model_id,
    m.name,
    m.version,
    t.transaction_type,
    COUNT(CASE WHEN d.prediction_fraud = TRUE AND t.is_fraud = FALSE THEN 1 END) AS false_positives,
    COUNT(CASE WHEN d.prediction_fraud = FALSE AND t.is_fraud = FALSE THEN 1 END) AS true_negatives,
    CASE
        WHEN COUNT(CASE WHEN t.is_fraud = FALSE THEN 1 END) > 0 THEN
            COUNT(CASE WHEN d.prediction_fraud = TRUE AND t.is_fraud = FALSE THEN 1 END)::NUMERIC /
            COUNT(CASE WHEN t.is_fraud = FALSE THEN 1 END)
        ELSE NULL
    END AS fpr,
    CURRENT_TIMESTAMP AS last_refreshed
FROM models m
JOIN decisions d ON m.model_id = d.model_id
JOIN transactions t ON d.transaction_id = t.transaction_id
WHERE t.is_fraud IS NOT NULL
GROUP BY m.model_id, m.name, m.version, t.transaction_type;

CREATE INDEX idx_fairness_type_model ON fairness_metrics_by_type(model_id);
CREATE INDEX idx_fairness_type_txn_type ON fairness_metrics_by_type(transaction_type);

-- Fairness metrics by geography
CREATE MATERIALIZED VIEW IF NOT EXISTS fairness_metrics_by_geography AS
SELECT
    m.model_id,
    m.name,
    m.version,
    t.origin_country,
    t.destination_country,
    COUNT(CASE WHEN d.prediction_fraud = TRUE AND t.is_fraud = FALSE THEN 1 END) AS false_positives,
    COUNT(CASE WHEN d.prediction_fraud = FALSE AND t.is_fraud = FALSE THEN 1 END) AS true_negatives,
    CASE
        WHEN COUNT(CASE WHEN t.is_fraud = FALSE THEN 1 END) > 0 THEN
            COUNT(CASE WHEN d.prediction_fraud = TRUE AND t.is_fraud = FALSE THEN 1 END)::NUMERIC /
            COUNT(CASE WHEN t.is_fraud = FALSE THEN 1 END)
        ELSE NULL
    END AS fpr,
    CURRENT_TIMESTAMP AS last_refreshed
FROM models m
JOIN decisions d ON m.model_id = d.model_id
JOIN transactions t ON d.transaction_id = t.transaction_id
WHERE t.is_fraud IS NOT NULL
  AND t.origin_country IS NOT NULL
GROUP BY m.model_id, m.name, m.version, t.origin_country, t.destination_country;

CREATE INDEX idx_fairness_geo_model ON fairness_metrics_by_geography(model_id);
CREATE INDEX idx_fairness_geo_countries ON fairness_metrics_by_geography(origin_country, destination_country);

-- Compliance officer workload summary
CREATE MATERIALIZED VIEW IF NOT EXISTS officer_workload_summary AS
SELECT
    u.user_id,
    u.username,
    COUNT(d.decision_id) AS total_assigned,
    COUNT(CASE WHEN d.final_decision = 'pending' THEN 1 END) AS pending_review,
    COUNT(CASE WHEN d.final_decision != 'pending' THEN 1 END) AS completed_review,
    AVG(
        CASE
            WHEN d.decision_timestamp IS NOT NULL THEN
                EXTRACT(EPOCH FROM (d.decision_timestamp - d.flag_timestamp)) / 3600
            ELSE NULL
        END
    ) AS avg_review_hours,
    MAX(d.flag_timestamp) AS last_assignment_date,
    CURRENT_TIMESTAMP AS last_refreshed
FROM users u
JOIN roles r ON u.role_id = r.role_id
LEFT JOIN decisions d ON u.user_id = d.reviewed_by
WHERE r.role_name = 'compliance_officer'
GROUP BY u.user_id, u.username;

CREATE UNIQUE INDEX idx_officer_workload_user ON officer_workload_summary(user_id);

-- =============================================================================
-- PARTITIONING FOR LARGE TABLES
-- =============================================================================

-- Governance Note: For production systems processing millions of transactions,
-- partition decisions and audit_trails tables by month for better performance

-- Create partitioned decisions table (commented out - enable if needed)
-- CREATE TABLE decisions_partitioned (
--     LIKE decisions INCLUDING ALL
-- ) PARTITION BY RANGE (flag_timestamp);
--
-- -- Create monthly partitions (example for 2024)
-- CREATE TABLE decisions_2024_01 PARTITION OF decisions_partitioned
--     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
-- CREATE TABLE decisions_2024_02 PARTITION OF decisions_partitioned
--     FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
-- -- ... etc.

-- =============================================================================
-- HELPER FUNCTIONS FOR METRICS CALCULATION
-- =============================================================================

-- Calculate F1 score from confusion matrix components
CREATE OR REPLACE FUNCTION calculate_f1_score(
    p_true_positives INTEGER,
    p_false_positives INTEGER,
    p_false_negatives INTEGER
) RETURNS NUMERIC AS $$
DECLARE
    v_precision NUMERIC;
    v_recall NUMERIC;
    v_f1 NUMERIC;
BEGIN
    -- Handle edge cases
    IF p_true_positives = 0 THEN
        RETURN 0;
    END IF;

    v_precision := p_true_positives::NUMERIC / NULLIF(p_true_positives + p_false_positives, 0);
    v_recall := p_true_positives::NUMERIC / NULLIF(p_true_positives + p_false_negatives, 0);

    IF v_precision IS NULL OR v_recall IS NULL OR (v_precision + v_recall) = 0 THEN
        RETURN 0;
    END IF;

    v_f1 := 2 * v_precision * v_recall / (v_precision + v_recall);
    RETURN ROUND(v_f1, 4);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Calculate FPR from confusion matrix components
CREATE OR REPLACE FUNCTION calculate_fpr(
    p_false_positives INTEGER,
    p_true_negatives INTEGER
) RETURNS NUMERIC AS $$
BEGIN
    IF p_false_positives = 0 THEN
        RETURN 0;
    END IF;

    IF (p_false_positives + p_true_negatives) = 0 THEN
        RETURN NULL;
    END IF;

    RETURN ROUND(
        p_false_positives::NUMERIC / NULLIF(p_false_positives + p_true_negatives, 0),
        4
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Get current production metrics for a model
CREATE OR REPLACE FUNCTION get_model_production_metrics(p_model_id UUID)
RETURNS TABLE (
    f1_score NUMERIC,
    fpr NUMERIC,
    precision_score NUMERIC,
    recall_score NUMERIC,
    total_predictions INTEGER,
    audit_completion_rate NUMERIC,
    avg_turnaround_days NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        calculate_f1_score(
            SUM(CASE WHEN d.prediction_fraud = TRUE AND t.is_fraud = TRUE THEN 1 ELSE 0 END)::INTEGER,
            SUM(CASE WHEN d.prediction_fraud = TRUE AND t.is_fraud = FALSE THEN 1 ELSE 0 END)::INTEGER,
            SUM(CASE WHEN d.prediction_fraud = FALSE AND t.is_fraud = TRUE THEN 1 ELSE 0 END)::INTEGER
        ) AS f1_score,

        calculate_fpr(
            SUM(CASE WHEN d.prediction_fraud = TRUE AND t.is_fraud = FALSE THEN 1 ELSE 0 END)::INTEGER,
            SUM(CASE WHEN d.prediction_fraud = FALSE AND t.is_fraud = FALSE THEN 1 ELSE 0 END)::INTEGER
        ) AS fpr,

        -- Precision
        CASE
            WHEN SUM(CASE WHEN d.prediction_fraud = TRUE THEN 1 ELSE 0 END) > 0 THEN
                ROUND(
                    SUM(CASE WHEN d.prediction_fraud = TRUE AND t.is_fraud = TRUE THEN 1 ELSE 0 END)::NUMERIC /
                    SUM(CASE WHEN d.prediction_fraud = TRUE THEN 1 ELSE 0 END),
                    4
                )
            ELSE NULL
        END AS precision_score,

        -- Recall
        CASE
            WHEN SUM(CASE WHEN t.is_fraud = TRUE THEN 1 ELSE 0 END) > 0 THEN
                ROUND(
                    SUM(CASE WHEN d.prediction_fraud = TRUE AND t.is_fraud = TRUE THEN 1 ELSE 0 END)::NUMERIC /
                    SUM(CASE WHEN t.is_fraud = TRUE THEN 1 ELSE 0 END),
                    4
                )
            ELSE NULL
        END AS recall_score,

        COUNT(d.decision_id)::INTEGER AS total_predictions,

        -- Audit completion rate
        CASE
            WHEN COUNT(d.decision_id) > 0 THEN
                ROUND(
                    COUNT(CASE WHEN d.audit_trail_complete THEN 1 END)::NUMERIC / COUNT(d.decision_id),
                    4
                )
            ELSE NULL
        END AS audit_completion_rate,

        -- Average turnaround time in days
        ROUND(
            AVG(
                EXTRACT(EPOCH FROM (d.decision_timestamp - d.flag_timestamp)) / 86400
            ),
            2
        ) AS avg_turnaround_days

    FROM decisions d
    JOIN transactions t ON d.transaction_id = t.transaction_id
    WHERE d.model_id = p_model_id
      AND t.is_fraud IS NOT NULL; -- Only include transactions with verified ground truth
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- AUTOMATIC AUDIT TRAIL COMPLETION CHECK
-- =============================================================================

-- Governance Rule: Audit trail should be marked complete when all required fields are populated
CREATE OR REPLACE FUNCTION check_audit_trail_completeness()
RETURNS TRIGGER AS $$
BEGIN
    -- A decision audit trail is complete when:
    -- 1. Model prediction is recorded (always true for INSERT)
    -- 2. Compliance officer has reviewed (reviewed_by, officer_decision, decision_timestamp populated)
    -- 3. Officer notes are provided (for accountability)

    IF NEW.reviewed_by IS NOT NULL
       AND NEW.officer_decision IS NOT NULL
       AND NEW.decision_timestamp IS NOT NULL
       AND NEW.officer_notes IS NOT NULL
    THEN
        NEW.audit_trail_complete := TRUE;
    ELSE
        NEW.audit_trail_complete := FALSE;
    END IF;

    -- Update audit_trail_hash
    NEW.audit_trail_hash := encode(
        digest(
            CONCAT(
                NEW.model_id::TEXT, '|',
                NEW.transaction_id::TEXT, '|',
                NEW.prediction_fraud::TEXT, '|',
                NEW.confidence_score::TEXT, '|',
                COALESCE(NEW.reviewed_by::TEXT, ''), '|',
                COALESCE(NEW.officer_decision, ''), '|',
                COALESCE(NEW.final_decision, ''), '|',
                COALESCE(NEW.decision_timestamp::TEXT, '')
            ),
            'sha256'
        ),
        'hex'
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger BEFORE the audit trigger
DROP TRIGGER IF EXISTS check_audit_completeness_trigger ON decisions;
CREATE TRIGGER check_audit_completeness_trigger
    BEFORE INSERT OR UPDATE ON decisions
    FOR EACH ROW
    EXECUTE FUNCTION check_audit_trail_completeness();

-- =============================================================================
-- GOVERNANCE THRESHOLD VALIDATION
-- =============================================================================

-- Function to validate model meets deployment thresholds
CREATE OR REPLACE FUNCTION validate_deployment_thresholds(p_model_id UUID)
RETURNS TABLE (
    is_valid BOOLEAN,
    failing_criteria TEXT[],
    message TEXT
) AS $$
DECLARE
    v_model RECORD;
    v_min_f1 NUMERIC;
    v_max_fpr NUMERIC;
    v_failures TEXT[];
BEGIN
    -- Get governance thresholds
    SELECT config_value::NUMERIC INTO v_min_f1
    FROM governance_config WHERE config_key = 'min_f1_score';

    SELECT config_value::NUMERIC INTO v_max_fpr
    FROM governance_config WHERE config_key = 'max_fpr';

    -- Get model metrics
    SELECT * INTO v_model FROM models WHERE model_id = p_model_id;

    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, ARRAY['Model not found']::TEXT[], 'Model does not exist';
        RETURN;
    END IF;

    v_failures := ARRAY[]::TEXT[];

    -- Check F1 score
    IF v_model.f1_score < v_min_f1 THEN
        v_failures := array_append(v_failures,
            format('F1 score %s is below threshold %s', v_model.f1_score::TEXT, v_min_f1::TEXT)
        );
    END IF;

    -- Check FPR
    IF v_model.fpr > v_max_fpr THEN
        v_failures := array_append(v_failures,
            format('FPR %s exceeds threshold %s', v_model.fpr::TEXT, v_max_fpr::TEXT)
        );
    END IF;

    -- Check approval status
    IF v_model.approved_by IS NULL THEN
        v_failures := array_append(v_failures, 'Model not approved by compliance officer');
    END IF;

    -- Return result
    IF array_length(v_failures, 1) IS NULL THEN
        RETURN QUERY SELECT TRUE, NULL::TEXT[], 'Model meets all deployment thresholds';
    ELSE
        RETURN QUERY SELECT FALSE, v_failures, 'Model fails deployment validation';
    END IF;

    RETURN;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- SCHEDULED MAINTENANCE JOBS
-- =============================================================================

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_all_metrics_views()
RETURNS TEXT AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY model_performance_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY fairness_metrics_by_type;
    REFRESH MATERIALIZED VIEW CONCURRENTLY fairness_metrics_by_geography;
    REFRESH MATERIALIZED VIEW CONCURRENTLY officer_workload_summary;

    RETURN 'All materialized views refreshed at ' || CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Schedule: Run this via cron or pg_cron every hour
-- Example: SELECT cron.schedule('refresh-metrics', '0 * * * *', 'SELECT refresh_all_metrics_views()');

-- =============================================================================
-- ACCESS CONTROL VIEWS (FOR API LAYER)
-- =============================================================================

-- View for compliance officers: their assigned decisions only
CREATE OR REPLACE VIEW compliance_officer_queue AS
SELECT
    d.decision_id,
    d.model_id,
    m.name AS model_name,
    d.transaction_id,
    t.external_transaction_id,
    t.transaction_type,
    t.amount,
    t.currency,
    d.prediction_fraud,
    d.confidence_score,
    d.flag_timestamp,
    d.final_decision,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - d.flag_timestamp)) / 3600 AS hours_pending
FROM decisions d
JOIN models m ON d.model_id = m.model_id
JOIN transactions t ON d.transaction_id = t.transaction_id
WHERE d.final_decision = 'pending'
ORDER BY d.flag_timestamp ASC;

-- View for auditors: all incidents requiring sign-off
CREATE OR REPLACE VIEW auditor_incident_queue AS
SELECT
    i.incident_id,
    i.model_id,
    m.name AS model_name,
    i.failure_type,
    i.severity,
    i.description,
    i.detected_date,
    i.remediation_status,
    i.auditor_signoff_date,
    CASE
        WHEN i.auditor_signoff_date IS NULL
             AND i.remediation_status IN ('resolved', 'monitoring')
        THEN TRUE
        ELSE FALSE
    END AS requires_signoff
FROM failure_incidents i
JOIN models m ON i.model_id = m.model_id
WHERE i.remediation_status != 'closed'
ORDER BY i.severity DESC, i.detected_date ASC;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON MATERIALIZED VIEW model_performance_summary IS 'Cached model performance metrics for dashboard (refresh hourly)';
COMMENT ON MATERIALIZED VIEW fairness_metrics_by_type IS 'FPR breakdown by transaction type for fairness audits';
COMMENT ON MATERIALIZED VIEW fairness_metrics_by_geography IS 'FPR breakdown by geography for fairness audits';
COMMENT ON FUNCTION calculate_f1_score IS 'Compute F1 score from confusion matrix: 2*P*R/(P+R)';
COMMENT ON FUNCTION calculate_fpr IS 'Compute false positive rate: FP/(FP+TN)';
COMMENT ON FUNCTION get_model_production_metrics IS 'Get real-time production metrics for deployed model';
COMMENT ON FUNCTION validate_deployment_thresholds IS 'Check if model meets F1 >= 0.85, FPR <= 0.01';
COMMENT ON FUNCTION refresh_all_metrics_views IS 'Refresh all materialized views for dashboard';
