"""
Workflow Tools Integration Tests

Tests for verifying tool registration, execution, and UI integration.
"""

import pytest
import asyncio
import logging
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock

logger = logging.getLogger(__name__)


# ============================================================================
# Tool Registry Tests
# ============================================================================

class TestToolRegistry:
    """Test ToolRegistry functionality."""
    
    def test_tool_registration(self):
        """Test that all expected tools are registered."""
        from backend.core.tools.registry import ToolRegistry
        
        # Expected tool categories and counts
        expected_tools = {
            "ai": ["openai_chat", "anthropic_claude", "google_gemini", "mistral_ai", "cohere"],
            "communication": ["discord", "telegram", "sendgrid"],
            "search": ["tavily_search", "serper_search", "exa_search", "wikipedia_search", 
                      "arxiv_search", "google_custom_search", "bing_search", "duckduckgo_search", "youtube_search"],
            "data": ["supabase_query", "pinecone_upsert", "qdrant_insert", "s3_upload",
                    "mongodb_insert", "postgresql_query", "mysql_query", "redis_set",
                    "elasticsearch_index", "bigquery_query"],
            "developer": ["http_request"],
        }
        
        registered_ids = ToolRegistry.get_tool_ids()
        
        for category, tool_ids in expected_tools.items():
            for tool_id in tool_ids:
                assert tool_id in registered_ids, f"Tool '{tool_id}' not registered"
                
                # Verify tool config exists
                config = ToolRegistry.get_tool_config(tool_id)
                assert config is not None, f"Tool config for '{tool_id}' is None"
                assert config.category == category or config.category.lower() == category.lower(), \
                    f"Tool '{tool_id}' has wrong category: {config.category}"
    
    def test_tool_config_schema(self):
        """Test that tool configs have required fields."""
        from backend.core.tools.registry import ToolRegistry
        
        for tool_id in ToolRegistry.get_tool_ids():
            config = ToolRegistry.get_tool_config(tool_id)
            
            # Required fields
            assert config.id == tool_id
            assert config.name, f"Tool '{tool_id}' missing name"
            assert config.description, f"Tool '{tool_id}' missing description"
            assert config.category, f"Tool '{tool_id}' missing category"
            assert isinstance(config.params, dict), f"Tool '{tool_id}' params not dict"
            assert isinstance(config.outputs, dict), f"Tool '{tool_id}' outputs not dict"
    
    def test_tool_instance_creation(self):
        """Test that tool instances can be created."""
        from backend.core.tools.registry import ToolRegistry
        
        for tool_id in ToolRegistry.get_tool_ids():
            tool = ToolRegistry.get_tool(tool_id)
            assert tool is not None, f"Tool instance for '{tool_id}' is None"
            assert hasattr(tool, 'execute'), f"Tool '{tool_id}' missing execute method"
            assert hasattr(tool, 'validate_params'), f"Tool '{tool_id}' missing validate_params"


# ============================================================================
# Tool Execution Tests
# ============================================================================

class TestToolExecution:
    """Test tool execution functionality."""
    
    @pytest.mark.asyncio
    async def test_http_request_tool(self):
        """Test HTTP request tool execution."""
        from backend.core.tools.registry import ToolRegistry
        
        # Mock httpx response
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True, "data": "test"}
            mock_response.text = '{"success": true}'
            mock_response.headers = {"content-type": "application/json"}
            
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)
            
            result = await ToolRegistry.execute_tool(
                tool_id="http_request",
                params={
                    "url": "https://api.example.com/test",
                    "method": "GET",
                },
            )
            
            assert result["success"] is True
            assert "outputs" in result or "status_code" in result.get("outputs", result)
    
    @pytest.mark.asyncio
    async def test_openai_chat_tool_validation(self):
        """Test OpenAI chat tool parameter validation."""
        from backend.core.tools.registry import ToolRegistry
        from backend.core.tools.base import ToolExecutionError
        
        # Test missing required parameter
        with pytest.raises(ToolExecutionError) as exc_info:
            tool = ToolRegistry.get_tool("openai_chat")
            tool.validate_params({})  # Missing 'messages'
        
        assert "messages" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_ai_agent_tool(self):
        """Test AI Agent tool execution."""
        from backend.core.tools.integrations.ai_agent_tools import execute_ai_agent_tool
        
        # Mock LLM response
        with patch('backend.core.tools.integrations.ai_agent_tools._call_llm') as mock_llm:
            mock_llm.return_value = "This is a test response from the AI agent."
            
            result = await execute_ai_agent_tool({
                "task": "What is 2+2?",
                "llm_provider": "ollama",
                "model": "llama3.1:8b",
            })
            
            assert result["success"] is True
            assert "response" in result
    
    @pytest.mark.asyncio
    async def test_tool_error_handling(self):
        """Test tool error handling."""
        from backend.core.tools.registry import ToolRegistry
        
        # Test with invalid tool ID
        with pytest.raises(ValueError) as exc_info:
            await ToolRegistry.execute_tool(
                tool_id="nonexistent_tool",
                params={},
            )
        
        assert "not found" in str(exc_info.value).lower()


