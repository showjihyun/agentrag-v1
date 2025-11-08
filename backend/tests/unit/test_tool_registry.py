"""Tests for Tool Registry."""

import pytest
from backend.core.tools.registry import ToolRegistry
from backend.core.tools.base import BaseTool, ToolConfig, ParamConfig, OutputConfig, RequestConfig
from backend.core.tools.init_tools import initialize_tools, get_tool_summary


class TestToolRegistry:
    """Test Tool Registry functionality."""
    
    def setup_method(self):
        """Clear registry before each test."""
        ToolRegistry.clear_registry()
    
    def test_register_tool(self):
        """Test tool registration."""
        
        @ToolRegistry.register(
            tool_id="test_tool",
            name="Test Tool",
            description="A test tool",
            category="test",
            params={
                "input": ParamConfig(
                    type="string",
                    description="Test input",
                    required=True
                )
            },
            outputs={
                "output": OutputConfig(
                    type="string",
                    description="Test output"
                )
            }
        )
        class TestTool:
            pass
        
        # Verify tool is registered
        assert ToolRegistry.is_registered("test_tool")
        
        # Get tool config
        config = ToolRegistry.get_tool_config("test_tool")
        assert config is not None
        assert config.id == "test_tool"
        assert config.name == "Test Tool"
        assert config.category == "test"
    
    def test_get_tool(self):
        """Test getting tool instance."""
        
        @ToolRegistry.register(
            tool_id="test_tool_2",
            name="Test Tool 2",
            description="Another test tool",
            category="test",
            params={},
            outputs={}
        )
        class TestTool2:
            pass
        
        # Get tool instance
        tool = ToolRegistry.get_tool("test_tool_2")
        assert tool is not None
        assert isinstance(tool, BaseTool)
    
    def test_list_tools(self):
        """Test listing tools."""
        
        # Register multiple tools
        @ToolRegistry.register(
            tool_id="tool_1",
            name="Tool 1",
            description="Tool 1",
            category="category_a",
            params={},
            outputs={}
        )
        class Tool1:
            pass
        
        @ToolRegistry.register(
            tool_id="tool_2",
            name="Tool 2",
            description="Tool 2",
            category="category_a",
            params={},
            outputs={}
        )
        class Tool2:
            pass
        
        @ToolRegistry.register(
            tool_id="tool_3",
            name="Tool 3",
            description="Tool 3",
            category="category_b",
            params={},
            outputs={}
        )
        class Tool3:
            pass
        
        # List all tools
        all_tools = ToolRegistry.list_tools()
        assert len(all_tools) == 3
        
        # List by category
        category_a_tools = ToolRegistry.list_tools(category="category_a")
        assert len(category_a_tools) == 2
        
        category_b_tools = ToolRegistry.list_tools(category="category_b")
        assert len(category_b_tools) == 1
    
    def test_list_by_category(self):
        """Test listing tools grouped by category."""
        
        @ToolRegistry.register(
            tool_id="ai_tool",
            name="AI Tool",
            description="AI tool",
            category="ai",
            params={},
            outputs={}
        )
        class AITool:
            pass
        
        @ToolRegistry.register(
            tool_id="data_tool",
            name="Data Tool",
            description="Data tool",
            category="data",
            params={},
            outputs={}
        )
        class DataTool:
            pass
        
        # Get tools by category
        by_category = ToolRegistry.list_by_category()
        
        assert "ai" in by_category
        assert "data" in by_category
        assert len(by_category["ai"]) == 1
        assert len(by_category["data"]) == 1
    
    def test_get_tool_ids(self):
        """Test getting all tool IDs."""
        
        @ToolRegistry.register(
            tool_id="tool_a",
            name="Tool A",
            description="Tool A",
            category="test",
            params={},
            outputs={}
        )
        class ToolA:
            pass
        
        @ToolRegistry.register(
            tool_id="tool_b",
            name="Tool B",
            description="Tool B",
            category="test",
            params={},
            outputs={}
        )
        class ToolB:
            pass
        
        tool_ids = ToolRegistry.get_tool_ids()
        assert "tool_a" in tool_ids
        assert "tool_b" in tool_ids
        assert len(tool_ids) == 2


class TestToolInitialization:
    """Test tool initialization."""
    
    def test_initialize_tools(self):
        """Test initializing all tools."""
        # Clear registry
        ToolRegistry.clear_registry()
        
        # Initialize tools
        tool_count = initialize_tools()
        
        # Verify tools are registered
        assert tool_count > 0
        assert len(ToolRegistry.get_tool_ids()) == tool_count
    
    def test_get_tool_summary(self):
        """Test getting tool summary."""
        # Clear and initialize
        ToolRegistry.clear_registry()
        initialize_tools()
        
        # Get summary
        summary = get_tool_summary()
        
        assert "total_tools" in summary
        assert "by_category" in summary
        assert "categories" in summary
        
        assert summary["total_tools"] > 0
        assert len(summary["categories"]) > 0
        
        # Verify expected categories
        expected_categories = ["ai", "communication", "productivity", "data", "search"]
        for category in expected_categories:
            assert category in summary["categories"]


class TestToolExecution:
    """Test tool execution."""
    
    @pytest.mark.asyncio
    async def test_execute_tool_with_validation(self):
        """Test tool execution with parameter validation."""
        
        @ToolRegistry.register(
            tool_id="validation_test_tool",
            name="Validation Test Tool",
            description="Tool for testing validation",
            category="test",
            params={
                "required_param": ParamConfig(
                    type="string",
                    description="Required parameter",
                    required=True
                ),
                "optional_param": ParamConfig(
                    type="string",
                    description="Optional parameter",
                    required=False
                )
            },
            outputs={
                "result": OutputConfig(
                    type="string",
                    description="Result"
                )
            }
        )
        class ValidationTestTool(BaseTool):
            async def execute(self, params, credentials=None):
                return {"result": f"Processed: {params.get('required_param')}"}
        
        # Get tool
        tool = ToolRegistry.get_tool("validation_test_tool")
        
        # Test with valid params
        result = await tool.execute_with_error_handling(
            params={"required_param": "test_value"}
        )
        assert result["success"] is True
        assert "Processed: test_value" in result["outputs"]["result"]
        
        # Test with missing required param
        result = await tool.execute_with_error_handling(
            params={}
        )
        assert result["success"] is False
        assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
