-- ============================================================================
-- File: 004_risk_stratification_and_sla.sql
-- Purpose: Implement risk stratification workflow and SLA tracking
--          as specified in AFAAP Design Document Section 3.2.2
-- ============================================================================

-- ============================================================================
-- SECTION 1: ALTER DECISIONS TABLE FOR RISK STRATIFICATION
-- ============================================================================
-- Add columns to support risk-tiered workflow from design document:
-- - High confidence (>80%): 1-hour SLA, transaction held
-- - Medium confidence (50-80%): 24-hour SLA, transaction proceeds
-- - Low confidence (<50%): log-only, no review required

ALTER TABLE decisions
ADD COLUMN risk_tier VARCHAR(10) CHECK (risk_tier IN ('high', 'medium', 'low')),
ADD COLUMN sla_deadline TIMESTAMP,
ADD COLUMN sla_met BOOLEAN DEFAULT NULL,
ADD COLUMN transaction_held BOOLEAN DEFAULT FALSE,
ADD COLUMN model_explanation TEXT; -- For SHAP or other explainability outputs

-- Add comment for documentation
COMMENT ON COLUMN decisions.risk_tier IS 'Risk stratification: high (>80% confidence), medium (50-80%), low (<50%)';
COMMENT ON COLUMN decisions.sla_deadline IS 'Deadline for compliance officer review based on risk tier';
COMMENT ON COLUMN decisions.sla_met IS 'Whether review was completed within SLA window (NULL if not yet reviewed)';
COMMENT ON COLUMN decisions.transaction_held IS 'Whether transaction was held pending review (TRUE for high-risk only)';
COMMENT ON COLUMN decisions.model_explanation IS 'Model explainability output (e.g., SHAP values, feature importance)';

-- ============================================================================
-- SECTION 2: FUNCTION TO AUTO-ASSIGN RISK TIER AND SLA
-- ============================================================================
-- Automatically calculates risk tier and SLA deadline based on confidence score
-- Design Document Section 3.2.2 requirements:
--   High (>80%): 1 hour SLA
--   Medium (50-80%): 24 hour SLA
--   Low (<50%): No SLA (log only)

CREATE OR REPLACE FUNCTION assign_risk_tier_and_sla()
RETURNS TRIGGER AS $$
DECLARE
    v_sla_hours INTEGER;
BEGIN
    -- Determine risk tier based on confidence score
    IF NEW.confidence_score > 0.80 THEN
        NEW.risk_tier := 'high';
        v_sla_hours := 1;  -- 1 hour for high-risk
        NEW.transaction_held := TRUE;  -- Hold transaction for high-risk
    ELSIF NEW.confidence_score >= 0.50 THEN
        NEW.risk_tier := 'medium';
        v_sla_hours := 24;  -- 24 hours for medium-risk
        NEW.transaction_held := FALSE;  -- Transaction proceeds normally
    ELSE
        NEW.risk_tier := 'low';
        v_sla_hours := NULL;  -- No SLA for low-risk (log only)
        NEW.transaction_held := FALSE;
    END IF;

    -- Set SLA deadline (NULL for low-risk)
    IF v_sla_hours IS NOT NULL THEN
        NEW.sla_deadline := NEW.created_at + (v_sla_hours || ' hours')::INTERVAL;
    ELSE
        NEW.sla_deadline := NULL;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-assign on INSERT
CREATE TRIGGER trigger_assign_risk_tier
BEFORE INSERT ON decisions
FOR EACH ROW
EXECUTE FUNCTION assign_risk_tier_and_sla();

COMMENT ON FUNCTION assign_risk_tier_and_sla() IS 'Auto-assigns risk tier and SLA deadline based on confidence score per AFAAP Section 3.2.2';

-- ============================================================================
-- SECTION 3: FUNCTION TO CHECK SLA COMPLIANCE ON REVIEW
-- ============================================================================
-- Automatically checks if review was completed within SLA window

CREATE OR REPLACE FUNCTION check_sla_compliance()
RETURNS TRIGGER AS $$
BEGIN
    -- Only check SLA if this is the first review (reviewed_by was NULL before)
    IF OLD.reviewed_by IS NULL AND NEW.reviewed_by IS NOT NULL THEN
        -- Check if review timestamp is within SLA deadline
        IF NEW.sla_deadline IS NOT NULL THEN
            NEW.sla_met := (NEW.decision_timestamp <= NEW.sla_deadline);
        ELSE
            -- Low-risk cases have no SLA requirement
            NEW.sla_met := NULL;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to check SLA on UPDATE (when reviewed_by is set)
