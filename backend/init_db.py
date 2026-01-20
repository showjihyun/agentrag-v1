"""
Initialize database with basic tables for development
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from backend.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database with basic tables"""
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    logger.info("Creating basic database tables...")
    
    with engine.connect() as conn:
        # Enable UUID extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
        conn.commit()
        
        # Create users table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                email VARCHAR(255) UNIQUE NOT NULL,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                role VARCHAR(50) DEFAULT 'user',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login_at TIMESTAMP,
                query_count INTEGER DEFAULT 0,
                storage_used_bytes BIGINT DEFAULT 0,
                preferences JSONB DEFAULT '{}'
            );
        """))
        conn.commit()
        logger.info("✓ Users table created")
        
        # Create sessions table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sessions (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                title VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()
        logger.info("✓ Sessions table created")
        
        # Create messages table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS messages (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
                role VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()
        logger.info("✓ Messages table created")
        
        # Create workflows table for agent builder
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS workflows (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                config JSONB DEFAULT '{}',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()
        logger.info("✓ Workflows table created")
        
        # Create knowledge_bases table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS knowledge_bases (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()
        logger.info("✓ Knowledge bases table created")
        
        # Create documents table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS documents (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                knowledge_base_id UUID REFERENCES knowledge_bases(id) ON DELETE CASCADE,
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                filename VARCHAR(500) NOT NULL,
                file_path VARCHAR(1000),
                file_size INTEGER,
                mime_type VARCHAR(100),
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()
        logger.info("✓ Documents table created")
        
        # Create agent_templates table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS agent_templates (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                name VARCHAR(255) NOT NULL,
                description TEXT,
                category VARCHAR(100),
                configuration JSONB NOT NULL DEFAULT '{}',
                required_tools JSONB,
                use_case_examples JSONB,
                is_published BOOLEAN DEFAULT FALSE,
                rating FLOAT,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT check_rating_range CHECK (rating >= 0.0 AND rating <= 5.0),
                CONSTRAINT check_usage_count_positive CHECK (usage_count >= 0)
            );
        """))
        conn.commit()
        logger.info("✓ Agent templates table created")
        
        # Create prompt_templates table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS prompt_templates (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                template_text TEXT NOT NULL,
                variables JSONB,
                is_system BOOLEAN DEFAULT FALSE,
                category VARCHAR(100),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()
        logger.info("✓ Prompt templates table created")
        
        # Create agents table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS agents (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                template_id UUID REFERENCES agent_templates(id) ON DELETE SET NULL,
                prompt_template_id UUID REFERENCES prompt_templates(id) ON DELETE SET NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                agent_type VARCHAR(50) NOT NULL,
                llm_provider VARCHAR(100) NOT NULL,
                llm_model VARCHAR(100) NOT NULL,
                configuration JSONB,
                context_items JSONB,
                mcp_servers JSONB,
                is_public BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP,
                CONSTRAINT check_agent_type_valid CHECK (agent_type IN ('custom', 'template_based'))
            );
        """))
        conn.commit()
        logger.info("✓ Agents table created")
        
        # Create blocks table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS blocks (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                block_type VARCHAR(50) NOT NULL,
                input_schema JSONB NOT NULL DEFAULT '{}',
                output_schema JSONB NOT NULL DEFAULT '{}',
                configuration JSONB,
                implementation TEXT,
                is_public BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT check_block_type_valid CHECK (block_type IN ('llm', 'tool', 'logic', 'composite')),
                CONSTRAINT uq_block_name_per_user UNIQUE (user_id, name)
            );
        """))
        conn.commit()
        logger.info("✓ Blocks table created")
        
        # Create agentflows table
        conn.execute(text("""
            DROP TABLE IF EXISTS agentflows CASCADE;
        """))
        conn.execute(text("""
            CREATE TABLE agentflows (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                orchestration_type VARCHAR(50) NOT NULL,
                supervisor_config JSONB,
                communication_protocol VARCHAR(50),
                graph_definition JSONB NOT NULL DEFAULT '{}',
                version VARCHAR(50),
                tags JSONB,
                category VARCHAR(100),
                is_public BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                execution_count INTEGER DEFAULT 0,
                last_execution_status VARCHAR(50),
                last_execution_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP,
                CONSTRAINT check_orchestration_type_valid 
                    CHECK (orchestration_type IN ('sequential', 'parallel', 'hierarchical', 'adaptive'))
            );
        """))
        conn.commit()
        logger.info("✓ Agentflows table created")
        
        # Create flow_executions table
        conn.execute(text("""
            DROP TABLE IF EXISTS flow_executions CASCADE;
        """))
        conn.execute(text("""
            CREATE TABLE flow_executions (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                agentflow_id UUID REFERENCES agentflows(id) ON DELETE CASCADE,
                chatflow_id UUID REFERENCES chatflows(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                flow_type VARCHAR(50) NOT NULL,
                flow_name VARCHAR(255),
                input_data JSONB,
                output_data JSONB,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                error_message TEXT,
                started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                duration_ms INTEGER,
                metrics JSONB,
                CONSTRAINT check_flow_type_valid 
                    CHECK (flow_type IN ('agentflow', 'chatflow')),
                CONSTRAINT check_flow_execution_status_valid 
                    CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
            );
        """))
        conn.commit()
        logger.info("✓ Flow executions table created")
        
        # Create chatflows table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chatflows (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                chat_config JSONB NOT NULL DEFAULT '{}',
                memory_config JSONB,
                rag_config JSONB,
                graph_definition JSONB NOT NULL DEFAULT '{}',
                version VARCHAR(50),
                tags JSONB,
                category VARCHAR(100),
                is_public BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                execution_count INTEGER DEFAULT 0,
                last_execution_status VARCHAR(50),
                last_execution_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP
            );
        """))
        conn.commit()
        logger.info("✓ Chatflows table created")
        
        # Create indexes for performance
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_flow_executions_agentflow 
            ON flow_executions(agentflow_id);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_flow_executions_chatflow 
            ON flow_executions(chatflow_id);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_flow_executions_started 
            ON flow_executions(started_at);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_flow_executions_status 
            ON flow_executions(status);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_flow_executions_user_id 
            ON flow_executions(user_id);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_flow_executions_user_status 
            ON flow_executions(user_id, status);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_workflows_user 
            ON workflows(user_id);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_documents_kb 
            ON documents(knowledge_base_id);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chatflows_user_id 
            ON chatflows(user_id);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chatflows_is_active 
            ON chatflows(is_active);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chatflows_is_public 
            ON chatflows(is_public);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chatflows_user_active 
            ON chatflows(user_id, is_active);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chatflows_user_created 
            ON chatflows(user_id, created_at);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_agentflows_user_id 
            ON agentflows(user_id);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_agentflows_is_active 
            ON agentflows(is_active);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_agentflows_is_public 
            ON agentflows(is_public);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_agentflows_user_active 
            ON agentflows(user_id, is_active);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_agentflows_user_created 
            ON agentflows(user_id, created_at);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_agents_user_id 
            ON agents(user_id);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_agents_agent_type 
            ON agents(agent_type);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_agents_is_public 
            ON agents(is_public);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_agents_user_created 
            ON agents(user_id, created_at);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_agents_user_type 
            ON agents(user_id, agent_type);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_blocks_user_id 
            ON blocks(user_id);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_blocks_block_type 
            ON blocks(block_type);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_blocks_is_public 
            ON blocks(is_public);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_blocks_user_public 
            ON blocks(user_id, is_public);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_blocks_user_type 
            ON blocks(user_id, block_type);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_prompt_templates_category 
            ON prompt_templates(category);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_prompt_templates_is_system 
            ON prompt_templates(is_system);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_agent_templates_category 
            ON agent_templates(category);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_agent_templates_is_published 
            ON agent_templates(is_published);
        """))
        conn.commit()
        logger.info("✓ Indexes created")
        
        logger.info("\n✅ Database initialization complete!")
        logger.info("You can now start the backend server.")

if __name__ == "__main__":
    try:
        init_database()
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        sys.exit(1)
