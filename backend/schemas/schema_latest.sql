-- Database Schema Export
-- Generated: 2026-01-20 13:28:59
-- Database: agenticrag
-- Total Tables: 47

-- ============================================
-- DROP EXISTING TABLES (if needed)
-- ============================================

DROP TABLE IF EXISTS rate_limit_configs CASCADE;
DROP TABLE IF EXISTS credits CASCADE;
DROP TABLE IF EXISTS marketplace_revenue CASCADE;
DROP TABLE IF EXISTS marketplace_reviews CASCADE;
DROP TABLE IF EXISTS marketplace_purchases CASCADE;
DROP TABLE IF EXISTS plugin_security_scans CASCADE;
DROP TABLE IF EXISTS plugin_audit_logs CASCADE;
DROP TABLE IF EXISTS plugin_dependencies CASCADE;
DROP TABLE IF EXISTS plugin_metrics CASCADE;
DROP TABLE IF EXISTS plugin_configurations CASCADE;
DROP TABLE IF EXISTS plugin_registry CASCADE;
DROP TABLE IF EXISTS user_settings CASCADE;
DROP TABLE IF EXISTS query_logs CASCADE;
DROP TABLE IF EXISTS tool_executions CASCADE;
DROP TABLE IF EXISTS knowledge_graphs CASCADE;
DROP TABLE IF EXISTS agentflow_edges CASCADE;
DROP TABLE IF EXISTS agentflow_agents CASCADE;
DROP TABLE IF EXISTS event_store CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;
DROP TABLE IF EXISTS conversation_shares CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS bookmarks CASCADE;
DROP TABLE IF EXISTS teams CASCADE;
DROP TABLE IF EXISTS organizations CASCADE;
DROP TABLE IF EXISTS agent_memories CASCADE;
DROP TABLE IF EXISTS agent_executions CASCADE;
DROP TABLE IF EXISTS agent_knowledgebases CASCADE;
DROP TABLE IF EXISTS agent_tools CASCADE;
DROP TABLE IF EXISTS agent_versions CASCADE;
DROP TABLE IF EXISTS flow_executions CASCADE;
DROP TABLE IF EXISTS blocks CASCADE;
DROP TABLE IF EXISTS agentflows CASCADE;
DROP TABLE IF EXISTS feedback CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS chatflows CASCADE;
DROP TABLE IF EXISTS alembic_version CASCADE;
DROP TABLE IF EXISTS tools CASCADE;
DROP TABLE IF EXISTS agent_templates CASCADE;
DROP TABLE IF EXISTS agents CASCADE;
DROP TABLE IF EXISTS prompt_templates CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS knowledge_bases CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS workflows CASCADE;
DROP TABLE IF EXISTS migration_history CASCADE;

-- ============================================
-- CREATE TABLES
-- ============================================


-- Table: migration_history
-- ============================================
CREATE TABLE migration_history (
    id INTEGER NOT NULL DEFAULT nextval('migration_history_id_seq'::regclass),
    filename VARCHAR(255) NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT true,
    PRIMARY KEY (id),
    CONSTRAINT migration_history_filename_key UNIQUE (filename)
);


-- Table: workflows
-- ============================================
CREATE TABLE workflows (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    user_id UUID,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    config JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    graph_definition JSONB DEFAULT '{}'::jsonb,
    compiled_graph JSONB,
    is_public BOOLEAN DEFAULT false,
    deleted_at TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION
);
CREATE INDEX idx_workflows_user ON workflows(user_id);


-- Table: sessions
-- ============================================
CREATE TABLE sessions (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    user_id UUID,
    title VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION
);


-- Table: messages
-- ============================================
CREATE TABLE messages (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    session_id UUID,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE NO ACTION
);


-- Table: users
-- ============================================
CREATE TABLE users (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL,
    username VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user'::character varying,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    full_name VARCHAR(255),
    last_login_at TIMESTAMP,
    query_count INTEGER DEFAULT 0,
    storage_used_bytes BIGINT DEFAULT 0,
    preferences JSONB DEFAULT '{}'::jsonb,
    PRIMARY KEY (id),
    CONSTRAINT users_email_key UNIQUE (email),
    CONSTRAINT users_username_key UNIQUE (username)
);


