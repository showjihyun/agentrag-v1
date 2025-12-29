-- Security Enhancements Migration Script
-- Implements Row-Level Security and Advanced Encryption from DATABASE_REVIEW.md
-- Phase 3: Enterprise Security Features

-- ============================================================================
-- ROW-LEVEL SECURITY (RLS) SETUP
-- ============================================================================

-- Enable RLS for sensitive tables
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE blocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledgebases ENABLE ROW LEVEL SECURITY;
ALTER TABLE variables ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_api_keys ENABLE ROW LEVEL SECURITY;

-- Create application roles
DO $$ 
BEGIN
    -- Create roles if they don't exist
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'application_role') THEN
        CREATE ROLE application_role;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'admin_role') THEN
        CREATE ROLE admin_role;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'readonly_role') THEN
        CREATE ROLE readonly_role;
    END IF;
END $$;

-- Grant basic permissions to application role
GRANT USAGE ON SCHEMA public TO application_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO application_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO application_role;

-- Grant admin permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin_role;

-- Grant readonly permissions
GRANT USAGE ON SCHEMA public TO readonly_role;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_role;

-- ============================================================================
-- RLS POLICIES FOR WORKFLOWS
-- ============================================================================

-- Policy for workflow access (owner or public)
CREATE POLICY workflow_access_policy ON workflows
    FOR ALL TO application_role
    USING (
        user_id = COALESCE(
            (current_setting('app.current_user_id', true))::UUID, 
            '00000000-0000-0000-0000-000000000000'::UUID
        ) 
        OR is_public = true
        OR deleted_at IS NOT NULL  -- Allow access to deleted records for cleanup
    );

-- Policy for workflow creation (only own records)
CREATE POLICY workflow_create_policy ON workflows
    FOR INSERT TO application_role
    WITH CHECK (
        user_id = COALESCE(
            (current_setting('app.current_user_id', true))::UUID, 
            '00000000-0000-0000-0000-000000000000'::UUID
        )
    );

-- Policy for workflow updates (only owner)
CREATE POLICY workflow_update_policy ON workflows
    FOR UPDATE TO application_role
    USING (
        user_id = COALESCE(
            (current_setting('app.current_user_id', true))::UUID, 
            '00000000-0000-0000-0000-000000000000'::UUID
        )
    );

-- Admin bypass policy for workflows
CREATE POLICY workflow_admin_policy ON workflows
    FOR ALL TO admin_role
    USING (true);

-- ============================================================================
-- RLS POLICIES FOR AGENTS
-- ============================================================================

-- Policy for agent access (owner or public)
CREATE POLICY agent_access_policy ON agents
    FOR ALL TO application_role
    USING (
        user_id = COALESCE(
            (current_setting('app.current_user_id', true))::UUID, 
            '00000000-0000-0000-0000-000000000000'::UUID
        ) 
        OR is_public = true
        OR deleted_at IS NOT NULL
    );

-- Policy for agent creation
CREATE POLICY agent_create_policy ON agents
    FOR INSERT TO application_role
    WITH CHECK (
        user_id = COALESCE(
            (current_setting('app.current_user_id', true))::UUID, 
            '00000000-0000-0000-0000-000000000000'::UUID
        )
    );

-- Admin bypass policy for agents
CREATE POLICY agent_admin_policy ON agents
    FOR ALL TO admin_role
    USING (true);

-- ============================================================================
-- RLS POLICIES FOR BLOCKS
-- ============================================================================

-- Policy for block access (owner or public)
CREATE POLICY block_access_policy ON blocks
    FOR ALL TO application_role
    USING (
        user_id = COALESCE(
            (current_setting('app.current_user_id', true))::UUID, 
            '00000000-0000-0000-0000-000000000000'::UUID
        ) 
        OR is_public = true
    );

-- Policy for block creation
CREATE POLICY block_create_policy ON blocks
    FOR INSERT TO application_role
    WITH CHECK (
        user_id = COALESCE(
            (current_setting('app.current_user_id', true))::UUID, 
            '00000000-0000-0000-0000-000000000000'::UUID
        )
    );

-- Admin bypass policy for blocks
CREATE POLICY block_admin_policy ON blocks
    FOR ALL TO admin_role
    USING (true);

