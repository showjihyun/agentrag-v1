-- ============================================
-- Agent Builder - Database Creation Script
-- ============================================
-- Run this script to create the database manually
-- Usage: psql -U postgres -f create-database.sql
-- ============================================

-- Create database
CREATE DATABASE agenticrag
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Connect to the database
\c agenticrag

-- Create extensions (optional but recommended)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE agenticrag TO postgres;

-- Success message
\echo 'Database "agenticrag" created successfully!'
\echo 'You can now run migrations with: cd backend && alembic upgrade head'