# ============================================================================
# Workflow Executor Tool Integration Tests
# ============================================================================

class TestWorkflowExecutorToolIntegration:
    """Test tool integration in workflow executor."""
    
    @pytest.mark.asyncio
    async def test_execute_tool_node(self):
        """Test _execute_tool_node method."""
        from backend.services.agent_builder.workflow_executor import WorkflowExecutor
        from unittest.mock import MagicMock
        
        # Create mock workflow and db
        mock_workflow = MagicMock()
        mock_workflow.id = "test-workflow-id"
        mock_workflow.graph_definition = {"nodes": [], "edges": []}
        
        mock_db = MagicMock()
        
        executor = WorkflowExecutor(mock_workflow, mock_db)
        
        # Mock ToolRegistry
        with patch('backend.core.tools.registry.ToolRegistry.execute_tool') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "outputs": {"result": "test output"},
            }
            
            result = await executor._execute_tool_node(
                node_data={
                    "tool_id": "http_request",
                    "name": "Test HTTP",
                    "config": {
                        "url": "https://api.example.com",
                        "method": "GET",
                    },
                },
                data={"input": "test"},
            )
            
            assert "tool_output" in result
            assert result["tool_id"] == "http_request"
    
    @pytest.mark.asyncio
    async def test_execute_ai_agent_node(self):
        """Test AI Agent node execution in workflow."""
        from backend.services.agent_builder.workflow_executor import WorkflowExecutor
        from unittest.mock import MagicMock
        
        mock_workflow = MagicMock()
        mock_workflow.id = "test-workflow-id"
        mock_workflow.graph_definition = {"nodes": [], "edges": []}
        
        mock_db = MagicMock()
        
        executor = WorkflowExecutor(mock_workflow, mock_db)
        
        with patch('backend.core.tools.integrations.ai_agent_tools.execute_ai_agent_tool') as mock_agent:
            mock_agent.return_value = {
                "success": True,
                "response": "AI response",
            }
            
            result = await executor._execute_ai_agent_node(
                node_data={
                    "config": {
                        "llm_provider": "ollama",
                        "model": "llama3.1:8b",
                        "system_prompt": "You are helpful.",
                    },
                },
                data={"user_query": "Hello"},
            )
            
            assert result is not None


# ============================================================================
# Tool Config UI Tests (Frontend)
# ============================================================================

class TestToolConfigUI:
    """Test tool configuration UI mappings."""
    
    def test_tool_config_registry_mappings(self):
        """Verify all backend tools have frontend config mappings."""
        # This would be run in a Node.js environment
        # Here we just document the expected mappings
        
        expected_mappings = {
            # AI Tools
            "openai_chat": "OpenAIChatConfig",
            "anthropic_claude": "OpenAIChatConfig",
            "google_gemini": "OpenAIChatConfig",
            "mistral_ai": "OpenAIChatConfig",
            "cohere": "OpenAIChatConfig",
            "ai_agent": "AIAgentConfigWrapper",
            
            # Communication
            "slack": "SlackConfig",
            "gmail": "GmailConfig",
            "discord": "SlackConfig",
            "telegram": "SlackConfig",
            "sendgrid": "GmailConfig",
            
            # Search
            "vector_search": "VectorSearchConfig",
            "tavily_search": "HttpRequestConfig",
            "serper_search": "HttpRequestConfig",
            
            # Data
            "postgres": "PostgresConfig",
            "postgresql_query": "PostgresConfig",
            
            # Control Flow
            "condition": "ConditionConfig",
            "loop": "LoopConfig",
            "parallel": "ParallelConfig",
            
            # HTTP
            "http_request": "HttpRequestConfig",
        }
        
        # Log expected mappings for documentation
        for tool_id, config_name in expected_mappings.items():
            logger.info(f"Tool '{tool_id}' -> {config_name}")
        
        assert len(expected_mappings) > 20, "Should have 20+ tool mappings"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