-- Table: knowledge_bases
-- ============================================
CREATE TABLE knowledge_bases (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    user_id UUID,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION
);


-- Table: documents
-- ============================================
CREATE TABLE documents (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    knowledge_base_id UUID,
    user_id UUID,
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000),
    file_size INTEGER,
    mime_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending'::character varying,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE NO ACTION,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION
);
CREATE INDEX idx_documents_kb ON documents(knowledge_base_id);


-- Table: prompt_templates
-- ============================================
CREATE TABLE prompt_templates (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    user_id UUID,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_text TEXT NOT NULL,
    variables JSONB,
    is_system BOOLEAN DEFAULT false,
    category VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION
);
CREATE INDEX idx_prompt_templates_category ON prompt_templates(category);
CREATE INDEX idx_prompt_templates_is_system ON prompt_templates(is_system);


-- Table: agents
-- ============================================
CREATE TABLE agents (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    template_id UUID,
    prompt_template_id UUID,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    agent_type VARCHAR(50) NOT NULL,
    llm_provider VARCHAR(100) NOT NULL,
    llm_model VARCHAR(100) NOT NULL,
    configuration JSONB,
    context_items JSONB,
    mcp_servers JSONB,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (prompt_template_id) REFERENCES prompt_templates(id) ON DELETE NO ACTION,
    FOREIGN KEY (template_id) REFERENCES agent_templates(id) ON DELETE NO ACTION,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION
);
CREATE INDEX idx_agents_agent_type ON agents(agent_type);
CREATE INDEX idx_agents_is_public ON agents(is_public);
CREATE INDEX idx_agents_user_id ON agents(user_id);
CREATE INDEX ix_agents_user_created ON agents(user_id, created_at);
CREATE INDEX ix_agents_user_type ON agents(user_id, agent_type);


-- Table: agent_templates
-- ============================================
CREATE TABLE agent_templates (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
    required_tools JSONB,
    use_case_examples JSONB,
    is_published BOOLEAN DEFAULT false,
    rating DOUBLE PRECISION,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);
CREATE INDEX idx_agent_templates_category ON agent_templates(category);
CREATE INDEX idx_agent_templates_is_published ON agent_templates(is_published);


-- Table: tools
-- ============================================
CREATE TABLE tools (
    id VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    input_schema JSONB,
    output_schema JSONB,
    implementation_type VARCHAR(50),
    implementation_ref VARCHAR(500),
    requires_auth BOOLEAN DEFAULT false,
    is_builtin BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);


-- Table: alembic_version
-- ============================================
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    PRIMARY KEY (version_num)
);


-- Table: chatflows
-- ============================================
CREATE TABLE chatflows (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    chat_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    memory_config JSONB,
    rag_config JSONB,
    graph_definition JSONB NOT NULL DEFAULT '{}'::jsonb,
    version VARCHAR(50),
    tags JSONB,
    category VARCHAR(100),
    is_public BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    execution_count INTEGER DEFAULT 0,
    last_execution_status VARCHAR(50),
    last_execution_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION
);
CREATE INDEX idx_chatflows_is_active ON chatflows(is_active);
CREATE INDEX idx_chatflows_is_public ON chatflows(is_public);
CREATE INDEX idx_chatflows_user_active ON chatflows(user_id, is_active);
CREATE INDEX idx_chatflows_user_created ON chatflows(user_id, created_at);
CREATE INDEX idx_chatflows_user_id ON chatflows(user_id);


-- Table: conversations
-- ============================================
CREATE TABLE conversations (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    title VARCHAR(255),
    description TEXT,
    metadata JSONB,
    is_archived BOOLEAN DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    deleted_at TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION
);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);
CREATE INDEX idx_conversations_user_created ON conversations(user_id, created_at);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);


