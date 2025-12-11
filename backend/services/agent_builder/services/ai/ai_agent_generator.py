"""
AI Agent Generator - Automatically generates agents from natural language.

Uses LLM to analyze requirements and create optimized agent configurations.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AIAgentGenerator:
    """
    Automatically generates agents from natural language descriptions.
    
    Features:
    - Requirement analysis
    - Automatic agent design
    - Prompt generation
    - Tool selection
    - Configuration optimization
    """
    
    def __init__(
        self,
        db: Session,
        llm_service: Optional[Any] = None
    ):
        """
        Initialize AI agent generator.
        
        Args:
            db: Database session
            llm_service: LLM service for generation
        """
        self.db = db
        self.llm_service = llm_service
        
        logger.info("AIAgentGenerator initialized")
    
    async def generate_agent(
        self,
        description: str,
        examples: Optional[List[str]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate agent from natural language description.
        
        Args:
            description: Natural language description of agent
            examples: Optional example inputs/outputs
            constraints: Optional constraints (max_tokens, tools, etc.)
            
        Returns:
            Generated agent configuration
        """
        logger.info(f"Generating agent from description: {description[:100]}...")
        
        # Step 1: Analyze requirements
        requirements = await self._analyze_requirements(description, examples)
        
        # Step 2: Design agent architecture
        design = await self._design_agent(requirements, constraints)
        
        # Step 3: Generate prompt template
        prompt = await self._generate_prompt(requirements, design, examples)
        
        # Step 4: Select tools
        tools = await self._select_tools(requirements, design)
        
        # Step 5: Optimize configuration
        config = await self._optimize_configuration(design, tools, constraints)
        
        # Step 6: Create agent specification
        agent_spec = {
            "name": design.get("name", "Generated Agent"),
            "description": design.get("description", description[:200]),
            "agent_type": design.get("type", "custom"),
            "llm_provider": config.get("llm_provider", "ollama"),
            "llm_model": config.get("llm_model", "llama2"),
            "prompt_template": prompt,
            "tools": tools,
            "configuration": config,
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "requirements": requirements,
                "design": design
            }
        }
        
        logger.info(f"Generated agent: {agent_spec['name']}")
        
        return agent_spec
    
    async def _analyze_requirements(
        self,
        description: str,
        examples: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Analyze requirements from description."""
        analysis_prompt = f"""Analyze this agent requirement and extract key information:

Description: {description}

Examples: {json.dumps(examples) if examples else "None"}

Extract:
1. Primary purpose/goal
2. Required capabilities
3. Input/output types
4. Complexity level (simple/medium/complex)
5. Domain/category
6. Special requirements

Respond in JSON format."""
        
        # Use LLM to analyze
        if self.llm_service:
            response = await self.llm_service.generate(analysis_prompt)
            try:
                return json.loads(response)
            except:
                pass
        
        # Fallback: Simple analysis
        return {
            "purpose": description[:100],
            "capabilities": ["general_purpose"],
            "input_type": "text",
            "output_type": "text",
            "complexity": "medium",
            "domain": "general",
            "requirements": []
        }
    
    async def _design_agent(
        self,
        requirements: Dict[str, Any],
        constraints: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Design agent architecture based on requirements."""
        design_prompt = f"""Design an agent architecture for these requirements:

Requirements: {json.dumps(requirements)}
Constraints: {json.dumps(constraints) if constraints else "None"}

Design:
1. Agent name
2. Agent type (custom/template)
3. Architecture pattern (single/multi-step/workflow)
4. Reasoning approach (direct/chain-of-thought/tree-of-thought)
5. Memory requirements
6. Tool requirements

Respond in JSON format."""
        
        if self.llm_service:
            response = await self.llm_service.generate(design_prompt)
            try:
                return json.loads(response)
            except:
                pass
        
        # Fallback: Simple design
        complexity = requirements.get("complexity", "medium")
        
        return {
            "name": f"{requirements.get('domain', 'General')} Agent",
            "description": requirements.get("purpose", ""),
            "type": "custom",
            "architecture": "single" if complexity == "simple" else "multi-step",
            "reasoning": "chain-of-thought" if complexity == "complex" else "direct",
            "memory": complexity != "simple",
            "tools_needed": True
        }
    
    async def _generate_prompt(
        self,
        requirements: Dict[str, Any],
        design: Dict[str, Any],
        examples: Optional[List[str]]
    ) -> str:
        """Generate optimized prompt template."""
        generation_prompt = f"""Generate an optimized prompt template for this agent:

Requirements: {json.dumps(requirements)}
Design: {json.dumps(design)}
Examples: {json.dumps(examples) if examples else "None"}

Create a prompt that:
1. Clearly defines the agent's role
2. Specifies expected behavior
3. Includes reasoning instructions if needed
4. Handles edge cases
5. Uses best practices

Return only the prompt template with {{variable}} placeholders."""
        
        if self.llm_service:
            response = await self.llm_service.generate(generation_prompt)
            return response.strip()
        
        # Fallback: Template-based prompt
        purpose = requirements.get("purpose", "assist users")
        reasoning = design.get("reasoning", "direct")
        
        if reasoning == "chain-of-thought":
            return f"""You are an AI agent designed to {purpose}.

For each query:
1. Analyze the question carefully
2. Break down the problem into steps
3. Think through each step
4. Provide a clear, comprehensive answer

Query: {{query}}

Let's think step by step:"""
        else:
            return f"""You are an AI agent designed to {purpose}.

Provide clear, accurate, and helpful responses.

Query: {{query}}

Response:"""
    
    async def _select_tools(
        self,
        requirements: Dict[str, Any],
        design: Dict[str, Any]
    ) -> List[str]:
        """Select appropriate tools for the agent."""
        if not design.get("tools_needed"):
            return []
        
        # Map capabilities to tools
        capability_tool_map = {
            "search": ["vector_search", "web_search"],
            "data_analysis": ["local_data"],
            "calculation": ["calculator"],
            "code_execution": ["python_executor"],
            "api_calls": ["http_api"],
            "file_operations": ["file_operations"]
        }
        
        capabilities = requirements.get("capabilities", [])
        tools = set()
        
        for capability in capabilities:
            if capability in capability_tool_map:
                tools.update(capability_tool_map[capability])
        
        # Default tools for general purpose
        if not tools:
            tools = {"vector_search"}
        
        return list(tools)
    
    async def _optimize_configuration(
        self,
        design: Dict[str, Any],
        tools: List[str],
        constraints: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Optimize agent configuration."""
        config = {
            "llm_provider": "ollama",
            "llm_model": "llama2",
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.9,
            "tools": tools,
            "memory_enabled": design.get("memory", False),
            "streaming": True
        }
        
        # Apply constraints
        if constraints:
            if "max_tokens" in constraints:
                config["max_tokens"] = constraints["max_tokens"]
            if "temperature" in constraints:
                config["temperature"] = constraints["temperature"]
            if "llm_model" in constraints:
                config["llm_model"] = constraints["llm_model"]
        
        # Optimize based on complexity
        complexity = design.get("architecture", "single")
        if complexity == "complex":
            config["temperature"] = 0.3  # More deterministic
            config["max_tokens"] = 4000  # More space for reasoning
        
        return config
    
    async def generate_from_examples(
        self,
        examples: List[Dict[str, str]],
        agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate agent from input/output examples.
        
        Args:
            examples: List of {"input": "...", "output": "..."} examples
            agent_name: Optional agent name
            
        Returns:
            Generated agent configuration
        """
        logger.info(f"Generating agent from {len(examples)} examples")
        
        # Analyze examples to infer requirements
        analysis_prompt = f"""Analyze these input/output examples and infer the agent's purpose:

Examples:
{json.dumps(examples, indent=2)}

Infer:
1. What task is this agent performing?
2. What patterns do you see?
3. What capabilities are needed?
4. What is the input/output format?

Respond in JSON format."""
        
        if self.llm_service:
            response = await self.llm_service.generate(analysis_prompt)
            try:
                analysis = json.loads(response)
                description = analysis.get("task", "Agent from examples")
            except:
                description = "Agent generated from examples"
        else:
            description = "Agent generated from examples"
        
        # Generate agent with examples
        return await self.generate_agent(
            description=description,
            examples=[f"Input: {ex['input']}\nOutput: {ex['output']}" for ex in examples]
        )
    
    async def refine_agent(
        self,
        agent_id: str,
        feedback: List[Dict[str, Any]],
        performance_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Refine existing agent based on feedback and performance.
        
        Args:
            agent_id: Agent ID to refine
            feedback: User feedback
            performance_metrics: Performance metrics
            
        Returns:
            Refined agent configuration
        """
        logger.info(f"Refining agent {agent_id}")
        
        refinement_prompt = f"""Refine this agent based on feedback and performance:

Feedback: {json.dumps(feedback)}
Performance: {json.dumps(performance_metrics)}

Suggest improvements to:
1. Prompt template
2. Tool selection
3. Configuration parameters
4. Reasoning approach

Respond in JSON format with specific changes."""
        
        if self.llm_service:
            response = await self.llm_service.generate(refinement_prompt)
            try:
                improvements = json.loads(response)
                return improvements
            except:
                pass
        
        # Fallback: Basic improvements
        improvements = {
            "prompt_changes": [],
            "tool_changes": [],
            "config_changes": {}
        }
        
        # Analyze feedback
        negative_feedback = [f for f in feedback if f.get("rating", 5) < 3]
        if negative_feedback:
            improvements["prompt_changes"].append(
                "Add more detailed instructions based on negative feedback"
            )
        
        # Analyze performance
        if performance_metrics.get("avg_duration_ms", 0) > 5000:
            improvements["config_changes"]["max_tokens"] = 1000
            improvements["config_changes"]["temperature"] = 0.5
        
        return improvements


# Example usage
EXAMPLE_DESCRIPTIONS = [
    "Create an agent that analyzes customer feedback and extracts sentiment, key themes, and actionable insights",
    "Build an agent that helps developers debug code by analyzing error messages and suggesting fixes",
    "Design an agent that summarizes long documents and answers questions about them",
]

EXAMPLE_EXAMPLES = [
    {
        "input": "The product is great but shipping was slow",
        "output": "Sentiment: Positive (product), Negative (shipping)\nThemes: Product quality, Delivery speed\nInsight: Improve shipping logistics"
    },
    {
        "input": "TypeError: 'NoneType' object is not subscriptable",
        "output": "Issue: Attempting to access an index on a None value\nSolution: Add null check before accessing\nExample: if obj is not None: obj[0]"
    }
]
