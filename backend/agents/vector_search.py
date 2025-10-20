"""
Vector Search Agent for performing similarity search via MCP Vector Server.

This agent specializes in vector similarity search operations with advanced features:
- Hybrid search (vector + keyword)
- Query expansion (HyDE)
- Result reranking
- Caching
"""

import logging
from typing import List, Optional, Dict, Any

from backend.mcp.manager import MCPServerManager
from backend.models.query import SearchResult

logger = logging.getLogger(__name__)


class VectorSearchAgent:
    """
    Advanced Vector Search Agent with hybrid search and optimization.

    Features:
    - Hybrid search (vector + BM25 keyword)
    - Query expansion (HyDE, multi-query)
    - Cross-encoder reranking
    - Multi-level caching (L1/L2)
    - Result diversity (MMR)
    """

    def __init__(
        self,
        mcp_manager: MCPServerManager = None,
        hybrid_search_manager=None,
        query_expansion_service=None,
        reranker_service=None,
        cache_manager=None,
        server_name: str = "vector_server",
        enable_cross_encoder: bool = True,
        milvus_manager=None,
        embedding_service=None,
        colpali_processor=None,
        colpali_milvus=None,
        enable_colpali_search: bool = True,
        structured_data_service=None,
        enable_table_search: bool = True,
    ):
        """
        Initialize the Vector Search Agent.

        Args:
            mcp_manager: MCPServerManager instance (optional, can use direct Milvus)
            hybrid_search_manager: HybridSearchManager for hybrid search
            query_expansion_service: QueryExpansionService for query expansion
            reranker_service: RerankerService for result reranking
            cache_manager: SearchCacheManager for caching
            server_name: Name of the MCP vector server
            enable_cross_encoder: Enable cross-encoder reranking
            milvus_manager: Direct MilvusManager for fallback (optional)
            embedding_service: EmbeddingService for direct search (optional)
            colpali_processor: ColPaliProcessor for image search (optional)
            colpali_milvus: ColPaliMilvusService for image search (optional)
            enable_colpali_search: Enable ColPali image search
            structured_data_service: StructuredDataService for table search (optional)
            enable_table_search: Enable table search
        """
        self.mcp = mcp_manager
        self.hybrid_search = hybrid_search_manager
        self.query_expansion = query_expansion_service
        self.reranker = reranker_service
        self.cache = cache_manager
        self.server_name = server_name
        
        # Direct Milvus fallback
        self.milvus_manager = milvus_manager
        self.embedding_service = embedding_service
        self.use_direct_milvus = milvus_manager is not None and embedding_service is not None
        
        # ColPali image search
        self.colpali_processor = colpali_processor
        self.colpali_milvus = colpali_milvus
        self.enable_colpali_search = enable_colpali_search and colpali_processor is not None and colpali_milvus is not None
        
        # Structured data (table) search
        self.structured_data_service = structured_data_service
        self.enable_table_search = enable_table_search and structured_data_service is not None

        # Initialize adaptive reranker if enabled (replaces cross-encoder)
        self.adaptive_reranker = None
        self.cross_encoder = None  # Keep for backward compatibility
        
        if enable_cross_encoder:
            try:
                from backend.services.adaptive_reranker import get_adaptive_reranker
                self.adaptive_reranker = get_adaptive_reranker()
                self.cross_encoder = self.adaptive_reranker  # Backward compatibility
                logger.info("Adaptive reranker initialized (auto-selects best model)")
            except Exception as e:
                logger.warning(f"Failed to initialize adaptive reranker: {e}")
                # Fallback to regular cross-encoder
                try:
                    from backend.services.cross_encoder_reranker import get_cross_encoder_reranker
                    self.cross_encoder = get_cross_encoder_reranker()
                    logger.info("Cross-encoder reranker initialized (fallback)")
                except Exception as e2:
                    logger.warning(f"Failed to initialize cross-encoder fallback: {e2}")

        # Feature flags
        self.use_hybrid = hybrid_search_manager is not None
        self.use_expansion = query_expansion_service is not None
        self.use_reranking = reranker_service is not None
        self.use_caching = cache_manager is not None
        self.use_cross_encoder = self.cross_encoder is not None
        self.use_colpali = self.enable_colpali_search

        logger.info(
            f"VectorSearchAgent initialized: "
            f"hybrid={self.use_hybrid}, expansion={self.use_expansion}, "
            f"reranking={self.use_reranking}, caching={self.use_caching}, "
            f"cross_encoder={self.use_cross_encoder}, colpali={self.use_colpali}"
        )

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        search_mode: str = "hybrid",
        use_expansion: bool = False,
        use_reranking: bool = False,
        expansion_method: str = "hyde",
        rerank_method: str = "cross_encoder",
    ) -> List[Dict[str, Any]]:
        """
        Advanced search with hybrid search, expansion, and reranking.

        Args:
            query: Search query
            top_k: Number of results
            filters: Optional filters
            search_mode: "hybrid", "vector_only", or "keyword_only"
            use_expansion: Enable query expansion
            use_reranking: Enable result reranking
            expansion_method: "hyde", "multi", or "semantic"
            rerank_method: "cross_encoder", "mmr", or "hybrid"

        Returns:
            List of search results with scores
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if top_k < 1 or top_k > 100:
            raise ValueError("top_k must be between 1 and 100")

        # Track search start time
        import time

        start_time = time.time()

        try:
            # 1. Check cache first
            if self.use_caching:
                cached_results = await self.cache.get_cached_results(
                    query, top_k, filters, search_mode
                )
                if cached_results:
                    logger.info(f"Cache hit for query: {query[:50]}...")
                    return cached_results

            # 2. Query expansion (optional)
            queries = [query]
            if use_expansion and self.use_expansion:
                queries = await self.query_expansion.expand_query(
                    query, method=expansion_method
                )
                logger.info(f"Query expanded to {len(queries)} variations")

            # 3. Perform search (Text + Image + Tables)
            text_results = []
            image_results = []
            table_results = []
            
            # 3a. Text search
            if self.use_hybrid and search_mode != "vector_only":
                # Hybrid search
                text_results = await self._hybrid_search(
                    queries, top_k, filters, search_mode
                )
            else:
                # Vector-only search
                text_results = await self._vector_search(queries, top_k, filters)
            
            # 3b. Image search (ColPali)
            if self.use_colpali:
                try:
                    image_results = await self._colpali_search(query, top_k, filters)
                    logger.info(f"ColPali search returned {len(image_results)} results")
                except Exception as e:
                    logger.warning(f"ColPali search failed: {e}")
            
            # 3c. Table search (Structured data)
            if self.enable_table_search:
                try:
                    table_results = await self._table_search(query, top_k, filters)
                    logger.info(f"Table search returned {len(table_results)} results")
                except Exception as e:
                    logger.warning(f"Table search failed: {e}")
            
            # 3d. Merge text, image, and table results
            results = self._merge_multimodal_results(
                text_results, image_results, top_k, table_results
            )

            # 4. Reranking (optional)
            if use_reranking and results:
                # Try cross-encoder first (best quality)
                if self.use_cross_encoder and rerank_method == "cross_encoder":
                    try:
                        results = await self.cross_encoder.rerank(
                            query=query,
                            results=results,
                            top_k=top_k,
                            score_threshold=0.0
                        )
                        logger.info(f"Results reranked using cross-encoder")
                    except Exception as e:
                        logger.warning(f"Cross-encoder reranking failed: {e}")
                        # Fallback to original reranker
                        if self.use_reranking:
                            results = self.reranker.rerank(
                                query, results, top_k, method=rerank_method
                            )
                            logger.info(f"Results reranked using fallback {rerank_method}")
                # Use original reranker
                elif self.use_reranking:
                    results = self.reranker.rerank(
                        query, results, top_k, method=rerank_method
                    )
                    logger.info(f"Results reranked using {rerank_method}")

            # 5. Cache results
            if self.use_caching:
                await self.cache.cache_results(
                    query, top_k, filters, search_mode, results
                )

            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000

            logger.info(
                f"Search completed: {len(results)} results "
                f"(mode={search_mode}, expansion={use_expansion}, "
                f"reranking={use_reranking}, latency={latency_ms:.2f}ms)"
            )

            # Track search quality
            try:
                from backend.services.search_quality_monitor import get_quality_monitor

                quality_monitor = get_quality_monitor()
                await quality_monitor.track_search(
                    query=query,
                    results=results[:top_k],
                    search_mode=search_mode,
                    latency_ms=latency_ms,
                )
            except Exception as e:
                logger.debug(f"Failed to track search quality: {e}")

            return results[:top_k]

        except ValueError:
            raise
        except Exception as e:
            error_msg = f"Search failed for query '{query[:50]}...': {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def _hybrid_search(
        self,
        queries: List[str],
        top_k: int,
        filters: Optional[Dict[str, Any]],
        search_mode: str,
    ) -> List[Dict[str, Any]]:
        """하이브리드 검색 수행"""
        # Check if MCP is available, otherwise use direct Milvus
        use_mcp = self.mcp is not None and self.mcp.is_connected(self.server_name)
        
        if not use_mcp and not self.use_direct_milvus:
            logger.warning(f"MCP server '{self.server_name}' not available and no direct Milvus fallback configured")
            # Fall back to vector-only search
            return await self._vector_search(queries, top_k, filters)
        
        all_results = []

        for query in queries:
            # Define vector search function for HybridSearchService
            async def vector_search_fn(q: str, k: int) -> List[tuple]:
                if use_mcp:
                    # Use MCP for vector search
                    arguments = {"query": q, "top_k": k}
                    if filters:
                        arguments["filters"] = filters

                    result = await self.mcp.call_tool(
                        server_name=self.server_name,
                        tool_name="vector_search",
                        arguments=arguments,
                    )

                    # Parse and convert to (doc_id, score) tuples
                    search_results = self._parse_results(result)
                    return [
                        (r.get("chunk_id") or r.get("id"), r.get("score", 0.0))
                        for r in search_results
                    ]
                else:
                    # Use direct Milvus for vector search
                    query_embedding = await self.embedding_service.embed_text(q)
                    search_results = await self.milvus_manager.search(
                        query_embedding=query_embedding,
                        top_k=k,
                        filters=filters
                    )
                    return [
                        (r.get("chunk_id") or r.get("id"), r.get("score", 0.0))
                        for r in search_results
                    ]

            # Define BM25 search function for HybridSearchService
            async def bm25_search_fn(q: str, k: int) -> List[tuple]:
                # BM25 search requires indexed documents
                # For now, return empty list as BM25 index may not be ready
                try:
                    from backend.services.bm25_search import get_bm25_service

                    bm25_service = get_bm25_service()
                    return await bm25_service.search(q, k)
                except Exception as e:
                    logger.debug(f"BM25 search not available: {e}")
                    return []

            # Perform hybrid search
            try:
                hybrid_results = await self.hybrid_search.search(
                    query=query,
                    vector_search_fn=vector_search_fn,
                    bm25_search_fn=bm25_search_fn,
                    top_k=top_k * 2,
                    fusion_method="rrf",
                )

                # Convert HybridSearchService results to our format
                for result in hybrid_results:
                    all_results.append(
                        {
                            "id": result.doc_id,
                            "chunk_id": result.doc_id,
                            "score": result.score,
                            "combined_score": result.score,
                            "source": result.source,
                            "text": result.content,
                            "metadata": result.metadata or {},
                        }
                    )

            except Exception as e:
                logger.warning(
                    f"Hybrid search failed, falling back to vector-only: {e}"
                )
                # Fall back to vector-only search
                results = await self._vector_search([query], top_k * 2, filters)
                all_results.extend(results)

        # Deduplicate and merge scores
        return self._merge_results(all_results, top_k)

    async def _vector_search(
        self, queries: List[str], top_k: int, filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """벡터 검색 수행 (MCP 또는 직접 Milvus)"""
        
        # Try MCP first if available and connected
        if self.mcp is not None and self.mcp.is_connected(self.server_name):
            try:
                all_results = []
                for query in queries:
                    # Prepare arguments for MCP tool call
                    arguments = {"query": query, "top_k": top_k * 2}
                    if filters:
                        arguments["filters"] = filters

                    # Call MCP vector search
                    result = await self.mcp.call_tool(
                        server_name=self.server_name,
                        tool_name="vector_search",
                        arguments=arguments,
                    )

                    # Parse results
                    search_results = self._parse_results(result)
                    all_results.extend(search_results)

                # Merge and deduplicate
                return self._merge_results(all_results, top_k)
                
            except Exception as e:
                logger.warning(f"MCP search failed: {e}, falling back to direct Milvus")
                # Fall through to direct Milvus
        
        # Fallback to direct Milvus search
        if self.use_direct_milvus:
            logger.info("Using direct Milvus search (MCP not available)")
            return await self._direct_milvus_search(queries, top_k, filters)
        else:
            raise RuntimeError(
                f"MCP server '{self.server_name}' is not available and no direct Milvus fallback configured"
            )
    
    async def _direct_milvus_search(
        self, queries: List[str], top_k: int, filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """직접 Milvus를 사용한 벡터 검색"""
        all_results = []
        
        for query in queries:
            try:
                # Generate query embedding
                query_embedding = await self.embedding_service.embed_text(query)
                
                # Search in Milvus
                search_results = await self.milvus_manager.search(
                    query_embedding=query_embedding,
                    top_k=top_k * 2,
                    filters=filters
                )
                
                # Convert to standard format
                for result in search_results:
                    # Handle both dict and SearchResult object
                    if isinstance(result, dict):
                        all_results.append({
                            "id": result.get("chunk_id", result.get("id", "")),
                            "chunk_id": result.get("chunk_id", ""),
                            "document_id": result.get("document_id", ""),
                            "document_name": result.get("document_name", "Unknown"),
                            "text": result.get("text", ""),
                            "score": result.get("score", 0.0),
                            "metadata": result.get("metadata", {})
                        })
                    else:
                        # Handle Milvus SearchResult object
                        all_results.append({
                            "id": getattr(result, "chunk_id", getattr(result, "id", "")),
                            "chunk_id": getattr(result, "chunk_id", ""),
                            "document_id": getattr(result, "document_id", ""),
                            "document_name": getattr(result, "document_name", "Unknown"),
                            "text": getattr(result, "text", ""),
                            "score": getattr(result, "score", getattr(result, "distance", 0.0)),
                            "metadata": getattr(result, "metadata", {})
                        })
                    
            except Exception as e:
                logger.error(f"Direct Milvus search failed for query '{query}': {e}")
                continue
        
        # Merge and deduplicate
        return self._merge_results(all_results, top_k)

    async def _colpali_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        ColPali 이미지 검색 with caching and user isolation
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 수
            filters: 필터 (user_id 포함)
        
        Returns:
            이미지 검색 결과
        """
        try:
            # Extract user_id for isolation
            user_id = filters.get("user_id") if filters else None
            
            # Check cache
            cache_key = f"colpali:{query}:{top_k}:{user_id}:{filters.get('document_id') if filters else None}"
            
            if self.cache:
                try:
                    cached_results = await self.cache.get_cached_results(cache_key)
                    if cached_results:
                        logger.info(f"✅ ColPali cache hit for query: {query[:50]}...")
                        return cached_results
                except Exception as e:
                    logger.debug(f"Cache check failed: {e}")
            
            # 1. 쿼리를 ColPali 임베딩으로 변환
            query_embeddings = self.colpali_processor.process_text_query(query)
            
            # 2. ColPali Milvus에서 검색 (user isolation)
            filter_expr = None
            if filters and filters.get("document_id"):
                filter_expr = f'document_id == "{filters["document_id"]}"'
            
            image_results = self.colpali_milvus.search_images(
                query_embeddings=query_embeddings,
                top_k=top_k,
                filter_expr=filter_expr,
                user_id=user_id  # NEW: User isolation
            )
            
            # 3. 결과를 표준 형식으로 변환
            formatted_results = []
            for result in image_results:
                formatted_results.append({
                    "id": result.get("image_id"),
                    "chunk_id": result.get("image_id"),
                    "document_id": result.get("document_id"),
                    "document_name": result.get("metadata", {}).get("file_name", "Image Document"),
                    "text": f"[Image content from {result.get('image_path', 'unknown')}]",
                    "score": result.get("score", 0.0),
                    "metadata": {
                        **result.get("metadata", {}),
                        "source_type": "image",
                        "search_method": "colpali",
                        "user_id": result.get("user_id")
                    }
                })
            
            # Cache results
            if self.cache:
                try:
                    await self.cache.cache_results(cache_key, formatted_results, ttl=3600)
                    logger.debug(f"Cached ColPali results for: {query[:50]}...")
                except Exception as e:
                    logger.debug(f"Cache save failed: {e}")
            
            logger.info(f"✅ ColPali search completed: {len(formatted_results)} results (user: {user_id})")
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ ColPali search failed: {e}")
            return []
    
    async def _hybrid_image_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        하이브리드 이미지 검색: Visual (ColPali) + Text (associated_text)
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 수
            filters: 필터
        
        Returns:
            하이브리드 검색 결과
        """
        try:
            user_id = filters.get("user_id") if filters else None
            
            # 1. Visual search (ColPali)
            visual_results = await self._colpali_search(query, top_k * 2, filters)
            
            # 2. Text-based search (associated_text)
            text_results = []
            try:
                text_matches = self.colpali_milvus.search_by_text(
                    text_query=query,
                    top_k=top_k * 2,
                    user_id=user_id
                )
                
                for result in text_matches:
                    text_results.append({
                        "id": result.get("image_id"),
                        "chunk_id": result.get("image_id"),
                        "document_id": result.get("document_id"),
                        "document_name": result.get("metadata", {}).get("file_name", "Image Document"),
                        "text": f"[Image with text: {result.get('associated_text', '')[:200]}...]",
                        "score": result.get("score", 0.0),
                        "metadata": {
                            **result.get("metadata", {}),
                            "source_type": "image",
                            "search_method": "text_match",
                            "page_number": result.get("page_number"),
                            "associated_text": result.get("associated_text", "")
                        }
                    })
                
                logger.info(f"Text-based image search: {len(text_results)} results")
                
            except Exception as e:
                logger.warning(f"Text-based image search failed: {e}")
            
            # 3. Merge visual and text results
            if not text_results:
                return visual_results[:top_k]
            
            if not visual_results:
                return text_results[:top_k]
            
            # Simple RRF merge
            merged = {}
            
            for rank, result in enumerate(visual_results, 1):
                result_id = result.get("id")
                merged[result_id] = {
                    **result,
                    "visual_rank": rank,
                    "combined_score": 1.0 / (60 + rank)
                }
            
            for rank, result in enumerate(text_results, 1):
                result_id = result.get("id")
                if result_id in merged:
                    merged[result_id]["combined_score"] += 1.0 / (60 + rank)
                    merged[result_id]["text_rank"] = rank
                    merged[result_id]["metadata"]["has_text_match"] = True
                else:
                    merged[result_id] = {
                        **result,
                        "text_rank": rank,
                        "combined_score": 1.0 / (60 + rank)
                    }
            
            # Sort by combined score
            final_results = sorted(
                merged.values(),
                key=lambda x: x["combined_score"],
                reverse=True
            )
            
            logger.info(f"✅ Hybrid image search: {len(final_results[:top_k])} results")
            return final_results[:top_k]
            
        except Exception as e:
            logger.error(f"❌ Hybrid image search failed: {e}")
            # Fallback to visual-only search
            return await self._colpali_search(query, top_k, filters)
    
    async def _table_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        표 검색 (구조화된 데이터)
        
        Args:
            query: 검색 쿼리
            top_k: 반환 개수
            filters: 필터 (user_id, document_id 등)
        
        Returns:
            표 검색 결과
        """
        try:
            user_id = filters.get("user_id") if filters else None
            document_id = filters.get("document_id") if filters else None
            
            results = self.structured_data_service.search_tables(
                query=query,
                user_id=user_id,
                document_id=document_id,
                top_k=top_k
            )
            
            # 결과 포맷 변환
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': result['table_id'],
                    'chunk_id': result['table_id'],
                    'document_id': result['document_id'],
                    'text': result['searchable_text'],
                    'score': result['score'],
                    'page_number': result['page_number'],
                    'type': 'table',
                    'metadata': {
                        'caption': result.get('caption', ''),
                        'table_data': result.get('table_data', {}),
                        'bbox': result.get('bbox'),
                        **result.get('metadata', {})
                    }
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Table search failed: {e}")
            return []
    
    def _merge_multimodal_results(
        self,
        text_results: List[Dict[str, Any]],
        image_results: List[Dict[str, Any]],
        top_k: int,
        table_results: Optional[List[Dict[str, Any]]] = None,
        alpha: float = 0.6,  # Text weight
        beta: float = 0.2,   # Image weight
        gamma: float = 0.2   # Table weight
    ) -> List[Dict[str, Any]]:
        """
        텍스트 + 이미지 + 표 검색 결과 병합 with weighted fusion
        
        Args:
            text_results: 텍스트 검색 결과
            image_results: 이미지 검색 결과
            top_k: 반환할 결과 수
            table_results: 표 검색 결과 (선택적)
            alpha: 텍스트 가중치 (기본 0.6)
            beta: 이미지 가중치 (기본 0.2)
            gamma: 표 가중치 (기본 0.2)
        
        Returns:
            병합된 결과
        """
        table_results = table_results or []
        
        # 결과가 하나만 있으면 그것 반환
        if not text_results and not image_results:
            return table_results[:top_k]
        if not text_results and not table_results:
            return image_results[:top_k]
        if not image_results and not table_results:
            return text_results[:top_k]
        # 결과가 없으면 다른 쪽 반환
        if not text_results:
            return image_results[:top_k]
        if not image_results:
            return text_results[:top_k]
        
        # 점수 정규화 (0-1 범위로) - 개선된 버전
        def normalize_scores(results, modality="text"):
            if not results:
                return results
            
            scores = [r.get("score", 0) for r in results]
            max_score = max(scores) if scores else 1.0
            min_score = min(scores) if scores else 0.0
            score_range = max_score - min_score if max_score > min_score else 1.0
            
            for r in results:
                original_score = r.get("score", 0)
                normalized = (original_score - min_score) / score_range if score_range > 0 else 0.5
                r["normalized_score"] = normalized
                r["modality"] = modality
            
            return results
        
        text_results = normalize_scores(text_results, "text")
        image_results = normalize_scores(image_results, "image")
        
        # Weighted RRF (Reciprocal Rank Fusion) 병합
        # 텍스트와 이미지 결과를 가중치 기반으로 병합
        all_results = {}
        
        # 텍스트 결과 추가 (alpha 가중치)
        for rank, result in enumerate(text_results, 1):
            result_id = result.get("id") or result.get("chunk_id")
            rrf_score = 1.0 / (60 + rank)  # RRF 공식
            
            # Weighted score: normalized_score * alpha + rrf * (1-alpha)
            combined_score = result.get("normalized_score", 0.5) * alpha + rrf_score * (1 - alpha)
            
            all_results[result_id] = {
                **result,
                "rrf_score": rrf_score,
                "text_rank": rank,
                "combined_score": combined_score,
                "score_breakdown": {
                    "text_score": result.get("score", 0),
                    "text_normalized": result.get("normalized_score", 0.5),
                    "text_weight": alpha
                }
            }
        
        # 이미지 결과 추가/병합 (1-alpha 가중치)
        for rank, result in enumerate(image_results, 1):
            result_id = result.get("id") or result.get("chunk_id")
            rrf_score = 1.0 / (60 + rank)
            
            # Weighted score for images
            combined_score = result.get("normalized_score", 0.5) * (1 - alpha) + rrf_score * alpha
            
            if result_id in all_results:
                # 이미 있으면 점수 병합 (평균)
                existing = all_results[result_id]
                existing["combined_score"] = (
                    existing["combined_score"] + combined_score
                ) / 2
                existing["image_rank"] = rank
                existing["metadata"]["has_both"] = True
                existing["score_breakdown"]["image_score"] = result.get("score", 0)
                existing["score_breakdown"]["image_normalized"] = result.get("normalized_score", 0.5)
                existing["score_breakdown"]["image_weight"] = 1 - alpha
            else:
                # 새로 추가
                all_results[result_id] = {
                    **result,
                    "rrf_score": rrf_score,
                    "image_rank": rank,
                    "combined_score": combined_score,
                    "score_breakdown": {
                        "image_score": result.get("score", 0),
                        "image_normalized": result.get("normalized_score", 0.5),
                        "image_weight": 1 - alpha
                    }
                }
        
        # 점수로 정렬
        sorted_results = sorted(
            all_results.values(),
            key=lambda x: x.get("combined_score", 0),
            reverse=True
        )
        
        logger.info(
            f"Merged results: {len(text_results)} text + {len(image_results)} image "
            f"→ {len(sorted_results)} total"
        )
        
        return sorted_results[:top_k]
    
    def _merge_results(
        self, results: List[Dict[str, Any]], top_k: int
    ) -> List[Dict[str, Any]]:
        """결과 병합 및 중복 제거"""
        # ID로 그룹화
        merged = {}

        for result in results:
            result_id = result.get("id") or result.get("chunk_id")

            if result_id not in merged:
                merged[result_id] = result
            else:
                # 점수 평균
                existing = merged[result_id]
                existing_score = existing.get(
                    "combined_score", existing.get("score", 0)
                )
                new_score = result.get("combined_score", result.get("score", 0))
                merged[result_id]["combined_score"] = (existing_score + new_score) / 2

        # 점수로 정렬
        sorted_results = sorted(
            merged.values(),
            key=lambda x: x.get("combined_score", x.get("score", 0)),
            reverse=True,
        )

        return sorted_results[:top_k]

    def _parse_results(self, mcp_result: Any) -> List[SearchResult]:
        """
        Parse MCP tool result and convert to SearchResult objects.

        Args:
            mcp_result: Raw result from MCP tool call

        Returns:
            List of SearchResult objects

        Raises:
            ValueError: If result format is invalid
        """
        try:
            # Handle different result formats from MCP
            if hasattr(mcp_result, "content"):
                # MCP returns results in content field
                results_data = mcp_result.content
            elif isinstance(mcp_result, dict):
                results_data = mcp_result.get("results", mcp_result)
            elif isinstance(mcp_result, list):
                results_data = mcp_result
            else:
                results_data = []

            # Convert to list if needed
            if isinstance(results_data, str):
                # If content is a string, try to parse as JSON
                import json

                try:
                    results_data = json.loads(results_data)
                except json.JSONDecodeError:
                    logger.warning(
                        f"Could not parse MCP result as JSON: {results_data[:100]}"
                    )
                    results_data = []

            # Ensure we have a list
            if not isinstance(results_data, list):
                if isinstance(results_data, dict) and "results" in results_data:
                    results_data = results_data["results"]
                else:
                    results_data = [results_data] if results_data else []

            # Convert each result to SearchResult
            search_results = []
            for idx, item in enumerate(results_data):
                try:
                    search_result = self._convert_to_search_result(item, idx)
                    if search_result:
                        search_results.append(search_result)
                except Exception as e:
                    logger.warning(f"Failed to convert result item {idx}: {str(e)}")
                    continue

            return search_results

        except Exception as e:
            logger.error(f"Failed to parse MCP results: {str(e)}")
            # Return empty list rather than failing completely
            return []

    def _convert_to_search_result(
        self, item: Dict[str, Any], index: int
    ) -> Optional[SearchResult]:
        """
        Convert a single result item to SearchResult object.

        Args:
            item: Result item from MCP response
            index: Index of the item in results list

        Returns:
            SearchResult object or None if conversion fails
        """
        try:
            # Handle different field naming conventions
            chunk_id = item.get("chunk_id") or item.get("id") or f"chunk_{index}"
            document_id = item.get("document_id") or item.get("doc_id") or "unknown"
            document_name = (
                item.get("document_name")
                or item.get("filename")
                or item.get("doc_name")
                or f"document_{document_id}"
            )
            text = item.get("text") or item.get("content") or ""
            score = float(item.get("score", 0.0))

            # Extract metadata
            metadata = item.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}

            # Add any additional fields to metadata
            for key, value in item.items():
                if key not in [
                    "chunk_id",
                    "id",
                    "document_id",
                    "doc_id",
                    "document_name",
                    "filename",
                    "text",
                    "content",
                    "score",
                    "metadata",
                ]:
                    metadata[key] = value

            return SearchResult(
                chunk_id=chunk_id,
                document_id=document_id,
                document_name=document_name,
                text=text,
                score=score,
                metadata=metadata,
            )

        except Exception as e:
            logger.warning(
                f"Failed to convert item to SearchResult: {str(e)}, item: {item}"
            )
            return None

    async def health_check(self) -> bool:
        """
        Check if the MCP Vector Server is available and responsive.

        Returns:
            bool: True if server is healthy, False otherwise
        """
        try:
            # Check if server is connected
            if not self.mcp.is_connected(self.server_name):
                logger.warning(f"Vector server '{self.server_name}' is not connected")
                return False

            # Try to list tools to verify server is responsive
            tools = await self.mcp.list_tools(self.server_name)

            # Check if vector_search tool is available
            tool_names = [tool["name"] for tool in tools]
            if "vector_search" not in tool_names:
                logger.warning(
                    f"vector_search tool not found on server '{self.server_name}'"
                )
                return False

            logger.info(f"Vector server '{self.server_name}' is healthy")
            return True

        except Exception as e:
            logger.error(
                f"Health check failed for vector server '{self.server_name}': {str(e)}"
            )
            return False

    def __repr__(self) -> str:
        return f"VectorSearchAgent(server={self.server_name})"
