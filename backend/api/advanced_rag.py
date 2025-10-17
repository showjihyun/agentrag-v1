# Advanced RAG API Endpoints
from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from pydantic import BaseModel, Field

from backend.core.dependencies import get_llm_manager
from backend.core.auth_dependencies import get_optional_user
from backend.db.models.user import User
from backend.services.query_analyzer import get_query_analyzer

router = APIRouter(prefix="/api/advanced-rag", tags=["advanced-rag"])


class SelfRAGRequest(BaseModel):
    """Self-RAG request"""

    query: str = Field(..., description="User query")
    max_iterations: int = Field(3, description="Maximum reflection iterations")
    top_k: int = Field(10, description="Number of documents to retrieve")


class SelfRAGResponse(BaseModel):
    """Self-RAG response"""

    response: str
    retrieval_quality: str
    generation_quality: str
    iterations: int
    confidence: float
    reasoning: str


class CorrectiveRAGRequest(BaseModel):
    """Corrective RAG request"""

    query: str = Field(..., description="User query")
    enable_web_search: bool = Field(True, description="Enable web search fallback")
    top_k: int = Field(10, description="Number of documents to retrieve")


class CorrectiveRAGResponse(BaseModel):
    """Corrective RAG response"""

    response: str
    retrieval_quality: str
    corrections_applied: List[str]
    confidence: float
    source_count: int


class AdaptiveRAGRequest(BaseModel):
    """Adaptive RAG request"""

    query: str = Field(..., description="User query")
    fast_mode: bool = Field(False, description="Optimize for speed")
    high_accuracy: bool = Field(False, description="Optimize for accuracy")


class AdaptiveRAGResponse(BaseModel):
    """Adaptive RAG response"""

    response: str
    strategy_used: str
    selection_reasoning: str
    execution_time_ms: float
    confidence: float
    source_count: int


class StrategyRecommendationRequest(BaseModel):
    """Strategy recommendation request"""

    query: str = Field(..., description="User query")


class StrategyRecommendationResponse(BaseModel):
    """Strategy recommendation response"""

    recommended_strategy: str
    confidence: float
    reasoning: str
    query_complexity: str
    query_type: str
    parameters: dict


@router.post("/self-rag", response_model=SelfRAGResponse)
async def self_rag_query(
    request: SelfRAGRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    llm_manager=Depends(get_llm_manager),
):
    """
    Process query using Self-RAG with reflection.

    Self-RAG evaluates retrieval quality and generation quality,
    iteratively refining until satisfactory results are achieved.
    """
    from backend.services.self_rag import get_self_rag
    from backend.services.milvus import get_milvus_manager

    self_rag = get_self_rag(llm_manager)
    milvus_manager = get_milvus_manager()

    # Define retrieval and generation functions
    async def retrieve_fn(query: str, top_k: int):
        results = await milvus_manager.search(query, top_k)
        return [{"content": r.get("text", "")} for r in results]

    async def generate_fn(query: str, documents: List[dict]):
        context = "\n\n".join([doc["content"][:500] for doc in documents[:5]])
        prompt = f"Context:\n{context}\n\nQuery: {query}\n\nAnswer:"
        response = await llm_manager.generate(prompt, max_tokens=500)
        return response

    # Execute Self-RAG
    result = await self_rag.generate_with_reflection(
        query=request.query,
        retrieve_fn=retrieve_fn,
        generate_fn=generate_fn,
        initial_top_k=request.top_k,
    )

    return SelfRAGResponse(
        response=result.response,
        retrieval_quality=result.retrieval_assessment.relevance.value,
        generation_quality=result.generation_assessment.support.value,
        iterations=result.iterations,
        confidence=result.final_confidence,
        reasoning=result.generation_assessment.reasoning,
    )


