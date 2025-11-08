"""Initialize Agent Builder with default data."""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.db.database import SessionLocal
from backend.db.models import Tool
from backend.services.agent_builder.secret_manager import SecretManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_builtin_tools():
    """Initialize built-in tools."""
    db = SessionLocal()
    
    try:
        tools = [
            Tool(
                id="vector_search",
                name="Vector Search",
                description="Search documents using semantic similarity",
                category="search",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "top_k": {"type": "integer", "default": 10, "description": "Number of results"}
                    },
                    "required": ["query"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "results": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string"},
                                    "score": {"type": "number"},
                                    "metadata": {"type": "object"}
                                }
                            }
                        }
                    }
                },
                implementation_type="builtin",
                implementation_ref="backend.services.hybrid_search.HybridSearchService",
                is_builtin=True
            ),
            Tool(
                id="web_search",
                name="Web Search",
                description="Search the web using DuckDuckGo",
                category="search",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "default": 5, "description": "Maximum results"}
                    },
                    "required": ["query"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "results": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "url": {"type": "string"},
                                    "snippet": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                implementation_type="builtin",
                implementation_ref="backend.services.web_search_service.WebSearchService",
                is_builtin=True
            ),
            Tool(
                id="llm_generate",
                name="LLM Generate",
                description="Generate text using LLM",
                category="llm",
                input_schema={
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "Prompt for LLM"},
                        "temperature": {"type": "number", "default": 0.7},
                        "max_tokens": {"type": "integer", "default": 2000}
                    },
                    "required": ["prompt"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "tokens_used": {"type": "integer"}
                    }
                },
                implementation_type="builtin",
                implementation_ref="backend.services.llm_manager.LLMManager",
                is_builtin=True
            ),
        ]
        
        added_count = 0
        for tool in tools:
            existing = db.query(Tool).filter(Tool.id == tool.id).first()
            if not existing:
                db.add(tool)
                added_count += 1
                logger.info(f"Added tool: {tool.name}")
            else:
                logger.info(f"Tool already exists: {tool.name}")
        
        db.commit()
        logger.info(f"✅ Initialized {added_count} new built-in tools (total: {len(tools)})")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to initialize tools: {e}", exc_info=True)
        raise
    finally:
        db.close()


async def validate_encryption():
    """Validate secret encryption is working."""
    db = SessionLocal()
    
    try:
        secret_manager = SecretManager(db)
        
        is_valid = secret_manager.validate_encryption()
        if is_valid:
            logger.info("✅ Secret encryption validated")
        else:
            logger.error("❌ Secret encryption validation failed")
            
    except Exception as e:
        logger.error(f"❌ Encryption validation error: {e}", exc_info=True)
    finally:
        db.close()


async def check_database_connection():
    """Check database connection."""
    db = SessionLocal()
    
    try:
        # Try a simple query
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False
    finally:
        db.close()


async def main():
    """Run all initialization tasks."""
    logger.info("🚀 Initializing Agent Builder...")
    logger.info("=" * 60)
    
    # Check database connection
    logger.info("\n[1/3] Checking database connection...")
    if not await check_database_connection():
        logger.error("Cannot proceed without database connection")
        return
    
    # Initialize built-in tools
    logger.info("\n[2/3] Initializing built-in tools...")
    await init_builtin_tools()
    
    # Validate encryption
    logger.info("\n[3/3] Validating encryption...")
    await validate_encryption()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Agent Builder initialization complete!")
    logger.info("\nNext steps:")
    logger.info("1. Update SECRET_ENCRYPTION_KEY in .env file")
    logger.info("2. Run database migrations: alembic upgrade head")
    logger.info("3. Start the application: uvicorn main:app --reload")


if __name__ == "__main__":
    asyncio.run(main())
