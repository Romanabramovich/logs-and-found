CREATE TABLE logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    level VARCHAR(10) NOT NULL,
    source VARCHAR(100) NOT NULL,
    application VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    log_metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- log table indexes for performance
CREATE INDEX idx_timestamp ON logs(timestamp DESC);
CREATE INDEX idx_level ON logs(level);
CREATE INDEX idx_source ON logs(source);
CREATE INDEX idx_log_metadata ON logs USING GIN(log_metadata);