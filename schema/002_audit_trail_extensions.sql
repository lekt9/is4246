-- AFAAP - Audit Trail Extensions
-- Version: 1.0.0
--
-- Governance Note: This schema implements append-only audit logging to ensure
-- immutable audit trails. All changes to critical tables are logged with
-- timestamps, user attribution, and change deltas.

-- =============================================================================
-- AUDIT TRAILS TABLE (Immutable, Append-Only)
-- =============================================================================

-- Governance Rule: Every change to decisions, models, and revalidation workflows
-- must be recorded in an immutable audit trail. Deletes are forbidden; updates
-- create new audit records showing old value → new value transitions.
CREATE TABLE IF NOT EXISTS audit_trails (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- What was changed
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL, -- ID of the record that was changed
    operation VARCHAR(50) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE' (soft delete only)

    -- Change details
    field_changed VARCHAR(255), -- NULL for INSERT (entire record new)
    old_value TEXT, -- NULL for INSERT
    new_value TEXT, -- NULL for DELETE

    -- Who and when
    changed_by UUID NOT NULL REFERENCES users(user_id),
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Context
    change_reason TEXT, -- Optional justification
    session_id VARCHAR(255), -- For grouping related changes
    ip_address INET, -- Source IP for security audit

    -- Tamper detection
    previous_audit_hash VARCHAR(64), -- Hash of previous audit record (blockchain-style)
    current_audit_hash VARCHAR(64) NOT NULL, -- SHA-256 of this record

    -- Governance constraints
    CONSTRAINT valid_operation CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    CONSTRAINT valid_table CHECK (
        table_name IN ('models', 'decisions', 'revalidation_workflows', 'failure_incidents', 'users', 'transactions')
    ),
    CONSTRAINT update_requires_field CHECK (
        operation != 'UPDATE' OR field_changed IS NOT NULL
    )
);

-- No UPDATE or DELETE allowed on audit_trails (enforced by policy)
-- Index for querying audit history
CREATE INDEX idx_audit_table_record ON audit_trails(table_name, record_id);
CREATE INDEX idx_audit_changed_by ON audit_trails(changed_by);
CREATE INDEX idx_audit_changed_at ON audit_trails(changed_at);
CREATE INDEX idx_audit_session ON audit_trails(session_id);

-- Function to compute audit hash
CREATE OR REPLACE FUNCTION compute_audit_hash(
    p_table_name VARCHAR,
    p_record_id UUID,
    p_operation VARCHAR,
    p_field_changed VARCHAR,
    p_old_value TEXT,
    p_new_value TEXT,
    p_changed_by UUID,
    p_changed_at TIMESTAMP WITH TIME ZONE,
    p_previous_hash VARCHAR
) RETURNS VARCHAR AS $$
DECLARE
    v_hash_input TEXT;
BEGIN
    -- Concatenate all fields for hashing
    v_hash_input := COALESCE(p_table_name, '') || '|' ||
                    COALESCE(p_record_id::TEXT, '') || '|' ||
                    COALESCE(p_operation, '') || '|' ||
                    COALESCE(p_field_changed, '') || '|' ||
                    COALESCE(p_old_value, '') || '|' ||
                    COALESCE(p_new_value, '') || '|' ||
                    COALESCE(p_changed_by::TEXT, '') || '|' ||
                    COALESCE(p_changed_at::TEXT, '') || '|' ||
                    COALESCE(p_previous_hash, '');

    RETURN encode(digest(v_hash_input, 'sha256'), 'hex');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =============================================================================
-- DECISION AUDIT TRIGGERS
-- =============================================================================

-- Trigger function for decisions table
CREATE OR REPLACE FUNCTION audit_decisions_changes()
RETURNS TRIGGER AS $$
DECLARE
    v_changed_by UUID;
    v_session_id VARCHAR(255);
    v_previous_hash VARCHAR(64);
    v_current_hash VARCHAR(64);
