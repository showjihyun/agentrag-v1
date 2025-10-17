# Self-RAG: Self-Reflective Retrieval-Augmented Generation
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RelevanceScore(Enum):
    """Relevance assessment scores"""

    HIGHLY_RELEVANT = "highly_relevant"
    RELEVANT = "relevant"
    PARTIALLY_RELEVANT = "partially_relevant"
    NOT_RELEVANT = "not_relevant"


class SupportScore(Enum):
    """Support assessment scores"""

    FULLY_SUPPORTED = "fully_supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    NOT_SUPPORTED = "not_supported"


class UsefulnessScore(Enum):
    """Usefulness assessment scores"""

    VERY_USEFUL = "very_useful"
    USEFUL = "useful"
    SOMEWHAT_USEFUL = "somewhat_useful"
    NOT_USEFUL = "not_useful"


@dataclass
class RetrievalAssessment:
    """Assessment of retrieved documents"""

    relevance: RelevanceScore
    confidence: float  # 0.0 - 1.0
    reasoning: str
    should_retrieve_more: bool


@dataclass
class GenerationAssessment:
    """Assessment of generated response"""

    support: SupportScore
    usefulness: UsefulnessScore
    confidence: float
    reasoning: str
    should_regenerate: bool


@dataclass
class SelfRAGResult:
    """Self-RAG result with assessments"""

    response: str
    retrieval_assessment: RetrievalAssessment
    generation_assessment: GenerationAssessment
    iterations: int
    final_confidence: float


