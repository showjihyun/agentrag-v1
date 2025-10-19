"""
Token Budget Manager for LLM calls.

Manages token budgets to prevent overages and optimize costs:
- Token counting with tiktoken
- Budget allocation and enforcement
- Text truncation to fit budget
- Cost estimation
"""

import logging
from typing import List, Optional, Tuple
import tiktoken

logger = logging.getLogger(__name__)


class TokenBudgetManager:
    """
    Manages token budgets for LLM calls.
    
    Features:
    - Accurate token counting with tiktoken
    - Budget allocation (system, context, response)
    - Text truncation to fit budget
    - Cost estimation
    """
    
    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 4096,
        system_tokens: int = 500,
        response_tokens: int = 1000
    ):
        """
        Initialize TokenBudgetManager.
        
        Args:
            model: Model name for tiktoken encoding
            max_tokens: Maximum total tokens
            system_tokens: Reserved tokens for system prompt
            response_tokens: Reserved tokens for response
        """
        self.model = model
        self.max_tokens = max_tokens
        self.system_tokens = system_tokens
        self.response_tokens = response_tokens
        self.available_tokens = max_tokens - system_tokens - response_tokens
        
        # Initialize tiktoken encoding
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base for unknown models
            logger.warning(f"Model {model} not found, using cl100k_base encoding")
            self.encoding = tiktoken.get_encoding("cl100k_base")
        
        logger.info(
            f"TokenBudgetManager initialized: model={model}, "
            f"max_tokens={max_tokens}, available={self.available_tokens}"
        )
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count
            
        Returns:
            Number of tokens
        """
        if not text:
            return 0
        
        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.warning(f"Token counting failed: {e}, using char estimate")
            # Fallback to character-based estimate (4 chars per token)
            return len(text) // 4
    
    def truncate_to_budget(
        self,
        texts: List[str],
        budget: int,
        preserve_order: bool = True
    ) -> List[str]:
        """
        Truncate texts to fit within budget.
        
        Args:
            texts: List of texts to truncate
            budget: Token budget
            preserve_order: Whether to preserve text order
            
        Returns:
            List of texts that fit within budget
        """
        if not texts:
            return []
        
        result = []
        used = 0
        
        for text in texts:
            tokens = self.count_tokens(text)
            
            if used + tokens <= budget:
                # Text fits completely
                result.append(text)
                used += tokens
            else:
                # Partial fit
                remaining = budget - used
                if remaining > 100:  # Minimum 100 tokens
                    truncated = self._truncate_text(text, remaining)
                    result.append(truncated)
                break
        
        logger.debug(
            f"Truncated {len(texts)} texts to {len(result)} texts "
            f"({used}/{budget} tokens used)"
        )
        
        return result
    
    def _truncate_text(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to maximum tokens.
        
        Args:
            text: Text to truncate
            max_tokens: Maximum tokens
            
        Returns:
            Truncated text
        """
        if not text:
            return ""
        
        try:
            tokens = self.encoding.encode(text)
            
            if len(tokens) <= max_tokens:
                return text
            
            # Truncate tokens
            truncated_tokens = tokens[:max_tokens]
            truncated_text = self.encoding.decode(truncated_tokens)
            
            return truncated_text + "..."
            
        except Exception as e:
            logger.warning(f"Text truncation failed: {e}, using char estimate")
            # Fallback to character-based truncation
            max_chars = max_tokens * 4
            if len(text) <= max_chars:
                return text
            return text[:max_chars] + "..."
    
    def allocate_budget(
        self,
        rag_ratio: float = 0.4,
        web_ratio: float = 0.4,
        query_ratio: float = 0.2
    ) -> Tuple[int, int, int]:
        """
        Allocate available budget across components.
        
        Args:
            rag_ratio: Ratio for RAG results (default: 40%)
            web_ratio: Ratio for web results (default: 40%)
            query_ratio: Ratio for query context (default: 20%)
            
        Returns:
            Tuple of (rag_budget, web_budget, query_budget)
        """
        # Validate ratios
        total_ratio = rag_ratio + web_ratio + query_ratio
        if abs(total_ratio - 1.0) > 0.01:
            logger.warning(
                f"Budget ratios don't sum to 1.0 ({total_ratio}), normalizing"
            )
            rag_ratio /= total_ratio
            web_ratio /= total_ratio
            query_ratio /= total_ratio
        
        rag_budget = int(self.available_tokens * rag_ratio)
        web_budget = int(self.available_tokens * web_ratio)
        query_budget = int(self.available_tokens * query_ratio)
        
        logger.debug(
            f"Budget allocated: RAG={rag_budget}, Web={web_budget}, "
            f"Query={query_budget} (total={self.available_tokens})"
        )
        
        return rag_budget, web_budget, query_budget
    
    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: Optional[str] = None
    ) -> float:
        """
        Estimate cost for token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name (uses self.model if not provided)
            
        Returns:
            Estimated cost in USD
        """
        model = model or self.model
        
        # Pricing per 1M tokens (as of 2024)
        pricing = {
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
            "gpt-4": {"input": 30.00, "output": 60.00},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            "claude-3-opus": {"input": 15.00, "output": 75.00},
            "claude-3-sonnet": {"input": 3.00, "output": 15.00},
            "claude-3-haiku": {"input": 0.25, "output": 1.25},
        }
        
        # Get pricing or use default
        model_pricing = pricing.get(model, {"input": 1.00, "output": 2.00})
        
        # Calculate cost
        input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (output_tokens / 1_000_000) * model_pricing["output"]
        total_cost = input_cost + output_cost
        
        return total_cost
    
    def check_budget(
        self,
        system_prompt: str,
        user_prompt: str,
        max_output_tokens: int
    ) -> Tuple[bool, int, str]:
        """
        Check if prompts fit within budget.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            max_output_tokens: Maximum output tokens
            
        Returns:
            Tuple of (fits, total_tokens, message)
        """
        system_tokens = self.count_tokens(system_prompt)
        user_tokens = self.count_tokens(user_prompt)
        total_input = system_tokens + user_tokens
        total_tokens = total_input + max_output_tokens
        
        fits = total_tokens <= self.max_tokens
        
        if fits:
            message = (
                f"Budget OK: {total_tokens}/{self.max_tokens} tokens "
                f"(system={system_tokens}, user={user_tokens}, "
                f"output={max_output_tokens})"
            )
        else:
            overage = total_tokens - self.max_tokens
            message = (
                f"Budget exceeded by {overage} tokens! "
                f"({total_tokens}/{self.max_tokens})"
            )
        
        return fits, total_tokens, message


# Singleton instance
_token_budget_manager: Optional[TokenBudgetManager] = None


def get_token_budget_manager(
    model: str = "gpt-3.5-turbo",
    max_tokens: int = 4096
) -> TokenBudgetManager:
    """
    Get or create global TokenBudgetManager instance.
    
    Args:
        model: Model name
        max_tokens: Maximum tokens
        
    Returns:
        TokenBudgetManager instance
    """
    global _token_budget_manager
    
    if _token_budget_manager is None:
        _token_budget_manager = TokenBudgetManager(
            model=model,
            max_tokens=max_tokens
        )
    
    return _token_budget_manager
