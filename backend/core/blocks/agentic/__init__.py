"""
Agentic Workflow Blocks

Advanced blocks implementing agentic design patterns:
- Reflection: Self-evaluation and iterative improvement
- Planning: Task decomposition and subtask execution
- Tool Selection: Dynamic tool selection based on context
- Agentic RAG: Intelligent retrieval with query decomposition and validation
"""

from .reflection_block import ReflectionBlock
from .planning_block import PlanningBlock
from .tool_selector_block import ToolSelectorBlock
from .agentic_rag_block import AgenticRAGBlock

# Auto-register blocks to BlockRegistry
from .register_blocks import register_agentic_blocks

__all__ = [
    "ReflectionBlock",
    "PlanningBlock", 
    "ToolSelectorBlock",
    "AgenticRAGBlock",
    "register_agentic_blocks",
]