class SelfRAG:
    """
    Self-RAG implementation with reflection and self-assessment.

    Key features:
    1. Retrieval Assessment: Evaluates relevance of retrieved documents
    2. Generation Assessment: Evaluates quality of generated response
    3. Iterative Refinement: Re-retrieves or regenerates if needed
    4. Confidence Scoring: Provides confidence in final answer
    """

    def __init__(
        self,
        llm_manager,
        max_iterations: int = 3,
        relevance_threshold: float = 0.6,
        support_threshold: float = 0.7,
    ):
        """
        Initialize Self-RAG.

        Args:
            llm_manager: LLM manager for generation
            max_iterations: Maximum refinement iterations
            relevance_threshold: Minimum relevance score to proceed
            support_threshold: Minimum support score to accept
        """
        self.llm_manager = llm_manager
        self.max_iterations = max_iterations
        self.relevance_threshold = relevance_threshold
        self.support_threshold = support_threshold

    async def assess_retrieval_relevance(
        self, query: str, documents: List[Dict[str, str]]
    ) -> RetrievalAssessment:
        """
        Assess relevance of retrieved documents to query.

        Args:
            query: User query
            documents: Retrieved documents

        Returns:
            RetrievalAssessment with relevance score and reasoning
        """
        if not documents:
            return RetrievalAssessment(
                relevance=RelevanceScore.NOT_RELEVANT,
                confidence=1.0,
                reasoning="No documents retrieved",
                should_retrieve_more=True,
            )

        # Create assessment prompt
        docs_text = "\n\n".join(
            [
                f"Document {i+1}:\n{doc.get('content', '')[:500]}"
                for i, doc in enumerate(documents[:3])
            ]
        )

        prompt = f"""Assess the relevance of the retrieved documents to the query.

Query: {query}

Retrieved Documents:
{docs_text}

Rate the overall relevance:
- highly_relevant: Documents directly answer the query
- relevant: Documents contain useful information
- partially_relevant: Documents have some related information
- not_relevant: Documents are not helpful

Provide your assessment in this format:
RELEVANCE: [score]
CONFIDENCE: [0.0-1.0]
REASONING: [brief explanation]
RETRIEVE_MORE: [yes/no]"""

        try:
            response = await self.llm_manager.generate(
                prompt=prompt, max_tokens=200, temperature=0.1
            )

            # Parse response
            lines = response.strip().split("\n")
            relevance_str = "relevant"
            confidence = 0.7
            reasoning = "Assessment completed"
            retrieve_more = False

            for line in lines:
                if line.startswith("RELEVANCE:"):
                    relevance_str = line.split(":", 1)[1].strip().lower()
                elif line.startswith("CONFIDENCE:"):
                    try:
                        confidence = float(line.split(":", 1)[1].strip())
                    except:
                        pass
                elif line.startswith("REASONING:"):
                    reasoning = line.split(":", 1)[1].strip()
                elif line.startswith("RETRIEVE_MORE:"):
                    retrieve_more = "yes" in line.lower()

            # Map to enum
            relevance_map = {
                "highly_relevant": RelevanceScore.HIGHLY_RELEVANT,
                "relevant": RelevanceScore.RELEVANT,
                "partially_relevant": RelevanceScore.PARTIALLY_RELEVANT,
                "not_relevant": RelevanceScore.NOT_RELEVANT,
            }
            relevance = relevance_map.get(relevance_str, RelevanceScore.RELEVANT)

            # Decide if more retrieval needed
            should_retrieve = (
                retrieve_more
                or confidence < self.relevance_threshold
                or relevance
                in [RelevanceScore.PARTIALLY_RELEVANT, RelevanceScore.NOT_RELEVANT]
            )

            return RetrievalAssessment(
                relevance=relevance,
                confidence=confidence,
                reasoning=reasoning,
                should_retrieve_more=should_retrieve,
            )

        except Exception as e:
            logger.error(f"Error assessing retrieval relevance: {e}")
            return RetrievalAssessment(
                relevance=RelevanceScore.RELEVANT,
                confidence=0.5,
                reasoning=f"Assessment failed: {str(e)}",
                should_retrieve_more=False,
            )

    async def assess_generation_quality(
        self, query: str, response: str, documents: List[Dict[str, str]]
    ) -> GenerationAssessment:
        """
        Assess quality of generated response.

        Args:
            query: User query
            response: Generated response
            documents: Source documents

        Returns:
            GenerationAssessment with support and usefulness scores
        """
        docs_text = "\n\n".join(
            [
                f"Document {i+1}:\n{doc.get('content', '')[:300]}"
                for i, doc in enumerate(documents[:3])
            ]
        )

        prompt = f"""Assess the quality of the generated response.

Query: {query}

Response: {response}

Source Documents:
{docs_text}

Evaluate:
1. SUPPORT: Is the response supported by the documents?
   - fully_supported: All claims are backed by documents
   - partially_supported: Some claims are backed
   - not_supported: Claims are not in documents

2. USEFULNESS: Does the response answer the query?
   - very_useful: Directly and completely answers
   - useful: Answers the query adequately
   - somewhat_useful: Partially answers
   - not_useful: Doesn't answer the query

Provide assessment:
SUPPORT: [score]
USEFULNESS: [score]
CONFIDENCE: [0.0-1.0]
REASONING: [brief explanation]
REGENERATE: [yes/no]"""

        try:
            assessment = await self.llm_manager.generate(
                prompt=prompt, max_tokens=250, temperature=0.1
            )

            # Parse response
            lines = assessment.strip().split("\n")
            support_str = "partially_supported"
            usefulness_str = "useful"
            confidence = 0.7
            reasoning = "Assessment completed"
            regenerate = False

            for line in lines:
                if line.startswith("SUPPORT:"):
                    support_str = line.split(":", 1)[1].strip().lower()
                elif line.startswith("USEFULNESS:"):
                    usefulness_str = line.split(":", 1)[1].strip().lower()
                elif line.startswith("CONFIDENCE:"):
                    try:
                        confidence = float(line.split(":", 1)[1].strip())
                    except:
                        pass
                elif line.startswith("REASONING:"):
                    reasoning = line.split(":", 1)[1].strip()
                elif line.startswith("REGENERATE:"):
                    regenerate = "yes" in line.lower()

            # Map to enums
            support_map = {
                "fully_supported": SupportScore.FULLY_SUPPORTED,
                "partially_supported": SupportScore.PARTIALLY_SUPPORTED,
                "not_supported": SupportScore.NOT_SUPPORTED,
            }
            support = support_map.get(support_str, SupportScore.PARTIALLY_SUPPORTED)

            usefulness_map = {
                "very_useful": UsefulnessScore.VERY_USEFUL,
                "useful": UsefulnessScore.USEFUL,
                "somewhat_useful": UsefulnessScore.SOMEWHAT_USEFUL,
                "not_useful": UsefulnessScore.NOT_USEFUL,
            }
            usefulness = usefulness_map.get(usefulness_str, UsefulnessScore.USEFUL)

            # Decide if regeneration needed
            should_regenerate = (
                regenerate
                or confidence < self.support_threshold
                or support == SupportScore.NOT_SUPPORTED
                or usefulness == UsefulnessScore.NOT_USEFUL
            )

            return GenerationAssessment(
                support=support,
                usefulness=usefulness,
                confidence=confidence,
                reasoning=reasoning,
                should_regenerate=should_regenerate,
            )

        except Exception as e:
            logger.error(f"Error assessing generation quality: {e}")
            return GenerationAssessment(
                support=SupportScore.PARTIALLY_SUPPORTED,
                usefulness=UsefulnessScore.USEFUL,
                confidence=0.5,
                reasoning=f"Assessment failed: {str(e)}",
                should_regenerate=False,
            )

    async def generate_with_reflection(
        self, query: str, retrieve_fn, generate_fn, initial_top_k: int = 5
    ) -> SelfRAGResult:
        """
        Generate response with self-reflection and iterative refinement.

        Args:
            query: User query
            retrieve_fn: Async function to retrieve documents
            generate_fn: Async function to generate response
            initial_top_k: Initial number of documents to retrieve

        Returns:
            SelfRAGResult with final response and assessments
        """
        iteration = 0
        top_k = initial_top_k
        documents = []
        response = ""
        retrieval_assessment = None
        generation_assessment = None

        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"Self-RAG iteration {iteration}/{self.max_iterations}")

            # Retrieve documents
            documents = await retrieve_fn(query, top_k)

            # Assess retrieval
            retrieval_assessment = await self.assess_retrieval_relevance(
                query, documents
            )

            logger.info(
                f"Retrieval assessment: {retrieval_assessment.relevance.value}, "
                f"confidence: {retrieval_assessment.confidence:.2f}"
            )

            # If retrieval is poor and we can iterate, try with more documents
            if (
                retrieval_assessment.should_retrieve_more
                and iteration < self.max_iterations
            ):
                top_k = min(top_k + 5, 20)  # Increase top_k
                logger.info(f"Retrieving more documents (top_k={top_k})")
                continue

            # Generate response
            response = await generate_fn(query, documents)

            # Assess generation
            generation_assessment = await self.assess_generation_quality(
                query, response, documents
            )

            logger.info(
                f"Generation assessment: support={generation_assessment.support.value}, "
                f"usefulness={generation_assessment.usefulness.value}, "
                f"confidence: {generation_assessment.confidence:.2f}"
            )

            # If generation is good enough, stop
            if not generation_assessment.should_regenerate:
                break

            # Otherwise, continue iterating
            logger.info("Regenerating response...")

        # Calculate final confidence
        final_confidence = (
            retrieval_assessment.confidence * 0.4
            + generation_assessment.confidence * 0.6
        )

        return SelfRAGResult(
            response=response,
            retrieval_assessment=retrieval_assessment,
            generation_assessment=generation_assessment,
            iterations=iteration,
            final_confidence=final_confidence,
        )


# Global Self-RAG instance
_self_rag: Optional[SelfRAG] = None


def get_self_rag(llm_manager) -> SelfRAG:
    """Get global Self-RAG instance"""
    global _self_rag
    if _self_rag is None:
        _self_rag = SelfRAG(llm_manager)
    return _self_rag
