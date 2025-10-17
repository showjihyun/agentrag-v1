"""
검색 결과 리랭킹 서비스

Cross-encoder와 MMR을 사용하여 검색 결과의 정확도와 다양성을 향상시킵니다.
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)


class RerankerService:
    """
    검색 결과 리랭킹 서비스

    Features:
    - Cross-encoder 리랭킹 (정확도 향상)
    - MMR (Maximal Marginal Relevance) - 다양성 고려
    - LLM 기반 관련성 평가
    """

    def __init__(
        self,
        cross_encoder_model: str = "Dongjin-kr/ko-reranker",
        use_cross_encoder: bool = True,
    ):
        """
        Initialize RerankerService.

        Args:
            cross_encoder_model: Cross-encoder model name
                Default: "Dongjin-kr/ko-reranker" (BEST for Korean)
                - Specifically trained for Korean language
                - Superior Korean text understanding
                - Optimized for Korean RAG systems
                - Highest accuracy for Korean queries
            use_cross_encoder: Whether to use cross-encoder (requires model download)
        """
        self.use_cross_encoder = use_cross_encoder
        self.cross_encoder = None
        self.model_name = cross_encoder_model

        if use_cross_encoder:
            try:
                logger.info(f"Loading cross-encoder model: {cross_encoder_model}")
                logger.info(
                    "Note: ko-reranker is specifically optimized for Korean language"
                )

                # Auto-detect device (GPU if available)
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
                
                self.cross_encoder = CrossEncoder(
                    cross_encoder_model,
                    max_length=512,
                    device=device,  # Use GPU if available
                )
                logger.info(f"Cross-encoder loaded on device: {device}")

                logger.info("Cross-encoder model loaded successfully")
                logger.info(
                    f"Model: {cross_encoder_model} - Korean-specialized reranker"
                )

            except Exception as e:
                logger.warning(f"Failed to load cross-encoder: {e}")
                logger.warning("Falling back to score-based reranking")
                self.use_cross_encoder = False

        logger.info(
            f"RerankerService initialized "
            f"(cross_encoder={'enabled' if self.use_cross_encoder else 'disabled'}, "
            f"model={cross_encoder_model})"
        )

    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        method: str = "cross_encoder",
    ) -> List[Dict[str, Any]]:
        """
        검색 결과 리랭킹

        Args:
            query: 검색 쿼리
            results: 검색 결과 리스트
            top_k: 반환할 결과 개수 (None = 전체)
            method: "cross_encoder", "mmr", or "hybrid"

        Returns:
            리랭킹된 결과 리스트
        """
        if not results:
            return []

        if method == "cross_encoder" and self.use_cross_encoder:
            return self._cross_encoder_rerank(query, results, top_k)
        elif method == "mmr":
            return self._mmr_rerank(query, results, top_k)
        elif method == "hybrid":
            # Cross-encoder로 먼저 리랭킹, 그 다음 MMR로 다양성 추가
            reranked = self._cross_encoder_rerank(
                query, results, top_k * 2 if top_k else None
            )
            return self._mmr_rerank(query, reranked, top_k)
        else:
            # 기본: 원본 점수로 정렬
            return self._score_based_rerank(results, top_k)

    def _cross_encoder_rerank(
        self, query: str, results: List[Dict[str, Any]], top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Cross-encoder를 사용한 리랭킹

        Cross-encoder는 쿼리와 문서를 함께 입력받아
        더 정확한 관련성 점수를 계산합니다.

        장점:
        - Bi-encoder보다 정확함
        - 쿼리-문서 간 상호작용 고려

        단점:
        - 느림 (모든 쌍을 평가)
        - 대규모 검색에는 부적합
        """
        if not self.use_cross_encoder or not self.cross_encoder:
            logger.warning("Cross-encoder not available, using score-based reranking")
            return self._score_based_rerank(results, top_k)

        try:
            # 쿼리-문서 쌍 생성
            pairs = [[query, result.get("text", "")] for result in results]

            # Cross-encoder로 점수 계산
            logger.debug(f"Reranking {len(pairs)} results with cross-encoder")
            scores = self.cross_encoder.predict(pairs)

            # 점수 추가 및 정렬
            for result, score in zip(results, scores):
                result["rerank_score"] = float(score)
                result["original_score"] = result.get(
                    "combined_score", result.get("score", 0.0)
                )

            # 리랭킹 점수로 정렬
            reranked = sorted(results, key=lambda x: x["rerank_score"], reverse=True)

            logger.info(
                f"Cross-encoder reranking completed: "
                f"top score changed from {results[0].get('original_score', 0):.4f} "
                f"to {reranked[0]['rerank_score']:.4f}"
            )

            return reranked[:top_k] if top_k else reranked

        except Exception as e:
            logger.error(f"Cross-encoder reranking failed: {e}")
            return self._score_based_rerank(results, top_k)

    def _mmr_rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        lambda_param: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        MMR (Maximal Marginal Relevance)를 사용한 리랭킹

        MMR은 관련성과 다양성을 모두 고려합니다:
        - 관련성: 쿼리와의 유사도
        - 다양성: 이미 선택된 문서와의 차이

        Args:
            query: 검색 쿼리
            results: 검색 결과
            top_k: 반환할 결과 개수
            lambda_param: 관련성 vs 다양성 가중치
                - 1.0: 관련성만 고려 (기존 검색과 동일)
                - 0.5: 관련성과 다양성 균형
                - 0.0: 다양성만 고려

        Returns:
            MMR로 선택된 결과 리스트
        """
        if not results:
            return []

        try:
            # 임베딩이 없으면 텍스트 기반 유사도 사용
            if "embedding" not in results[0]:
                logger.warning("No embeddings found, using text-based similarity")
                return self._text_based_mmr(query, results, top_k, lambda_param)

            selected = []
            remaining = results.copy()

            target_count = top_k if top_k else len(results)

            while len(selected) < target_count and remaining:
                mmr_scores = []

                for candidate in remaining:
                    # 관련성 점수 (원본 점수 사용)
                    relevance = candidate.get(
                        "combined_score", candidate.get("score", 0.0)
                    )

                    # 다양성 점수 (이미 선택된 문서와의 유사도)
                    if selected:
                        similarities = [
                            self._cosine_similarity(
                                candidate.get("embedding", []), s.get("embedding", [])
                            )
                            for s in selected
                        ]
                        diversity = max(similarities) if similarities else 0
                    else:
                        diversity = 0

                    # MMR 점수 계산
                    mmr_score = (
                        lambda_param * relevance - (1 - lambda_param) * diversity
                    )
                    mmr_scores.append(mmr_score)

                # 최고 MMR 점수 선택
                best_idx = mmr_scores.index(max(mmr_scores))
                selected_result = remaining.pop(best_idx)
                selected_result["mmr_score"] = mmr_scores[best_idx]
                selected.append(selected_result)

            logger.info(
                f"MMR reranking completed with lambda={lambda_param}: "
                f"selected {len(selected)} diverse results"
            )

            return selected

        except Exception as e:
            logger.error(f"MMR reranking failed: {e}")
            return self._score_based_rerank(results, top_k)

    def _text_based_mmr(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: Optional[int],
        lambda_param: float,
    ) -> List[Dict[str, Any]]:
        """텍스트 기반 MMR (임베딩 없을 때)"""
        selected = []
        remaining = results.copy()

        target_count = top_k if top_k else len(results)

        while len(selected) < target_count and remaining:
            mmr_scores = []

            for candidate in remaining:
                # 관련성 점수
                relevance = candidate.get("combined_score", candidate.get("score", 0.0))

                # 다양성 점수 (텍스트 중복도)
                if selected:
                    candidate_text = set(candidate.get("text", "").lower().split())
                    similarities = [
                        len(candidate_text & set(s.get("text", "").lower().split()))
                        / max(len(candidate_text), 1)
                        for s in selected
                    ]
                    diversity = max(similarities) if similarities else 0
                else:
                    diversity = 0

                # MMR 점수
                mmr_score = lambda_param * relevance - (1 - lambda_param) * diversity
                mmr_scores.append(mmr_score)

            # 최고 점수 선택
            best_idx = mmr_scores.index(max(mmr_scores))
            selected.append(remaining.pop(best_idx))

        return selected

    def _score_based_rerank(
        self, results: List[Dict[str, Any]], top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """원본 점수 기반 정렬"""
        sorted_results = sorted(
            results,
            key=lambda x: x.get("combined_score", x.get("score", 0.0)),
            reverse=True,
        )
        return sorted_results[:top_k] if top_k else sorted_results

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """코사인 유사도 계산"""
        if not vec1 or not vec2:
            return 0.0

        try:
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)

            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return float(dot_product / (norm1 * norm2))

        except Exception as e:
            logger.warning(f"Cosine similarity calculation failed: {e}")
            return 0.0

    async def rerank_with_llm(
        self, query: str, results: List[Dict[str, Any]], llm_manager, top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        LLM을 사용한 관련성 평가 및 리랭킹

        장점:
        - 매우 정확한 관련성 평가
        - 복잡한 쿼리 이해

        단점:
        - 느림
        - 비용 발생 (API 사용 시)
        """
        try:
            # 상위 결과만 LLM으로 평가 (비용 절감)
            candidates = results[: min(20, len(results))]

            # 프롬프트 생성
            prompt = f"""다음 검색 결과들의 관련성을 평가하세요.

쿼리: {query}

검색 결과:
"""
            for i, result in enumerate(candidates, 1):
                text = result.get("text", "")[:200]  # 처음 200자만
                prompt += f"\n{i}. {text}...\n"

            prompt += """
각 결과의 관련성을 0-10 점수로 평가하세요.
형식: "1: 8점, 2: 6점, 3: 9점, ..."
"""

            # LLM 평가
            response = await llm_manager.generate([{"role": "user", "content": prompt}])

            # 점수 파싱
            scores = self._parse_llm_scores(response, len(candidates))

            # 점수 추가
            for result, score in zip(candidates, scores):
                result["llm_score"] = score

            # LLM 점수로 정렬
            reranked = sorted(
                candidates, key=lambda x: x.get("llm_score", 0), reverse=True
            )

            # 나머지 결과 추가
            remaining = results[len(candidates) :]
            reranked.extend(remaining)

            logger.info(f"LLM reranking completed for {len(candidates)} results")

            return reranked[:top_k]

        except Exception as e:
            logger.error(f"LLM reranking failed: {e}")
            return results[:top_k]

    def _parse_llm_scores(self, response: str, count: int) -> List[float]:
        """LLM 응답에서 점수 추출"""
        import re

        scores = []

        # 패턴: "1: 8점" 또는 "1: 8"
        pattern = r"(\d+):\s*(\d+)"
        matches = re.findall(pattern, response)

        score_dict = {int(idx): float(score) for idx, score in matches}

        # 순서대로 점수 추출
        for i in range(1, count + 1):
            scores.append(score_dict.get(i, 5.0))  # 기본값 5.0

        return scores

    def __repr__(self) -> str:
        return f"RerankerService(cross_encoder={'enabled' if self.use_cross_encoder else 'disabled'})"
