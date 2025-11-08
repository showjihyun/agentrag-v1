-- System Configuration Table
-- Stores system-wide configuration including embedding model info

CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    config_type VARCHAR(50) NOT NULL DEFAULT 'string',  -- string, integer, float, json
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on config_key for fast lookup
CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key);

-- Insert default embedding model configuration
INSERT INTO system_config (config_key, config_value, config_type, description)
VALUES 
    ('embedding_model_name', 'jhgan/ko-sroberta-multitask', 'string', 'Current embedding model name'),
    ('embedding_dimension', '768', 'integer', 'Embedding vector dimension')
ON CONFLICT (config_key) DO NOTHING;

-- Create trigger to update updated_at
CREATE OR REPLACE FUNCTION update_system_config_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_system_config_updated_at
    BEFORE UPDATE ON system_config
    FOR EACH ROW
    EXECUTE FUNCTION update_system_config_updated_at();

-- Comments
COMMENT ON TABLE system_config IS 'System-wide configuration storage';
COMMENT ON COLUMN system_config.config_key IS 'Unique configuration key';
COMMENT ON COLUMN system_config.config_value IS 'Configuration value (stored as text)';
COMMENT ON COLUMN system_config.config_type IS 'Data type of the value';
COMMENT ON COLUMN system_config.description IS 'Human-readable description';