CREATE TRIGGER trigger_check_sla_compliance
BEFORE UPDATE ON decisions
FOR EACH ROW
EXECUTE FUNCTION check_sla_compliance();

COMMENT ON FUNCTION check_sla_compliance() IS 'Checks if compliance officer review met SLA deadline (AFAAP Section 4.3.2)';

-- ============================================================================
-- SECTION 4: REVIEW TURNAROUND TIME (RTT) CALCULATION
-- ============================================================================
-- Design Document Section 4.3.2 metric: RTT ≤ 5 days

-- Function to calculate RTT for a single decision
CREATE OR REPLACE FUNCTION calculate_rtt(p_decision_id UUID)
RETURNS INTERVAL AS $$
    SELECT
        CASE
            WHEN decision_timestamp IS NOT NULL THEN decision_timestamp - created_at
            ELSE NULL
        END
    FROM decisions
    WHERE decision_id = p_decision_id;
$$ LANGUAGE SQL IMMUTABLE;

COMMENT ON FUNCTION calculate_rtt(UUID) IS 'Calculates Review Turnaround Time (AFAAP Section 4.3.2 metric)';

-- Materialized view for RTT monitoring
CREATE MATERIALIZED VIEW review_turnaround_time_summary AS
SELECT
    risk_tier,
    COUNT(*) AS total_reviews,
    COUNT(CASE WHEN sla_met = TRUE THEN 1 END) AS reviews_within_sla,
    COUNT(CASE WHEN sla_met = FALSE THEN 1 END) AS reviews_missed_sla,
    ROUND(100.0 * COUNT(CASE WHEN sla_met = TRUE THEN 1 END) / NULLIF(COUNT(*), 0), 2) AS sla_compliance_pct,
    AVG(EXTRACT(EPOCH FROM (decision_timestamp - created_at)) / 3600)::NUMERIC(10,2) AS avg_rtt_hours,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (decision_timestamp - created_at)) / 3600)::NUMERIC(10,2) AS median_rtt_hours,
    MAX(EXTRACT(EPOCH FROM (decision_timestamp - created_at)) / 3600)::NUMERIC(10,2) AS max_rtt_hours,
    COUNT(CASE WHEN (decision_timestamp - created_at) > INTERVAL '5 days' THEN 1 END) AS reviews_exceeding_5day_threshold
FROM decisions
WHERE reviewed_by IS NOT NULL  -- Only completed reviews
GROUP BY risk_tier;

COMMENT ON MATERIALIZED VIEW review_turnaround_time_summary IS 'RTT metrics dashboard (AFAAP Section 4.3.2: RTT ≤ 5 days)';

-- Index for RTT queries
CREATE INDEX idx_decisions_rtt ON decisions(created_at, decision_timestamp) WHERE reviewed_by IS NOT NULL;

-- ============================================================================
-- SECTION 5: SLA MONITORING DASHBOARD
-- ============================================================================
-- Real-time view of SLA compliance by risk tier

CREATE MATERIALIZED VIEW sla_compliance_dashboard AS
SELECT
    risk_tier,
    COUNT(*) AS total_flagged,
    COUNT(CASE WHEN reviewed_by IS NOT NULL THEN 1 END) AS total_reviewed,
    COUNT(CASE WHEN sla_met = TRUE THEN 1 END) AS reviews_on_time,
    COUNT(CASE WHEN sla_met = FALSE THEN 1 END) AS reviews_late,
    COUNT(CASE WHEN reviewed_by IS NULL AND NOW() > sla_deadline THEN 1 END) AS pending_overdue,
    ROUND(100.0 * COUNT(CASE WHEN sla_met = TRUE THEN 1 END) /
          NULLIF(COUNT(CASE WHEN reviewed_by IS NOT NULL THEN 1 END), 0), 2) AS sla_success_rate_pct
FROM decisions
WHERE risk_tier IN ('high', 'medium')  -- Only tiers with SLA requirements
GROUP BY risk_tier;

COMMENT ON MATERIALIZED VIEW sla_compliance_dashboard IS 'SLA compliance tracking by risk tier (AFAAP Section 3.2.2)';

-- ============================================================================
-- SECTION 6: ALERTS FOR SLA VIOLATIONS
-- ============================================================================
-- View to identify decisions that missed or will miss SLA