-- Table: feedback
-- ============================================
CREATE TABLE feedback (
    id UUID NOT NULL,
    conversation_id UUID NOT NULL,
    user_id UUID NOT NULL,
    agent_id UUID,
    rating INTEGER NOT NULL,
    comment TEXT,
    feedback_type VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE NO ACTION,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE NO ACTION,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION
);
CREATE INDEX idx_feedback_agent_id ON feedback(agent_id);
CREATE INDEX idx_feedback_conversation_id ON feedback(conversation_id);
CREATE INDEX idx_feedback_rating ON feedback(rating);
CREATE INDEX idx_feedback_user_id ON feedback(user_id);


-- Table: agentflows
-- ============================================
CREATE TABLE agentflows (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    orchestration_type VARCHAR(50) NOT NULL,
    supervisor_config JSONB,
    communication_protocol VARCHAR(50),
    graph_definition JSONB NOT NULL DEFAULT '{}'::jsonb,
    version VARCHAR(50),
    tags JSONB,
    category VARCHAR(100),
    is_public BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    execution_count INTEGER DEFAULT 0,
    last_execution_status VARCHAR(50),
    last_execution_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION
);
CREATE INDEX idx_agentflows_is_active ON agentflows(is_active);
CREATE INDEX idx_agentflows_is_public ON agentflows(is_public);
CREATE INDEX idx_agentflows_user_active ON agentflows(user_id, is_active);
CREATE INDEX idx_agentflows_user_created ON agentflows(user_id, created_at);
CREATE INDEX idx_agentflows_user_id ON agentflows(user_id);


-- Table: blocks
-- ============================================
CREATE TABLE blocks (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    block_type VARCHAR(50) NOT NULL,
    input_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
    configuration JSONB,
    implementation TEXT,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION,
    CONSTRAINT uq_block_name_per_user UNIQUE (user_id, name)
);
CREATE INDEX idx_blocks_block_type ON blocks(block_type);
CREATE INDEX idx_blocks_is_public ON blocks(is_public);
CREATE INDEX idx_blocks_user_id ON blocks(user_id);
CREATE INDEX ix_blocks_user_public ON blocks(user_id, is_public);
CREATE INDEX ix_blocks_user_type ON blocks(user_id, block_type);


-- Table: flow_executions
-- ============================================
CREATE TABLE flow_executions (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    agentflow_id UUID,
    chatflow_id UUID,
    user_id UUID NOT NULL,
    flow_type VARCHAR(50) NOT NULL,
    flow_name VARCHAR(255),
    input_data JSONB,
    output_data JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'pending'::character varying,
    error_message TEXT,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    metrics JSONB,
    PRIMARY KEY (id),
    FOREIGN KEY (agentflow_id) REFERENCES agentflows(id) ON DELETE NO ACTION,
    FOREIGN KEY (chatflow_id) REFERENCES chatflows(id) ON DELETE NO ACTION,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION
);
CREATE INDEX idx_flow_executions_agentflow ON flow_executions(agentflow_id);
CREATE INDEX idx_flow_executions_chatflow ON flow_executions(chatflow_id);
CREATE INDEX idx_flow_executions_started ON flow_executions(started_at);
CREATE INDEX idx_flow_executions_status ON flow_executions(status);
CREATE INDEX idx_flow_executions_user_id ON flow_executions(user_id);
CREATE INDEX idx_flow_executions_user_status ON flow_executions(user_id, status);


-- Table: agent_versions
-- ============================================
CREATE TABLE agent_versions (
    id UUID NOT NULL,
    agent_id UUID NOT NULL,
    version_number INTEGER NOT NULL,
    configuration JSONB,
    context_items JSONB,
    mcp_servers JSONB,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE NO ACTION,
    CONSTRAINT uq_agent_version UNIQUE (agent_id, version_number)
);
CREATE INDEX idx_agent_versions_agent_id ON agent_versions(agent_id);
CREATE INDEX idx_agent_versions_created_at ON agent_versions(created_at);