BEGIN
    -- Get current user (from session variable or default to system)
    v_changed_by := COALESCE(
        NULLIF(current_setting('app.current_user_id', TRUE), ''),
        '00000000-0000-0000-0000-000000000000'
    )::UUID;

    -- Get session ID if set
    v_session_id := current_setting('app.session_id', TRUE);

    -- Get latest audit hash for blockchain-style chaining
    SELECT current_audit_hash INTO v_previous_hash
    FROM audit_trails
    WHERE table_name = 'decisions' AND record_id = COALESCE(NEW.decision_id, OLD.decision_id)
    ORDER BY changed_at DESC
    LIMIT 1;

    IF TG_OP = 'INSERT' THEN
        -- Compute hash for new record
        v_current_hash := compute_audit_hash(
            'decisions',
            NEW.decision_id,
            'INSERT',
            NULL,
            NULL,
            row_to_json(NEW)::TEXT,
            v_changed_by,
            CURRENT_TIMESTAMP,
            v_previous_hash
        );

        -- Log entire new record
        INSERT INTO audit_trails (
            table_name, record_id, operation,
            field_changed, old_value, new_value,
            changed_by, changed_at, session_id,
            previous_audit_hash, current_audit_hash
        ) VALUES (
            'decisions', NEW.decision_id, 'INSERT',
            NULL, NULL, row_to_json(NEW)::TEXT,
            v_changed_by, CURRENT_TIMESTAMP, v_session_id,
            v_previous_hash, v_current_hash
        );

        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        -- Log each changed field separately for granular audit trail
        IF OLD.reviewed_by IS DISTINCT FROM NEW.reviewed_by THEN
            v_current_hash := compute_audit_hash(
                'decisions', NEW.decision_id, 'UPDATE', 'reviewed_by',
                OLD.reviewed_by::TEXT, NEW.reviewed_by::TEXT,
                v_changed_by, CURRENT_TIMESTAMP, v_previous_hash
            );
            INSERT INTO audit_trails (
                table_name, record_id, operation, field_changed,
                old_value, new_value, changed_by, session_id,
                previous_audit_hash, current_audit_hash
            ) VALUES (
                'decisions', NEW.decision_id, 'UPDATE', 'reviewed_by',
                OLD.reviewed_by::TEXT, NEW.reviewed_by::TEXT,
                v_changed_by, v_session_id, v_previous_hash, v_current_hash
            );
            v_previous_hash := v_current_hash;
        END IF;

        IF OLD.officer_decision IS DISTINCT FROM NEW.officer_decision THEN
            v_current_hash := compute_audit_hash(
                'decisions', NEW.decision_id, 'UPDATE', 'officer_decision',
                OLD.officer_decision, NEW.officer_decision,
                v_changed_by, CURRENT_TIMESTAMP, v_previous_hash
            );
            INSERT INTO audit_trails (
                table_name, record_id, operation, field_changed,
                old_value, new_value, changed_by, session_id,
                previous_audit_hash, current_audit_hash
            ) VALUES (
                'decisions', NEW.decision_id, 'UPDATE', 'officer_decision',
                OLD.officer_decision, NEW.officer_decision,
                v_changed_by, v_session_id, v_previous_hash, v_current_hash
            );
            v_previous_hash := v_current_hash;
        END IF;

        IF OLD.officer_notes IS DISTINCT FROM NEW.officer_notes THEN
            v_current_hash := compute_audit_hash(
                'decisions', NEW.decision_id, 'UPDATE', 'officer_notes',
                OLD.officer_notes, NEW.officer_notes,
                v_changed_by, CURRENT_TIMESTAMP, v_previous_hash
            );
            INSERT INTO audit_trails (
                table_name, record_id, operation, field_changed,
                old_value, new_value, changed_by, session_id,
                previous_audit_hash, current_audit_hash
            ) VALUES (
                'decisions', NEW.decision_id, 'UPDATE', 'officer_notes',
                OLD.officer_notes, NEW.officer_notes,
                v_changed_by, v_session_id, v_previous_hash, v_current_hash
            );
            v_previous_hash := v_current_hash;
        END IF;

        IF OLD.final_decision IS DISTINCT FROM NEW.final_decision THEN
            v_current_hash := compute_audit_hash(
                'decisions', NEW.decision_id, 'UPDATE', 'final_decision',
                OLD.final_decision, NEW.final_decision,
                v_changed_by, CURRENT_TIMESTAMP, v_previous_hash
            );
            INSERT INTO audit_trails (
                table_name, record_id, operation, field_changed,
                old_value, new_value, changed_by, session_id,
                previous_audit_hash, current_audit_hash
            ) VALUES (
                'decisions', NEW.decision_id, 'UPDATE', 'final_decision',
                OLD.final_decision, NEW.final_decision,
                v_changed_by, v_session_id, v_previous_hash, v_current_hash
            );
            v_previous_hash := v_current_hash;
        END IF;

        IF OLD.audit_trail_complete IS DISTINCT FROM NEW.audit_trail_complete THEN
            v_current_hash := compute_audit_hash(
                'decisions', NEW.decision_id, 'UPDATE', 'audit_trail_complete',
                OLD.audit_trail_complete::TEXT, NEW.audit_trail_complete::TEXT,
                v_changed_by, CURRENT_TIMESTAMP, v_previous_hash
            );
            INSERT INTO audit_trails (
                table_name, record_id, operation, field_changed,
                old_value, new_value, changed_by, session_id,
                previous_audit_hash, current_audit_hash
            ) VALUES (
                'decisions', NEW.decision_id, 'UPDATE', 'audit_trail_complete',
                OLD.audit_trail_complete::TEXT, NEW.audit_trail_complete::TEXT,
                v_changed_by, v_session_id, v_previous_hash, v_current_hash
            );
        END IF;

        -- Update the audit_trail_hash in decisions table
        NEW.audit_trail_hash := encode(
            digest(row_to_json(NEW)::TEXT, 'sha256'),
            'hex'
        );

        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        -- Governance Rule: Physical deletes are forbidden for compliance
        RAISE EXCEPTION 'Physical deletion of decisions is not allowed. Use soft delete or mark as inactive.';
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to decisions table
CREATE TRIGGER audit_decisions_trigger
    BEFORE INSERT OR UPDATE OR DELETE ON decisions
    FOR EACH ROW
    EXECUTE FUNCTION audit_decisions_changes();

