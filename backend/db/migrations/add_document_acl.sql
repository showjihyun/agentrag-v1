-- Migration: Add Document ACL (Access Control List)
-- Date: 2025-01-08
-- Description: Adds permission management tables for fine-grained document access control

-- Create permission type enum
DO $$ BEGIN
    CREATE TYPE permission_type AS ENUM ('read', 'write', 'admin');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create groups table
CREATE TABLE IF NOT EXISTS groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(500),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create group_members table
CREATE TABLE IF NOT EXISTS group_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    added_by UUID REFERENCES users(id) ON DELETE SET NULL,
    added_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_group_user_membership UNIQUE (group_id, user_id)
);

-- Create document_permissions table
CREATE TABLE IF NOT EXISTS document_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    granted_by UUID REFERENCES users(id) ON DELETE SET NULL,
    permission_type permission_type NOT NULL DEFAULT 'read',
    granted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP,
    CONSTRAINT uq_document_user_permission UNIQUE (document_id, user_id),
    CONSTRAINT uq_document_group_permission UNIQUE (document_id, group_id),
    CONSTRAINT check_user_or_group CHECK (
        (user_id IS NOT NULL AND group_id IS NULL) OR 
        (user_id IS NULL AND group_id IS NOT NULL)
    )
);

-- Create indexes for groups
CREATE INDEX IF NOT EXISTS ix_groups_name ON groups(name);
CREATE INDEX IF NOT EXISTS ix_groups_created_by ON groups(created_by);

-- Create indexes for group_members
CREATE INDEX IF NOT EXISTS ix_group_members_group ON group_members(group_id);
CREATE INDEX IF NOT EXISTS ix_group_members_user ON group_members(user_id);

-- Create indexes for document_permissions
CREATE INDEX IF NOT EXISTS ix_document_permissions_document ON document_permissions(document_id);
CREATE INDEX IF NOT EXISTS ix_document_permissions_user ON document_permissions(user_id);
CREATE INDEX IF NOT EXISTS ix_document_permissions_group ON document_permissions(group_id);
CREATE INDEX IF NOT EXISTS ix_document_permissions_expires ON document_permissions(expires_at);

-- Add comments
COMMENT ON TABLE groups IS 'User groups for permission management';
COMMENT ON TABLE group_members IS 'Group membership relationships';
COMMENT ON TABLE document_permissions IS 'Document access control permissions';

COMMENT ON COLUMN document_permissions.permission_type IS 'Permission level: read < write < admin';
COMMENT ON COLUMN document_permissions.expires_at IS 'Optional expiration timestamp for temporary permissions';
