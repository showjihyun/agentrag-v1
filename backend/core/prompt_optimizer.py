"""
Prompt Optimizer for LLM calls.

Optimizes prompts to reduce token usage while maintaining quality:
- Concise system prompts
- Dynamic max_tokens based on query complexity
- Conversation context compression
- Template optimization
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OptimizedPrompt:
    """Result of prompt optimization."""

    system_prompt: str
    user_prompt: str
    max_tokens: int
    temperature: float
    estimated_input_tokens: int
    estimated_output_tokens: int
    optimization_applied: List[str]


class PromptOptimizer:
    """
    Optimizes prompts for LLM calls to reduce token usage.

    Features:
    - Concise prompt templates
    - Dynamic token budgets
    - Context compression
    - Query-aware optimization
    """

    # Optimized system prompts (much shorter than originals)
    SYSTEM_PROMPTS = {
        "fast": "Answer concisely in 2-3 sentences.",
        "balanced": "Provide a clear, focused answer.",
        "deep": "Give a comprehensive answer with details.",
        "synthesis": "Synthesize information from documents.",
    }

    # Token budgets by query complexity
    TOKEN_BUDGETS = {
        "simple": {"input": 500, "output": 100},
        "medium": {"input": 1000, "output": 200},
        "complex": {"input": 2000, "output": 400},
    }

    def __init__(
        self, chars_per_token: float = 4.0, enable_context_compression: bool = True
    ):
        """
        Initialize PromptOptimizer.

        Args:
            chars_per_token: Approximate characters per token
            enable_context_compression: Enable conversation context compression
        """
        self.chars_per_token = chars_per_token
        self.enable_context_compression = enable_context_compression

        logger.info(
            f"PromptOptimizer initialized: "
            f"context_compression={enable_context_compression}"
        )

    def get_optimized_system_prompt(
        self, mode: str = "balanced", custom_instructions: Optional[str] = None
    ) -> str:
        """
        Get optimized system prompt.

        Args:
            mode: Prompt mode (fast, balanced, deep, synthesis)
            custom_instructions: Optional custom instructions to append

        Returns:
            Optimized system prompt
        """
        base_prompt = self.SYSTEM_PROMPTS.get(mode, self.SYSTEM_PROMPTS["balanced"])

        if custom_instructions:
            # Keep custom instructions concise
            return f"{base_prompt} {custom_instructions}"

        return base_prompt

    def compress_conversation_context(
        self,
        messages: List[Dict[str, str]],
        max_messages: int = 3,
        max_chars_per_message: int = 200,
    ) -> str:
        """
        Compress conversation context to essential information.

        Args:
            messages: List of conversation messages
            max_messages: Maximum messages to include
            max_chars_per_message: Maximum characters per message

        Returns:
            Compressed context string
        """
        if not messages:
            return ""

        # Take only recent messages
        recent_messages = messages[-max_messages:]

        # Compress each message
        compressed = []
        for msg in recent_messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            # Truncate long messages
            if len(content) > max_chars_per_message:
                content = content[:max_chars_per_message] + "..."

            # Simple format without labels
            compressed.append(f"{role}: {content}")

        return "\n".join(compressed)

    def calculate_dynamic_max_tokens(
        self, query: str, complexity: str = "medium"
    ) -> int:
        """
        Calculate dynamic max_tokens based on query complexity.

        Args:
            query: User query
            complexity: Query complexity (simple, medium, complex)

        Returns:
            Optimal max_tokens
        """
        budget = self.TOKEN_BUDGETS.get(complexity, self.TOKEN_BUDGETS["medium"])
        base_max_tokens = budget["output"]

        # Adjust based on query length
        query_length = len(query)

        if query_length < 50:
            # Short query: likely needs short answer
            adjustment = 0.8
        elif query_length > 200:
            # Long query: might need longer answer
            adjustment = 1.3
        else:
            # Medium query
            adjustment = 1.0

        max_tokens = int(base_max_tokens * adjustment)

        # Ensure minimum and maximum bounds
        max_tokens = max(50, min(max_tokens, 500))

        return max_tokens

    def optimize_user_prompt(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        include_instructions: bool = False,
    ) -> str:
        """
        Optimize user prompt for minimal tokens.

        Args:
            query: User query
            context: Document context
            conversation_history: Optional conversation history
            include_instructions: Whether to include answering instructions

        Returns:
            Optimized user prompt
        """
        parts = []

        # Add compressed conversation history if available
        if conversation_history and self.enable_context_compression:
            compressed_history = self.compress_conversation_context(
                conversation_history,
                max_messages=2,
                max_chars_per_message=150,  # Only 2 most recent
            )
            if compressed_history:
                parts.append(f"Context:\n{compressed_history}\n")

        # Add document context (already optimized by ContextOptimizer)
        if context:
            parts.append(f"Documents:\n{context}\n")

        # Add query
        parts.append(f"Q: {query}")

        # Optional: Add brief instruction (only if needed)
        if include_instructions:
            parts.append("\nA:")  # Minimal prompt for answer

        return "\n".join(parts)

    def optimize_prompt(
        self,
        query: str,
        context: str,
        mode: str = "balanced",
        complexity: str = "medium",
        conversation_history: Optional[List[Dict[str, str]]] = None,
        custom_system_prompt: Optional[str] = None,
    ) -> OptimizedPrompt:
        """
        Optimize complete prompt (system + user).

        Args:
            query: User query
            context: Document context
            mode: Prompt mode (fast, balanced, deep)
            complexity: Query complexity (simple, medium, complex)
            conversation_history: Optional conversation history
            custom_system_prompt: Optional custom system prompt

        Returns:
            OptimizedPrompt with all optimizations applied
        """
        optimizations_applied = []

        # Optimize system prompt
        if custom_system_prompt:
            system_prompt = custom_system_prompt
        else:
            system_prompt = self.get_optimized_system_prompt(mode)
            optimizations_applied.append("concise_system_prompt")

        # Optimize user prompt
        user_prompt = self.optimize_user_prompt(
            query=query,
            context=context,
            conversation_history=conversation_history,
            include_instructions=(mode == "fast"),
        )

        if conversation_history and self.enable_context_compression:
            optimizations_applied.append("compressed_conversation")

        # Calculate dynamic max_tokens
        max_tokens = self.calculate_dynamic_max_tokens(query, complexity)
        optimizations_applied.append("dynamic_max_tokens")

        # Optimize temperature based on mode
        temperature_map = {
            "fast": 0.3,  # Low for consistency and speed
            "balanced": 0.5,  # Moderate
            "deep": 0.7,  # Higher for creativity
        }
        temperature = temperature_map.get(mode, 0.5)

        # Estimate tokens
        total_prompt = system_prompt + user_prompt
        estimated_input_tokens = int(len(total_prompt) / self.chars_per_token)
        estimated_output_tokens = max_tokens

        result = OptimizedPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
            optimization_applied=optimizations_applied,
        )

        logger.debug(
            f"Prompt optimized: ~{estimated_input_tokens} input tokens, "
            f"max {max_tokens} output tokens "
            f"(optimizations: {', '.join(optimizations_applied)})"
        )

        return result

    def create_minimal_synthesis_prompt(
        self, query: str, context: str
    ) -> Tuple[str, str, int]:
        """
        Create minimal synthesis prompt (most aggressive optimization).

        Args:
            query: User query
            context: Document context

        Returns:
            Tuple of (system_prompt, user_prompt, max_tokens)
        """
        # Ultra-concise system prompt
        system_prompt = "Answer based on documents."

        # Minimal user prompt
        user_prompt = f"{context}\n\nQ: {query}\nA:"

        # Conservative max_tokens
        max_tokens = 150

        return system_prompt, user_prompt, max_tokens


# Singleton instance
_prompt_optimizer: Optional[PromptOptimizer] = None


def get_prompt_optimizer(enable_context_compression: bool = True) -> PromptOptimizer:
    """
    Get or create global PromptOptimizer instance.

    Args:
        enable_context_compression: Enable conversation context compression

    Returns:
        PromptOptimizer instance
    """
    global _prompt_optimizer

    if _prompt_optimizer is None:
        _prompt_optimizer = PromptOptimizer(
            enable_context_compression=enable_context_compression
        )

    return _prompt_optimizer