-- =============================================================================
-- MODEL AUDIT TRIGGERS
-- =============================================================================

CREATE OR REPLACE FUNCTION audit_models_changes()
RETURNS TRIGGER AS $$
DECLARE
    v_changed_by UUID;
    v_session_id VARCHAR(255);
    v_previous_hash VARCHAR(64);
    v_current_hash VARCHAR(64);
BEGIN
    v_changed_by := COALESCE(
        NULLIF(current_setting('app.current_user_id', TRUE), ''),
        '00000000-0000-0000-0000-000000000000'
    )::UUID;

    v_session_id := current_setting('app.session_id', TRUE);

    SELECT current_audit_hash INTO v_previous_hash
    FROM audit_trails
    WHERE table_name = 'models' AND record_id = COALESCE(NEW.model_id, OLD.model_id)
    ORDER BY changed_at DESC
    LIMIT 1;

    IF TG_OP = 'INSERT' THEN
        v_current_hash := compute_audit_hash(
            'models', NEW.model_id, 'INSERT', NULL, NULL,
            row_to_json(NEW)::TEXT, v_changed_by, CURRENT_TIMESTAMP, v_previous_hash
        );

        INSERT INTO audit_trails (
            table_name, record_id, operation, new_value,
            changed_by, session_id,
            previous_audit_hash, current_audit_hash
        ) VALUES (
            'models', NEW.model_id, 'INSERT', row_to_json(NEW)::TEXT,
            v_changed_by, v_session_id, v_previous_hash, v_current_hash
        );

        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        -- Track critical status changes
        IF OLD.status IS DISTINCT FROM NEW.status THEN
            v_current_hash := compute_audit_hash(
                'models', NEW.model_id, 'UPDATE', 'status',
                OLD.status, NEW.status,
                v_changed_by, CURRENT_TIMESTAMP, v_previous_hash
            );
            INSERT INTO audit_trails (
                table_name, record_id, operation, field_changed,
                old_value, new_value, changed_by, session_id,
                previous_audit_hash, current_audit_hash
            ) VALUES (
                'models', NEW.model_id, 'UPDATE', 'status',
                OLD.status, NEW.status, v_changed_by, v_session_id,
                v_previous_hash, v_current_hash
            );
            v_previous_hash := v_current_hash;
        END IF;

        IF OLD.approved_by IS DISTINCT FROM NEW.approved_by THEN
            v_current_hash := compute_audit_hash(
                'models', NEW.model_id, 'UPDATE', 'approved_by',
                OLD.approved_by::TEXT, NEW.approved_by::TEXT,
                v_changed_by, CURRENT_TIMESTAMP, v_previous_hash
            );
            INSERT INTO audit_trails (
                table_name, record_id, operation, field_changed,
                old_value, new_value, changed_by, session_id,
                previous_audit_hash, current_audit_hash
            ) VALUES (
                'models', NEW.model_id, 'UPDATE', 'approved_by',
                OLD.approved_by::TEXT, NEW.approved_by::TEXT,
                v_changed_by, v_session_id, v_previous_hash, v_current_hash
            );
        END IF;

        -- Auto-update timestamp
        NEW.updated_at := CURRENT_TIMESTAMP;

        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Physical deletion of models is not allowed. Use retirement instead.';
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_models_trigger
    BEFORE INSERT OR UPDATE OR DELETE ON models
    FOR EACH ROW
    EXECUTE FUNCTION audit_models_changes();

