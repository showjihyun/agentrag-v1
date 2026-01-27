"""
Reflection Block - Agentic Design Pattern

Implements the Reflection pattern where an agent evaluates its own outputs
and iteratively improves them based on self-critique.

Key Features:
- Self-evaluation of outputs
- Iterative refinement (configurable max iterations)
- Quality scoring and improvement tracking
- Memory of reflections for learning
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from backend.services.llm_manager import LLMManager
from backend.config import settings

logger = logging.getLogger(__name__)


class ReflectionBlock:
    """
    Reflection Block for iterative self-improvement.
    
    The agent generates an output, critiques it, and refines it
    until quality threshold is met or max iterations reached.
    """
    
    def __init__(
        self,
        llm_manager: LLMManager,
        max_iterations: int = 3,
        quality_threshold: float = 0.8,
        reflection_prompt: Optional[str] = None,
        improvement_prompt: Optional[str] = None,
    ):
        """
        Initialize Reflection Block.
        
        Args:
            llm_manager: LLM manager for generating and evaluating outputs
            max_iterations: Maximum refinement iterations
            quality_threshold: Quality score threshold (0-1) to stop iteration
            reflection_prompt: Custom prompt for self-critique
            improvement_prompt: Custom prompt for improvement
        """
        self.llm_manager = llm_manager
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        self.reflection_prompt = reflection_prompt or self._default_reflection_prompt()
        self.improvement_prompt = improvement_prompt or self._default_improvement_prompt()
        
        self.reflection_history: List[Dict[str, Any]] = []
    
    def _default_reflection_prompt(self) -> str:
        """Default prompt for self-critique."""
        return """You are a critical evaluator. Analyze the following output and provide:

1. Quality Score (0-1): Overall quality assessment
2. Strengths: What works well
3. Weaknesses: What needs improvement
4. Specific Improvements: Concrete suggestions for enhancement

Output to evaluate:
{output}

Context:
{context}

Provide your evaluation in JSON format:
{{
    "quality_score": <float 0-1>,
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "improvements": ["improvement1", "improvement2"]
}}"""
    
    def _default_improvement_prompt(self) -> str:
        """Default prompt for improvement."""
        return """Based on the critique below, improve the original output.

Original Output:
{output}

Critique:
{critique}

Context:
{context}

