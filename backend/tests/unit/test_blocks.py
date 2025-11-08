"""Tests for workflow blocks."""

import pytest
import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from backend.core.blocks import BlockRegistry, BaseBlock, BlockExecutionError
from backend.core.blocks.openai_block import OpenAIBlock
from backend.core.blocks.http_block import HTTPBlock
from backend.core.blocks.condition_block import ConditionBlock
from backend.core.blocks.loop_block import LoopBlock
from backend.core.blocks.parallel_block import ParallelBlock


# ============================================================================
# BlockRegistry Tests
# ============================================================================

def test_block_registry_registration():
    """Test block registration in registry."""
    # OpenAI block should be registered
    assert BlockRegistry.is_registered("openai")
    
    # Get block config
    config = BlockRegistry.get_block_config("openai")
    assert config is not None
    assert config["name"] == "OpenAI"
    assert config["category"] == "tools"


def test_block_registry_list_blocks():
    """Test listing blocks from registry."""
    blocks = BlockRegistry.list_blocks()
    assert len(blocks) > 0
    
    # Check that our blocks are in the list
    block_types = [b["type"] for b in blocks]
    assert "openai" in block_types
    assert "http" in block_types
    assert "condition" in block_types


def test_block_registry_list_by_category():
    """Test listing blocks by category."""
    categorized = BlockRegistry.list_by_category()
    
    assert "tools" in categorized
    assert "blocks" in categorized
    
    # OpenAI should be in tools
    tool_types = [b["type"] for b in categorized["tools"]]
    assert "openai" in tool_types


def test_block_registry_get_block_class():
    """Test getting block class from registry."""
    block_class = BlockRegistry.get_block_class("openai")
    assert block_class is not None
    assert block_class == OpenAIBlock


def test_block_registry_create_instance():
    """Test creating block instance from registry."""
    block = BlockRegistry.create_block_instance(
        "openai",
        block_id="test_block",
        config={},
        sub_blocks={}
    )
    assert isinstance(block, OpenAIBlock)
    assert block.block_id == "test_block"


# ============================================================================
# OpenAI Block Tests
# ============================================================================

@pytest.mark.asyncio
async def test_openai_block_validation():
    """Test OpenAI block input validation."""
    block = OpenAIBlock(
        block_id="test_openai",
        sub_blocks={}
    )
    
    # Should fail without API key
    result = await block.execute_with_error_handling(
        inputs={"prompt": "Hello"},
        context={}
    )
    
    assert result["success"] is False
    assert "api_key" in result["error"].lower()


@pytest.mark.asyncio
async def test_openai_block_variable_interpolation():
    """Test variable interpolation in OpenAI block."""
    block = OpenAIBlock(
        block_id="test_openai",
        sub_blocks={
            "api_key": "test_key",
            "model": "gpt-4",
            "prompt": "Hello {{name}}, how are you?"
        }
    )
    
    # Test interpolation
    prompt = block._interpolate_variables(
        "Hello {{name}}, how are you?",
        {"name": "Alice"}
    )
    
    assert prompt == "Hello Alice, how are you?"


# ============================================================================
# HTTP Block Tests
# ============================================================================

@pytest.mark.asyncio
async def test_http_block_validation():
    """Test HTTP block input validation."""
    block = HTTPBlock(
        block_id="test_http",
        sub_blocks={}
    )
    
    # Should fail without URL
    result = await block.execute_with_error_handling(
        inputs={},
        context={}
    )
    
    assert result["success"] is False
    assert "url" in result["error"].lower()


def test_http_block_json_parsing():
    """Test JSON parsing in HTTP block."""
    block = HTTPBlock(
        block_id="test_http",
        sub_blocks={}
    )
    
    # Valid JSON
    result = block._parse_json('{"key": "value"}', "test")
    assert result == {"key": "value"}
    
    # Empty string
    result = block._parse_json("", "test")
    assert result == {}
    
    # Invalid JSON should raise error
    with pytest.raises(BlockExecutionError):
        block._parse_json("{invalid}", "test")


def test_http_block_variable_interpolation():
    """Test variable interpolation in HTTP block."""
    block = HTTPBlock(
        block_id="test_http",
        sub_blocks={}
    )
    
    # Test URL interpolation
    url = block._interpolate_variables(
        "https://api.example.com/users/{{user_id}}",
        {"user_id": "123"}
    )
    assert url == "https://api.example.com/users/123"
    
    # Test dict interpolation
    data = block._interpolate_dict_variables(
        {"name": "{{name}}", "age": 30},
        {"name": "Alice"}
    )
    assert data == {"name": "Alice", "age": 30}


# ============================================================================
# Condition Block Tests
# ============================================================================

@pytest.mark.asyncio
async def test_condition_block_equals():
    """Test condition block with equals operator."""
    block = ConditionBlock(
        block_id="test_condition",
        sub_blocks={
            "conditions": '[{"variable": "status", "operator": "==", "value": "success", "path": "true"}]',
            "default_path": "false"
        }
    )
    
    # Matching condition
    result = await block.execute(
        inputs={"variables": {"status": "success"}},
        context={}
    )
    
    assert result["path"] == "true"
    assert result["matched_condition"] is not None


