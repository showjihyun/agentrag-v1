"""
Hierarchical Memory System for Agent Builder.

Implements multi-level memory management with automatic consolidation and retrieval.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum
import json
import hashlib
from collections import defaultdict

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class MemoryType(str, Enum):
    """Types of memory in the hierarchical system."""
    SHORT_TERM = "short_term"      # Current session/conversation
    LONG_TERM = "long_term"        # Persistent across sessions
    EPISODIC = "episodic"          # Specific events/experiences
    SEMANTIC = "semantic"          # General knowledge/facts
    WORKING = "working"            # Active processing buffer


class MemoryImportance(str, Enum):
    """Importance levels for memory consolidation."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    TRIVIAL = "trivial"


class Memory:
    """Represents a single memory item."""
    
    def __init__(
        self,
        memory_id: str,
        content: str,
        memory_type: MemoryType,
        agent_id: str,
        session_id: Optional[str] = None,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ):
        self.memory_id = memory_id
        self.content = content
        self.memory_type = memory_type
        self.agent_id = agent_id
        self.session_id = session_id
        self.importance = importance
        self.metadata = metadata or {}
        self.embedding = embedding
        
        self.created_at = datetime.now(timezone.utc)
        self.last_accessed = self.created_at
        self.access_count = 0
        self.decay_factor = 1.0  # For forgetting curve
        
        # Relationships
        self.related_memories: List[str] = []
        self.tags: List[str] = []
    
    def access(self):
        """Record memory access."""
        self.last_accessed = datetime.now(timezone.utc)
        self.access_count += 1
        # Boost decay factor on access (spaced repetition)
        self.decay_factor = min(1.0, self.decay_factor + 0.1)
    
    def decay(self, time_delta_hours: float):
        """Apply forgetting curve decay."""
        # Ebbinghaus forgetting curve: R = e^(-t/S)
        # where R is retention, t is time, S is strength
        import math
        strength = 24 * self.decay_factor  # Base strength in hours
        self.decay_factor *= math.exp(-time_delta_hours / strength)
    
    @property
    def relevance_score(self) -> float:
        """
        Calculate relevance score for retrieval.
        
        Combines recency, frequency, and importance.
        """
        # Recency score (0-1)
        hours_since_access = (datetime.now(timezone.utc) - self.last_accessed).total_seconds() / 3600
        recency_score = 1.0 / (1.0 + hours_since_access / 24)  # Decay over days
        
        # Frequency score (0-1)
        frequency_score = min(1.0, self.access_count / 10)
        
        # Importance score (0-1)
        importance_scores = {
            MemoryImportance.CRITICAL: 1.0,
            MemoryImportance.HIGH: 0.8,
            MemoryImportance.MEDIUM: 0.5,
            MemoryImportance.LOW: 0.3,
            MemoryImportance.TRIVIAL: 0.1
        }
        importance_score = importance_scores.get(self.importance, 0.5)
        
        # Combined score with weights
        return (
            0.3 * recency_score +
            0.3 * frequency_score +
            0.4 * importance_score
        ) * self.decay_factor