Generate an improved version that addresses all weaknesses and incorporates the suggested improvements.
Maintain the strengths while fixing the issues."""
    
    async def execute(
        self,
        initial_output: str,
        context: Dict[str, Any],
        task_description: str = "",
    ) -> Dict[str, Any]:
        """
        Execute reflection loop with iterative improvement.
        
        Args:
            initial_output: Initial output to refine
            context: Context information for evaluation
            task_description: Description of the task
            
        Returns:
            Dict containing:
                - final_output: Refined output
                - iterations: Number of iterations performed
                - quality_score: Final quality score
                - reflection_history: History of all reflections
                - improvement_made: Whether improvement occurred
        """
        current_output = initial_output
        iteration = 0
        best_output = initial_output
        best_score = 0.0
        
        logger.info(f"Starting reflection loop (max_iterations={self.max_iterations})")
        
        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"Reflection iteration {iteration}/{self.max_iterations}")
            
            # Step 1: Critique current output
            critique = await self._critique_output(
                output=current_output,
                context=context,
                task_description=task_description,
            )
            
            quality_score = critique.get("quality_score", 0.0)
            logger.info(f"Quality score: {quality_score:.2f}")
            
            # Track best output
            if quality_score > best_score:
                best_score = quality_score
                best_output = current_output
            
            # Record reflection
            reflection_record = {
                "iteration": iteration,
                "output": current_output,
                "critique": critique,
                "quality_score": quality_score,
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.reflection_history.append(reflection_record)
            
            # Check if quality threshold met
            if quality_score >= self.quality_threshold:
                logger.info(f"Quality threshold met: {quality_score:.2f} >= {self.quality_threshold}")
                break
            
            # Step 2: Generate improved output
            if iteration < self.max_iterations:
                improved_output = await self._improve_output(
                    output=current_output,
                    critique=critique,
                    context=context,
                    task_description=task_description,
                )
                current_output = improved_output
        
        improvement_made = best_score > 0.0 and len(self.reflection_history) > 1
        
        result = {
            "final_output": best_output,
            "iterations": iteration,
            "quality_score": best_score,
            "reflection_history": self.reflection_history,
            "improvement_made": improvement_made,
            "initial_score": self.reflection_history[0]["quality_score"] if self.reflection_history else 0.0,
            "final_score": best_score,
            "score_improvement": best_score - (self.reflection_history[0]["quality_score"] if self.reflection_history else 0.0),
        }
        
        logger.info(
            f"Reflection complete: {iteration} iterations, "
            f"score improved from {result['initial_score']:.2f} to {result['final_score']:.2f}"
        )
        
        return result
    
    async def _critique_output(
        self,
        output: str,
        context: Dict[str, Any],
        task_description: str,
    ) -> Dict[str, Any]:
        """
        Generate critique of output.
        
        Returns:
            Dict with quality_score, strengths, weaknesses, improvements
        """
        try:
            prompt = self.reflection_prompt.format(
                output=output,
                context=self._format_context(context, task_description),
            )
            
            response = await self.llm_manager.generate(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for consistent evaluation
            )
            
            # Parse JSON response
            import json
            critique = json.loads(response)
            
            # Validate structure
            if "quality_score" not in critique:
                critique["quality_score"] = 0.5
            if "strengths" not in critique:
                critique["strengths"] = []
            if "weaknesses" not in critique:
                critique["weaknesses"] = []
            if "improvements" not in critique:
                critique["improvements"] = []
            
            return critique
            
        except Exception as e:
            logger.error(f"Error in critique generation: {e}", exc_info=True)
            return {
                "quality_score": 0.5,
                "strengths": [],
                "weaknesses": [f"Error in evaluation: {str(e)}"],
                "improvements": ["Retry evaluation"],
            }
    
    async def _improve_output(
        self,
        output: str,
        critique: Dict[str, Any],
        context: Dict[str, Any],
        task_description: str,
    ) -> str:
        """
        Generate improved output based on critique.
        
        Returns:
            Improved output string
        """
        try:
            critique_text = self._format_critique(critique)
            
            prompt = self.improvement_prompt.format(
                output=output,
                critique=critique_text,
                context=self._format_context(context, task_description),
            )
            
            improved_output = await self.llm_manager.generate(
                prompt=prompt,
                temperature=0.7,  # Higher temperature for creative improvement
            )
            
            return improved_output
            
        except Exception as e:
            logger.error(f"Error in improvement generation: {e}", exc_info=True)
            return output  # Return original if improvement fails
    
    def _format_context(self, context: Dict[str, Any], task_description: str) -> str:
        """Format context for prompts."""
        context_parts = []
        
        if task_description:
            context_parts.append(f"Task: {task_description}")
        
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                context_parts.append(f"{key}: {value}")
            elif isinstance(value, (list, dict)):
                import json
                context_parts.append(f"{key}: {json.dumps(value, indent=2)}")
        
        return "\n".join(context_parts)
    
    def _format_critique(self, critique: Dict[str, Any]) -> str:
        """Format critique for improvement prompt."""
        parts = [
            f"Quality Score: {critique.get('quality_score', 0.0):.2f}",
            "",
            "Strengths:",
        ]
        
        for strength in critique.get("strengths", []):
            parts.append(f"  - {strength}")
        
        parts.append("")
        parts.append("Weaknesses:")
        for weakness in critique.get("weaknesses", []):
            parts.append(f"  - {weakness}")
        
        parts.append("")
        parts.append("Suggested Improvements:")
        for improvement in critique.get("improvements", []):
            parts.append(f"  - {improvement}")
        
        return "\n".join(parts)
    
    def get_reflection_summary(self) -> Dict[str, Any]:
        """Get summary of reflection process."""
        if not self.reflection_history:
            return {"status": "no_reflections"}
        
        scores = [r["quality_score"] for r in self.reflection_history]
        
        return {
            "total_iterations": len(self.reflection_history),
            "initial_score": scores[0],
            "final_score": scores[-1],
            "max_score": max(scores),
            "min_score": min(scores),
            "average_score": sum(scores) / len(scores),
            "improvement": scores[-1] - scores[0],
            "converged": scores[-1] >= self.quality_threshold,
        }
    
    def clear_history(self):
        """Clear reflection history."""
        self.reflection_history = []