@pytest.mark.asyncio
async def test_condition_block_default_path():
    """Test condition block default path."""
    block = ConditionBlock(
        block_id="test_condition",
        sub_blocks={
            "conditions": '[{"variable": "status", "operator": "==", "value": "success", "path": "true"}]',
            "default_path": "false"
        }
    )
    
    # Non-matching condition
    result = await block.execute(
        inputs={"variables": {"status": "failed"}},
        context={}
    )
    
    assert result["path"] == "false"
    assert result["matched_condition"] is None


def test_condition_block_nested_value():
    """Test getting nested values in condition block."""
    block = ConditionBlock(
        block_id="test_condition",
        sub_blocks={}
    )
    
    data = {
        "user": {
            "profile": {
                "name": "Alice"
            }
        }
    }
    
    value = block._get_nested_value(data, "user.profile.name")
    assert value == "Alice"
    
    # Non-existent path
    value = block._get_nested_value(data, "user.profile.age", default="unknown")
    assert value == "unknown"


# ============================================================================
# Loop Block Tests
# ============================================================================

@pytest.mark.asyncio
async def test_loop_block_for_type():
    """Test loop block with 'for' type."""
    block = LoopBlock(
        block_id="test_loop",
        sub_blocks={
            "loop_type": "for",
            "iterations": "3",
            "index_variable": "i"
        }
    )
    
    result = await block.execute(
        inputs={"variables": {}},
        context={}
    )
    
    assert result["count"] == 3
    assert len(result["iterations"]) == 3
    assert result["iterations"][0]["index"] == 0
    assert result["iterations"][2]["index"] == 2


@pytest.mark.asyncio
async def test_loop_block_foreach_type():
    """Test loop block with 'forEach' type."""
    block = LoopBlock(
        block_id="test_loop",
        sub_blocks={
            "loop_type": "forEach",
            "item_variable": "item",
            "index_variable": "i"
        }
    )
    
    result = await block.execute(
        inputs={
            "collection": ["a", "b", "c"],
            "variables": {}
        },
        context={}
    )
    
    assert result["count"] == 3
    assert len(result["iterations"]) == 3
    assert result["iterations"][0]["item"] == "a"
    assert result["iterations"][1]["item"] == "b"
    assert result["iterations"][2]["item"] == "c"


@pytest.mark.asyncio
async def test_loop_block_foreach_validation():
    """Test loop block validation for forEach."""
    block = LoopBlock(
        block_id="test_loop",
        sub_blocks={
            "loop_type": "forEach"
        }
    )
    
    # Should fail without collection
    result = await block.execute_with_error_handling(
        inputs={"variables": {}},
        context={}
    )
    
    assert result["success"] is False
    assert "collection" in result["error"].lower()


# ============================================================================
# Parallel Block Tests
# ============================================================================

@pytest.mark.asyncio
async def test_parallel_block_fixed_type():
    """Test parallel block with 'fixed' type."""
    block = ParallelBlock(
        block_id="test_parallel",
        sub_blocks={
            "parallel_type": "fixed",
            "branch_count": "3",
            "aggregation_strategy": "array"
        }
    )
    
    result = await block.execute(
        inputs={"variables": {}},
        context={}
    )
    
    assert result["count"] == 3
    assert len(result["branches"]) == 3
    assert result["aggregation_strategy"] == "array"


@pytest.mark.asyncio
async def test_parallel_block_collection_type():
    """Test parallel block with 'collection' type."""
    block = ParallelBlock(
        block_id="test_parallel",
        sub_blocks={
            "parallel_type": "collection",
            "item_variable": "item",
            "aggregation_strategy": "array"
        }
    )
    
    result = await block.execute(
        inputs={
            "collection": ["x", "y", "z"],
            "variables": {}
        },
        context={}
    )
    
    assert result["count"] == 3
    assert len(result["branches"]) == 3
    assert result["branches"][0]["item"] == "x"


def test_parallel_block_aggregation():
    """Test parallel block result aggregation."""
    # Array strategy
    results = [{"a": 1}, {"b": 2}, {"c": 3}]
    aggregated = ParallelBlock.aggregate_results(results, "array")
    assert aggregated == results
    
    # Merge strategy
    aggregated = ParallelBlock.aggregate_results(results, "merge")
    assert aggregated == {"a": 1, "b": 2, "c": 3}
    
    # First strategy
    aggregated = ParallelBlock.aggregate_results(results, "first")
    assert aggregated == {"a": 1}


# ============================================================================
# Base Block Tests
# ============================================================================

@pytest.mark.asyncio
async def test_base_block_execution_history():
    """Test base block execution history tracking."""
    block = LoopBlock(
        block_id="test_history",
        sub_blocks={
            "loop_type": "for",
            "iterations": "2"
        }
    )
    
    # Execute block
    await block.execute_with_error_handling(
        inputs={"variables": {}},
        context={}
    )
    
    # Check history
    history = block.get_execution_history()
    assert len(history) == 1
    assert history[0]["success"] is True
    assert "duration_ms" in history[0]


@pytest.mark.asyncio
async def test_base_block_error_handling():
    """Test base block error handling."""
    block = HTTPBlock(
        block_id="test_error",
        sub_blocks={}  # Missing required URL
    )
    
    # Execute should fail gracefully
    result = await block.execute_with_error_handling(
        inputs={},
        context={}
    )
    
    assert result["success"] is False
    assert "error" in result
    assert "duration_ms" in result
    
    # Check error was recorded in history
    history = block.get_execution_history()
    assert len(history) == 1
    assert history[0]["success"] is False