class HierarchicalMemory:
    """
    Hierarchical memory system with multiple memory types.
    
    Features:
    - Short-term memory (current session)
    - Long-term memory (persistent)
    - Episodic memory (events)
    - Semantic memory (knowledge)
    - Automatic consolidation
    - Context compression
    - Vector-based retrieval
    """
    
    def __init__(
        self,
        db: Session,
        embedding_service: Optional[Any] = None,
        vector_store: Optional[Any] = None,
        cache_manager: Optional[Any] = None
    ):
        """
        Initialize hierarchical memory system.
        
        Args:
            db: Database session
            embedding_service: Service for generating embeddings
            vector_store: Vector database for similarity search
            cache_manager: Cache manager for fast access
        """
        self.db = db
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.cache_manager = cache_manager
        
        # Memory stores
        self.short_term: Dict[str, Dict[str, Memory]] = defaultdict(dict)  # session_id -> memories
        self.long_term: Dict[str, Dict[str, Memory]] = defaultdict(dict)   # agent_id -> memories
        self.episodic: Dict[str, Dict[str, Memory]] = defaultdict(dict)    # agent_id -> memories
        self.semantic: Dict[str, Dict[str, Memory]] = defaultdict(dict)    # agent_id -> memories
        self.working: Dict[str, List[Memory]] = defaultdict(list)          # agent_id -> buffer
        
        # Configuration
        self.short_term_capacity = 50  # Max items in short-term
        self.working_capacity = 10     # Max items in working memory
        self.consolidation_threshold = 0.7  # Threshold for moving to long-term
        
        logger.info("HierarchicalMemory initialized")
    
    async def store(
        self,
        agent_id: str,
        content: str,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        session_id: Optional[str] = None,
        importance: MemoryImportance = MemoryImportance.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Memory:
        """
        Store a memory.
        
        Args:
            agent_id: Agent ID
            content: Memory content
            memory_type: Type of memory
            session_id: Session ID (for short-term)
            importance: Importance level
            metadata: Additional metadata
            tags: Tags for categorization
            
        Returns:
            Created memory object
        """
        memory_id = self._generate_memory_id(agent_id, content)
        
        # Generate embedding if service available
        embedding = None
        if self.embedding_service:
            embedding = await self._generate_embedding(content)
        
        memory = Memory(
            memory_id=memory_id,
            content=content,
            memory_type=memory_type,
            agent_id=agent_id,
            session_id=session_id,
            importance=importance,
            metadata=metadata,
            embedding=embedding
        )
        
        if tags:
            memory.tags = tags
        
        # Store in appropriate memory type
        if memory_type == MemoryType.SHORT_TERM:
            session_key = session_id or "default"
            self.short_term[session_key][memory_id] = memory
            
            # Check capacity
            if len(self.short_term[session_key]) > self.short_term_capacity:
                await self._consolidate_short_term(session_key)
        
        elif memory_type == MemoryType.LONG_TERM:
            self.long_term[agent_id][memory_id] = memory
        
        elif memory_type == MemoryType.EPISODIC:
            self.episodic[agent_id][memory_id] = memory
        
        elif memory_type == MemoryType.SEMANTIC:
            self.semantic[agent_id][memory_id] = memory
        
        elif memory_type == MemoryType.WORKING:
            self.working[agent_id].append(memory)
            
            # Check capacity
            if len(self.working[agent_id]) > self.working_capacity:
                self.working[agent_id].pop(0)  # Remove oldest
        
        # Store in vector database if available
        if self.vector_store and embedding:
            await self._store_in_vector_db(memory)
        
        logger.debug(f"Stored {memory_type.value} memory: {memory_id}")
        
        return memory
    
    async def retrieve(
        self,
        agent_id: str,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        top_k: int = 5,
        min_relevance: float = 0.3,
        session_id: Optional[str] = None
    ) -> List[Memory]:
        """
        Retrieve relevant memories.
        
        Args:
            agent_id: Agent ID
            query: Query string
            memory_types: Types of memory to search (None = all)
            top_k: Number of results to return
            min_relevance: Minimum relevance score
            session_id: Session ID for short-term memory
            
        Returns:
            List of relevant memories
        """
        # Generate query embedding
        query_embedding = None
        if self.embedding_service:
            query_embedding = await self._generate_embedding(query)
        
        # Collect memories from specified types
        all_memories = []
        
        if not memory_types:
            memory_types = list(MemoryType)
        
        for mem_type in memory_types:
            if mem_type == MemoryType.SHORT_TERM:
                session_key = session_id or "default"
                all_memories.extend(self.short_term[session_key].values())
            elif mem_type == MemoryType.LONG_TERM:
                all_memories.extend(self.long_term[agent_id].values())
            elif mem_type == MemoryType.EPISODIC:
                all_memories.extend(self.episodic[agent_id].values())
            elif mem_type == MemoryType.SEMANTIC:
                all_memories.extend(self.semantic[agent_id].values())
            elif mem_type == MemoryType.WORKING:
                all_memories.extend(self.working[agent_id])
        
        # Calculate relevance scores
        scored_memories = []
        for memory in all_memories:
            # Semantic similarity if embeddings available
            semantic_score = 0.0
            if query_embedding and memory.embedding:
                semantic_score = self._cosine_similarity(query_embedding, memory.embedding)
            
            # Keyword matching
            keyword_score = self._keyword_match_score(query, memory.content)
            
            # Combined score
            combined_score = (
                0.6 * semantic_score +
                0.2 * keyword_score +
                0.2 * memory.relevance_score
            )
            
            if combined_score >= min_relevance:
                scored_memories.append((memory, combined_score))
        
        # Sort by score and return top_k
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        results = [mem for mem, score in scored_memories[:top_k]]
        
        # Mark as accessed
        for memory in results:
            memory.access()
        
        logger.debug(f"Retrieved {len(results)} memories for query: {query[:50]}")
        
        return results
    
    async def consolidate_memory(
        self,
        agent_id: str,
        session_id: Optional[str] = None
    ):
        """
        Consolidate short-term memories to long-term.
        
        Moves important short-term memories to long-term storage.
        """
        session_key = session_id or "default"
        short_term_memories = list(self.short_term[session_key].values())
        
        if not short_term_memories:
            return
        
        logger.info(f"Consolidating {len(short_term_memories)} short-term memories")
        
        # Identify memories to consolidate
        to_consolidate = [
            mem for mem in short_term_memories
            if mem.relevance_score >= self.consolidation_threshold
        ]
        
        # Move to long-term
        for memory in to_consolidate:
            # Update type
            memory.memory_type = MemoryType.LONG_TERM
            
            # Store in long-term
            self.long_term[agent_id][memory.memory_id] = memory
            
            # Remove from short-term
            del self.short_term[session_key][memory.memory_id]
            
            logger.debug(f"Consolidated memory {memory.memory_id} to long-term")
        
        logger.info(f"Consolidated {len(to_consolidate)} memories to long-term")
    
    async def compress_context(
        self,
        context: str,
        max_length: int = 1000,
        preserve_key_info: bool = True
    ) -> str:
        """
        Compress context while preserving key information.
        
        Args:
            context: Context to compress
            max_length: Maximum length in characters
            preserve_key_info: Whether to preserve key information
            
        Returns:
            Compressed context
        """
        if len(context) <= max_length:
            return context
        
        logger.info(f"Compressing context from {len(context)} to {max_length} chars")
        
        if not self.embedding_service:
            # Simple truncation
            return context[:max_length] + "..."
        
        # Split into sentences
        sentences = self._split_sentences(context)
        
        if preserve_key_info:
            # Extract key sentences using embeddings
            key_sentences = await self._extract_key_sentences(
                sentences,
                max_length
            )
            compressed = " ".join(key_sentences)
        else:
            # Simple truncation
            compressed = context[:max_length]
        
        logger.info(f"Compressed to {len(compressed)} chars")
        
        return compressed
    
    async def summarize_memories(
        self,
        agent_id: str,
        memory_type: MemoryType,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> str:
        """
        Generate summary of memories.
        
        Args:
            agent_id: Agent ID
            memory_type: Type of memory to summarize
            time_range: Optional time range (start, end)
            
        Returns:
            Summary text
        """
        # Get memories
        if memory_type == MemoryType.SHORT_TERM:
            memories = list(self.short_term.get("default", {}).values())
        elif memory_type == MemoryType.LONG_TERM:
            memories = list(self.long_term.get(agent_id, {}).values())
        elif memory_type == MemoryType.EPISODIC:
            memories = list(self.episodic.get(agent_id, {}).values())
        elif memory_type == MemoryType.SEMANTIC:
            memories = list(self.semantic.get(agent_id, {}).values())
        else:
            memories = []
        
        # Filter by time range
        if time_range:
            start, end = time_range
            memories = [
                m for m in memories
                if start <= m.created_at <= end
            ]
        
        if not memories:
            return "No memories to summarize."
        
        # Sort by relevance
        memories.sort(key=lambda m: m.relevance_score, reverse=True)
        
        # Create summary
        summary_parts = [
            f"Summary of {len(memories)} {memory_type.value} memories:",
            ""
        ]
        
        # Group by importance
        by_importance = defaultdict(list)
        for memory in memories:
            by_importance[memory.importance].append(memory)
        
        for importance in [MemoryImportance.CRITICAL, MemoryImportance.HIGH, MemoryImportance.MEDIUM]:
            if importance in by_importance:
                summary_parts.append(f"\n{importance.value.title()} importance:")
                for memory in by_importance[importance][:5]:  # Top 5 per importance
                    summary_parts.append(f"- {memory.content[:100]}")
        
        return "\n".join(summary_parts)
    
    async def forget_old_memories(
        self,
        agent_id: str,
        age_threshold_days: int = 30,
        min_access_count: int = 2
    ):
        """
        Remove old, rarely accessed memories.
        
        Args:
            agent_id: Agent ID
            age_threshold_days: Age threshold in days
            min_access_count: Minimum access count to keep
        """
        threshold_date = datetime.now(timezone.utc) - timedelta(days=age_threshold_days)
        
        removed_count = 0
        
        # Check long-term memories
        to_remove = []
        for memory_id, memory in self.long_term[agent_id].items():
            if (memory.created_at < threshold_date and
                memory.access_count < min_access_count and
                memory.importance in [MemoryImportance.LOW, MemoryImportance.TRIVIAL]):
                to_remove.append(memory_id)
        
        for memory_id in to_remove:
            del self.long_term[agent_id][memory_id]
            removed_count += 1
        
        logger.info(f"Forgot {removed_count} old memories for agent {agent_id}")
    
    async def apply_decay(
        self,
        agent_id: str
    ):
        """
        Apply forgetting curve decay to all memories.
        
        Args:
            agent_id: Agent ID
        """
        now = datetime.now(timezone.utc)
        
        # Apply decay to all memory types
        for memory_store in [
            self.long_term[agent_id],
            self.episodic[agent_id],
            self.semantic[agent_id]
        ]:
            for memory in memory_store.values():
                hours_since_access = (now - memory.last_accessed).total_seconds() / 3600
                memory.decay(hours_since_access)
        
        logger.debug(f"Applied decay to memories for agent {agent_id}")
    
    def get_memory_stats(
        self,
        agent_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get memory statistics.
        
        Args:
            agent_id: Agent ID
            session_id: Session ID for short-term stats
            
        Returns:
            Memory statistics
        """
        session_key = session_id or "default"
        
        return {
            "short_term_count": len(self.short_term[session_key]),
            "long_term_count": len(self.long_term[agent_id]),
            "episodic_count": len(self.episodic[agent_id]),
            "semantic_count": len(self.semantic[agent_id]),
            "working_count": len(self.working[agent_id]),
            "total_count": (
                len(self.short_term[session_key]) +
                len(self.long_term[agent_id]) +
                len(self.episodic[agent_id]) +
                len(self.semantic[agent_id]) +
                len(self.working[agent_id])
            ),
            "short_term_capacity": self.short_term_capacity,
            "working_capacity": self.working_capacity
        }
    
    async def _consolidate_short_term(
        self,
        session_key: str
    ):
        """Consolidate short-term memories when capacity exceeded."""
        memories = list(self.short_term[session_key].values())
        
        # Sort by relevance
        memories.sort(key=lambda m: m.relevance_score)
        
        # Remove least relevant
        to_remove = memories[:len(memories) - self.short_term_capacity]
        
        for memory in to_remove:
            del self.short_term[session_key][memory.memory_id]
    
    async def _generate_embedding(
        self,
        text: str
    ) -> List[float]:
        """Generate embedding for text."""
        if not self.embedding_service:
            return []
        
        try:
            embedding = await self.embedding_service.embed_text(text)
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return []
    
    async def _store_in_vector_db(
        self,
        memory: Memory
    ):
        """Store memory in vector database."""
        if not self.vector_store or not memory.embedding:
            return
        
        try:
            await self.vector_store.insert(
                collection_name=f"memories_{memory.agent_id}",
                vectors=[memory.embedding],
                payloads=[{
                    "memory_id": memory.memory_id,
                    "content": memory.content,
                    "memory_type": memory.memory_type.value,
                    "importance": memory.importance.value,
                    "created_at": memory.created_at.isoformat()
                }]
            )
        except Exception as e:
            logger.error(f"Failed to store in vector DB: {e}")
    
    def _cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _keyword_match_score(
        self,
        query: str,
        content: str
    ) -> float:
        """Calculate keyword match score."""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words:
            return 0.0
        
        matches = query_words.intersection(content_words)
        return len(matches) / len(query_words)
    
    def _split_sentences(
        self,
        text: str
    ) -> List[str]:
        """Split text into sentences."""
        import re
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    async def _extract_key_sentences(
        self,
        sentences: List[str],
        max_length: int
    ) -> List[str]:
        """Extract key sentences that fit within max_length."""
        # Generate embeddings for all sentences
        embeddings = []
        for sentence in sentences:
            emb = await self._generate_embedding(sentence)
            embeddings.append(emb)
        
        # Calculate importance scores (distance from centroid)
        if not embeddings or not embeddings[0]:
            return sentences[:max_length // 100]  # Fallback
        
        # Calculate centroid
        dim = len(embeddings[0])
        centroid = [sum(emb[i] for emb in embeddings) / len(embeddings) for i in range(dim)]
        
        # Score sentences by distance to centroid (closer = more representative)
        scored = []
        for i, (sentence, embedding) in enumerate(zip(sentences, embeddings)):
            if embedding:
                distance = self._cosine_similarity(embedding, centroid)
                scored.append((sentence, distance, i))
        
        # Sort by score and original order
        scored.sort(key=lambda x: (-x[1], x[2]))
        
        # Select sentences that fit
        selected = []
        current_length = 0
        
        for sentence, _, _ in scored:
            if current_length + len(sentence) <= max_length:
                selected.append(sentence)
                current_length += len(sentence) + 1  # +1 for space
            else:
                break
        
        # Sort by original order
        selected.sort(key=lambda s: sentences.index(s))
        
        return selected
    
    def _generate_memory_id(
        self,
        agent_id: str,
        content: str
    ) -> str:
        """Generate unique memory ID."""
        content_hash = hashlib.sha256(
            f"{agent_id}:{content}:{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()
        return content_hash[:16]


# Example usage
EXAMPLE_USAGE = """
# Initialize
memory = HierarchicalMemory(db, embedding_service, vector_store)

# Store memories
await memory.store(
    agent_id="agent_123",
    content="User prefers concise answers",
    memory_type=MemoryType.SEMANTIC,
    importance=MemoryImportance.HIGH,
    tags=["preference", "style"]
)

await memory.store(
    agent_id="agent_123",
    content="Discussed project requirements on 2025-10-26",
    memory_type=MemoryType.EPISODIC,
    importance=MemoryImportance.MEDIUM,
    metadata={"date": "2025-10-26", "topic": "requirements"}
)

# Retrieve relevant memories
relevant = await memory.retrieve(
    agent_id="agent_123",
    query="What are the user's preferences?",
    memory_types=[MemoryType.SEMANTIC, MemoryType.LONG_TERM],
    top_k=5
)

# Consolidate short-term to long-term
await memory.consolidate_memory(agent_id="agent_123")

# Compress context
compressed = await memory.compress_context(
    context="Very long context...",
    max_length=500
)

# Get statistics
stats = memory.get_memory_stats(agent_id="agent_123")
# {
#   "short_term_count": 15,
#   "long_term_count": 42,
#   "episodic_count": 8,
#   "semantic_count": 12,
#   "total_count": 77
# }

# Apply decay (forgetting curve)
await memory.apply_decay(agent_id="agent_123")

# Forget old memories
await memory.forget_old_memories(
    agent_id="agent_123",
    age_threshold_days=30,
    min_access_count=2
)
"""
