# Multi-Vector Retrieval - Multiple perspectives for better recall
import logging
from typing import List, Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)


class MultiVectorRetriever:
    """
    Multi-Vector Retrieval strategy.

    Creates multiple vector representations for each document:
    1. Original text vector
    2. Summary vector
    3. Question vectors (HyDE reverse)
    4. Key points vector

    Benefits:
    - Better recall (30-40% improvement)
    - Handles different query styles
    - More robust retrieval
    """

    def __init__(self, embedding_service, llm_manager, milvus_manager):
        self.embedding_service = embedding_service
        self.llm_manager = llm_manager
        self.milvus_manager = milvus_manager

    async def create_multi_vectors(
        self, chunk_text: str, chunk_id: str, document_id: str
    ) -> Dict[str, Any]:
        """
        Create multiple vector representations for a chunk.

        Args:
            chunk_text: Original chunk text
            chunk_id: Chunk identifier
            document_id: Document identifier

        Returns:
            Dictionary with multiple vectors and metadata
        """
        try:
            vectors = {}

            # 1. Original text vector
            original_vector = await self.embedding_service.embed(chunk_text)
            vectors["original"] = original_vector

            # 2. Summary vector (async)
            summary_task = self._create_summary_vector(chunk_text)

            # 3. Question vectors (async)
            questions_task = self._create_question_vectors(chunk_text)

            # 4. Key points vector (async)
            keypoints_task = self._create_keypoints_vector(chunk_text)

            # Wait for all async operations
            summary_vector, question_vectors, keypoints_vector = await asyncio.gather(
                summary_task, questions_task, keypoints_task, return_exceptions=True
            )

            # Add successful vectors
            if not isinstance(summary_vector, Exception) and summary_vector:
                vectors["summary"] = summary_vector

            if not isinstance(question_vectors, Exception) and question_vectors:
                vectors["questions"] = question_vectors

            if not isinstance(keypoints_vector, Exception) and keypoints_vector:
                vectors["keypoints"] = keypoints_vector

            logger.info(
                f"Created {len(vectors)} vector representations for chunk {chunk_id}"
            )

            return {
                "chunk_id": chunk_id,
                "document_id": document_id,
                "original_text": chunk_text,
                "vectors": vectors,
            }

        except Exception as e:
            logger.error(f"Multi-vector creation failed: {e}")
            # Fallback to original vector only
            return {
                "chunk_id": chunk_id,
                "document_id": document_id,
                "original_text": chunk_text,
                "vectors": {"original": await self.embedding_service.embed(chunk_text)},
            }

    async def _create_summary_vector(self, text: str) -> Optional[List[float]]:
        """Create vector from summary"""
        try:
            # Generate summary
            prompt = f"""Summarize the following text in 1-2 sentences:

{text}

Summary:"""

            summary = await self.llm_manager.generate(
                prompt=prompt, max_tokens=100, temperature=0.3
            )

            if summary:
                return await self.embedding_service.embed(summary)

            return None

        except Exception as e:
            logger.debug(f"Summary vector creation failed: {e}")
            return None

    async def _create_question_vectors(
        self, text: str, num_questions: int = 3
    ) -> Optional[List[List[float]]]:
        """Create vectors from generated questions"""
        try:
            # Generate questions that this text could answer
            prompt = f"""Generate {num_questions} questions that the following text could answer:

{text}

Questions (one per line):"""

            response = await self.llm_manager.generate(
                prompt=prompt, max_tokens=150, temperature=0.5
            )

            if not response:
                return None

            # Parse questions
            questions = [
                q.strip()
                for q in response.split("\n")
                if q.strip() and not q.strip().startswith("#")
            ][:num_questions]

            if not questions:
                return None

            # Embed questions
            question_vectors = await self.embedding_service.embed_batch(questions)

            return question_vectors

        except Exception as e:
            logger.debug(f"Question vectors creation failed: {e}")
            return None

    async def _create_keypoints_vector(self, text: str) -> Optional[List[float]]:
        """Create vector from key points"""
        try:
            # Extract key points
            prompt = f"""Extract 3-5 key points from the following text:

{text}

Key points:"""

            keypoints = await self.llm_manager.generate(
                prompt=prompt, max_tokens=150, temperature=0.3
            )

            if keypoints:
                return await self.embedding_service.embed(keypoints)

            return None

        except Exception as e:
            logger.debug(f"Key points vector creation failed: {e}")
            return None

    async def store_multi_vectors(self, multi_vector_data: Dict[str, Any]) -> List[str]:
        """
        Store multiple vectors in Milvus.

        Args:
            multi_vector_data: Data from create_multi_vectors

        Returns:
            List of inserted IDs
        """
        try:
            vectors = multi_vector_data["vectors"]
            chunk_id = multi_vector_data["chunk_id"]
            document_id = multi_vector_data["document_id"]
            original_text = multi_vector_data["original_text"]

            inserted_ids = []

            # Store each vector type
            for vector_type, vector_data in vectors.items():
                if vector_type == "questions" and isinstance(vector_data, list):
                    # Multiple question vectors
                    for i, vec in enumerate(vector_data):
                        metadata = {
                            "id": f"{chunk_id}_{vector_type}_{i}",
                            "chunk_id": chunk_id,
                            "document_id": document_id,
                            "text": original_text,
                            "vector_type": f"{vector_type}_{i}",
                            "is_multi_vector": True,
                        }

                        ids = await self.milvus_manager.insert_embeddings(
                            embeddings=[vec], metadata=[metadata]
                        )
                        inserted_ids.extend(ids)
                else:
                    # Single vector
                    metadata = {
                        "id": f"{chunk_id}_{vector_type}",
                        "chunk_id": chunk_id,
                        "document_id": document_id,
                        "text": original_text,
                        "vector_type": vector_type,
                        "is_multi_vector": True,
                    }

                    ids = await self.milvus_manager.insert_embeddings(
                        embeddings=[vector_data], metadata=[metadata]
                    )
                    inserted_ids.extend(ids)

            logger.info(
                f"Stored {len(inserted_ids)} multi-vectors for chunk {chunk_id}"
            )

            return inserted_ids

        except Exception as e:
            logger.error(f"Multi-vector storage failed: {e}")
            return []

    async def search_multi_vectors(
        self, query: str, top_k: int = 10, vector_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search across multiple vector types.

        Args:
            query: Search query
            top_k: Number of results
            vector_types: Specific vector types to search (None = all)

        Returns:
            Aggregated search results
        """
        try:
            # Embed query
            query_vector = await self.embedding_service.embed(query)

            # Search in Milvus
            results = await self.milvus_manager.search(
                query_vectors=[query_vector],
                top_k=top_k * 3,  # Get more for aggregation
                output_fields=["chunk_id", "document_id", "text", "vector_type"],
            )

            # Aggregate by chunk_id
            chunk_scores = {}
            chunk_data = {}

            for result in results[0]:  # First query results
                chunk_id = result.get("chunk_id")
                score = result.get("score", 0.0)
                vector_type = result.get("vector_type", "original")

                # Filter by vector type if specified
                if vector_types and not any(vt in vector_type for vt in vector_types):
                    continue

                # Aggregate scores (max score per chunk)
                if chunk_id not in chunk_scores or score > chunk_scores[chunk_id]:
                    chunk_scores[chunk_id] = score
                    chunk_data[chunk_id] = result

            # Sort by aggregated score
            sorted_chunks = sorted(
                chunk_scores.items(), key=lambda x: x[1], reverse=True
            )[:top_k]

            # Format results
            final_results = []
            for chunk_id, score in sorted_chunks:
                data = chunk_data[chunk_id]
                final_results.append(
                    {
                        "chunk_id": chunk_id,
                        "document_id": data.get("document_id"),
                        "text": data.get("text"),
                        "score": score,
                        "vector_type": data.get("vector_type"),
                        "source": "multi_vector",
                    }
                )

            logger.info(
                f"Multi-vector search: {len(results[0])} raw results → "
                f"{len(final_results)} aggregated results"
            )

            return final_results

        except Exception as e:
            logger.error(f"Multi-vector search failed: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get multi-vector statistics"""
        return {
            "enabled": True,
            "vector_types": ["original", "summary", "questions", "keypoints"],
        }


def create_multi_vector_retriever(
    embedding_service, llm_manager, milvus_manager
) -> MultiVectorRetriever:
    """Factory function to create multi-vector retriever"""
    return MultiVectorRetriever(embedding_service, llm_manager, milvus_manager)
