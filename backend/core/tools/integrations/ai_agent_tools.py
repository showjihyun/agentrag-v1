"""
AI Agent Tools - n8n level implementation.
Comprehensive autonomous agent capabilities with tool use, reasoning, and memory.
"""

import logging
from typing import Dict, Any, List, Optional
import httpx
import json
from datetime import datetime

from backend.core.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class AIAgentTool:
    """Comprehensive AI Agent with n8n-level capabilities."""
    
    @staticmethod
    async def execute_agent(
        task: str,
        llm_provider: str = "ollama",
        model: str = "llama3.1:8b",
        enable_web_search: bool = True,
        enable_vector_search: bool = True,
        knowledgebase_id: Optional[str] = None,
        available_tools: Optional[List[str]] = None,
        max_iterations: int = 10,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        memory_enabled: bool = True,
        conversation_id: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute an autonomous AI agent with tool use and reasoning.
        
        Args:
            task: Task or question for the agent
            llm_provider: LLM provider (ollama, openai, anthropic)
            model: Model name
            enable_web_search: Allow web search
            enable_vector_search: Allow knowledge base search
            knowledgebase_id: Knowledge base ID
            available_tools: List of tool IDs the agent can use
            max_iterations: Maximum reasoning iterations
            temperature: Sampling temperature
            system_prompt: Custom system prompt
            max_tokens: Maximum tokens to generate
            memory_enabled: Enable conversation memory
            conversation_id: Conversation ID for memory
            
        Returns:
            Agent execution result with reasoning trace
        """
        # Initialize agent state
        agent_state = {
            "task": task,
            "iterations": 0,
            "max_iterations": max_iterations,
            "reasoning_trace": [],
            "tool_calls": [],
            "final_answer": None,
            "status": "running"
        }
        
        # Build system prompt
        if not system_prompt:
            system_prompt = f"""You are an autonomous AI agent that can use tools to accomplish tasks.

Available Tools:
{_format_available_tools(available_tools, enable_web_search, enable_vector_search)}

Instructions:
1. Analyze the task carefully
2. Break it down into steps
3. Use tools when needed
4. Reason through each step
5. Provide a final answer

Use this format:
Thought: [Your reasoning]
Action: [Tool name]
Action Input: [Tool parameters as JSON]
Observation: [Tool result]
... (repeat as needed)
Final Answer: [Your final response]
"""
        
        # Execute agent loop
        while agent_state["iterations"] < max_iterations:
            agent_state["iterations"] += 1
            
            # Generate next action
            try:
                response = await _call_llm(
                    provider=llm_provider,
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": task}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    api_key=api_key
                )
                
                # Parse response
                action = _parse_agent_response(response)
                
                if action["type"] == "final_answer":
                    agent_state["final_answer"] = action["content"]
                    agent_state["status"] = "completed"
                    break
                
                elif action["type"] == "tool_call":
                    # Execute tool
                    tool_result = await _execute_tool(
                        tool_name=action["tool"],
                        tool_input=action["input"],
                        enable_web_search=enable_web_search,
                        enable_vector_search=enable_vector_search,
                        knowledgebase_id=knowledgebase_id
                    )
                    
                    agent_state["tool_calls"].append({
                        "tool": action["tool"],
                        "input": action["input"],
                        "output": tool_result,
                        "iteration": agent_state["iterations"]
                    })
                    
                    agent_state["reasoning_trace"].append({
                        "iteration": agent_state["iterations"],
                        "thought": action.get("thought"),
                        "action": action["tool"],
                        "observation": tool_result
                    })
                
            except Exception as e:
                logger.error(f"Agent iteration error: {e}")
                agent_state["status"] = "error"
                agent_state["error"] = str(e)
                break
        
        if agent_state["iterations"] >= max_iterations and not agent_state["final_answer"]:
            agent_state["status"] = "max_iterations_reached"
            agent_state["final_answer"] = "Maximum iterations reached without finding a final answer."
        
        return {
            "success": agent_state["status"] in ["completed", "max_iterations_reached"],
            "answer": agent_state["final_answer"],
            "reasoning_trace": agent_state["reasoning_trace"],
            "tool_calls": agent_state["tool_calls"],
            "iterations": agent_state["iterations"],
            "status": agent_state["status"]
        }


def _format_available_tools(
    tools: Optional[List[str]],
    enable_web_search: bool,
    enable_vector_search: bool
) -> str:
    """Format available tools for system prompt."""
    tool_descriptions = []
    
    if enable_web_search:
        tool_descriptions.append("- web_search: Search the internet for information")
    
    if enable_vector_search:
        tool_descriptions.append("- vector_search: Search in knowledge base documents")
    
    if tools:
        for tool in tools:
            tool_descriptions.append(f"- {tool}: Execute {tool} tool")
    
    return "\n".join(tool_descriptions) if tool_descriptions else "No tools available"


async def _call_llm(
    provider: str,
    model: str,
    messages: List[Dict],
    temperature: float,
    max_tokens: int,
    api_key: Optional[str] = None
) -> str:
    """Call LLM provider using LLMManager."""
    from backend.services.llm_manager import LLMManager, LLMProvider
    
    try:
        # Map provider string to LLMProvider enum
        # Note: LLMProvider only has OLLAMA, OPENAI, CLAUDE
        provider_map = {
            "ollama": LLMProvider.OLLAMA,
            "openai": LLMProvider.OPENAI,
            "anthropic": LLMProvider.CLAUDE,
            "claude": LLMProvider.CLAUDE,
        }
        
        provider_enum = provider_map.get(provider.lower(), LLMProvider.OLLAMA)
        if not provider_enum:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        # Initialize LLM Manager
        llm_manager = LLMManager(
            provider=provider_enum,
            model=model,
            api_key=api_key
        )
        
        # Generate response (non-streaming for agent reasoning)
        response = await llm_manager.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )
        
        return response
        
    except Exception as e:
        logger.error(f"LLM call failed: {e}", exc_info=True)
        raise


def _parse_agent_response(response: str) -> Dict[str, Any]:
    """Parse agent response to extract action."""
    lines = response.strip().split("\n")
    
    action = {
        "type": "unknown",
        "thought": None,
        "tool": None,
        "input": None,
        "content": None
    }
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("Thought:"):
            action["thought"] = line.replace("Thought:", "").strip()
        
        elif line.startswith("Action:"):
            action["type"] = "tool_call"
            action["tool"] = line.replace("Action:", "").strip()
        
        elif line.startswith("Action Input:"):
            input_str = line.replace("Action Input:", "").strip()
            try:
                action["input"] = json.loads(input_str)
            except:
                action["input"] = input_str
        
        elif line.startswith("Final Answer:"):
            action["type"] = "final_answer"
            action["content"] = line.replace("Final Answer:", "").strip()
    
    return action


async def _execute_tool(
    tool_name: str,
    tool_input: Any,
    enable_web_search: bool,
    enable_vector_search: bool,
    knowledgebase_id: Optional[str]
) -> Any:
    """Execute a tool."""
    if tool_name == "web_search" and enable_web_search:
        # Execute web search
        return await _web_search(tool_input.get("query"))
    
    elif tool_name == "vector_search" and enable_vector_search:
        # Execute vector search
        return await _vector_search(
            query=tool_input.get("query"),
            knowledgebase_id=knowledgebase_id
        )
    
    else:
        return {"error": f"Tool {tool_name} not available or not enabled"}


async def _web_search(query: str) -> Dict[str, Any]:
    """Execute web search."""
    try:
        from duckduckgo_search import DDGS
        
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            return {
                "results": results,
                "count": len(results)
            }
    except Exception as e:
        return {"error": str(e)}


async def _vector_search(query: str, knowledgebase_id: Optional[str]) -> Dict[str, Any]:
    """Execute vector search."""
    # Implementation would call your vector search service
    return {
        "results": [],
        "message": "Vector search not implemented in this context"
    }


async def execute_ai_agent_tool(parameters: Dict[str, Any], credentials: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Execute AI Agent tool - simplified for direct LLM response."""
    try:
        # Extract API key from credentials if provided
        api_key = None
        if credentials and "api_key" in credentials:
            api_key = credentials["api_key"]
        
        task = parameters.get("task")
        if not task:
            return {
                "success": False,
                "error": "No task provided"
            }
        
        provider = parameters.get("llm_provider", "ollama")
        model = parameters.get("model", "llama3.1:8b")
        temperature = parameters.get("temperature", 0.7)
        max_tokens = parameters.get("max_tokens", 2000)
        system_prompt = parameters.get("system_prompt", "You are a helpful AI assistant.")
        
        logger.info(f"Executing AI Agent: provider={provider}, model={model}, task={task[:100]}")
        
        # Call LLM directly for simple response
        response = await _call_llm(
            provider=provider,
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key
        )
        
        return {
            "success": True,
            "response": response,
            "provider": provider,
            "model": model,
            "task": task,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"AI Agent tool error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "provider": parameters.get("llm_provider", "unknown"),
            "model": parameters.get("model", "unknown")
        }


# Register the tool with Tool Registry
from backend.core.tools.registry import ToolRegistry
from backend.core.tools.base import ToolConfig, ParamConfig, OutputConfig

ai_agent_config = ToolConfig(
    id="ai_agent",
    name="AI Agent",
    description="Autonomous AI agent with LLM, memory, and tool use capabilities",
    category="AI",
    params={
        "task": ParamConfig(
            type="text",
            required=True,
            description="Task or question for the AI agent",
            display_name="Task"
        ),
        "llm_provider": ParamConfig(
            type="select",
            required=False,  # Has default value
            description="LLM provider to use",
            display_name="LLM Provider",
            default="ollama",
            options=[
                {"label": "Ollama (Local)", "value": "ollama"},
                {"label": "OpenAI", "value": "openai"},
                {"label": "Anthropic Claude", "value": "anthropic"}
            ]
        ),
        "model": ParamConfig(
            type="text",
            required=False,  # Has default value
            description="Model name",
            display_name="Model",
            default="llama3.1:8b"
        ),
        "chat_input": ParamConfig(
            type="chat",
            required=False,
            description="Interactive chat input for the agent",
            display_name="Chat Input"
        ),
        "memory_type": ParamConfig(
            type="select",
            required=False,  # Has default value
            description="Memory duration type",
            display_name="Memory Type",
            default="short_term",
            options=[
                {"label": "Very Short Term (1 message)", "value": "very_short_term"},
                {"label": "Short Term (5 messages)", "value": "short_term"},
                {"label": "Medium Term (20 messages)", "value": "medium_term"},
                {"label": "Long Term (100+ messages)", "value": "long_term"}
            ]
        ),
        "enable_web_search": ParamConfig(
            type="boolean",
            required=False,
            description="Enable web search capability",
            display_name="Enable Web Search",
            default=True
        ),
        "enable_vector_search": ParamConfig(
            type="boolean",
            required=False,
            description="Enable knowledge base search",
            display_name="Enable Vector Search",
            default=True
        ),
        "knowledgebase_id": ParamConfig(
            type="text",
            required=False,
            description="Knowledge base ID for vector search",
            display_name="Knowledge Base ID"
        ),
        "max_iterations": ParamConfig(
            type="number",
            required=False,
            description="Maximum reasoning iterations",
            display_name="Max Iterations",
            default=10
        ),
        "temperature": ParamConfig(
            type="number",
            required=False,
            description="Sampling temperature (0-1)",
            display_name="Temperature",
            default=0.7
        ),
        "system_prompt": ParamConfig(
            type="text",
            required=False,
            description="Custom system prompt",
            display_name="System Prompt"
        ),
        "max_tokens": ParamConfig(
            type="number",
            required=False,
            description="Maximum tokens to generate",
            display_name="Max Tokens",
            default=2000
        ),
        "conversation_id": ParamConfig(
            type="text",
            required=False,
            description="Conversation ID for memory persistence",
            display_name="Conversation ID"
        )
    },
    outputs={
        "answer": OutputConfig(
            type="text",
            description="Agent's final answer"
        ),
        "reasoning_trace": OutputConfig(
            type="array",
            description="Agent's reasoning steps"
        ),
        "tool_calls": OutputConfig(
            type="array",
            description="Tools used by the agent"
        ),
        "iterations": OutputConfig(
            type="number",
            description="Number of reasoning iterations"
        ),
        "status": OutputConfig(
            type="text",
            description="Execution status"
        )
    },
    icon="brain",
    bg_color="#8B5CF6",
    docs_link="https://docs.example.com/ai-agent"
)

# Register with custom executor
ToolRegistry.register_tool_config(ai_agent_config)

logger.info("Registered AI Agent tool with n8n-level capabilities")