@router.post("/corrective-rag", response_model=CorrectiveRAGResponse)
async def corrective_rag_query(
    request: CorrectiveRAGRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    llm_manager=Depends(get_llm_manager),
):
    """
    Process query using Corrective RAG with automatic corrections.

    Corrective RAG evaluates retrieval quality and applies corrections
    such as query refinement or web search when needed.
    """
    from backend.services.corrective_rag import get_corrective_rag
    from backend.services.milvus import get_milvus_manager

    web_search_service = None
    if request.enable_web_search:
        try:
            from backend.agents.web_search import WebSearchAgent

            web_search_service = WebSearchAgent()
        except:
            pass

    corrective_rag = get_corrective_rag(llm_manager, web_search_service)
    milvus_manager = get_milvus_manager()

    # Define retrieval and generation functions
    async def retrieve_fn(query: str, top_k: int):
        results = await milvus_manager.search(query, top_k)
        return [{"content": r.get("text", "")} for r in results]

    async def generate_fn(query: str, documents: List[dict]):
        context = "\n\n".join([doc["content"][:500] for doc in documents[:5]])
        prompt = f"Context:\n{context}\n\nQuery: {query}\n\nAnswer:"
        response = await llm_manager.generate(prompt, max_tokens=500)
        return response

    # Execute Corrective RAG
    result = await corrective_rag.generate_with_correction(
        query=request.query,
        retrieve_fn=retrieve_fn,
        generate_fn=generate_fn,
        top_k=request.top_k,
    )

    return CorrectiveRAGResponse(
        response=result.response,
        retrieval_quality=result.evaluation.quality.value,
        corrections_applied=result.corrections_applied,
        confidence=result.final_confidence,
        source_count=len(result.sources),
    )


@router.post("/adaptive-rag", response_model=AdaptiveRAGResponse)
async def adaptive_rag_query(
    request: AdaptiveRAGRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    llm_manager=Depends(get_llm_manager),
):
    """
    Process query using Adaptive RAG with automatic strategy selection.

    Adaptive RAG analyzes the query and automatically selects the best
    RAG strategy (direct, hybrid, self-reflective, corrective, etc.).
    """
    from backend.services.adaptive_rag import get_adaptive_rag
    from backend.services.milvus import get_milvus_manager

    query_analyzer = get_query_analyzer()
    adaptive_rag = get_adaptive_rag(llm_manager, query_analyzer)
    milvus_manager = get_milvus_manager()

    # Define retrieval and generation functions
    async def retrieve_fn(query: str, top_k: int):
        results = await milvus_manager.search(query, top_k)
        return [{"content": r.get("text", "")} for r in results]

    async def generate_fn(query: str, documents: List[dict]):
        context = "\n\n".join([doc["content"][:500] for doc in documents[:5]])
        prompt = f"Context:\n{context}\n\nQuery: {query}\n\nAnswer:"
        response = await llm_manager.generate(prompt, max_tokens=500)
        return response

    # Prepare context
    context = {"fast_mode": request.fast_mode, "high_accuracy": request.high_accuracy}

    # Execute Adaptive RAG
    result = await adaptive_rag.generate(
        query=request.query,
        retrieve_fn=retrieve_fn,
        generate_fn=generate_fn,
        context=context,
    )

    return AdaptiveRAGResponse(
        response=result.response,
        strategy_used=result.strategy_used.value,
        selection_reasoning=result.selection_reasoning,
        execution_time_ms=result.execution_time_ms,
        confidence=result.confidence,
        source_count=len(result.sources),
    )


@router.post("/recommend-strategy", response_model=StrategyRecommendationResponse)
async def recommend_strategy(
    request: StrategyRecommendationRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    llm_manager=Depends(get_llm_manager),
):
    """
    Get strategy recommendation for a query without executing it.

    Useful for understanding which RAG strategy would be used
    and why, before actually processing the query.
    """
    from backend.services.adaptive_rag import get_adaptive_rag

    query_analyzer = get_query_analyzer()
    adaptive_rag = get_adaptive_rag(llm_manager, query_analyzer)

    # Analyze query
    analysis = query_analyzer.analyze(request.query)

    # Get strategy recommendation
    selection = await adaptive_rag.select_strategy(request.query)

    return StrategyRecommendationResponse(
        recommended_strategy=selection.strategy.value,
        confidence=selection.confidence,
        reasoning=selection.reasoning,
        query_complexity=str(analysis.complexity_score),
        query_type=analysis.query_type,
        parameters=selection.parameters,
    )