-- =============================================================================
-- REVALIDATION WORKFLOW AUDIT TRIGGERS
-- =============================================================================

CREATE OR REPLACE FUNCTION audit_revalidation_changes()
RETURNS TRIGGER AS $$
DECLARE
    v_changed_by UUID;
    v_session_id VARCHAR(255);
    v_previous_hash VARCHAR(64);
    v_current_hash VARCHAR(64);
BEGIN
    v_changed_by := COALESCE(
        NULLIF(current_setting('app.current_user_id', TRUE), ''),
        '00000000-0000-0000-0000-000000000000'
    )::UUID;

    v_session_id := current_setting('app.session_id', TRUE);

    SELECT current_audit_hash INTO v_previous_hash
    FROM audit_trails
    WHERE table_name = 'revalidation_workflows'
          AND record_id = COALESCE(NEW.revalidation_id, OLD.revalidation_id)
    ORDER BY changed_at DESC
    LIMIT 1;

    IF TG_OP = 'INSERT' THEN
        v_current_hash := compute_audit_hash(
            'revalidation_workflows', NEW.revalidation_id, 'INSERT',
            NULL, NULL, row_to_json(NEW)::TEXT,
            v_changed_by, CURRENT_TIMESTAMP, v_previous_hash
        );

        INSERT INTO audit_trails (
            table_name, record_id, operation, new_value,
            changed_by, session_id,
            previous_audit_hash, current_audit_hash
        ) VALUES (
            'revalidation_workflows', NEW.revalidation_id, 'INSERT',
            row_to_json(NEW)::TEXT, v_changed_by, v_session_id,
            v_previous_hash, v_current_hash
        );

        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.status IS DISTINCT FROM NEW.status THEN
            v_current_hash := compute_audit_hash(
                'revalidation_workflows', NEW.revalidation_id, 'UPDATE', 'status',
                OLD.status, NEW.status,
                v_changed_by, CURRENT_TIMESTAMP, v_previous_hash
            );
            INSERT INTO audit_trails (
                table_name, record_id, operation, field_changed,
                old_value, new_value, changed_by, session_id,
                previous_audit_hash, current_audit_hash
            ) VALUES (
                'revalidation_workflows', NEW.revalidation_id, 'UPDATE', 'status',
                OLD.status, NEW.status, v_changed_by, v_session_id,
                v_previous_hash, v_current_hash
            );
        END IF;

        NEW.updated_at := CURRENT_TIMESTAMP;
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Physical deletion of revalidation workflows is not allowed.';
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_revalidation_trigger
    BEFORE INSERT OR UPDATE OR DELETE ON revalidation_workflows
    FOR EACH ROW
    EXECUTE FUNCTION audit_revalidation_changes();

-- =============================================================================
-- FAILURE INCIDENT AUDIT TRIGGERS
-- =============================================================================