-- Table: agent_tools
-- ============================================
CREATE TABLE agent_tools (
    id UUID NOT NULL,
    agent_id UUID NOT NULL,
    tool_id VARCHAR(100) NOT NULL,
    configuration JSONB,
    is_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE NO ACTION,
    FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE NO ACTION,
    CONSTRAINT uq_agent_tool UNIQUE (agent_id, tool_id)
);
CREATE INDEX idx_agent_tools_agent_id ON agent_tools(agent_id);
CREATE INDEX idx_agent_tools_tool_id ON agent_tools(tool_id);


-- Table: agent_knowledgebases
-- ============================================
CREATE TABLE agent_knowledgebases (
    id UUID NOT NULL,
    agent_id UUID NOT NULL,
    knowledge_base_id UUID NOT NULL,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE NO ACTION,
    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE NO ACTION,
    CONSTRAINT uq_agent_kb UNIQUE (agent_id, knowledge_base_id)
);
CREATE INDEX idx_agent_kb_agent_id ON agent_knowledgebases(agent_id);
CREATE INDEX idx_agent_kb_kb_id ON agent_knowledgebases(knowledge_base_id);


-- Table: agent_executions
-- ============================================
CREATE TABLE agent_executions (
    id UUID NOT NULL,
    agent_id UUID NOT NULL,
    user_id UUID NOT NULL,
    conversation_id UUID,
    status VARCHAR(50) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE NO ACTION,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE NO ACTION,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION
);
CREATE INDEX idx_agent_executions_agent_id ON agent_executions(agent_id);
CREATE INDEX idx_agent_executions_created_at ON agent_executions(created_at);
CREATE INDEX idx_agent_executions_status ON agent_executions(status);
CREATE INDEX idx_agent_executions_user_id ON agent_executions(user_id);


-- Table: agent_memories
-- ============================================
CREATE TABLE agent_memories (
    id UUID NOT NULL,
    agent_id UUID NOT NULL,
    memory_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    importance_score DOUBLE PRECISION,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE NO ACTION
);
CREATE INDEX idx_agent_memories_agent_id ON agent_memories(agent_id);
CREATE INDEX idx_agent_memories_created_at ON agent_memories(created_at);
CREATE INDEX idx_agent_memories_type ON agent_memories(memory_type);


-- Table: organizations
-- ============================================
CREATE TABLE organizations (
    id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL,
    logo_url VARCHAR(500),
    settings JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE NO ACTION
);
CREATE INDEX idx_organizations_created_at ON organizations(created_at);
CREATE INDEX idx_organizations_owner_id ON organizations(owner_id);


-- Table: teams
-- ============================================
CREATE TABLE teams (
    id UUID NOT NULL,
    organization_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE NO ACTION,
    CONSTRAINT uq_team_org_name UNIQUE (organization_id, name)
);
CREATE INDEX idx_teams_organization_id ON teams(organization_id);


-- Table: bookmarks
-- ============================================
CREATE TABLE bookmarks (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    conversation_id UUID NOT NULL,
    title VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE NO ACTION,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION,
    CONSTRAINT uq_bookmark_user_conv UNIQUE (user_id, conversation_id)
);
CREATE INDEX idx_bookmarks_conversation_id ON bookmarks(conversation_id);
CREATE INDEX idx_bookmarks_user_id ON bookmarks(user_id);


-- Table: notifications
-- ============================================
CREATE TABLE notifications (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50),
    is_read BOOLEAN DEFAULT false,
    data JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    read_at TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION
);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);


-- Table: conversation_shares
-- ============================================
CREATE TABLE conversation_shares (
    id UUID NOT NULL,
    conversation_id UUID NOT NULL,
    shared_by_user_id UUID NOT NULL,
    shared_with_user_id UUID NOT NULL,
    permission_level VARCHAR(50) DEFAULT 'view'::character varying,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE NO ACTION,
    FOREIGN KEY (shared_by_user_id) REFERENCES users(id) ON DELETE NO ACTION,
    FOREIGN KEY (shared_with_user_id) REFERENCES users(id) ON DELETE NO ACTION,
    CONSTRAINT uq_share_conv_user UNIQUE (conversation_id, shared_with_user_id)
);
CREATE INDEX idx_conversation_shares_conversation_id ON conversation_shares(conversation_id);
CREATE INDEX idx_conversation_shares_shared_with_user_id ON conversation_shares(shared_with_user_id);


