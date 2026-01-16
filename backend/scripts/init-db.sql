-- ============================================
-- PostgreSQL Initialization Script
-- Updated: 2026-01-16
-- Purpose: Initialize database for Agentic RAG
-- ============================================

-- Create database if not exists (handled by POSTGRES_DB env var)
-- This script runs after database creation

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Create custom types
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('user', 'admin', 'super_admin');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE organization_role AS ENUM ('owner', 'admin', 'member', 'viewer');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE subscription_tier AS ENUM ('FREE', 'BASIC', 'PRO', 'BUSINESS', 'ENTERPRISE');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create indexes for common queries (will be created by Alembic migrations)
-- This is just a placeholder for any custom initialization

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE agenticrag TO postgres;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully at %', NOW();
END $$;