-- ============================================================================
-- RLS POLICIES FOR DOCUMENTS
-- ============================================================================

-- Policy for document access (owner only)
CREATE POLICY document_access_policy ON documents
    FOR ALL TO application_role
    USING (
        user_id = COALESCE(
            (current_setting('app.current_user_id', true))::UUID, 
            '00000000-0000-0000-0000-000000000000'::UUID
        )
    );

-- Admin bypass policy for documents
CREATE POLICY document_admin_policy ON documents
    FOR ALL TO admin_role
    USING (true);

-- ============================================================================
-- RLS POLICIES FOR KNOWLEDGEBASES
-- ============================================================================

-- Policy for knowledgebase access (owner only)
CREATE POLICY knowledgebase_access_policy ON knowledgebases
    FOR ALL TO application_role
    USING (
        user_id = COALESCE(
            (current_setting('app.current_user_id', true))::UUID, 
            '00000000-0000-0000-0000-000000000000'::UUID
        )
    );

-- Admin bypass policy for knowledgebases
CREATE POLICY knowledgebase_admin_policy ON knowledgebases
    FOR ALL TO admin_role
    USING (true);

-- ============================================================================
-- RLS POLICIES FOR VARIABLES AND SECRETS
-- ============================================================================

-- Policy for variable access based on scope
CREATE POLICY variable_access_policy ON variables
    FOR ALL TO application_role
    USING (
        scope = 'global' OR
        (scope = 'user' AND scope_id = COALESCE(
            (current_setting('app.current_user_id', true))::UUID, 
            '00000000-0000-0000-0000-000000000000'::UUID
        )) OR
        (scope IN ('workspace', 'agent') AND scope_id IN (
            -- Add logic here to check workspace/agent ownership
            SELECT id FROM workflows WHERE user_id = COALESCE(
                (current_setting('app.current_user_id', true))::UUID, 
                '00000000-0000-0000-0000-000000000000'::UUID
            )
            UNION
            SELECT id FROM agents WHERE user_id = COALESCE(
                (current_setting('app.current_user_id', true))::UUID, 
                '00000000-0000-0000-0000-000000000000'::UUID
            )
        ))
    );

-- Admin bypass policy for variables
CREATE POLICY variable_admin_policy ON variables
    FOR ALL TO admin_role
    USING (true);

-- ============================================================================
-- RLS POLICIES FOR USER API KEYS
-- ============================================================================

-- Policy for user API key access (owner only)
CREATE POLICY user_api_key_access_policy ON user_api_keys
    FOR ALL TO application_role
    USING (
        user_id = COALESCE(
            (current_setting('app.current_user_id', true))::UUID, 
            '00000000-0000-0000-0000-000000000000'::UUID
        )
    );

-- Admin bypass policy for user API keys
CREATE POLICY user_api_key_admin_policy ON user_api_keys
    FOR ALL TO admin_role
    USING (true);

-- ============================================================================
-- ENCRYPTION FUNCTIONS
-- ============================================================================

-- Enable pgcrypto extension for encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Function to encrypt sensitive data
CREATE OR REPLACE FUNCTION encrypt_data(plaintext TEXT, key_id TEXT DEFAULT 'default')
RETURNS TEXT AS $
DECLARE
    encryption_key TEXT;
BEGIN
    -- Get encryption key from environment or configuration
    encryption_key := COALESCE(
        current_setting('app.encryption_key', true),
        'default_key_change_in_production'
    );
    
    RETURN encode(
        encrypt(
            plaintext::bytea, 
            encryption_key::bytea, 
            'aes'
        ), 
        'base64'
    );
END;
$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to decrypt sensitive data
CREATE OR REPLACE FUNCTION decrypt_data(ciphertext TEXT, key_id TEXT DEFAULT 'default')
RETURNS TEXT AS $
DECLARE
    encryption_key TEXT;
