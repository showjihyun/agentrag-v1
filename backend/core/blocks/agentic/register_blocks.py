"""
Register Agentic Workflow Blocks

Registers all agentic blocks (Reflection, Planning, Tool Selection, Agentic RAG)
to the BlockRegistry for use in visual workflows.
"""

import logging
from backend.core.blocks.registry import BlockRegistry

logger = logging.getLogger(__name__)


def register_agentic_blocks():
    """Register all agentic workflow blocks to the registry."""
    
    # 1. Reflection Block
    BlockRegistry.register_block_config(
        block_type="agentic_reflection",
        config={
            "name": "Reflection",
            "description": "Self-evaluate and iteratively improve responses with quality scoring",
            "category": "agentic",
            "bg_color": "#8B5CF6",  # Purple
            "icon": "sparkles",
            "sub_blocks": [
                {
                    "id": "input",
                    "type": "textarea",
                    "title": "Input",
                    "required": True,
                    "placeholder": "Content to reflect on and improve"
                },
                {
                    "id": "max_iterations",
                    "type": "number",
                    "title": "Max Iterations",
                    "required": False,
                    "default": 3,
                    "min": 1,
                    "max": 10
                },
                {
                    "id": "quality_threshold",
                    "type": "slider",
                    "title": "Quality Threshold",
                    "required": False,
                    "default": 0.8,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.1
                },
                {
                    "id": "llm_provider",
                    "type": "dropdown",
                    "title": "LLM Provider",
                    "required": False,
                    "default": "ollama",
                    "options": [
                        {"label": "Ollama (Local)", "value": "ollama"},
                        {"label": "OpenAI", "value": "openai"},
                        {"label": "Claude (Anthropic)", "value": "claude"}
                    ]
                },
                {
                    "id": "llm_model",
                    "type": "text",
                    "title": "Model Name",
                    "required": False,
                    "placeholder": "e.g., llama3.3:70b, gpt-4, claude-3-sonnet"
                },
                {
                    "id": "temperature",
                    "type": "slider",
                    "title": "Temperature",
                    "required": False,
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1
                }
            ],
            "inputs": {
                "input": {"type": "string", "required": True},
                "max_iterations": {"type": "integer", "default": 3},
                "quality_threshold": {"type": "number", "default": 0.8}
            },
            "outputs": {
                "improved_output": {"type": "string"},
                "quality_score": {"type": "number"},
                "iteration_count": {"type": "integer"},
                "reflection_history": {"type": "array"}
            },
            "docs_link": "/docs/blocks/agentic-reflection"
        }
    )
    
    # 2. Planning Block
    BlockRegistry.register_block_config(
        block_type="agentic_planning",
        config={
            "name": "Planning",
            "description": "Decompose complex tasks into subtasks with dependency management",
            "category": "agentic",
            "bg_color": "#10B981",  # Green
            "icon": "list-tree",
            "sub_blocks": [
                {
                    "id": "task",
                    "type": "textarea",
                    "title": "Task",
                    "required": True,
                    "placeholder": "Complex task to decompose"
                },
                {
                    "id": "execution_mode",
                    "type": "dropdown",
                    "title": "Execution Mode",
                    "required": False,
                    "default": "sequential",
                    "options": [
                        {"label": "Sequential", "value": "sequential"},
                        {"label": "Parallel", "value": "parallel"},
                        {"label": "Adaptive", "value": "adaptive"}
                    ]
                },
                {
                    "id": "enable_replanning",
                    "type": "toggle",
                    "title": "Enable Replanning",
                    "required": False,
                    "default": True
                },
                {
                    "id": "llm_provider",
                    "type": "dropdown",
                    "title": "LLM Provider",
                    "required": False,
                    "default": "ollama",
                    "options": [
                        {"label": "Ollama (Local)", "value": "ollama"},
                        {"label": "OpenAI", "value": "openai"},
                        {"label": "Claude (Anthropic)", "value": "claude"}
                    ]
                },
                {
                    "id": "llm_model",
                    "type": "text",
                    "title": "Model Name",
                    "required": False,
                    "placeholder": "e.g., llama3.3:70b, gpt-4, claude-3-sonnet"
                },
                {
                    "id": "temperature",
                    "type": "slider",
                    "title": "Temperature",
                    "required": False,
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1
                }
            ],
            "inputs": {
                "task": {"type": "string", "required": True},
                "execution_mode": {"type": "string", "default": "sequential"},
                "enable_replanning": {"type": "boolean", "default": True}
            },
            "outputs": {
                "plan": {"type": "object"},
                "subtasks": {"type": "array"},
                "execution_results": {"type": "array"},
                "success": {"type": "boolean"}
            },
            "docs_link": "/docs/blocks/agentic-planning"
        }
    )
    
    # 3. Tool Selector Block
    BlockRegistry.register_block_config(
        block_type="agentic_tool_selector",
        config={
            "name": "Tool Selector",
            "description": "Dynamically select the best tool based on task requirements",
            "category": "agentic",
            "bg_color": "#F59E0B",  # Amber
            "icon": "wrench",
            "sub_blocks": [
                {
                    "id": "task",
                    "type": "textarea",
                    "title": "Task",
                    "required": True,
                    "placeholder": "Task description for tool selection"
                },
                {
                    "id": "available_tools",
                    "type": "multi-select",
                    "title": "Available Tools",
                    "required": True,
                    "options": []  # Populated dynamically from tool registry
                },
                {
                    "id": "selection_strategy",
                    "type": "dropdown",
                    "title": "Selection Strategy",
                    "required": False,
                    "default": "best_match",
                    "options": [
                        {"label": "Best Match", "value": "best_match"},
                        {"label": "Cost Aware", "value": "cost_aware"},
                        {"label": "Success Rate", "value": "success_rate"}
                    ]
                },
                {
                    "id": "llm_provider",
                    "type": "dropdown",
                    "title": "LLM Provider",
                    "required": False,
                    "default": "ollama",
                    "options": [
                        {"label": "Ollama (Local)", "value": "ollama"},
                        {"label": "OpenAI", "value": "openai"},
                        {"label": "Claude (Anthropic)", "value": "claude"}
                    ]
                },
                {
                    "id": "llm_model",
                    "type": "text",
                    "title": "Model Name",
                    "required": False,
                    "placeholder": "e.g., llama3.3:70b, gpt-4, claude-3-sonnet"
                },
                {
                    "id": "temperature",
                    "type": "slider",
                    "title": "Temperature",
                    "required": False,
                    "default": 0.3,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1
                }
            ],
            "inputs": {
                "task": {"type": "string", "required": True},
                "available_tools": {"type": "array", "required": True},
                "selection_strategy": {"type": "string", "default": "best_match"}
            },
            "outputs": {
                "selected_tool": {"type": "string"},
                "confidence": {"type": "number"},
                "reasoning": {"type": "string"},
                "alternatives": {"type": "array"}
            },
            "docs_link": "/docs/blocks/agentic-tool-selector"
        }
    )
    
    # 4. Agentic RAG Block (FLAGSHIP)
    BlockRegistry.register_block_config(
        block_type="agentic_rag",
        config={
            "name": "Agentic RAG",
            "description": "Intelligent retrieval with query decomposition, multi-source search, and reflection",
            "category": "agentic",
            "bg_color": "#EC4899",  # Pink
            "icon": "brain",
            "sub_blocks": [
                {
                    "id": "query",
                    "type": "textarea",
                    "title": "Query",
                    "required": True,
                    "placeholder": "User query for intelligent retrieval"
                },
                {
                    "id": "strategy",
                    "type": "dropdown",
                    "title": "Retrieval Strategy",
                    "required": False,
                    "default": "adaptive",
                    "options": [
                        {"label": "Adaptive (Recommended)", "value": "adaptive"},
                        {"label": "Hybrid (Vector + Web)", "value": "hybrid"},
                        {"label": "Vector Only", "value": "vector_only"},
                        {"label": "Web Only", "value": "web_only"}
                    ]
                },
                {
                    "id": "top_k",
                    "type": "number",
                    "title": "Top K Sources",
                    "required": False,
                    "default": 10,
                    "min": 1,
                    "max": 50
                },
                {
                    "id": "enable_decomposition",
                    "type": "toggle",
                    "title": "Enable Query Decomposition",
                    "required": False,
                    "default": True
                },
                {
                    "id": "enable_reflection",
                    "type": "toggle",
                    "title": "Enable Response Reflection",
                    "required": False,
                    "default": True
                },
                {
                    "id": "max_iterations",
                    "type": "number",
                    "title": "Max Retrieval Iterations",
                    "required": False,
                    "default": 3,
                    "min": 1,
                    "max": 5
                },
                {
                    "id": "llm_provider",
                    "type": "dropdown",
                    "title": "LLM Provider",
                    "required": False,
                    "default": "ollama",
                    "options": [
                        {"label": "Ollama (Local)", "value": "ollama"},
                        {"label": "OpenAI", "value": "openai"},
                        {"label": "Claude (Anthropic)", "value": "claude"}
                    ]
                },
                {
                    "id": "llm_model",
                    "type": "text",
                    "title": "Model Name",
                    "required": False,
                    "placeholder": "e.g., llama3.3:70b, gpt-4, claude-3-sonnet"
                },
                {
                    "id": "temperature",
                    "type": "slider",
                    "title": "Temperature",
                    "required": False,
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1
                }
            ],
            "inputs": {
                "query": {"type": "string", "required": True},
                "strategy": {"type": "string", "default": "adaptive"},
                "top_k": {"type": "integer", "default": 10},
                "enable_decomposition": {"type": "boolean", "default": True},
                "enable_reflection": {"type": "boolean", "default": True},
                "max_iterations": {"type": "integer", "default": 3}
            },
            "outputs": {
                "answer": {"type": "string"},
                "sources": {"type": "array"},
                "query_complexity": {"type": "string"},
                "sub_queries": {"type": "array"},
                "confidence_score": {"type": "number"},
                "reflection_history": {"type": "array"},
                "total_sources": {"type": "integer"}
            },
            "docs_link": "/docs/blocks/agentic-rag"
        }
    )
    
    logger.info("✅ Registered 4 agentic workflow blocks")


# Auto-register on module import
register_agentic_blocks()
