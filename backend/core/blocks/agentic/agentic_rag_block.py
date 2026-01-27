"""
Agentic RAG Block - Advanced Retrieval-Augmented Generation

Implements intelligent RAG with agentic capabilities:
- Query decomposition for complex queries
- Iterative retrieval with quality validation
- Multi-source retrieval (vector, web, local)
- Response synthesis with reflection
- Adaptive retrieval strategy

This is the most advanced RAG implementation combining all agentic patterns.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum

from backend.services.llm_manager import LLMManager
from backend.services.embedding_service import EmbeddingService
from backend.services.milvus import MilvusManager

logger = logging.getLogger(__name__)


class QueryComplexity(str, Enum):
    """Query complexity levels."""
    SIMPLE = "simple"          # Single-hop, factual
    MODERATE = "moderate"      # Multi-hop, requires reasoning
    COMPLEX = "complex"        # Multi-step, requires decomposition


class RetrievalStrategy(str, Enum):
    """Retrieval strategies."""
    VECTOR_ONLY = "vector_only"
    WEB_ONLY = "web_only"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"


class SubQuery:
    """Represents a decomposed sub-query."""
    
    def __init__(self, id: str, query: str, dependencies: List[str] = None):
        self.id = id
        self.query = query
        self.dependencies = dependencies or []
        self.results: List[Dict[str, Any]] = []
        self.completed = False


class AgenticRAGBlock:
    """
    Agentic RAG Block with intelligent retrieval and synthesis.
    
    Features:
    - Automatic query complexity analysis
    - Query decomposition for complex queries
    - Multi-source retrieval (vector DB, web, local data)
    - Iterative retrieval with quality validation
    - Response synthesis with reflection
    - Adaptive strategy selection
    """
    
    def __init__(
        self,
        llm_manager: LLMManager,
        embedding_service: EmbeddingService,
        milvus_manager: MilvusManager,
        enable_query_decomposition: bool = True,
        enable_reflection: bool = True,
        enable_web_search: bool = True,
        max_retrieval_iterations: int = 3,
        relevance_threshold: float = 0.7,
    ):
        """
        Initialize Agentic RAG Block.
        
        Args:
            llm_manager: LLM manager
            embedding_service: Embedding service for vector search
            milvus_manager: Milvus manager for vector DB
            enable_query_decomposition: Enable query decomposition
            enable_reflection: Enable response reflection
            enable_web_search: Enable web search fallback
            max_retrieval_iterations: Max retrieval attempts
            relevance_threshold: Minimum relevance score
        """
        self.llm_manager = llm_manager
        self.embedding_service = embedding_service
        self.milvus_manager = milvus_manager
        self.enable_query_decomposition = enable_query_decomposition
        self.enable_reflection = enable_reflection
        self.enable_web_search = enable_web_search
        self.max_retrieval_iterations = max_retrieval_iterations
        self.relevance_threshold = relevance_threshold

    
    async def execute(
        self,
        query: str,
        context: Dict[str, Any] = None,
        strategy: RetrievalStrategy = RetrievalStrategy.ADAPTIVE,
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """
        Execute Agentic RAG workflow.
        
        Args:
            query: User query
            context: Additional context
            strategy: Retrieval strategy
            top_k: Number of documents to retrieve
            
        Returns:
            Dict containing:
                - answer: Final synthesized answer
                - sources: Retrieved sources
                - query_complexity: Detected complexity
                - sub_queries: Decomposed queries (if applicable)
                - retrieval_iterations: Number of retrieval attempts
                - confidence_score: Answer confidence
                - reflection_applied: Whether reflection was used
        """
        start_time = datetime.utcnow()
        context = context or {}
        
        logger.info(f"Starting Agentic RAG for query: {query}")
        
        # Step 1: Analyze query complexity
        complexity = await self._analyze_query_complexity(query, context)
        logger.info(f"Query complexity: {complexity.value}")
        
        # Step 2: Query decomposition (if complex)
        if complexity == QueryComplexity.COMPLEX and self.enable_query_decomposition:
            sub_queries = await self._decompose_query(query, context)
            logger.info(f"Decomposed into {len(sub_queries)} sub-queries")
        else:
            sub_queries = [SubQuery(id="main", query=query)]
        
        # Step 3: Iterative retrieval for each sub-query
        all_sources = []
        retrieval_iterations = 0
        
        for sub_query in sub_queries:
            sources, iterations = await self._iterative_retrieval(
                sub_query=sub_query,
                strategy=strategy,
                top_k=top_k,
                context=context,
            )
            sub_query.results = sources
            sub_query.completed = True
            all_sources.extend(sources)
            retrieval_iterations += iterations
        
        logger.info(f"Retrieved {len(all_sources)} total sources")
        
        # Step 4: Synthesize answer
        answer = await self._synthesize_answer(
            query=query,
            sub_queries=sub_queries,
            sources=all_sources,
            context=context,
        )
        
        # Step 5: Reflection (if enabled)
        reflection_applied = False
        confidence_score = 0.8
        
        if self.enable_reflection:
            answer, confidence_score, reflection_applied = await self._reflect_on_answer(
                query=query,
                answer=answer,
                sources=all_sources,
                context=context,
            )
        
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        return {
            "answer": answer,
            "sources": all_sources,
            "query_complexity": complexity.value,
            "sub_queries": [
                {
                    "id": sq.id,
                    "query": sq.query,
                    "num_results": len(sq.results),
                }
                for sq in sub_queries
            ],
            "retrieval_iterations": retrieval_iterations,
            "confidence_score": confidence_score,
            "reflection_applied": reflection_applied,
            "execution_time": execution_time,
            "total_sources": len(all_sources),
        }

    
    async def _analyze_query_complexity(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> QueryComplexity:
        """
        Analyze query complexity to determine processing strategy.
        
        Returns:
            QueryComplexity enum value
        """
        analysis_prompt = f"""Analyze the complexity of this query:

