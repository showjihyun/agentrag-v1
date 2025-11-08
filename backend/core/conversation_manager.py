"""
Conversation Manager for multi-turn dialogue support.

Manages conversation history and context:
- Conversation history compression
- Context-aware query reformulation
- Relevant history selection
- Token budget management for history
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Single conversation turn"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class ConversationContext:
    """Conversation context for LLM"""
    messages: List[Dict[str, str]]
    summary: Optional[str]
    estimated_tokens: int
    turns_included: int


class ConversationManager:
    """
    Manages multi-turn conversations with token budget awareness.
    
    Features:
    - Conversation history compression
    - Relevant turn selection
    - Context summarization
    - Token budget management
    """
    
    def __init__(
        self,
        max_history_turns: int = 5,
        max_tokens_per_turn: int = 200,
        enable_summarization: bool = True
    ):
        """
        Initialize ConversationManager.
        
        Args:
            max_history_turns: Maximum conversation turns to include
            max_tokens_per_turn: Maximum tokens per turn
            enable_summarization: Enable conversation summarization
        """
        self.max_history_turns = max_history_turns
        self.max_tokens_per_turn = max_tokens_per_turn
        self.enable_summarization = enable_summarization
        
        logger.info(
            f"ConversationManager initialized: "
            f"max_turns={max_history_turns}, "
            f"max_tokens_per_turn={max_tokens_per_turn}"
        )
    
    def compress_turn(
        self,
        content: str,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Compress a conversation turn to fit token budget.
        
        Args:
            content: Turn content
            max_tokens: Maximum tokens (uses default if None)
            
        Returns:
            Compressed content
        """
        max_tokens = max_tokens or self.max_tokens_per_turn
        max_chars = max_tokens * 4  # Approximate
        
        if len(content) <= max_chars:
            return content
        
        # Truncate with ellipsis
        return content[:max_chars] + "..."
    
    def select_relevant_turns(
        self,
        history: List[ConversationTurn],
        current_query: str,
        max_turns: Optional[int] = None
    ) -> List[ConversationTurn]:
        """
        Select most relevant conversation turns for current query.
        
        Uses embedding-based relevance scoring when available, falls back to recency.
        
        Args:
            history: Full conversation history
            current_query: Current user query
            max_turns: Maximum turns to select
            
        Returns:
            Selected relevant turns
        """
        max_turns = max_turns or self.max_history_turns
        
        if not history:
            return []
        
        # Try embedding-based relevance selection
        try:
            from backend.services.embedding import EmbeddingService
            embedding_service = EmbeddingService()
            
            # Embed current query
            query_embedding = embedding_service.embed_text(current_query)
            
            # Score each turn by relevance
            scored_turns = []
            for turn in history:
                if turn.role == "user":  # Only score user queries
                    turn_embedding = embedding_service.embed_text(turn.content)
                    # Cosine similarity
                    import numpy as np
                    similarity = np.dot(query_embedding, turn_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(turn_embedding)
                    )
                    scored_turns.append((similarity, turn))
            
            # Sort by relevance and take top turns
            scored_turns.sort(key=lambda x: x[0], reverse=True)
            relevant_user_turns = [turn for _, turn in scored_turns[:max_turns]]
            
            # Include corresponding assistant responses
            selected = []
            for user_turn in relevant_user_turns:
                user_idx = history.index(user_turn)
                selected.append(user_turn)
                # Add assistant response if exists
                if user_idx + 1 < len(history) and history[user_idx + 1].role == "assistant":
                    selected.append(history[user_idx + 1])
            
            # Sort by original order
            selected.sort(key=lambda t: history.index(t))
            
            logger.debug(f"Selected {len(selected)} turns using embedding-based relevance")
            return selected
            
        except Exception as e:
            logger.debug(f"Embedding-based selection failed, using recency: {e}")
            # Fallback to recency-based selection
            pass
        
        # Recency-based selection (fallback)
        recent_turns = history[-max_turns * 2:]  # Get recent turns (user + assistant pairs)
        
        # Ensure we have complete pairs (user + assistant)
        selected = []
        for i in range(len(recent_turns) - 1, -1, -2):
            if len(selected) >= max_turns * 2:
                break
            
            # Add assistant response
            if i >= 0 and recent_turns[i].role == "assistant":
                selected.insert(0, recent_turns[i])
            
            # Add user query
            if i - 1 >= 0 and recent_turns[i - 1].role == "user":
                selected.insert(0, recent_turns[i - 1])
        
        logger.debug(
            f"Selected {len(selected)} turns from {len(history)} total "
            f"(max_turns={max_turns})"
        )
        
        return selected
    
    def build_conversation_context(
        self,
        history: List[ConversationTurn],
        current_query: str,
        token_budget: int = 1000
    ) -> ConversationContext:
        """
        Build conversation context for LLM with token budget.
        
        Args:
            history: Conversation history
            current_query: Current user query
            token_budget: Token budget for history
            
        Returns:
            ConversationContext with formatted messages
        """
        # Select relevant turns
        relevant_turns = self.select_relevant_turns(
            history=history,
            current_query=current_query
        )
        
        # Build messages list
        messages = []
        total_tokens = 0
        turns_included = 0
        
        for turn in relevant_turns:
            # Compress turn content
            compressed_content = self.compress_turn(
                content=turn.content,
                max_tokens=self.max_tokens_per_turn
            )
            
            # Estimate tokens
            turn_tokens = len(compressed_content) // 4
            
            # Check budget
            if total_tokens + turn_tokens > token_budget:
                logger.debug(
                    f"Token budget exceeded, stopping at {turns_included} turns"
                )
                break
            
            # Add message
            messages.append({
                "role": turn.role,
                "content": compressed_content
            })
            
            total_tokens += turn_tokens
            turns_included += 1
        
        # Generate summary if enabled and history is long
        summary = None
        if self.enable_summarization and len(history) > self.max_history_turns * 2:
            summary = self._generate_summary(relevant_turns)
        
        context = ConversationContext(
            messages=messages,
            summary=summary,
            estimated_tokens=total_tokens,
            turns_included=turns_included
        )
        
        logger.debug(
            f"Built conversation context: {turns_included} turns, "
            f"~{total_tokens} tokens"
        )
        
        return context
    
    def _generate_summary(
        self,
        turns: List[ConversationTurn]
    ) -> str:
        """
        Generate summary of conversation turns using LLM.
        
        Args:
            turns: Conversation turns to summarize
            
        Returns:
            Summary text
        """
        if not turns:
            return ""
        
        # Try LLM-based summarization
        try:
            from backend.services.llm_manager import LLMManager
            
            # Format conversation for summarization
            conversation_text = "\n".join([
                f"{turn.role.capitalize()}: {turn.content[:200]}"
                for turn in turns[-10:]  # Last 10 turns
            ])
            
            llm_manager = LLMManager()
            summary_prompt = f"""Summarize the following conversation in 1-2 sentences, focusing on key topics and questions:

{conversation_text}

Summary:"""
            
            summary = llm_manager.generate(
                prompt=summary_prompt,
                max_tokens=100,
                temperature=0.3
            )
            
            logger.debug(f"Generated LLM-based summary: {summary[:100]}...")
            return summary.strip()
            
        except Exception as e:
            logger.debug(f"LLM summarization failed, using simple summary: {e}")
            # Fallback to simple summary
            pass
        
        # Simple summary: extract key topics (fallback)
        user_queries = [
            turn.content[:100] for turn in turns 
            if turn.role == "user"
        ]
        
        if not user_queries:
            return ""
        
        summary = f"Previous topics discussed: {', '.join(user_queries[:3])}"
        
        return summary
    
    def format_with_history(
        self,
        current_query: str,
        history: List[ConversationTurn],
        system_prompt: str,
        token_budget: int = 1000
    ) -> List[Dict[str, str]]:
        """
        Format messages with conversation history for LLM.
        
        Args:
            current_query: Current user query
            history: Conversation history
            system_prompt: System prompt
            token_budget: Token budget for history
            
        Returns:
            Formatted messages list
        """
        # Build conversation context
        context = self.build_conversation_context(
            history=history,
            current_query=current_query,
            token_budget=token_budget
        )
        
        # Build messages
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add summary if available
        if context.summary:
            messages.append({
                "role": "system",
                "content": f"Conversation summary: {context.summary}"
            })
        
        # Add conversation history
        messages.extend(context.messages)
        
        # Add current query
        messages.append({
            "role": "user",
            "content": current_query
        })
        
        logger.debug(
            f"Formatted {len(messages)} messages "
            f"(history={context.turns_included} turns)"
        )
        
        return messages
    
    def extract_context_from_history(
        self,
        history: List[ConversationTurn],
        max_chars: int = 500
    ) -> str:
        """
        Extract context string from conversation history.
        
        Args:
            history: Conversation history
            max_chars: Maximum characters
            
        Returns:
            Context string
        """
        if not history:
            return ""
        
        # Get recent turns
        recent = history[-4:]  # Last 2 exchanges
        
        context_parts = []
        total_chars = 0
        
        for turn in recent:
            # Format turn
            turn_text = f"{turn.role.capitalize()}: {turn.content}"
            
            # Check length
            if total_chars + len(turn_text) > max_chars:
                # Truncate
                remaining = max_chars - total_chars
                if remaining > 50:
                    turn_text = turn_text[:remaining] + "..."
                    context_parts.append(turn_text)
                break
            
            context_parts.append(turn_text)
            total_chars += len(turn_text)
        
        return "\n".join(context_parts)


# Singleton instance
_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager(
    max_history_turns: int = 5,
    max_tokens_per_turn: int = 200
) -> ConversationManager:
    """
    Get or create global ConversationManager instance.
    
    Args:
        max_history_turns: Maximum history turns
        max_tokens_per_turn: Maximum tokens per turn
        
    Returns:
        ConversationManager instance
    """
    global _conversation_manager
    
    if _conversation_manager is None:
        _conversation_manager = ConversationManager(
            max_history_turns=max_history_turns,
            max_tokens_per_turn=max_tokens_per_turn
        )
    
    return _conversation_manager
