# Parent-Child Chunking Strategy
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import uuid

logger = logging.getLogger(__name__)


@dataclass
class ChildChunk:
    """Small chunk for precise retrieval"""

    chunk_id: str
    text: str
    parent_id: str
    chunk_index: int
    start_char: int
    end_char: int


@dataclass
class ParentChunk:
    """Large chunk for rich context"""

    chunk_id: str
    text: str
    child_ids: List[str]
    chunk_index: int
    start_char: int
    end_char: int


class ParentChildChunker:
    """
    Two-level chunking strategy for better retrieval.

    Strategy:
    - Small chunks (256 tokens) for precise search
    - Large chunks (1024 tokens) for rich context
    - Mapping between child and parent chunks

    Benefits:
    - Search with small chunks (high precision)
    - Provide context with large chunks (completeness)
    - Best of both worlds
    """

    def __init__(
        self,
        child_size: int = 256,
        child_overlap: int = 50,
        parent_size: int = 1024,
        parent_overlap: int = 100,
    ):
        """
        Initialize chunker.

        Args:
            child_size: Small chunk size in tokens
            child_overlap: Overlap for small chunks
            parent_size: Large chunk size in tokens
            parent_overlap: Overlap for large chunks
        """
        self.child_size = child_size
        self.child_overlap = child_overlap
        self.parent_size = parent_size
        self.parent_overlap = parent_overlap

    def chunk_document(
        self, text: str, document_id: str
    ) -> Tuple[List[ChildChunk], List[ParentChunk]]:
        """
        Create parent and child chunks from document.

        Args:
            text: Document text
            document_id: Document identifier

        Returns:
            Tuple of (child_chunks, parent_chunks)
        """
        try:
            # Create parent chunks first (large)
            parent_chunks = self._create_parent_chunks(text, document_id)

            # Create child chunks (small) and map to parents
            child_chunks = self._create_child_chunks(text, document_id, parent_chunks)

            logger.info(
                f"Created {len(child_chunks)} child chunks and "
                f"{len(parent_chunks)} parent chunks for document {document_id}"
            )

            return child_chunks, parent_chunks

        except Exception as e:
            logger.error(f"Parent-child chunking failed: {e}")
            raise

    def _create_parent_chunks(self, text: str, document_id: str) -> List[ParentChunk]:
        """Create large parent chunks"""
        chunks = []
        char_size = self.parent_size * 4  # Rough token-to-char conversion
        char_overlap = self.parent_overlap * 4

        start = 0
        chunk_index = 0

        while start < len(text):
            end = min(start + char_size, len(text))

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence end
                for delimiter in [". ", "! ", "? ", "\n\n"]:
                    last_delim = text[start:end].rfind(delimiter)
                    if last_delim > char_size * 0.7:  # At least 70% of chunk
                        end = start + last_delim + len(delimiter)
                        break

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunk = ParentChunk(
                    chunk_id=f"{document_id}_parent_{chunk_index}",
                    text=chunk_text,
                    child_ids=[],  # Will be populated later
                    chunk_index=chunk_index,
                    start_char=start,
                    end_char=end,
                )
                chunks.append(chunk)
                chunk_index += 1

            # Move to next chunk with overlap
            start = end - char_overlap if end < len(text) else end

        return chunks

    def _create_child_chunks(
        self, text: str, document_id: str, parent_chunks: List[ParentChunk]
    ) -> List[ChildChunk]:
        """Create small child chunks and map to parents"""
        chunks = []
        char_size = self.child_size * 4
        char_overlap = self.child_overlap * 4

        start = 0
        chunk_index = 0

        while start < len(text):
            end = min(start + char_size, len(text))

            # Try to break at sentence boundary
            if end < len(text):
                for delimiter in [". ", "! ", "? ", "\n"]:
                    last_delim = text[start:end].rfind(delimiter)
                    if last_delim > char_size * 0.7:
                        end = start + last_delim + len(delimiter)
                        break

            chunk_text = text[start:end].strip()

            if chunk_text:
                # Find parent chunk
                parent_id = self._find_parent(start, end, parent_chunks)

                chunk = ChildChunk(
                    chunk_id=f"{document_id}_child_{chunk_index}",
                    text=chunk_text,
                    parent_id=parent_id,
                    chunk_index=chunk_index,
                    start_char=start,
                    end_char=end,
                )
                chunks.append(chunk)

                # Add to parent's child list
                for parent in parent_chunks:
                    if parent.chunk_id == parent_id:
                        parent.child_ids.append(chunk.chunk_id)
                        break

                chunk_index += 1

            start = end - char_overlap if end < len(text) else end

        return chunks

    def _find_parent(
        self, child_start: int, child_end: int, parent_chunks: List[ParentChunk]
    ) -> str:
        """Find parent chunk that contains this child chunk"""
        child_mid = (child_start + child_end) // 2

        for parent in parent_chunks:
            if parent.start_char <= child_mid < parent.end_char:
                return parent.chunk_id

        # Fallback: return closest parent
        if parent_chunks:
            return parent_chunks[0].chunk_id

        return "unknown"

    def get_parent_context(
        self,
        child_chunk_id: str,
        child_chunks: List[ChildChunk],
        parent_chunks: List[ParentChunk],
    ) -> Optional[ParentChunk]:
        """Get parent chunk for a child chunk"""
        # Find child chunk
        child = None
        for c in child_chunks:
            if c.chunk_id == child_chunk_id:
                child = c
                break

        if not child:
            return None

        # Find parent chunk
        for parent in parent_chunks:
            if parent.chunk_id == child.parent_id:
                return parent

        return None

    def convert_to_dict(
        self, child_chunks: List[ChildChunk], parent_chunks: List[ParentChunk]
    ) -> Dict[str, Any]:
        """Convert chunks to dictionary format for storage"""
        return {
            "child_chunks": [
                {
                    "chunk_id": c.chunk_id,
                    "text": c.text,
                    "parent_id": c.parent_id,
                    "chunk_index": c.chunk_index,
                    "start_char": c.start_char,
                    "end_char": c.end_char,
                }
                for c in child_chunks
            ],
            "parent_chunks": [
                {
                    "chunk_id": p.chunk_id,
                    "text": p.text,
                    "child_ids": p.child_ids,
                    "chunk_index": p.chunk_index,
                    "start_char": p.start_char,
                    "end_char": p.end_char,
                }
                for p in parent_chunks
            ],
        }


