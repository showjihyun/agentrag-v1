"""
Integration tests for Agent Builder with existing RAG system components.

Tests verify that Agent Builder integrates seamlessly with:
- VectorSearchAgent, WebSearchAgent, LocalDataAgent as tools
- MemoryManager for session management
- LLMManager for model selection
- Milvus for vector storage
- PostgreSQL for metadata
"""

import pytest
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from backend.services.agent_builder.tool_registry import ToolRegistry
from backend.services.agent_builder.workflow_executor import WorkflowExecutor
from backend.services.agent_builder.agent_service import AgentService
from backend.services.llm_manager import LLMManager
from backend.services.milvus import MilvusManager
from backend.services.embedding import EmbeddingService
from backend.memory.manager import MemoryManager
from backend.db.database import get_db
from backend.db.models.agent_builder import Agent, Tool
from backend.agents.vector_search import VectorSearchAgent
from backend.agents.web_search_agent import WebSearchAgent
from backend.agents.local_data import LocalDataAgent


class TestAgentBuilderIntegration:
    """Test Agent Builder integration with existing RAG components."""
    
    @pytest.fixture
    async def db_session(self):
        """Get database session."""
        db = next(get_db())
        try:
            yield db
        finally:
            db.close()
    
    @pytest.fixture
    async def llm_manager(self):
        """Get LLM Manager instance."""
        return LLMManager()
    
    @pytest.fixture
    async def embedding_service(self):
        """Get Embedding Service instance."""
        return EmbeddingService()
    
    @pytest.fixture
    async def milvus_manager(self):
        """Get Milvus Manager instance."""
        return MilvusManager()
    
    @pytest.fixture
    async def memory_manager(self):
        """Get Memory Manager instance."""
        return MemoryManager()
    
    @pytest.fixture
    async def vector_search_agent(
        self,
        embedding_service,
        milvus_manager,
        llm_manager
    ):
        """Get VectorSearchAgent instance."""
        return VectorSearchAgent(
            embedding_service=embedding_service,
            milvus_manager=milvus_manager,
            llm_manager=llm_manager
        )
    
    @pytest.fixture
    async def web_search_agent(
        self,
        embedding_service,
        milvus_manager,
        llm_manager
    ):
        """Get WebSearchAgent instance."""
        return WebSearchAgent(
            embedding_service=embedding_service,
            milvus_manager=milvus_manager,
            llm_manager=llm_manager
        )
    
    @pytest.fixture
    async def local_data_agent(
        self,
        embedding_service,
        milvus_manager,
        llm_manager
    ):
        """Get LocalDataAgent instance."""
        return LocalDataAgent(
            embedding_service=embedding_service,
            milvus_manager=milvus_manager,
            llm_manager=llm_manager
        )
    
    @pytest.fixture
    async def tool_registry(
        self,
        db_session,
        vector_search_agent,
        web_search_agent,
        local_data_agent
    ):
        """Get ToolRegistry with existing agents."""
        return ToolRegistry(
            db=db_session,
            vector_search_agent=vector_search_agent,
            web_search_agent=web_search_agent,
            local_data_agent=local_data_agent
        )
    
    @pytest.mark.asyncio
    async def test_tool_registry_initialization(self, tool_registry, db_session):
        """Test that ToolRegistry initializes with existing agents as tools."""
        # Verify built-in tools are registered
        tools = tool_registry.list_tools(builtin_only=True)
        
        assert len(tools) >= 6, "Should have at least 6 built-in tools"
        
        tool_ids = [tool.id for tool in tools]
        assert "vector_search" in tool_ids
        assert "web_search" in tool_ids
        assert "local_data" in tool_ids
        assert "database_query" in tool_ids
        assert "file_operation" in tool_ids
        assert "http_api_call" in tool_ids
    
    @pytest.mark.asyncio
    async def test_vector_search_tool_integration(self, tool_registry):
        """Test VectorSearchAgent works as a tool in ToolRegistry."""
        # Get vector search tool
        tool = tool_registry.get_tool("vector_search")
        
        assert tool is not None
        assert tool.name == "vector_search"
        assert hasattr(tool, "_run")
        assert hasattr(tool, "_arun")
        
        # Verify tool has agent reference
        assert hasattr(tool, "vector_search_agent")
    
    @pytest.mark.asyncio
    async def test_web_search_tool_integration(self, tool_registry):
        """Test WebSearchAgent works as a tool in ToolRegistry."""
        # Get web search tool
        tool = tool_registry.get_tool("web_search")
        
        assert tool is not None
        assert tool.name == "web_search"
        assert hasattr(tool, "_run")
        assert hasattr(tool, "_arun")
        
        # Verify tool has agent reference
        assert hasattr(tool, "web_search_agent")
    
    @pytest.mark.asyncio
    async def test_local_data_tool_integration(self, tool_registry):
        """Test LocalDataAgent works as a tool in ToolRegistry."""
        # Get local data tool
        tool = tool_registry.get_tool("local_data")
        
        assert tool is not None
        assert tool.name == "local_data"
        assert hasattr(tool, "_run")
        assert hasattr(tool, "_arun")
        
        # Verify tool has agent reference
        assert hasattr(tool, "local_data_agent")
    
    @pytest.mark.asyncio
    async def test_tool_input_validation(self, tool_registry, db_session):
        """Test tool input validation against schemas."""
        # Test vector search tool validation
        valid_input = {
            "query": "test query",
            "top_k": 10
        }
        assert tool_registry.validate_tool_input("vector_search", valid_input)
        
        # Test invalid input (missing required field)
        invalid_input = {
            "top_k": 10
        }
        assert not tool_registry.validate_tool_input("vector_search", invalid_input)
    
    @pytest.mark.asyncio
    async def test_llm_manager_integration(self, llm_manager):
        """Test LLM Manager integration with Agent Builder."""
        # Verify LLM Manager is accessible
        assert llm_manager is not None
        
        # Test basic LLM call
        messages = [
            {"role": "user", "content": "Hello, this is a test."}
        ]
        
        response = await llm_manager.generate(
            messages=messages,
            stream=False,
            temperature=0.7,
            max_tokens=50
        )
        
        assert response is not None
        assert isinstance(response, str) or isinstance(response, dict)
    
    @pytest.mark.asyncio
    async def test_memory_manager_integration(self, memory_manager):
        """Test Memory Manager integration with Agent Builder."""
        # Verify Memory Manager is accessible
        assert memory_manager is not None
        
        # Test session creation
        session_id = "test_session_" + datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Add message to memory
        await memory_manager.add_message(
            session_id=session_id,
            role="user",
            content="Test message"
        )
        
        # Retrieve memory
        history = await memory_manager.get_history(session_id)
        
        assert len(history) > 0
        assert history[-1]["content"] == "Test message"
    
    @pytest.mark.asyncio
    async def test_milvus_integration(self, milvus_manager, embedding_service):
        """Test Milvus integration with Agent Builder."""
        # Verify Milvus Manager is accessible
        assert milvus_manager is not None
        
        # Test embedding generation
        text = "Test document for Milvus integration"
        embedding = await embedding_service.embed_text(text)
        
        assert embedding is not None
        assert isinstance(embedding, list)
        assert len(embedding) > 0
    
    @pytest.mark.asyncio
    async def test_postgresql_integration(self, db_session):
        """Test PostgreSQL integration with Agent Builder."""
        # Verify database session is accessible
        assert db_session is not None
        
        # Test querying tools table
        tools = db_session.query(Tool).filter(Tool.is_builtin == True).all()
        
        assert len(tools) >= 6
        
        # Verify tool data structure
        for tool in tools:
            assert tool.id is not None
            assert tool.name is not None
            assert tool.category is not None
            assert tool.input_schema is not None
    
    @pytest.mark.asyncio
    async def test_agent_service_with_existing_components(
        self,
        db_session,
        tool_registry,
        llm_manager
    ):
        """Test AgentService integration with existing components."""
        agent_service = AgentService(
            db=db_session,
            tool_registry=tool_registry,
            llm_manager=llm_manager
        )
        
        # Create test agent
        from backend.models.agent_builder import AgentCreate
        
        agent_data = AgentCreate(
            name="Test Integration Agent",
            description="Agent for testing integration",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.2:latest",
            prompt_template="Answer the question: {query}",
            tool_ids=["vector_search", "web_search"]
        )
        
        # Create agent
        agent = await agent_service.create_agent(
            user_id="test_user",
            agent_data=agent_data
        )
        
        assert agent is not None
        assert agent.name == "Test Integration Agent"
        assert len(agent.tools) == 2
        
        # Cleanup
        await agent_service.delete_agent(agent.id)
    
    @pytest.mark.asyncio
    async def test_workflow_executor_with_existing_components(
        self,
        llm_manager,
        memory_manager,
        tool_registry
    ):
        """Test WorkflowExecutor integration with existing components."""
        from backend.core.cache_manager import get_cache_manager
        
        cache = get_cache_manager()
        
        executor = WorkflowExecutor(
            llm_manager=llm_manager,
            memory_manager=memory_manager,
            tool_registry=tool_registry,
            cache=cache
        )
        
        assert executor is not None
        assert executor.llm_manager is llm_manager
        assert executor.memory_manager is memory_manager
        assert executor.tool_registry is tool_registry
    
    @pytest.mark.asyncio
    async def test_end_to_end_agent_execution(
        self,
        db_session,
        tool_registry,
        llm_manager,
        memory_manager
    ):
        """Test end-to-end agent execution with existing components."""
        # Create agent service
        agent_service = AgentService(
            db=db_session,
            tool_registry=tool_registry,
            llm_manager=llm_manager
        )
        
        # Create simple agent
        from backend.models.agent_builder import AgentCreate
        
        agent_data = AgentCreate(
            name="E2E Test Agent",
            description="End-to-end test agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.2:latest",
            prompt_template="You are a helpful assistant. Answer: {query}",
            tool_ids=[]  # No tools for simple test
        )
        
        agent = await agent_service.create_agent(
            user_id="test_user",
            agent_data=agent_data
        )
        
        # Execute agent (simplified - actual execution would use WorkflowExecutor)
        assert agent is not None
        assert agent.llm_provider == "ollama"
        assert agent.llm_model == "llama3.2:latest"
        
        # Cleanup
        await agent_service.delete_agent(agent.id)


class TestAgentBuilderErrorHandling:
    """Test error handling in Agent Builder integration."""
    
    @pytest.mark.asyncio
    async def test_tool_not_found_error(self, db_session):
        """Test error handling when tool is not found."""
        tool_registry = ToolRegistry(db=db_session)
        
        with pytest.raises(ValueError, match="Tool not found"):
            tool_registry.get_tool("nonexistent_tool")
    
    @pytest.mark.asyncio
    async def test_invalid_tool_input_error(self, db_session):
        """Test error handling for invalid tool input."""
        tool_registry = ToolRegistry(db=db_session)
        
        # Missing required field
        invalid_input = {"top_k": 10}
        
        is_valid = tool_registry.validate_tool_input("vector_search", invalid_input)
        assert not is_valid
    
    @pytest.mark.asyncio
    async def test_database_connection_error_handling(self):
        """Test error handling for database connection issues."""
        # This test would verify graceful degradation
        # when database is unavailable
        pass
    
    @pytest.mark.asyncio
    async def test_milvus_connection_error_handling(self):
        """Test error handling for Milvus connection issues."""
        # This test would verify graceful degradation
        # when Milvus is unavailable
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