-- Table: api_keys
-- ============================================
CREATE TABLE api_keys (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    last_used_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    expires_at TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION,
    CONSTRAINT uq_api_key_hash UNIQUE (key_hash)
);
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);


-- Table: event_store
-- ============================================
CREATE TABLE event_store (
    id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    aggregate_id UUID,
    aggregate_type VARCHAR(100),
    data JSONB NOT NULL,
    metadata JSONB,
    user_id UUID,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (id)
);
CREATE INDEX idx_event_store_aggregate_id ON event_store(aggregate_id);
CREATE INDEX idx_event_store_created_at ON event_store(created_at);
CREATE INDEX idx_event_store_event_type ON event_store(event_type);
CREATE INDEX idx_event_store_user_id ON event_store(user_id);


-- Table: agentflow_agents
-- ============================================
CREATE TABLE agentflow_agents (
    id UUID NOT NULL,
    agentflow_id UUID NOT NULL,
    agent_id UUID NOT NULL,
    position_x DOUBLE PRECISION,
    position_y DOUBLE PRECISION,
    configuration JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE NO ACTION,
    FOREIGN KEY (agentflow_id) REFERENCES agentflows(id) ON DELETE NO ACTION,
    CONSTRAINT uq_agentflow_agent UNIQUE (agentflow_id, agent_id)
);
CREATE INDEX idx_agentflow_agents_agent_id ON agentflow_agents(agent_id);
CREATE INDEX idx_agentflow_agents_agentflow_id ON agentflow_agents(agentflow_id);


-- Table: agentflow_edges
-- ============================================
CREATE TABLE agentflow_edges (
    id UUID NOT NULL,
    agentflow_id UUID NOT NULL,
    source_agent_id UUID NOT NULL,
    target_agent_id UUID NOT NULL,
    edge_type VARCHAR(50),
    condition JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (agentflow_id) REFERENCES agentflows(id) ON DELETE NO ACTION,
    FOREIGN KEY (source_agent_id) REFERENCES agents(id) ON DELETE NO ACTION,
    FOREIGN KEY (target_agent_id) REFERENCES agents(id) ON DELETE NO ACTION
);
CREATE INDEX idx_agentflow_edges_agentflow_id ON agentflow_edges(agentflow_id);
CREATE INDEX idx_agentflow_edges_source_agent_id ON agentflow_edges(source_agent_id);
CREATE INDEX idx_agentflow_edges_target_agent_id ON agentflow_edges(target_agent_id);


-- Table: knowledge_graphs
-- ============================================
CREATE TABLE knowledge_graphs (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    graph_data JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION
);
CREATE INDEX idx_knowledge_graphs_created_at ON knowledge_graphs(created_at);
CREATE INDEX idx_knowledge_graphs_user_id ON knowledge_graphs(user_id);


-- Table: tool_executions
-- ============================================
CREATE TABLE tool_executions (
    id UUID NOT NULL,
    agent_id UUID NOT NULL,
    tool_id VARCHAR(100) NOT NULL,
    tool_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    input_params JSONB,
    output_result JSONB,
    error_message TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    completed_at TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE NO ACTION,
    FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE NO ACTION
);
CREATE INDEX idx_tool_executions_agent_id ON tool_executions(agent_id);
CREATE INDEX idx_tool_executions_created_at ON tool_executions(created_at);
CREATE INDEX idx_tool_executions_status ON tool_executions(status);
CREATE INDEX idx_tool_executions_tool_id ON tool_executions(tool_id);


-- Table: query_logs
-- ============================================
CREATE TABLE query_logs (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    query TEXT NOT NULL,
    query_type VARCHAR(50),
    results_count INTEGER,
    execution_time_ms INTEGER,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION
);
CREATE INDEX idx_query_logs_created_at ON query_logs(created_at);
CREATE INDEX idx_query_logs_query_type ON query_logs(query_type);
CREATE INDEX idx_query_logs_user_id ON query_logs(user_id);