class ParentChildRetriever:
    """
    Retriever that uses parent-child chunking strategy.

    Workflow:
    1. Search using small child chunks (precise)
    2. Retrieve large parent chunks (context)
    3. Provide rich context to LLM
    """

    def __init__(self, vector_search_agent, parent_store: Dict[str, ParentChunk]):
        self.vector_agent = vector_search_agent
        self.parent_store = parent_store  # Map child_id -> parent_chunk

    async def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve using parent-child strategy.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of parent chunks with rich context
        """
        try:
            # Step 1: Search with child chunks (precise)
            child_results = await self.vector_agent.search(
                query=query,
                top_k=top_k * 2,
                search_mode="vector_only",  # Get more children
            )

            # Step 2: Get parent chunks (context)
            parent_results = []
            seen_parents = set()

            for child in child_results:
                child_id = child.get("chunk_id") or child.get("id")
                parent = self.parent_store.get(child_id)

                if parent and parent.chunk_id not in seen_parents:
                    parent_results.append(
                        {
                            "chunk_id": parent.chunk_id,
                            "text": parent.text,
                            "score": child.get("score", 0.0),
                            "child_chunk_id": child_id,
                            "child_text": child.get("text", ""),
                            "source": "parent_child",
                        }
                    )
                    seen_parents.add(parent.chunk_id)

                if len(parent_results) >= top_k:
                    break

            logger.info(
                f"Retrieved {len(parent_results)} parent chunks "
                f"from {len(child_results)} child chunks"
            )

            return parent_results

        except Exception as e:
            logger.error(f"Parent-child retrieval failed: {e}")
            return []


def create_parent_child_chunker(
    child_size: int = 256, parent_size: int = 1024
) -> ParentChildChunker:
    """Factory function to create chunker"""
    return ParentChildChunker(
        child_size=child_size,
        child_overlap=child_size // 5,
        parent_size=parent_size,
        parent_overlap=parent_size // 10,
    )
