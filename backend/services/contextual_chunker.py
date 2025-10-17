"""
Contextual Chunker - Add document context to each chunk.

Based on Anthropic's Contextual Retrieval (2024):
- Adds document-level context to each chunk
- Improves retrieval accuracy by 30-50%
- Prevents context loss in chunking
"""

import logging
from typing import Optional, List, Dict
from uuid import UUID

from backend.db.models.document import Document

logger = logging.getLogger(__name__)


class ContextualChunker:
    """
    Add contextual information to chunks for better retrieval.

    Features:
    - Document metadata context
    - Section information
    - Document summary
    - Hierarchical context
    """

    def __init__(self):
        """Initialize ContextualChunker."""
        logger.info("ContextualChunker initialized")

    def add_context_to_chunk(
        self,
        chunk_text: str,
        document: Document,
        section_name: Optional[str] = None,
        document_summary: Optional[str] = None,
        chunk_index: Optional[int] = None,
        total_chunks: Optional[int] = None,
    ) -> str:
        """
        Add contextual information to chunk.

        Format:
        [Document: {title}]
        [Author: {author}]
        [Section: {section}]
        [Context: {summary}]
        [Position: Chunk {index} of {total}]

        {chunk_text}

        Args:
            chunk_text: Original chunk text
            document: Document object with metadata
            section_name: Section/chapter name (optional)
            document_summary: Brief document summary (optional)
            chunk_index: Chunk position (optional)
            total_chunks: Total number of chunks (optional)

        Returns:
            Chunk with contextual header
        """
        try:
            context_parts = []

            # Document title
            if document.document_title:
                context_parts.append(f"[Document: {document.document_title}]")
            elif document.filename:
                # Fallback to filename
                context_parts.append(f"[Document: {document.filename}]")

            # Author information
            if document.document_author:
                context_parts.append(f"[Author: {document.document_author}]")

            # Subject/Topic
            if document.document_subject:
                context_parts.append(f"[Subject: {document.document_subject}]")

            # Language
            if document.document_language:
                context_parts.append(f"[Language: {document.document_language}]")

            # Section information
            if section_name:
                context_parts.append(f"[Section: {section_name}]")

            # Document summary/context
            if document_summary:
                # Limit summary length
                max_summary_length = 200
                if len(document_summary) > max_summary_length:
                    document_summary = document_summary[:max_summary_length] + "..."
                context_parts.append(f"[Context: {document_summary}]")

            # Position information
            if chunk_index is not None and total_chunks is not None:
                context_parts.append(
                    f"[Position: Chunk {chunk_index + 1} of {total_chunks}]"
                )

            # Keywords
            if document.document_keywords:
                # Limit keywords
                keywords = document.document_keywords.split(",")[:5]
                keywords_str = ", ".join([k.strip() for k in keywords])
                context_parts.append(f"[Keywords: {keywords_str}]")

            # Combine context header
            if context_parts:
                context_header = "\n".join(context_parts)
                return f"{context_header}\n\n{chunk_text}"
            else:
                # No context available, return original
                return chunk_text

        except Exception as e:
            logger.error(f"Failed to add context to chunk: {e}", exc_info=True)
            # Return original chunk on error
            return chunk_text

    def add_context_to_chunks(
        self,
        chunks: List[str],
        document: Document,
        section_names: Optional[List[str]] = None,
        document_summary: Optional[str] = None,
    ) -> List[str]:
        """
        Add context to multiple chunks.

        Args:
            chunks: List of chunk texts
            document: Document object
            section_names: List of section names (one per chunk, optional)
            document_summary: Document summary (optional)

        Returns:
            List of chunks with context
        """
        try:
            contextual_chunks = []
            total_chunks = len(chunks)

            for i, chunk_text in enumerate(chunks):
                # Get section name for this chunk
                section_name = None
                if section_names and i < len(section_names):
                    section_name = section_names[i]

                # Add context
                contextual_chunk = self.add_context_to_chunk(
                    chunk_text=chunk_text,
                    document=document,
                    section_name=section_name,
                    document_summary=document_summary,
                    chunk_index=i,
                    total_chunks=total_chunks,
                )

                contextual_chunks.append(contextual_chunk)

            logger.info(
                f"Added context to {len(contextual_chunks)} chunks "
                f"for document {document.id}"
            )

            return contextual_chunks

        except Exception as e:
            logger.error(f"Failed to add context to chunks: {e}", exc_info=True)
            # Return original chunks on error
            return chunks

    def generate_document_summary(
        self, document: Document, first_chunk: str, max_length: int = 200
    ) -> str:
        """
        Generate a brief document summary from metadata and first chunk.

        Args:
            document: Document object
            first_chunk: First chunk of document
            max_length: Maximum summary length

        Returns:
            Document summary
        """
        try:
            summary_parts = []

            # Use subject if available
            if document.document_subject:
                summary_parts.append(document.document_subject)

            # Add keywords context
            if document.document_keywords:
                keywords = document.document_keywords.split(",")[:3]
                keywords_str = ", ".join([k.strip() for k in keywords])
                summary_parts.append(f"Topics: {keywords_str}")

            # If no metadata, use first chunk excerpt
            if not summary_parts and first_chunk:
                # Take first sentence or first 150 chars
                excerpt = first_chunk[:150].strip()
                if "." in excerpt:
                    excerpt = excerpt.split(".")[0] + "."
                summary_parts.append(excerpt)

            # Combine
            summary = ". ".join(summary_parts)

            # Limit length
            if len(summary) > max_length:
                summary = summary[:max_length] + "..."

            return summary if summary else "Document content"

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return "Document content"

    def extract_section_from_chunk(
        self, chunk_text: str, chunk_index: int
    ) -> Optional[str]:
        """
        Try to extract section name from chunk text.

        Looks for patterns like:
        - "Chapter 1: Introduction"
        - "Section 2.1 - Overview"
        - "# Heading"

        Args:
            chunk_text: Chunk text
            chunk_index: Chunk position

        Returns:
            Section name or None
        """
        try:
            lines = chunk_text.split("\n")

            for line in lines[:5]:  # Check first 5 lines
                line = line.strip()

                # Markdown heading
                if line.startswith("#"):
                    return line.lstrip("#").strip()

                # Chapter/Section patterns
                if any(
                    keyword in line.lower()
                    for keyword in ["chapter", "section", "장", "절"]
                ):
                    if len(line) < 100:  # Reasonable heading length
                        return line

            return None

        except Exception as e:
            logger.error(f"Failed to extract section: {e}")
            return None


def get_contextual_chunker() -> ContextualChunker:
    """
    Get ContextualChunker instance.

    Returns:
        ContextualChunker instance
    """
    return ContextualChunker()