CREATE OR REPLACE FUNCTION audit_incidents_changes()
RETURNS TRIGGER AS $$
DECLARE
    v_changed_by UUID;
    v_session_id VARCHAR(255);
    v_previous_hash VARCHAR(64);
    v_current_hash VARCHAR(64);
BEGIN
    v_changed_by := COALESCE(
        NULLIF(current_setting('app.current_user_id', TRUE), ''),
        '00000000-0000-0000-0000-000000000000'
    )::UUID;

    v_session_id := current_setting('app.session_id', TRUE);

    SELECT current_audit_hash INTO v_previous_hash
    FROM audit_trails
    WHERE table_name = 'failure_incidents'
          AND record_id = COALESCE(NEW.incident_id, OLD.incident_id)
    ORDER BY changed_at DESC
    LIMIT 1;

    IF TG_OP = 'INSERT' THEN
        v_current_hash := compute_audit_hash(
            'failure_incidents', NEW.incident_id, 'INSERT',
            NULL, NULL, row_to_json(NEW)::TEXT,
            v_changed_by, CURRENT_TIMESTAMP, v_previous_hash
        );

        INSERT INTO audit_trails (
            table_name, record_id, operation, new_value,
            changed_by, session_id,
            previous_audit_hash, current_audit_hash
        ) VALUES (
            'failure_incidents', NEW.incident_id, 'INSERT',
            row_to_json(NEW)::TEXT, v_changed_by, v_session_id,
            v_previous_hash, v_current_hash
        );

        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        -- Track remediation status changes
        IF OLD.remediation_status IS DISTINCT FROM NEW.remediation_status THEN
            v_current_hash := compute_audit_hash(
                'failure_incidents', NEW.incident_id, 'UPDATE', 'remediation_status',
                OLD.remediation_status, NEW.remediation_status,
                v_changed_by, CURRENT_TIMESTAMP, v_previous_hash
            );
            INSERT INTO audit_trails (
                table_name, record_id, operation, field_changed,
                old_value, new_value, changed_by, session_id,
                previous_audit_hash, current_audit_hash
            ) VALUES (
                'failure_incidents', NEW.incident_id, 'UPDATE', 'remediation_status',
                OLD.remediation_status, NEW.remediation_status,
                v_changed_by, v_session_id, v_previous_hash, v_current_hash
            );
            v_previous_hash := v_current_hash;
        END IF;

        -- Track auditor sign-off
        IF OLD.auditor_signoff_by IS DISTINCT FROM NEW.auditor_signoff_by THEN
            v_current_hash := compute_audit_hash(
                'failure_incidents', NEW.incident_id, 'UPDATE', 'auditor_signoff_by',
                OLD.auditor_signoff_by::TEXT, NEW.auditor_signoff_by::TEXT,
                v_changed_by, CURRENT_TIMESTAMP, v_previous_hash
            );
            INSERT INTO audit_trails (
                table_name, record_id, operation, field_changed,
                old_value, new_value, changed_by, session_id,
                previous_audit_hash, current_audit_hash
            ) VALUES (
                'failure_incidents', NEW.incident_id, 'UPDATE', 'auditor_signoff_by',
                OLD.auditor_signoff_by::TEXT, NEW.auditor_signoff_by::TEXT,
                v_changed_by, v_session_id, v_previous_hash, v_current_hash
            );
        END IF;

        NEW.updated_at := CURRENT_TIMESTAMP;
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Physical deletion of failure incidents is not allowed.';
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_incidents_trigger
    BEFORE INSERT OR UPDATE OR DELETE ON failure_incidents
    FOR EACH ROW
    EXECUTE FUNCTION audit_incidents_changes();

-- =============================================================================
-- ROW-LEVEL SECURITY (RLS) FOR AUDIT TRAILS
-- =============================================================================

-- Enable row-level security on audit_trails
ALTER TABLE audit_trails ENABLE ROW LEVEL SECURITY;