Query: {query}

Context: {context}

Classify as:
- SIMPLE: Single fact lookup, straightforward question
- MODERATE: Requires connecting 2-3 pieces of information
- COMPLEX: Multi-step reasoning, requires breaking down into sub-questions

Respond with just one word: SIMPLE, MODERATE, or COMPLEX"""
        
        try:
            response = await self.llm_manager.generate(
                prompt=analysis_prompt,
                temperature=0.1,
            )
            
            complexity_str = response.strip().upper()
            if "COMPLEX" in complexity_str:
                return QueryComplexity.COMPLEX
            elif "MODERATE" in complexity_str:
                return QueryComplexity.MODERATE
            else:
                return QueryComplexity.SIMPLE
                
        except Exception as e:
            logger.error(f"Error analyzing complexity: {e}")
            return QueryComplexity.MODERATE  # Default to moderate
    
    async def _decompose_query(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> List[SubQuery]:
        """
        Decompose complex query into sub-queries.
        
        Returns:
            List of SubQuery objects
        """
        decomposition_prompt = f"""Break down this complex query into simpler sub-queries.

Main Query: {query}

Context: {context}

Generate 2-4 sub-queries that:
1. Can be answered independently
2. Together provide information to answer the main query
3. Are ordered logically (dependencies noted)