-- Table: user_settings
-- ============================================
CREATE TABLE user_settings (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    theme VARCHAR(50) DEFAULT 'light'::character varying,
    language VARCHAR(10) DEFAULT 'en'::character varying,
    notifications_enabled BOOLEAN DEFAULT true,
    settings JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION,
    CONSTRAINT uq_user_settings_user_id UNIQUE (user_id)
);


-- Table: plugin_registry
-- ============================================
CREATE TABLE plugin_registry (
    id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    author VARCHAR(255),
    category VARCHAR(50),
    status VARCHAR(50),
    manifest JSONB NOT NULL,
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64),
    signature TEXT,
    installed_at TIMESTAMP,
    last_updated TIMESTAMP,
    created_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (id),
    CONSTRAINT uq_plugin_name_version UNIQUE (name, version)
);
CREATE INDEX idx_plugin_registry_category ON plugin_registry(category);
CREATE INDEX idx_plugin_registry_name ON plugin_registry(name);
CREATE INDEX idx_plugin_registry_status ON plugin_registry(status);


-- Table: plugin_configurations
-- ============================================
CREATE TABLE plugin_configurations (
    id UUID NOT NULL,
    plugin_id UUID NOT NULL,
    user_id UUID,
    environment VARCHAR(50),
    settings JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (plugin_id) REFERENCES plugin_registry(id) ON DELETE NO ACTION,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION,
    CONSTRAINT uq_plugin_config_user_env UNIQUE (plugin_id, user_id, environment)
);
CREATE INDEX idx_plugin_configurations_plugin_user ON plugin_configurations(plugin_id, user_id);


-- Table: plugin_metrics
-- ============================================
CREATE TABLE plugin_metrics (
    id UUID NOT NULL,
    plugin_id UUID NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    metric_value VARCHAR(255),
    metric_metadata JSONB,
    recorded_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (plugin_id) REFERENCES plugin_registry(id) ON DELETE NO ACTION
);
CREATE INDEX idx_plugin_metrics_name ON plugin_metrics(metric_name);
CREATE INDEX idx_plugin_metrics_plugin_time ON plugin_metrics(plugin_id, recorded_at);


-- Table: plugin_dependencies
-- ============================================
CREATE TABLE plugin_dependencies (
    id UUID NOT NULL,
    plugin_id UUID NOT NULL,
    dependency_name VARCHAR(255) NOT NULL,
    version_constraint VARCHAR(100),
    optional BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (plugin_id) REFERENCES plugin_registry(id) ON DELETE NO ACTION
);
CREATE INDEX idx_plugin_dependencies_name ON plugin_dependencies(dependency_name);
CREATE INDEX idx_plugin_dependencies_plugin ON plugin_dependencies(plugin_id);


-- Table: plugin_audit_logs
-- ============================================
CREATE TABLE plugin_audit_logs (
    id UUID NOT NULL,
    plugin_id UUID,
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (plugin_id) REFERENCES plugin_registry(id) ON DELETE NO ACTION,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION
);
CREATE INDEX idx_plugin_audit_action ON plugin_audit_logs(action);
CREATE INDEX idx_plugin_audit_plugin ON plugin_audit_logs(plugin_id);
CREATE INDEX idx_plugin_audit_timestamp ON plugin_audit_logs(timestamp);
CREATE INDEX idx_plugin_audit_user ON plugin_audit_logs(user_id);


-- Table: plugin_security_scans
-- ============================================
CREATE TABLE plugin_security_scans (
    id UUID NOT NULL,
    plugin_id UUID NOT NULL,
    scan_type VARCHAR(50) NOT NULL,
    scan_result VARCHAR(20) NOT NULL,
    findings JSONB,
    scan_version VARCHAR(20),
    scanned_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (plugin_id) REFERENCES plugin_registry(id) ON DELETE NO ACTION
);
CREATE INDEX idx_plugin_security_plugin ON plugin_security_scans(plugin_id);
CREATE INDEX idx_plugin_security_result ON plugin_security_scans(scan_result);
CREATE INDEX idx_plugin_security_timestamp ON plugin_security_scans(scanned_at);


