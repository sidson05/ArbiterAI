CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Policies metadata
CREATE TABLE IF NOT EXISTS policies (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    policy_type VARCHAR(64) NOT NULL, -- HEALTH, MOTOR, PROPERTY
    version VARCHAR(32) NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Policy Clauses with pgvector embedding
CREATE TABLE IF NOT EXISTS policy_clauses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id VARCHAR(64) REFERENCES policies(id) ON DELETE CASCADE,
    clause_number VARCHAR(64) NOT NULL,
    section_name VARCHAR(128) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    deductible NUMERIC(10, 2) DEFAULT 0.00,
    sub_limit NUMERIC(10, 2),
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_policy_clauses_policy_id ON policy_clauses(policy_id);
CREATE INDEX IF NOT EXISTS idx_policy_clauses_number ON policy_clauses(clause_number);

-- Claims Records
CREATE TABLE IF NOT EXISTS claims (
    id VARCHAR(64) PRIMARY KEY,
    policy_id VARCHAR(64) REFERENCES policies(id),
    claimant_id VARCHAR(64) NOT NULL,
    incident_date DATE NOT NULL,
    claimed_amount NUMERIC(10, 2) NOT NULL,
    approved_amount NUMERIC(10, 2) DEFAULT 0.00,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    document_s3_key VARCHAR(512),
    decision_summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit Trails
CREATE TABLE IF NOT EXISTS claim_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id VARCHAR(64) REFERENCES claims(id) ON DELETE CASCADE,
    step_name VARCHAR(64) NOT NULL,
    model_name VARCHAR(64),
    input_payload JSONB NOT NULL,
    output_payload JSONB NOT NULL,
    confidence_score NUMERIC(5, 4),
    latency_ms INTEGER,
    token_cost NUMERIC(8, 6),
    performed_by VARCHAR(64) DEFAULT 'AGENT',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