Respond in JSON format:
{{
    "sub_queries": [
        {{
            "id": "sq1",
            "query": "...",
            "dependencies": []
        }},
        {{
            "id": "sq2",
            "query": "...",
            "dependencies": ["sq1"]
        }}
    ]
}}"""
        
        try:
            response = await self.llm_manager.generate(
                prompt=decomposition_prompt,
                temperature=0.5,
            )
            
            import json
            data = json.loads(response)
            
            sub_queries = []
            for sq_data in data.get("sub_queries", []):
                sub_query = SubQuery(
                    id=sq_data.get("id", f"sq{len(sub_queries) + 1}"),
                    query=sq_data.get("query", ""),
                    dependencies=sq_data.get("dependencies", []),
                )
                sub_queries.append(sub_query)
            
            return sub_queries if sub_queries else [SubQuery(id="main", query=query)]
            
        except Exception as e:
            logger.error(f"Error decomposing query: {e}", exc_info=True)
            return [SubQuery(id="main", query=query)]

    
    async def _iterative_retrieval(
        self,
        sub_query: SubQuery,
        strategy: RetrievalStrategy,
        top_k: int,
        context: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Perform iterative retrieval with quality validation.
        
        Returns:
            Tuple of (sources, iteration_count)
        """
        iteration = 0
        all_sources = []
        
        while iteration < self.max_retrieval_iterations:
            iteration += 1
            logger.info(f"Retrieval iteration {iteration} for: {sub_query.query}")
            
            # Retrieve from sources based on strategy
            if strategy == RetrievalStrategy.ADAPTIVE:
                sources = await self._adaptive_retrieval(sub_query.query, top_k, context)
            elif strategy == RetrievalStrategy.HYBRID:
                sources = await self._hybrid_retrieval(sub_query.query, top_k, context)
            elif strategy == RetrievalStrategy.VECTOR_ONLY:
                sources = await self._vector_retrieval(sub_query.query, top_k)
            else:  # WEB_ONLY
                sources = await self._web_retrieval(sub_query.query, top_k)
            
            # Validate relevance
            relevant_sources = await self._validate_relevance(
                query=sub_query.query,
                sources=sources,
            )
            
            all_sources.extend(relevant_sources)
            
            # Check if we have enough relevant sources
            if len(relevant_sources) >= top_k * 0.5:  # At least 50% of requested
                logger.info(f"Found {len(relevant_sources)} relevant sources")
                break
            
            # If not enough, reformulate query for next iteration
            if iteration < self.max_retrieval_iterations:
                sub_query.query = await self._reformulate_query(
                    original_query=sub_query.query,
                    retrieved_sources=sources,
                    context=context,
                )
                logger.info(f"Reformulated query: {sub_query.query}")
        
        return all_sources, iteration
    
    async def _adaptive_retrieval(
        self,
        query: str,
        top_k: int,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Adaptive retrieval: intelligently choose best sources.
        """
        # Try vector search first
        vector_sources = await self._vector_retrieval(query, top_k)
        
        # Check if vector search was successful
        if len(vector_sources) >= top_k * 0.7:  # 70% threshold
            return vector_sources
        
        # Fallback to hybrid if vector search insufficient
        logger.info("Vector search insufficient, trying hybrid approach")
        return await self._hybrid_retrieval(query, top_k, context)
    
    async def _hybrid_retrieval(
        self,
        query: str,
        top_k: int,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval: combine vector and web search.
        """
        import asyncio
        
        # Parallel retrieval from multiple sources
        vector_task = self._vector_retrieval(query, top_k // 2)
        web_task = self._web_retrieval(query, top_k // 2) if self.enable_web_search else asyncio.sleep(0)
        
        results = await asyncio.gather(vector_task, web_task, return_exceptions=True)
        
        all_sources = []
        for result in results:
            if isinstance(result, list):
                all_sources.extend(result)
        
        # Deduplicate and rank
        return self._deduplicate_sources(all_sources)[:top_k]
    
    async def _vector_retrieval(
        self,
        query: str,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        Vector-based retrieval from Milvus.
        """
        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.embed_text(query)
            
            # Search in Milvus
            results = await self.milvus_manager.search(
                collection_name="documents",
                query_vector=query_embedding,
                top_k=top_k,
                output_fields=["content", "metadata", "source"],
            )
            
            sources = []
            for result in results:
                sources.append({
                    "content": result.get("content", ""),
                    "metadata": result.get("metadata", {}),
                    "source": result.get("source", "vector_db"),
                    "score": result.get("distance", 0.0),
                    "type": "vector",
                })
            
            return sources
            
        except Exception as e:
            logger.error(f"Vector retrieval error: {e}", exc_info=True)
            return []
    
    async def _web_retrieval(
        self,
        query: str,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        Web search retrieval.
        """
        try:
            from duckduckgo_search import DDGS
            
            ddgs = DDGS()
            results = ddgs.text(query, max_results=top_k)
            
            sources = []
            for result in results:
                sources.append({
                    "content": result.get("body", ""),
                    "metadata": {
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                    },
                    "source": "web",
                    "score": 0.8,  # Default score for web results
                    "type": "web",
                })
            
            return sources
            
        except Exception as e:
            logger.error(f"Web retrieval error: {e}", exc_info=True)
            return []

    
    async def _validate_relevance(
        self,
        query: str,
        sources: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Validate relevance of retrieved sources using LLM.
        
        Returns:
            List of relevant sources with relevance scores
        """
        if not sources:
            return []
        
        relevant_sources = []
        
        for source in sources:
            relevance_prompt = f"""Evaluate the relevance of this source to the query.

Query: {query}

Source Content: {source.get('content', '')[:500]}...

Rate relevance from 0.0 (not relevant) to 1.0 (highly relevant).
Respond with just a number between 0.0 and 1.0."""
            
            try:
                response = await self.llm_manager.generate(
                    prompt=relevance_prompt,
                    temperature=0.1,
                )
                
                relevance_score = float(response.strip())
                
                if relevance_score >= self.relevance_threshold:
                    source["relevance_score"] = relevance_score
                    relevant_sources.append(source)
                    
            except Exception as e:
                logger.warning(f"Error validating relevance: {e}")
                # Include source with default score if validation fails
                source["relevance_score"] = 0.7
                relevant_sources.append(source)
        
        # Sort by relevance score
        relevant_sources.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return relevant_sources
    
    async def _reformulate_query(
        self,
        original_query: str,
        retrieved_sources: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> str:
        """
        Reformulate query based on retrieval results.
        """
        reformulation_prompt = f"""The initial query didn't retrieve enough relevant results.
Reformulate the query to improve retrieval.

Original Query: {original_query}

Retrieved {len(retrieved_sources)} sources, but need more relevant ones.

Context: {context}

Generate a reformulated query that:
1. Uses different keywords or phrasing
2. Is more specific or more general as needed
3. Targets the core information need

Respond with just the reformulated query, nothing else."""
        
        try:
            reformulated = await self.llm_manager.generate(
                prompt=reformulation_prompt,
                temperature=0.7,
            )
            return reformulated.strip()
        except Exception as e:
            logger.error(f"Error reformulating query: {e}")
            return original_query
    
    async def _synthesize_answer(
        self,
        query: str,
        sub_queries: List[SubQuery],
        sources: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> str:
        """
        Synthesize final answer from all retrieved sources.
        """
        # Prepare source context
        source_context = self._format_sources(sources)
        
        # Prepare sub-query results
        sub_query_context = ""
        if len(sub_queries) > 1:
            sub_query_context = "\n\nSub-query Results:\n"
            for sq in sub_queries:
                sub_query_context += f"\nQ: {sq.query}\n"
                sub_query_context += f"Found {len(sq.results)} relevant sources\n"
        
        synthesis_prompt = f"""Synthesize a comprehensive answer based on the retrieved information.

Main Query: {query}
{sub_query_context}

Retrieved Sources:
{source_context}

Additional Context: {context}

Instructions:
1. Provide a clear, accurate answer to the query
2. Synthesize information from multiple sources
3. Cite sources when making specific claims
4. If information is insufficient, acknowledge limitations
5. Be concise but comprehensive

Generate the answer:"""
        
        try:
            answer = await self.llm_manager.generate(
                prompt=synthesis_prompt,
                temperature=0.5,
            )
            return answer.strip()
        except Exception as e:
            logger.error(f"Error synthesizing answer: {e}", exc_info=True)
            return "I apologize, but I encountered an error while synthesizing the answer."
    
    async def _reflect_on_answer(
        self,
        query: str,
        answer: str,
        sources: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Tuple[str, float, bool]:
        """
        Reflect on answer quality and improve if needed.
        
        Returns:
            Tuple of (improved_answer, confidence_score, was_improved)
        """
        reflection_prompt = f"""Evaluate this answer for quality and accuracy.

Query: {query}

Answer: {answer}

Available Sources: {len(sources)} sources

Evaluate:
1. Accuracy: Does it correctly answer the query?
2. Completeness: Does it address all aspects?
3. Source Support: Is it well-supported by sources?
4. Clarity: Is it clear and well-structured?

Provide:
- Confidence Score (0.0-1.0)
- Issues (if any)
- Improved Answer (if needed)

Respond in JSON:
{{
    "confidence_score": 0.85,
    "issues": ["issue1", "issue2"],
    "needs_improvement": true/false,
    "improved_answer": "..." (only if needs_improvement is true)
}}"""
        
        try:
            response = await self.llm_manager.generate(
                prompt=reflection_prompt,
                temperature=0.3,
            )
            
            import json
            reflection = json.loads(response)
            
            confidence_score = reflection.get("confidence_score", 0.8)
            needs_improvement = reflection.get("needs_improvement", False)
            
            if needs_improvement and "improved_answer" in reflection:
                improved_answer = reflection["improved_answer"]
                logger.info("Answer improved through reflection")
                return improved_answer, confidence_score, True
            else:
                return answer, confidence_score, False
                
        except Exception as e:
            logger.error(f"Error in reflection: {e}", exc_info=True)
            return answer, 0.8, False
    
    def _format_sources(self, sources: List[Dict[str, Any]]) -> str:
        """Format sources for prompt context."""
        formatted = []
        for i, source in enumerate(sources[:10], 1):  # Limit to top 10
            content = source.get("content", "")[:300]  # Truncate long content
            source_type = source.get("type", "unknown")
            score = source.get("relevance_score", source.get("score", 0))
            
            formatted.append(
                f"[Source {i}] ({source_type}, relevance: {score:.2f})\n{content}..."
            )
        
        return "\n\n".join(formatted)
    
    def _deduplicate_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate sources based on content similarity."""
        if not sources:
            return []
        
        unique_sources = []
        seen_contents = set()
        
        for source in sources:
            content = source.get("content", "")
            # Simple deduplication based on first 100 chars
            content_hash = content[:100].strip().lower()
            
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_sources.append(source)
        
        return unique_sources