-- Table: marketplace_purchases
-- ============================================
CREATE TABLE marketplace_purchases (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    agent_id UUID NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD'::character varying,
    payment_status VARCHAR(50) DEFAULT 'pending'::character varying,
    payment_method VARCHAR(50),
    transaction_id VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    completed_at TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE NO ACTION,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION
);
CREATE INDEX idx_marketplace_purchases_agent_id ON marketplace_purchases(agent_id);
CREATE INDEX idx_marketplace_purchases_created_at ON marketplace_purchases(created_at);
CREATE INDEX idx_marketplace_purchases_status ON marketplace_purchases(payment_status);
CREATE INDEX idx_marketplace_purchases_user_id ON marketplace_purchases(user_id);


-- Table: marketplace_reviews
-- ============================================
CREATE TABLE marketplace_reviews (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    agent_id UUID NOT NULL,
    rating INTEGER NOT NULL,
    title VARCHAR(255),
    comment TEXT,
    is_verified_purchase BOOLEAN DEFAULT false,
    helpful_count INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE NO ACTION,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION,
    CONSTRAINT uq_review_user_agent UNIQUE (user_id, agent_id)
);
CREATE INDEX idx_marketplace_reviews_agent_id ON marketplace_reviews(agent_id);
CREATE INDEX idx_marketplace_reviews_created_at ON marketplace_reviews(created_at);
CREATE INDEX idx_marketplace_reviews_rating ON marketplace_reviews(rating);
CREATE INDEX idx_marketplace_reviews_user_id ON marketplace_reviews(user_id);


-- Table: marketplace_revenue
-- ============================================
CREATE TABLE marketplace_revenue (
    id UUID NOT NULL,
    agent_id UUID NOT NULL,
    seller_id UUID NOT NULL,
    purchase_id UUID NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    platform_fee NUMERIC(10, 2),
    seller_amount NUMERIC(10, 2),
    currency VARCHAR(3) DEFAULT 'USD'::character varying,
    status VARCHAR(50) DEFAULT 'pending'::character varying,
    payout_date TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE NO ACTION,
    FOREIGN KEY (purchase_id) REFERENCES marketplace_purchases(id) ON DELETE NO ACTION,
    FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE NO ACTION
);
CREATE INDEX idx_marketplace_revenue_agent_id ON marketplace_revenue(agent_id);
CREATE INDEX idx_marketplace_revenue_created_at ON marketplace_revenue(created_at);
CREATE INDEX idx_marketplace_revenue_seller_id ON marketplace_revenue(seller_id);
CREATE INDEX idx_marketplace_revenue_status ON marketplace_revenue(status);


-- Table: credits
-- ============================================
CREATE TABLE credits (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    description TEXT,
    reference_id UUID,
    reference_type VARCHAR(50),
    balance_after NUMERIC(10, 2),
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION
);
CREATE INDEX idx_credits_created_at ON credits(created_at);
CREATE INDEX idx_credits_reference ON credits(reference_id, reference_type);
CREATE INDEX idx_credits_transaction_type ON credits(transaction_type);
CREATE INDEX idx_credits_user_id ON credits(user_id);


-- Table: rate_limit_configs
-- ============================================
CREATE TABLE rate_limit_configs (
    id UUID NOT NULL,
    user_id UUID,
    organization_id UUID,
    limit_type VARCHAR(50) NOT NULL,
    limit_value INTEGER NOT NULL,
    time_window INTEGER NOT NULL,
    time_unit VARCHAR(20) DEFAULT 'second'::character varying,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE NO ACTION,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE NO ACTION
);
CREATE INDEX idx_rate_limit_configs_is_active ON rate_limit_configs(is_active);
CREATE INDEX idx_rate_limit_configs_limit_type ON rate_limit_configs(limit_type);
CREATE INDEX idx_rate_limit_configs_org_id ON rate_limit_configs(organization_id);
CREATE INDEX idx_rate_limit_configs_user_id ON rate_limit_configs(user_id);


-- ============================================
-- SCHEMA EXPORT COMPLETE
-- ============================================
