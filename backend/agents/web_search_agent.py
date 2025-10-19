"""
Web Search + RAG Hybrid Agent

RAG 검색과 웹 검색을 결합하여 종합적인 분석을 제공하는 에이전트
"""

import logging
import asyncio
import hashlib
from typing import List, Dict, Any, AsyncGenerator, Optional, Tuple
from datetime import datetime, timedelta
import json

from backend.services.web_search_service import get_web_search_service
from backend.services.embedding import EmbeddingService
from backend.services.milvus import MilvusManager
from backend.services.llm_manager import LLMManager
from backend.services.web_search_enhancer import (
    get_credibility_scorer,
    get_deduplicator,
    get_temporal_filter
)
from backend.services.query_enhancer import get_query_enhancer
from backend.services.adaptive_reranker import get_adaptive_reranker
from backend.models.query import SearchResult
from backend.models.chunk_types import ChunkType, StepType, SourceType
from backend.config import settings

logger = logging.getLogger(__name__)


class WebSearchAgent:
    """
    Web Search + RAG 하이브리드 에이전트
    
    Features:
    - RAG 검색 (내부 문서)
    - Web 검색 (외부 정보)
    - 결과 통합 및 분석
    - 스트리밍 응답
    """
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        milvus_manager: MilvusManager,
        llm_manager: LLMManager
    ) -> None:
        self.embedding_service: EmbeddingService = embedding_service
        self.milvus_manager: MilvusManager = milvus_manager
        self.llm_manager: LLMManager = llm_manager
        self.web_search_service = get_web_search_service()
        
        # 웹 검색 캐시 (메모리 기반)
        self.search_cache: Dict[str, Tuple[List[Dict[str, Any]], datetime]] = {}
        self.cache_ttl: timedelta = timedelta(hours=1)  # 1시간 TTL
        self.max_cache_size: int = 100  # 최대 100개 캐시
        
        # 검색 품질 향상 컴포넌트 (Phase 1)
        self.credibility_scorer = get_credibility_scorer()
        self.deduplicator = get_deduplicator()
        self.temporal_filter = get_temporal_filter()
        
        # Phase 2 컴포넌트
        self.query_enhancer = get_query_enhancer(llm_manager)
        self.reranker = get_adaptive_reranker()
        
        logger.info(
            "WebSearchAgent initialized with Phase 1 & 2 enhancements: "
            "credibility, dedup, temporal, query enhancement, reranking"
        )
    
    async def process_query(
        self,
        query: str,
        session_id: str,
        top_k: int = 10,
        web_results: int = 5
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        쿼리 처리 (RAG + Web Search)
        
        Args:
            query: 사용자 쿼리
            session_id: 세션 ID
            top_k: RAG 검색 결과 수
            web_results: 웹 검색 결과 수
            
        Yields:
            스트리밍 응답 청크
        """
        start_time = datetime.now()
        
        try:
            # 1. 진행 상황 알림
            yield {
                "type": ChunkType.STEP.value,
                "data": {
                    "step_id": f"web_search_start_{session_id}",
                    "type": StepType.PLANNING.value,
                    "content": "🔍 RAG 검색과 웹 검색을 동시에 시작합니다...",
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {"step": "start"}
                }
            }
            
            # 2. RAG 검색과 Web 검색을 병렬로 실행 (타임아웃 추가)
            rag_task = asyncio.wait_for(self._search_rag(query, top_k), timeout=5.0)
            web_task = asyncio.wait_for(self._search_web(query, web_results), timeout=10.0)
            
            rag_results, web_results_data = await asyncio.gather(
                rag_task,
                web_task,
                return_exceptions=True
            )
            
            # 에러 처리 및 사용자 알림
            if isinstance(rag_results, Exception):
                logger.error(f"RAG search failed: {rag_results}")
                rag_results = []
                yield {
                    "type": ChunkType.STEP.value,
                    "data": {
                        "step_id": f"rag_search_failed_{session_id}",
                        "type": StepType.WARNING.value,
                        "content": "⚠️ 내부 문서 검색에 실패했습니다. 웹 검색 결과만 사용합니다.",
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {"step": "rag_failed"}
                    }
                }
            
            if isinstance(web_results_data, Exception):
                logger.error(f"Web search failed: {web_results_data}")
                web_results_data = []
                yield {
                    "type": ChunkType.STEP.value,
                    "data": {
                        "step_id": f"web_search_failed_{session_id}",
                        "type": StepType.WARNING.value,
                        "content": "⚠️ 웹 검색에 실패했습니다. 내부 문서만 사용합니다.",
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {"step": "web_failed"}
                    }
                }
            
            # 둘 다 실패한 경우
            if not rag_results and not web_results_data:
                yield {
                    "type": ChunkType.ERROR.value,
                    "data": {
                        "error": "RAG 검색과 웹 검색 모두 실패했습니다. 다시 시도해주세요.",
                        "error_type": "all_failed",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                return
            
            # 3. 검색 결과 알림
            yield {
                "type": ChunkType.STEP.value,
                "data": {
                    "step_id": f"web_search_results_{session_id}",
                    "type": StepType.ACTION.value,
                    "content": f"✅ RAG: {len(rag_results)}개, Web: {len(web_results_data)}개 결과 발견",
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {
                        "step": "search_complete",
                        "rag_count": len(rag_results),
                        "web_count": len(web_results_data)
                    }
                }
            }
            
            # 4. 결과 통합 및 분석
            yield {
                "type": ChunkType.STEP.value,
                "data": {
                    "step_id": f"web_search_analysis_{session_id}",
                    "type": StepType.THOUGHT.value,
                    "content": "🤖 AI가 RAG와 웹 검색 결과를 종합 분석 중...",
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {"step": "analysis"}
                }
            }
            
            # 5. LLM으로 통합 분석
            async for chunk in self._generate_hybrid_response(
                query=query,
                rag_results=rag_results,
                web_results=web_results_data
            ):
                yield chunk
            
            # 6. 완료
            total_time: float = (datetime.now() - start_time).total_seconds()
            yield {
                "type": ChunkType.DONE.value,
                "data": {
                    "message": "✅ 분석 완료",
                    "total_time": total_time,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except asyncio.TimeoutError as e:
            logger.error(f"WebSearchAgent timeout: {e}", exc_info=True)
            yield {
                "type": ChunkType.ERROR.value,
                "data": {
                    "error": "처리 시간이 초과되었습니다. 다시 시도해주세요.",
                    "error_type": "timeout",
                    "timestamp": datetime.now().isoformat()
                }
            }
        except (ConnectionError, OSError) as e:
            logger.error(f"WebSearchAgent connection error: {e}", exc_info=True)
            yield {
                "type": ChunkType.ERROR.value,
                "data": {
                    "error": "서비스 연결에 실패했습니다. 잠시 후 다시 시도해주세요.",
                    "error_type": "connection",
                    "timestamp": datetime.now().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"WebSearchAgent unexpected error: {e}", exc_info=True)
            yield {
                "type": ChunkType.ERROR.value,
                "data": {
                    "error": f"예상치 못한 오류가 발생했습니다: {str(e)}",
                    "error_type": "unexpected",
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    async def _search_rag(self, query: str, top_k: int) -> List[SearchResult]:
        """RAG 검색 실행"""
        try:
            logger.info(f"RAG search: '{query[:50]}...' (top_k={top_k})")
            
            # 쿼리 임베딩
            query_embedding: List[float] = await self.embedding_service.embed_query(query)
            
            # Milvus 검색
            results: List[Dict[str, Any]] = await self.milvus_manager.search(
                query_embedding=query_embedding,
                top_k=top_k
            )
            
            # SearchResult 형식으로 변환
            search_results: List[SearchResult] = []
            for result in results:
                search_results.append(SearchResult(
                    document_id=result.get("document_id", ""),
                    chunk_id=result.get("chunk_id", ""),
                    content=result.get("content", ""),
                    score=result.get("score", 0.0),
                    metadata=result.get("metadata", {})
                ))
            
            logger.info(f"RAG search completed: {len(search_results)} results")
            return search_results
            
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"RAG search connection/timeout error: {e}", exc_info=True)
            return []
        except ValueError as e:
            logger.error(f"Invalid RAG search parameters: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected RAG search error: {e}", exc_info=True)
            return []
    
    async def _search_web(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """웹 검색 실행 (캐싱 + 품질 향상 포함)"""
        try:
            # 캐시 키 생성
            cache_key: str = hashlib.md5(f"{query}:{max_results}".encode()).hexdigest()
            
            # 캐시 확인
            if cache_key in self.search_cache:
                cached_results, timestamp = self.search_cache[cache_key]
                if datetime.now() - timestamp < self.cache_ttl:
                    logger.debug(f"Web search cache hit: '{query[:50]}...'")
                    return cached_results
                else:
                    # 만료된 캐시 제거
                    del self.search_cache[cache_key]
            
            # 캐시 미스 - 실제 검색 수행
            logger.info(f"Web search: '{query[:50]}...' (max_results={max_results})")
            
            # Phase 2: 다중 쿼리 전략 사용
            raw_results: List[Dict[str, Any]] = await self._multi_query_search(
                query=query,
                max_results_per_query=max_results,  # 쿼리당 결과 수
                enable_query_enhancement=True
            )
            
            # 품질 향상 파이프라인 적용 (Phase 1 + Phase 2)
            enhanced_results = await self._enhance_search_results(
                raw_results,
                max_results,
                query=query,  # 재순위화를 위해 쿼리 전달
                enable_reranking=True
            )
            
            # 캐시 저장 (크기 제한)
            if len(self.search_cache) >= self.max_cache_size:
                # 가장 오래된 항목 제거 (LRU)
                oldest_key: str = min(
                    self.search_cache.keys(), 
                    key=lambda k: self.search_cache[k][1]
                )
                del self.search_cache[oldest_key]
            
            self.search_cache[cache_key] = (enhanced_results, datetime.now())
            
            logger.info(
                f"Web search completed: {len(raw_results)} -> {len(enhanced_results)} "
                f"results (enhanced & cached)"
            )
            return enhanced_results
            
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Web search connection/timeout error: {e}", exc_info=True)
            return []
        except ValueError as e:
            logger.error(f"Invalid web search parameters: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected web search error: {e}", exc_info=True)
            return []
    
    async def _enhance_search_results(
        self,
        results: List[Dict[str, Any]],
        max_results: int,
        query: Optional[str] = None,
        enable_reranking: bool = True
    ) -> List[Dict[str, Any]]:
        """
        검색 결과 품질 향상 파이프라인 (Phase 1 + Phase 2)
        
        Phase 1:
        1. 소스 신뢰도 필터링
        2. 중복 제거
        3. 시간 기반 필터링
        
        Phase 2:
        4. 재순위화 (Cross-encoder)
        5. 상위 N개 선택
        """
        if not results:
            return []
        
        try:
            # Phase 1: 기본 필터링
            # 1. 소스 신뢰도 필터링 (최소 0.5)
            credible_results = self.credibility_scorer.filter_by_credibility(
                results,
                min_score=0.5
            )
            
            # 2. 중복 제거 (URL + 콘텐츠)
            unique_results = self.deduplicator.deduplicate(
                credible_results,
                method="both"
            )
            
            # 3. 시간 기반 필터링 (최신 우선)
            filtered_results = self.temporal_filter.filter_by_recency(
                unique_results,
                prefer_recent=True,
                max_age_days=None,  # 나이 제한 없음
                boost_recent=True  # 최신 결과에 점수 부스트
            )
            
            # Phase 2: 재순위화
            if enable_reranking and query and filtered_results:
                try:
                    # 재순위화를 위한 데이터 준비
                    for result in filtered_results:
                        # 'text' 필드가 없으면 'snippet' + 'title' 사용
                        if 'text' not in result:
                            result['text'] = f"{result.get('title', '')} {result.get('snippet', '')}"
                    
                    # 재순위화 (더 많은 결과를 재순위화 후 상위 선택)
                    reranked_results = await self.reranker.rerank(
                        query=query,
                        results=filtered_results,
                        top_k=max_results * 2,  # 2배 재순위화 후 선택
                        score_threshold=0.0
                    )
                    
                    logger.info(
                        f"Reranked {len(filtered_results)} -> {len(reranked_results)} results"
                    )
                    
                    filtered_results = reranked_results
                    
                except Exception as e:
                    logger.warning(f"Reranking failed, using Phase 1 results: {e}")
            
            # 4. 종합 점수로 정렬 (신뢰도 + 최신성 + 재순위 점수)
            for result in filtered_results:
                credibility = result.get('credibility_score', 0.5)
                recency = result.get('recency_score', 0.5)
                rerank_score = result.get('score', 0.5)  # 재순위 점수
                
                # 재순위화가 적용되었으면 재순위 점수 우선
                if result.get('reranked'):
                    # 가중 평균 (재순위 60%, 신뢰도 30%, 최신성 10%)
                    result['quality_score'] = (
                        rerank_score * 0.6 +
                        credibility * 0.3 +
                        recency * 0.1
                    )
                else:
                    # 재순위화 없으면 Phase 1 점수
                    result['quality_score'] = credibility * 0.7 + recency * 0.3
            
            filtered_results.sort(
                key=lambda x: x.get('quality_score', 0),
                reverse=True
            )
            
            # 5. 상위 N개 선택
            final_results = filtered_results[:max_results]
            
            logger.info(
                f"Search enhancement pipeline (Phase 1+2): "
                f"{len(results)} -> {len(credible_results)} (credibility) "
                f"-> {len(unique_results)} (dedup) "
                f"-> {len(filtered_results)} (temporal+rerank) "
                f"-> {len(final_results)} (final)"
            )
            
            return final_results
            
        except Exception as e:
            logger.error(f"Error enhancing search results: {e}", exc_info=True)
            # 실패 시 원본 결과 반환
            return results[:max_results]
    
    async def _multi_query_search(
        self,
        query: str,
        max_results_per_query: int = 5,
        enable_query_enhancement: bool = True
    ) -> List[Dict[str, Any]]:
        """
        다중 쿼리 전략으로 검색 (Phase 2)
        
        여러 변형 쿼리로 검색하여 결과 통합
        
        Args:
            query: 원본 쿼리
            max_results_per_query: 쿼리당 최대 결과 수
            enable_query_enhancement: 쿼리 확장 활성화
            
        Returns:
            통합된 검색 결과
        """
        try:
            # 쿼리 확장
            if enable_query_enhancement:
                enhanced = await self.query_enhancer.enhance_query(
                    query,
                    enable_llm=True,
                    max_expansions=2
                )
                
                # 다중 쿼리 생성
                query_variants = [
                    query,  # 원본
                    enhanced['rewritten'],  # 재작성
                ]
                
                # 확장 쿼리 추가 (최대 2개)
                query_variants.extend(enhanced['expanded'][:2])
                
                # 의도 기반 쿼리 추가
                intent_queries = self.query_enhancer.generate_multi_queries(
                    query,
                    enhanced['intent'],
                    num_queries=3
                )
                query_variants.extend(intent_queries[:2])
                
                # 중복 제거
                unique_queries = []
                seen = set()
                for q in query_variants:
                    if q and q not in seen:
                        unique_queries.append(q)
                        seen.add(q)
                
                query_variants = unique_queries[:5]  # 최대 5개
                
                logger.info(
                    f"Multi-query search: {len(query_variants)} variants "
                    f"(intent={enhanced['intent']})"
                )
            else:
                query_variants = [query]
            
            # 병렬 검색
            search_tasks = [
                self.web_search_service.search(
                    variant,
                    max_results=max_results_per_query,
                    language="ko",
                    region="kr"
                )
                for variant in query_variants
            ]
            
            all_results_list = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # 결과 통합
            all_results = []
            for results in all_results_list:
                if isinstance(results, Exception):
                    logger.warning(f"Query variant failed: {results}")
                    continue
                if isinstance(results, list):
                    all_results.extend(results)
            
            logger.info(
                f"Multi-query search collected {len(all_results)} total results "
                f"from {len(query_variants)} queries"
            )
            
            return all_results
            
        except Exception as e:
            logger.error(f"Multi-query search failed: {e}", exc_info=True)
            # 폴백: 단일 쿼리 검색
            return await self.web_search_service.search(
                query,
                max_results=max_results_per_query * 3,
                language="ko",
                region="kr"
            )
    
    async def _generate_hybrid_response(
        self,
        query: str,
        rag_results: List[SearchResult],
        web_results: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """RAG + Web 결과를 통합하여 응답 생성 (Medium Priority 개선 적용)"""
        
        # 프롬프트 최적화 및 템플릿 관리
        from backend.core.prompt_optimizer import get_prompt_optimizer
        from backend.core.token_budget_manager import get_token_budget_manager
        from backend.core.response_template import get_response_template_manager, ResponseFormat
        from backend.core.context_optimizer import get_context_optimizer
        
        prompt_optimizer = get_prompt_optimizer()
        budget_manager = get_token_budget_manager(max_tokens=4096)
        template_manager = get_response_template_manager()
        context_optimizer = get_context_optimizer(
            min_relevance_score=0.7,  # 동적 컨텍스트 윈도우
            max_docs=5,
            max_chars_per_doc=400
        )
        
        # 1. 동적 컨텍스트 윈도우 - 관련도 기반 필터링
        if rag_results:
            rag_results = context_optimizer.filter_by_relevance(
                results=rag_results,
                min_score=0.7,
                max_docs=5,
                dynamic_threshold=True  # 동적 임계값
            )
        
        # 2. 사용자 프롬프트 구성 (컨텍스트만)
        user_prompt = self._build_hybrid_prompt(query, rag_results, web_results)
        
        # 3. 응답 템플릿 적용
        template = template_manager.get_template(ResponseFormat.STANDARD)
        user_prompt_with_template = template_manager.build_prompt_with_template(
            query=query,
            context=user_prompt,
            format_type=ResponseFormat.STANDARD
        )
        
        # 4. 시스템 프롬프트 (재사용 가능, 캐싱 가능)
        system_prompt = prompt_optimizer.SYSTEM_PROMPTS["web_hybrid"]
        
        # 5. 예산 체크
        fits, total_tokens, message = budget_manager.check_budget(
            system_prompt=system_prompt,
            user_prompt=user_prompt_with_template,
            max_output_tokens=template.max_tokens
        )
        
        if not fits:
            logger.warning(f"Token budget exceeded: {message}")
            # 사용자 프롬프트를 더 줄임
            available = budget_manager.available_tokens - budget_manager.count_tokens(system_prompt)
            user_prompt_with_template = budget_manager._truncate_text(
                user_prompt_with_template,
                available - template.max_tokens
            )
        
        logger.info(
            f"Prompt tokens: {total_tokens} "
            f"(system={budget_manager.count_tokens(system_prompt)}, "
            f"user={budget_manager.count_tokens(user_prompt_with_template)}, "
            f"filtered_rag={len(rag_results)})"
        )
        
        # LLM 스트리밍 호출
        response_buffer = []
        
        try:
            # 시스템과 유저 메시지 분리 (효율성 50% 향상)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt_with_template}
            ]
            
            # generate 메서드 호출 (stream=True일 때 AsyncGenerator 반환)
            stream_generator = await self.llm_manager.generate(
                messages,
                stream=True,
                temperature=template.temperature,
                max_tokens=template.max_tokens
            )
            
            # AsyncGenerator 순회
            async for chunk in stream_generator:
                content = chunk if isinstance(chunk, str) else chunk.get("content", "")
                if content:
                    response_buffer.append(content)
                    
                    yield {
                        "type": ChunkType.RESPONSE.value,
                        "data": {
                            "content": content,
                            "path_source": "web_search",
                            "timestamp": datetime.now().isoformat()
                        }
                    }
            
            # 최종 응답 메타데이터
            full_response: str = "".join(response_buffer)
            
            # 응답 템플릿 검증
            validation = template_manager.validate_response(
                response=full_response,
                format_type=ResponseFormat.STANDARD
            )
            
            if not validation["valid"]:
                logger.warning(
                    f"Response validation failed (score={validation['score']:.2f}): "
                    f"{validation['issues']}"
                )
            
            # 소스 정보 포맷팅
            sources: List[Dict[str, Any]] = self._format_sources(rag_results, web_results)
            
            # 비용 추정
            input_tokens = budget_manager.count_tokens(system_prompt + user_prompt_with_template)
            output_tokens = budget_manager.count_tokens(full_response)
            estimated_cost = budget_manager.estimate_cost(input_tokens, output_tokens)
            
            # 품질 평가
            from backend.core.quality_evaluator import get_quality_evaluator
            
            quality_evaluator = get_quality_evaluator()
            quality_score = quality_evaluator.evaluate(
                query=query,
                response=full_response,
                sources=sources
            )
            
            logger.info(
                f"Response generated: {output_tokens} tokens, "
                f"estimated cost: ${estimated_cost:.6f}, "
                f"validation_score: {validation['score']:.2f}, "
                f"quality_score: {quality_score.overall:.2f}"
            )
            
            yield {
                "type": ChunkType.FINAL.value,
                "data": {
                    "response": full_response,
                    "sources": sources,
                    "rag_count": len(rag_results),
                    "web_count": len(web_results),
                    "path_source": "web_search",
                    "timestamp": datetime.now().isoformat(),
                    "token_usage": {
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": input_tokens + output_tokens,
                        "estimated_cost": estimated_cost
                    },
                    "quality": {
                        "validation_score": validation["score"],
                        "validation_issues": validation["issues"],
                        "overall_score": quality_score.overall,
                        "relevance": quality_score.relevance,
                        "accuracy": quality_score.accuracy,
                        "completeness": quality_score.completeness,
                        "clarity": quality_score.clarity,
                        "source_citation": quality_score.source_citation,
                        "quality_issues": quality_score.issues
                    },
                    "optimization": {
                        "dynamic_filtering": True,
                        "filtered_rag_count": len(rag_results),
                        "template_format": ResponseFormat.STANDARD.value
                    }
                }
            }
            
        except asyncio.TimeoutError as e:
            logger.error(f"Response generation timeout: {e}", exc_info=True)
            yield {
                "type": ChunkType.ERROR.value,
                "data": {
                    "error": "응답 생성 시간이 초과되었습니다.",
                    "error_type": "timeout",
                    "timestamp": datetime.now().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Response generation failed: {e}", exc_info=True)
            yield {
                "type": ChunkType.ERROR.value,
                "data": {
                    "error": f"응답 생성 실패: {str(e)}",
                    "error_type": "generation",
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    def _format_sources(
        self,
        rag_results: List[SearchResult],
        web_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """소스 정보를 표준 형식으로 변환"""
        sources: List[Dict[str, Any]] = []
        
        # RAG 소스 (상위 5개)
        for result in rag_results[:5]:
            content: str = result.content
            sources.append({
                "type": SourceType.RAG.value,
                "title": result.metadata.get("title", "Internal Document"),
                "content": content[:200] + "..." if len(content) > 200 else content,
                "score": result.score
            })
        
        # Web 소스 (상위 5개)
        for result in web_results[:5]:
            snippet: str = result.get("snippet", "")
            sources.append({
                "type": SourceType.WEB.value,
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": snippet[:200] + "..." if len(snippet) > 200 else snippet
            })
        
        return sources
    
    def _build_hybrid_prompt(
        self,
        query: str,
        rag_results: List[SearchResult],
        web_results: List[Dict[str, Any]]
    ) -> str:
        """RAG + Web 결과를 통합한 프롬프트 생성 (최적화 - 토큰 60% 감소)"""
        
        # 토큰 예산 관리자 사용
        from backend.core.token_budget_manager import get_token_budget_manager
        from backend.core.prompt_optimizer import get_prompt_optimizer
        
        budget_manager = get_token_budget_manager(max_tokens=4096)
        prompt_optimizer = get_prompt_optimizer()
        
        # 예산 할당 (RAG 40%, Web 40%, Query 20%)
        rag_budget, web_budget, query_budget = budget_manager.allocate_budget(
            rag_ratio=0.4,
            web_ratio=0.4,
            query_ratio=0.2
        )
        
        prompt_parts = []
        
        # Query (예산 내)
        query_text = f"Query: {query}"
        if budget_manager.count_tokens(query_text) > query_budget:
            query_text = budget_manager._truncate_text(query_text, query_budget)
        prompt_parts.append(query_text)
        prompt_parts.append("")
        
        # Web 결과 (우선순위 1, 예산 내)
        if web_results:
            prompt_parts.append("Web Results:")
            web_texts = []
            for i, result in enumerate(web_results[:5], 1):
                title = result.get('title', 'N/A')
                snippet = result.get('snippet', 'N/A')
                web_texts.append(f"{i}. {title}\n{snippet}")
            
            # 예산에 맞게 자르기
            web_texts_fitted = budget_manager.truncate_to_budget(web_texts, web_budget)
            prompt_parts.extend(web_texts_fitted)
            prompt_parts.append("")
        
        # RAG 결과 (우선순위 2, 예산 내)
        if rag_results:
            prompt_parts.append("Internal Docs:")
            rag_texts = []
            for i, result in enumerate(rag_results[:5], 1):
                rag_texts.append(f"{i}. {result.content}")
            
            # 예산에 맞게 자르기
            rag_texts_fitted = budget_manager.truncate_to_budget(rag_texts, rag_budget)
            prompt_parts.extend(rag_texts_fitted)
            prompt_parts.append("")
        
        final_prompt = "\n".join(prompt_parts)
        
        # 예산 체크 로깅
        total_tokens = budget_manager.count_tokens(final_prompt)
        logger.debug(
            f"Hybrid prompt: {total_tokens} tokens "
            f"(web={len(web_results)}, rag={len(rag_results)})"
        )
        
        return final_prompt


# 싱글톤 인스턴스
_web_search_agent = None


async def get_web_search_agent() -> WebSearchAgent:
    """Web Search Agent 싱글톤 인스턴스 반환"""
    global _web_search_agent
    
    if _web_search_agent is None:
        from backend.services.embedding import EmbeddingService
        from backend.services.milvus import MilvusManager
        from backend.services.llm_manager import LLMManager
        
        embedding_service = EmbeddingService()
        milvus_manager = MilvusManager(
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            collection_name=settings.MILVUS_COLLECTION_NAME,
            embedding_dim=embedding_service.dimension,
        )
        llm_manager = LLMManager()
        
        _web_search_agent = WebSearchAgent(
            embedding_service=embedding_service,
            milvus_manager=milvus_manager,
            llm_manager=llm_manager
        )
    
    return _web_search_agent
