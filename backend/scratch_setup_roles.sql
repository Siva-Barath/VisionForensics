-- Setup dedicated least-privilege application and migration roles
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'visionforensics_migrator') THEN
        CREATE ROLE visionforensics_migrator WITH LOGIN PASSWORD 'migrator_secure_pass_2026';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'visionforensics_app') THEN
        CREATE ROLE visionforensics_app WITH LOGIN PASSWORD 'app_secure_pass_2026';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE visionforensics TO visionforensics_migrator;
GRANT ALL PRIVILEGES ON SCHEMA public TO visionforensics_migrator;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO visionforensics_migrator;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO visionforensics_migrator;

GRANT CONNECT ON DATABASE visionforensics TO visionforensics_app;
GRANT USAGE ON SCHEMA public TO visionforensics_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO visionforensics_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO visionforensics_app;

-- Grant table-level permissions if tables exist
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON users, refresh_tokens, cases, documents, document_pages, analyses, evidence_records, detected_regions, document_comparisons, forensic_reports TO visionforensics_app;
        GRANT SELECT, INSERT ON exhibit_custody_logs, security_audit_logs TO visionforensics_app;
        REVOKE UPDATE, DELETE, TRUNCATE ON exhibit_custody_logs, security_audit_logs FROM visionforensics_app;
    END IF;
END
$$;

-- Grant sequence permissions if any
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO visionforensics_app;

-- Create engine-level immutable audit trigger function if audit tables exist
CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'DEFENSIBLE AUDIT INTEGRITY ERROR: Table % is strictly append-only. UPDATE, DELETE, and TRUNCATE operations are prohibited.', TG_TABLE_NAME;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'exhibit_custody_logs') THEN
        DROP TRIGGER IF EXISTS trg_prevent_custody_modification ON exhibit_custody_logs;
        CREATE TRIGGER trg_prevent_custody_modification
        BEFORE UPDATE OR DELETE ON exhibit_custody_logs
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_modification();
    END IF;
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'security_audit_logs') THEN
        DROP TRIGGER IF EXISTS trg_prevent_audit_modification ON security_audit_logs;
        CREATE TRIGGER trg_prevent_audit_modification
        BEFORE UPDATE OR DELETE ON security_audit_logs
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_modification();
    END IF;
END
$$;