BEGIN
    -- Get encryption key from environment or configuration
    encryption_key := COALESCE(
        current_setting('app.encryption_key', true),
        'default_key_change_in_production'
    );
    
    RETURN convert_from(
        decrypt(
            decode(ciphertext, 'base64'), 
            encryption_key::bytea, 
            'aes'
        ), 
        'UTF8'
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Return null if decryption fails (key rotation, corruption, etc.)
        RETURN NULL;
END;
$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to hash passwords with salt
CREATE OR REPLACE FUNCTION hash_password(password TEXT, salt TEXT DEFAULT NULL)
RETURNS TEXT AS $
DECLARE
    password_salt TEXT;
BEGIN
    -- Generate salt if not provided
    password_salt := COALESCE(salt, gen_salt('bf', 12));
    
    RETURN crypt(password, password_salt);
END;
$ LANGUAGE plpgsql;

-- Function to verify password
CREATE OR REPLACE FUNCTION verify_password(password TEXT, hash TEXT)
RETURNS BOOLEAN AS $
BEGIN
    RETURN crypt(password, hash) = hash;
END;
$ LANGUAGE plpgsql;

-- ============================================================================
-- AUDIT LOGGING ENHANCEMENTS
-- ============================================================================

-- Enhanced audit logging function with security context
CREATE OR REPLACE FUNCTION log_security_event(
    event_type TEXT,
    resource_type TEXT DEFAULT NULL,
    resource_id UUID DEFAULT NULL,
    details JSONB DEFAULT '{}'::JSONB,
    severity TEXT DEFAULT 'INFO'
)
RETURNS void AS $
DECLARE
    current_user_id UUID;
    client_ip TEXT;
    user_agent TEXT;
BEGIN
    -- Get current user context
    current_user_id := COALESCE(
        (current_setting('app.current_user_id', true))::UUID,
        '00000000-0000-0000-0000-000000000000'::UUID
    );
    
    -- Get client information
    client_ip := current_setting('app.client_ip', true);
    user_agent := current_setting('app.user_agent', true);
    
    -- Insert audit log with security context
    INSERT INTO audit_logs (
        user_id,
        action,
        resource_type,
        resource_id,
        details,
        ip_address,
        user_agent,
        timestamp
    ) VALUES (
        current_user_id,
        event_type,
        resource_type,
        resource_id,
        details || jsonb_build_object(
            'severity', severity,
            'session_id', current_setting('app.session_id', true),
            'request_id', current_setting('app.request_id', true)
        ),
        client_ip,
        user_agent,
        NOW()
    );
END;
$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- SECURITY MONITORING FUNCTIONS
-- ============================================================================

-- Function to detect suspicious activity
CREATE OR REPLACE FUNCTION detect_suspicious_activity(
    time_window_minutes INTEGER DEFAULT 60,
    max_failed_attempts INTEGER DEFAULT 10
)
RETURNS TABLE(
    user_id UUID,
    ip_address TEXT,
    failed_attempts BIGINT,
    first_attempt TIMESTAMP,
    last_attempt TIMESTAMP,
    risk_level TEXT
) AS $
BEGIN
    RETURN QUERY
    SELECT 
        al.user_id,
        al.ip_address,
        COUNT(*) as failed_attempts,
        MIN(al.timestamp) as first_attempt,
        MAX(al.timestamp) as last_attempt,
        CASE 
            WHEN COUNT(*) > max_failed_attempts * 2 THEN 'HIGH'
            WHEN COUNT(*) > max_failed_attempts THEN 'MEDIUM'
            ELSE 'LOW'
        END as risk_level
    FROM audit_logs al
    WHERE al.action LIKE '%failed%' 
    AND al.timestamp > NOW() - (time_window_minutes || ' minutes')::INTERVAL
    GROUP BY al.user_id, al.ip_address
    HAVING COUNT(*) >= max_failed_attempts
    ORDER BY failed_attempts DESC;
END;
$ LANGUAGE plpgsql;

-- Function to get security metrics
CREATE OR REPLACE FUNCTION get_security_metrics(days INTEGER DEFAULT 7)
RETURNS TABLE(
    metric TEXT,
    value BIGINT,
    description TEXT
) AS $
BEGIN
    RETURN QUERY
    SELECT 
        'total_logins'::TEXT,
        COUNT(*) as value,
        'Total login attempts in last ' || days || ' days'::TEXT
    FROM audit_logs 
    WHERE action = 'login' 
    AND timestamp > NOW() - (days || ' days')::INTERVAL
    
    UNION ALL
    
    SELECT 
        'failed_logins'::TEXT,
        COUNT(*) as value,
        'Failed login attempts in last ' || days || ' days'::TEXT
    FROM audit_logs 
    WHERE action = 'login_failed' 
    AND timestamp > NOW() - (days || ' days')::INTERVAL
    
    UNION ALL
    
    SELECT 
        'unique_users'::TEXT,
        COUNT(DISTINCT user_id) as value,
        'Unique active users in last ' || days || ' days'::TEXT
    FROM audit_logs 
    WHERE timestamp > NOW() - (days || ' days')::INTERVAL
    AND user_id IS NOT NULL
    
    UNION ALL
    
    SELECT 
        'admin_actions'::TEXT,
        COUNT(*) as value,
        'Admin actions in last ' || days || ' days'::TEXT
    FROM audit_logs 
    WHERE action LIKE '%admin%' 
    AND timestamp > NOW() - (days || ' days')::INTERVAL;
END;
$ LANGUAGE plpgsql;

-- ============================================================================
-- DATA MASKING FUNCTIONS
-- ============================================================================

-- Function to mask sensitive data for non-admin users
CREATE OR REPLACE FUNCTION mask_sensitive_data(
    data TEXT,
    mask_type TEXT DEFAULT 'partial'
)
RETURNS TEXT AS $
BEGIN
    CASE mask_type
        WHEN 'full' THEN
            RETURN '***MASKED***';
        WHEN 'partial' THEN
            IF LENGTH(data) <= 4 THEN
                RETURN '***';
            ELSE
                RETURN LEFT(data, 2) || REPEAT('*', LENGTH(data) - 4) || RIGHT(data, 2);
            END IF;
        WHEN 'email' THEN
            RETURN REGEXP_REPLACE(data, '(.{1,3})[^@]*(@.*)', '\1***\2');
        ELSE
            RETURN data;
    END CASE;
END;
$ LANGUAGE plpgsql;

-- ============================================================================
-- SECURITY VALIDATION FUNCTIONS
-- ============================================================================

-- Function to validate data access permissions
CREATE OR REPLACE FUNCTION validate_data_access(
    resource_type TEXT,
    resource_id UUID,
    action TEXT DEFAULT 'read'
)
RETURNS BOOLEAN AS $
DECLARE
    current_user_id UUID;
    has_permission BOOLEAN := false;
BEGIN
    -- Get current user
    current_user_id := COALESCE(
        (current_setting('app.current_user_id', true))::UUID,
        '00000000-0000-0000-0000-000000000000'::UUID
    );
    
    -- Check permissions based on resource type
    CASE resource_type
        WHEN 'workflow' THEN
            SELECT EXISTS(
                SELECT 1 FROM workflows 
                WHERE id = resource_id 
                AND (user_id = current_user_id OR is_public = true)
            ) INTO has_permission;
            
        WHEN 'agent' THEN
            SELECT EXISTS(
                SELECT 1 FROM agents 
                WHERE id = resource_id 
                AND (user_id = current_user_id OR is_public = true)
            ) INTO has_permission;
            
        WHEN 'block' THEN
            SELECT EXISTS(
                SELECT 1 FROM blocks 
                WHERE id = resource_id 
                AND (user_id = current_user_id OR is_public = true)
            ) INTO has_permission;
            
        ELSE
            has_permission := false;
    END CASE;
    
    -- Log access attempt
    PERFORM log_security_event(
        'data_access_check',
        resource_type,
        resource_id,
        jsonb_build_object(
            'action', action,
            'granted', has_permission,
            'user_id', current_user_id
        )
    );
    
    RETURN has_permission;
END;
$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- HELPER FUNCTIONS FOR APPLICATION
-- ============================================================================

-- Function to set user context for RLS
CREATE OR REPLACE FUNCTION set_user_context(
    user_id UUID,
    session_id TEXT DEFAULT NULL,
    client_ip TEXT DEFAULT NULL,
    user_agent TEXT DEFAULT NULL,
    request_id TEXT DEFAULT NULL
)
RETURNS void AS $
BEGIN
    -- Set user context for RLS policies
    PERFORM set_config('app.current_user_id', user_id::TEXT, true);
    
    -- Set additional context for audit logging
    IF session_id IS NOT NULL THEN
        PERFORM set_config('app.session_id', session_id, true);
    END IF;
    
    IF client_ip IS NOT NULL THEN
        PERFORM set_config('app.client_ip', client_ip, true);
    END IF;
    
    IF user_agent IS NOT NULL THEN
        PERFORM set_config('app.user_agent', user_agent, true);
    END IF;
    
    IF request_id IS NOT NULL THEN
        PERFORM set_config('app.request_id', request_id, true);
    END IF;
END;
$ LANGUAGE plpgsql;

-- Function to clear user context
CREATE OR REPLACE FUNCTION clear_user_context()
RETURNS void AS $
BEGIN
    PERFORM set_config('app.current_user_id', '', true);
    PERFORM set_config('app.session_id', '', true);
    PERFORM set_config('app.client_ip', '', true);
    PERFORM set_config('app.user_agent', '', true);
    PERFORM set_config('app.request_id', '', true);
END;
$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS AND DOCUMENTATION
-- ============================================================================

COMMENT ON FUNCTION encrypt_data(TEXT, TEXT) IS 'Encrypts sensitive data using AES encryption';
COMMENT ON FUNCTION decrypt_data(TEXT, TEXT) IS 'Decrypts sensitive data using AES encryption';
COMMENT ON FUNCTION hash_password(TEXT, TEXT) IS 'Hashes passwords with bcrypt and salt';
COMMENT ON FUNCTION verify_password(TEXT, TEXT) IS 'Verifies password against bcrypt hash';
COMMENT ON FUNCTION log_security_event(TEXT, TEXT, UUID, JSONB, TEXT) IS 'Logs security events with full context';
COMMENT ON FUNCTION detect_suspicious_activity(INTEGER, INTEGER) IS 'Detects suspicious login activity patterns';
COMMENT ON FUNCTION get_security_metrics(INTEGER) IS 'Returns security metrics for monitoring dashboard';
COMMENT ON FUNCTION mask_sensitive_data(TEXT, TEXT) IS 'Masks sensitive data for display to non-admin users';
COMMENT ON FUNCTION validate_data_access(TEXT, UUID, TEXT) IS 'Validates user permissions for data access';
COMMENT ON FUNCTION set_user_context(UUID, TEXT, TEXT, TEXT, TEXT) IS 'Sets user context for RLS and audit logging';
COMMENT ON FUNCTION clear_user_context() IS 'Clears user context variables';

-- ============================================================================
-- SECURITY CONFIGURATION RECOMMENDATIONS
-- ============================================================================

DO $$ 
BEGIN
    RAISE NOTICE 'Security enhancements completed successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'Implemented features:';
    RAISE NOTICE '- Row-Level Security (RLS) for all sensitive tables';
    RAISE NOTICE '- Application roles (application_role, admin_role, readonly_role)';
    RAISE NOTICE '- Advanced encryption functions with key rotation support';
    RAISE NOTICE '- Enhanced audit logging with security context';
    RAISE NOTICE '- Suspicious activity detection';
    RAISE NOTICE '- Data masking for sensitive information';
    RAISE NOTICE '- Permission validation functions';
    RAISE NOTICE '';
    RAISE NOTICE 'IMPORTANT: Configure these settings in production:';
    RAISE NOTICE '1. Set app.encryption_key to a strong 32-byte key';
    RAISE NOTICE '2. Create database users and assign appropriate roles';
    RAISE NOTICE '3. Configure connection pooling with role-based connections';
    RAISE NOTICE '4. Set up monitoring for security events';
    RAISE NOTICE '5. Regularly rotate encryption keys';
    RAISE NOTICE '';
    RAISE NOTICE 'Usage in application:';
    RAISE NOTICE '- Call set_user_context() at request start';
    RAISE NOTICE '- Call clear_user_context() at request end';
    RAISE NOTICE '- Use log_security_event() for security-related actions';
    RAISE NOTICE '- Monitor with detect_suspicious_activity() and get_security_metrics()';
END $$;