# Corrective RAG (CRAG): Corrective Retrieval-Augmented Generation
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RetrievalQuality(Enum):
    """Quality assessment of retrieval results"""

    EXCELLENT = "excellent"
    GOOD = "good"
    AMBIGUOUS = "ambiguous"
    POOR = "poor"


class CorrectionAction(Enum):
    """Action to take based on retrieval quality"""

    USE_RETRIEVED = "use_retrieved"
    REFINE_QUERY = "refine_query"
    WEB_SEARCH = "web_search"
    COMBINE_SOURCES = "combine_sources"


@dataclass
class RetrievalEvaluation:
    """Evaluation of retrieval quality"""

    quality: RetrievalQuality
    confidence: float
    action: CorrectionAction
    reasoning: str


@dataclass
class CorrectiveRAGResult:
    """Result from Corrective RAG"""

    response: str
    sources: List[Dict[str, str]]
    evaluation: RetrievalEvaluation
    corrections_applied: List[str]
    final_confidence: float


class CorrectiveRAG:
    """
    Corrective RAG implementation with automatic correction strategies.

    Key features:
    1. Retrieval Quality Assessment: Evaluates if retrieved docs are sufficient
    2. Automatic Correction: Applies correction strategies when needed
    3. Web Search Fallback: Searches web when local docs insufficient
    4. Query Refinement: Reformulates query for better results
    5. Multi-Source Combination: Combines local and web sources
    """

    def __init__(
        self, llm_manager, web_search_service=None, quality_threshold: float = 0.6
    ):
        """
        Initialize Corrective RAG.

        Args:
            llm_manager: LLM manager for generation
            web_search_service: Optional web search service
            quality_threshold: Minimum quality to accept retrieval
        """
        self.llm_manager = llm_manager
        self.web_search_service = web_search_service
        self.quality_threshold = quality_threshold

    async def evaluate_retrieval_quality(
        self, query: str, documents: List[Dict[str, str]]
    ) -> RetrievalEvaluation:
        """
        Evaluate quality of retrieved documents.

        Args:
            query: User query
            documents: Retrieved documents

        Returns:
            RetrievalEvaluation with quality assessment and recommended action
        """
        if not documents:
            return RetrievalEvaluation(
                quality=RetrievalQuality.POOR,
                confidence=1.0,
                action=CorrectionAction.WEB_SEARCH,
                reasoning="No documents retrieved",
            )

        # Create evaluation prompt
        docs_text = "\n\n".join(
            [
                f"Document {i+1}:\n{doc.get('content', '')[:400]}"
                for i, doc in enumerate(documents[:5])
            ]
        )

        prompt = f"""Evaluate the quality of retrieved documents for answering the query.

Query: {query}

Retrieved Documents:
{docs_text}

Assess the retrieval quality:
- excellent: Documents fully answer the query with high confidence
- good: Documents contain sufficient information to answer
- ambiguous: Documents have some relevant info but may need more
- poor: Documents don't contain useful information

Based on quality, recommend action:
- use_retrieved: Use these documents (excellent/good quality)
- refine_query: Reformulate query for better results (ambiguous)
- web_search: Search web for additional info (poor/ambiguous)
- combine_sources: Use both local and web sources (ambiguous)

Provide evaluation:
QUALITY: [score]
CONFIDENCE: [0.0-1.0]
ACTION: [recommended action]
REASONING: [brief explanation]"""

        try:
            response = await self.llm_manager.generate(
                prompt=prompt, max_tokens=200, temperature=0.1
            )

            # Parse response
            lines = response.strip().split("\n")
            quality_str = "good"
            confidence = 0.7
            action_str = "use_retrieved"
            reasoning = "Evaluation completed"

            for line in lines:
                if line.startswith("QUALITY:"):
                    quality_str = line.split(":", 1)[1].strip().lower()
                elif line.startswith("CONFIDENCE:"):
                    try:
                        confidence = float(line.split(":", 1)[1].strip())
                    except:
                        pass
                elif line.startswith("ACTION:"):
                    action_str = line.split(":", 1)[1].strip().lower()
                elif line.startswith("REASONING:"):
                    reasoning = line.split(":", 1)[1].strip()

            # Map to enums
            quality_map = {
                "excellent": RetrievalQuality.EXCELLENT,
                "good": RetrievalQuality.GOOD,
                "ambiguous": RetrievalQuality.AMBIGUOUS,
                "poor": RetrievalQuality.POOR,
            }
            quality = quality_map.get(quality_str, RetrievalQuality.GOOD)

            action_map = {
                "use_retrieved": CorrectionAction.USE_RETRIEVED,
                "refine_query": CorrectionAction.REFINE_QUERY,
                "web_search": CorrectionAction.WEB_SEARCH,
                "combine_sources": CorrectionAction.COMBINE_SOURCES,
            }
            action = action_map.get(action_str, CorrectionAction.USE_RETRIEVED)

            return RetrievalEvaluation(
                quality=quality,
                confidence=confidence,
                action=action,
                reasoning=reasoning,
            )

        except Exception as e:
            logger.error(f"Error evaluating retrieval quality: {e}")
            return RetrievalEvaluation(
                quality=RetrievalQuality.GOOD,
                confidence=0.5,
                action=CorrectionAction.USE_RETRIEVED,
                reasoning=f"Evaluation failed: {str(e)}",
            )

    async def refine_query(self, original_query: str) -> str:
        """
        Refine query for better retrieval.

        Args:
            original_query: Original user query

        Returns:
            Refined query
        """
        prompt = f"""Reformulate this query to improve retrieval results.

Original Query: {original_query}

Create a refined query that:
1. Expands key concepts
2. Adds relevant synonyms
3. Makes intent more explicit
4. Keeps it concise

Refined Query:"""

        try:
            refined = await self.llm_manager.generate(
                prompt=prompt, max_tokens=100, temperature=0.3
            )

            refined_query = refined.strip()
            logger.info(f"Query refined: '{original_query}' -> '{refined_query}'")

            return refined_query

        except Exception as e:
            logger.error(f"Error refining query: {e}")
            return original_query

    async def web_search(
        self, query: str, num_results: int = 5
    ) -> List[Dict[str, str]]:
        """
        Search web for additional information.

        Args:
            query: Search query
            num_results: Number of results to retrieve

        Returns:
            List of web search results
        """
        if not self.web_search_service:
            logger.warning("Web search service not available")
            return []

        try:
            results = await self.web_search_service.search(query, num_results)
            logger.info(f"Web search returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return []

    async def generate_with_correction(
        self, query: str, retrieve_fn, generate_fn, top_k: int = 10
    ) -> CorrectiveRAGResult:
        """
        Generate response with automatic correction.

        Args:
            query: User query
            retrieve_fn: Async function to retrieve documents
            generate_fn: Async function to generate response
            top_k: Number of documents to retrieve

        Returns:
            CorrectiveRAGResult with response and corrections applied
        """
        corrections_applied = []

        # Initial retrieval
        documents = await retrieve_fn(query, top_k)
        logger.info(f"Initial retrieval: {len(documents)} documents")

        # Evaluate retrieval quality
        evaluation = await self.evaluate_retrieval_quality(query, documents)
        logger.info(
            f"Retrieval quality: {evaluation.quality.value}, "
            f"action: {evaluation.action.value}"
        )

        # Apply correction based on evaluation
        if evaluation.action == CorrectionAction.REFINE_QUERY:
            # Refine query and re-retrieve
            refined_query = await self.refine_query(query)
            documents = await retrieve_fn(refined_query, top_k)
            corrections_applied.append(f"Query refined: '{refined_query}'")
            logger.info(f"Re-retrieved with refined query: {len(documents)} documents")

        elif evaluation.action == CorrectionAction.WEB_SEARCH:
            # Search web for additional info
            web_results = await self.web_search(query, num_results=5)
            if web_results:
                documents.extend(web_results)
                corrections_applied.append(f"Added {len(web_results)} web results")
                logger.info(f"Added web results: total {len(documents)} documents")

        elif evaluation.action == CorrectionAction.COMBINE_SOURCES:
            # Combine local and web sources
            refined_query = await self.refine_query(query)
            additional_docs = await retrieve_fn(refined_query, top_k // 2)
            web_results = await self.web_search(query, num_results=3)

            documents.extend(additional_docs)
            documents.extend(web_results)

            corrections_applied.append(
                f"Combined sources: {len(additional_docs)} refined + "
                f"{len(web_results)} web"
            )
            logger.info(f"Combined sources: total {len(documents)} documents")

        # Generate response with corrected sources
        response = await generate_fn(query, documents)

        # Calculate final confidence
        final_confidence = evaluation.confidence
        if corrections_applied:
            # Boost confidence if corrections were successful
            final_confidence = min(final_confidence + 0.1, 1.0)

        return CorrectiveRAGResult(
            response=response,
            sources=documents,
            evaluation=evaluation,
            corrections_applied=corrections_applied,
            final_confidence=final_confidence,
        )


# Global Corrective RAG instance
_corrective_rag: Optional[CorrectiveRAG] = None


def get_corrective_rag(llm_manager, web_search_service=None) -> CorrectiveRAG:
    """Get global Corrective RAG instance"""
    global _corrective_rag
    if _corrective_rag is None:
        _corrective_rag = CorrectiveRAG(llm_manager, web_search_service)
    return _corrective_rag