-- Only auditors can view all audit trails
CREATE POLICY audit_trails_auditor_view ON audit_trails
    FOR SELECT
    TO PUBLIC
    USING (
        EXISTS (
            SELECT 1 FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.user_id = COALESCE(
                NULLIF(current_setting('app.current_user_id', TRUE), ''),
                '00000000-0000-0000-0000-000000000000'
            )::UUID
            AND r.role_name = 'auditor'
        )
    );

-- Users can only view audit trails for their own actions
CREATE POLICY audit_trails_user_own_view ON audit_trails
    FOR SELECT
    TO PUBLIC
    USING (
        changed_by = COALESCE(
            NULLIF(current_setting('app.current_user_id', TRUE), ''),
            '00000000-0000-0000-0000-000000000000'
        )::UUID
    );

-- No one can update or delete audit trails (append-only)
CREATE POLICY audit_trails_no_update ON audit_trails
    FOR UPDATE
    TO PUBLIC
    USING (FALSE);

CREATE POLICY audit_trails_no_delete ON audit_trails
    FOR DELETE
    TO PUBLIC
    USING (FALSE);

-- =============================================================================
-- HELPER FUNCTIONS FOR AUDIT QUERIES
-- =============================================================================

-- Function to get complete audit trail for a decision
CREATE OR REPLACE FUNCTION get_decision_audit_trail(p_decision_id UUID)
RETURNS TABLE (
    audit_id UUID,
    operation VARCHAR,
    field_changed VARCHAR,
    old_value TEXT,
    new_value TEXT,
    changed_by_username VARCHAR,
    changed_by_role VARCHAR,
    changed_at TIMESTAMP WITH TIME ZONE,
    audit_hash VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.audit_id,
        a.operation,
        a.field_changed,
        a.old_value,
        a.new_value,
        u.username,
        r.role_name,
        a.changed_at,
        a.current_audit_hash
    FROM audit_trails a
    JOIN users u ON a.changed_by = u.user_id
    JOIN roles r ON u.role_id = r.role_id
    WHERE a.table_name = 'decisions'
      AND a.record_id = p_decision_id
    ORDER BY a.changed_at ASC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to verify audit trail integrity (blockchain-style verification)
CREATE OR REPLACE FUNCTION verify_audit_integrity(p_table_name VARCHAR, p_record_id UUID)
RETURNS TABLE (
    is_valid BOOLEAN,
    broken_chain_at TIMESTAMP WITH TIME ZONE,
    message TEXT
) AS $$
DECLARE
    v_record RECORD;
    v_expected_hash VARCHAR(64);
    v_previous_hash VARCHAR(64);
BEGIN
    v_previous_hash := NULL;

    FOR v_record IN
        SELECT * FROM audit_trails
        WHERE table_name = p_table_name AND record_id = p_record_id
        ORDER BY changed_at ASC
    LOOP
        -- Compute expected hash
        v_expected_hash := compute_audit_hash(
            v_record.table_name,
            v_record.record_id,
            v_record.operation,
            v_record.field_changed,
            v_record.old_value,
            v_record.new_value,
            v_record.changed_by,
            v_record.changed_at,
            v_previous_hash
        );

        -- Verify hash matches
        IF v_record.current_audit_hash != v_expected_hash THEN
            RETURN QUERY SELECT FALSE, v_record.changed_at,
                'Hash mismatch detected - possible tampering';
            RETURN;
        END IF;

        -- Verify chain integrity
        IF v_record.previous_audit_hash IS DISTINCT FROM v_previous_hash THEN
            RETURN QUERY SELECT FALSE, v_record.changed_at,
                'Chain broken - previous hash mismatch';
            RETURN;
        END IF;

        v_previous_hash := v_record.current_audit_hash;
    END LOOP;

    RETURN QUERY SELECT TRUE, NULL::TIMESTAMP WITH TIME ZONE, 'Audit trail integrity verified';
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE audit_trails IS 'Immutable append-only audit log for all critical table changes';
COMMENT ON FUNCTION compute_audit_hash IS 'Computes SHA-256 hash for audit trail tamper detection';
COMMENT ON FUNCTION get_decision_audit_trail IS 'Retrieves complete audit history for a decision';
COMMENT ON FUNCTION verify_audit_integrity IS 'Verifies blockchain-style audit trail integrity';