CREATE OR REPLACE VIEW sla_violations AS
SELECT
    d.decision_id,
    d.transaction_id,
    d.risk_tier,
    d.confidence_score,
    d.created_at,
    d.sla_deadline,
    d.decision_timestamp,
    d.sla_met,
    CASE
        WHEN d.reviewed_by IS NULL AND NOW() > d.sla_deadline THEN 'PENDING_OVERDUE'
        WHEN d.sla_met = FALSE THEN 'COMPLETED_LATE'
        ELSE 'UNKNOWN'
    END AS violation_type,
    EXTRACT(EPOCH FROM (COALESCE(d.decision_timestamp, NOW()) - d.sla_deadline)) / 3600 AS hours_past_deadline
FROM decisions d
WHERE
    d.sla_deadline IS NOT NULL  -- Only decisions with SLA requirements
    AND (
        (d.reviewed_by IS NULL AND NOW() > d.sla_deadline)  -- Pending but overdue
        OR d.sla_met = FALSE  -- Completed but late
    )
ORDER BY d.sla_deadline ASC;

COMMENT ON VIEW sla_violations IS 'Real-time alerts for SLA violations (Design Doc Section 3.2.2)';

-- ============================================================================
-- SECTION 7: BACKFILL EXISTING DATA (IF ANY)
-- ============================================================================
-- For existing decisions without risk_tier, calculate retroactively

UPDATE decisions
SET
    risk_tier = CASE
        WHEN confidence_score > 0.80 THEN 'high'
        WHEN confidence_score >= 0.50 THEN 'medium'
        ELSE 'low'
    END,
    sla_deadline = CASE
        WHEN confidence_score > 0.80 THEN created_at + INTERVAL '1 hour'
        WHEN confidence_score >= 0.50 THEN created_at + INTERVAL '24 hours'
        ELSE NULL
    END,
    transaction_held = (confidence_score > 0.80),
    sla_met = CASE
        WHEN reviewed_by IS NOT NULL AND confidence_score > 0.80
            THEN (decision_timestamp <= created_at + INTERVAL '1 hour')
        WHEN reviewed_by IS NOT NULL AND confidence_score >= 0.50
            THEN (decision_timestamp <= created_at + INTERVAL '24 hours')
        ELSE NULL
    END
WHERE risk_tier IS NULL;

-- ============================================================================
-- SECTION 8: VALIDATION QUERIES
-- ============================================================================
-- Test queries to verify implementation

-- Query 1: Verify risk tier distribution
-- Expected: High (>80%), Medium (50-80%), Low (<50%)
/*
SELECT
    risk_tier,
    COUNT(*) AS count,
    MIN(confidence_score) AS min_confidence,
    MAX(confidence_score) AS max_confidence
FROM decisions
GROUP BY risk_tier
ORDER BY risk_tier;
*/

-- Query 2: Check SLA compliance rates
-- Expected: High-risk should have 1hr SLA, Medium should have 24hr SLA
/*
SELECT * FROM sla_compliance_dashboard;
*/

-- Query 3: Find current SLA violations
-- Expected: List of overdue decisions needing immediate attention
/*
SELECT
    decision_id,
    risk_tier,
    hours_past_deadline,
    violation_type
FROM sla_violations
LIMIT 10;
*/

-- Query 4: RTT performance by risk tier
-- Expected: All tiers should have RTT < 5 days on average
/*
SELECT * FROM review_turnaround_time_summary;
*/

-- Query 5: Test calculate_rtt function
/*
SELECT
    decision_id,
    calculate_rtt(decision_id) AS turnaround_time
FROM decisions
WHERE reviewed_by IS NOT NULL
LIMIT 5;
*/

-- ============================================================================
-- SECTION 9: INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX idx_decisions_risk_tier ON decisions(risk_tier);
CREATE INDEX idx_decisions_sla_deadline ON decisions(sla_deadline) WHERE sla_deadline IS NOT NULL;
CREATE INDEX idx_decisions_sla_pending ON decisions(sla_deadline, reviewed_by) WHERE reviewed_by IS NULL;
CREATE INDEX idx_decisions_transaction_held ON decisions(transaction_held) WHERE transaction_held = TRUE;

-- ============================================================================
-- SECTION 10: REFRESH MATERIALIZED VIEWS
-- ============================================================================

REFRESH MATERIALIZED VIEW review_turnaround_time_summary;
REFRESH MATERIALIZED VIEW sla_compliance_dashboard;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
