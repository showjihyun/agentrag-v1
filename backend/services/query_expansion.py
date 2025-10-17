"""
쿼리 확장 서비스 (Query Expansion)

HyDE와 다중 쿼리 생성을 통해 검색 정확도를 향상시킵니다.
"""

import logging
import re
from typing import List, Optional
from backend.services.llm_manager import LLMManager
from backend.services.embedding import EmbeddingService

logger = logging.getLogger(__name__)


class QueryExpansionService:
    """
    쿼리 확장 서비스

    Features:
    - HyDE (Hypothetical Document Embeddings)
    - 다중 쿼리 생성
    - 쿼리 재작성
    - 한글/영어 지원
    """

    def __init__(self, llm_manager: LLMManager, embedding_service: EmbeddingService):
        """
        Initialize QueryExpansionService.

        Args:
            llm_manager: LLM manager for query generation
            embedding_service: Embedding service for vector generation
        """
        self.llm = llm_manager
        self.embedding = embedding_service

        logger.info("QueryExpansionService initialized")

    async def hyde_expansion(self, query: str, language: str = "auto") -> List[str]:
        """
        HyDE: 가상의 답변 문서를 생성하여 검색 향상

        원리:
        - 질문 대신 "이상적인 답변"을 생성
        - 답변 문서의 임베딩으로 검색
        - 질문-답변 간 의미 차이를 극복

        Args:
            query: 원본 쿼리
            language: "ko", "en", or "auto"

        Returns:
            [원본 쿼리, 가상 답변 문서]

        Example:
            쿼리: "인공지능이란?"
            생성: "인공지능은 컴퓨터가 인간의 지능을 모방하는 기술입니다..."
        """
        try:
            # 언어 자동 감지
            if language == "auto":
                language = self._detect_language(query)

            # 언어별 프롬프트
            if language == "ko":
                prompt = f"""다음 질문에 대한 상세하고 정확한 답변을 작성하세요.
실제 문서에서 발췌한 것처럼 작성하세요.

질문: {query}

답변:"""
            else:
                prompt = f"""Write a detailed and accurate answer to the following question.
Write as if it were excerpted from an actual document.

Question: {query}

Answer:"""

            # LLM으로 가상 답변 생성
            hypothetical_answer = await self.llm.generate(
                [{"role": "user", "content": prompt}]
            )

            # 답변 정제
            hypothetical_answer = hypothetical_answer.strip()

            logger.info(
                f"HyDE expansion generated {len(hypothetical_answer)} chars "
                f"for query: {query[:50]}..."
            )

            return [query, hypothetical_answer]

        except Exception as e:
            logger.error(f"HyDE expansion failed: {e}")
            # 실패 시 원본 쿼리만 반환
            return [query]

    async def multi_query_expansion(
        self, query: str, num_variations: int = 3, language: str = "auto"
    ) -> List[str]:
        """
        쿼리를 여러 방식으로 재작성

        목적:
        - 다양한 표현으로 검색 범위 확대
        - 동의어, 관련어 포함
        - 검색 누락 방지

        Args:
            query: 원본 쿼리
            num_variations: 생성할 변형 개수
            language: "ko", "en", or "auto"

        Returns:
            [원본 쿼리, 변형1, 변형2, ...]

        Example:
            원본: "AI 기술"
            변형: ["인공지능 기술", "머신러닝", "artificial intelligence"]
        """
        try:
            # 언어 자동 감지
            if language == "auto":
                language = self._detect_language(query)

            # 언어별 프롬프트
            if language == "ko":
                prompt = f"""다음 검색 쿼리를 {num_variations}가지 다른 방식으로 재작성하세요.
각 재작성은 같은 의도를 가지지만 다른 단어나 표현을 사용해야 합니다.

원본 쿼리: {query}

재작성된 쿼리:
1."""
            else:
                prompt = f"""Rewrite the following search query in {num_variations} different ways.
Each rewrite should have the same intent but use different words or expressions.

Original query: {query}

Rewritten queries:
1."""

            # LLM으로 재작성 생성
            response = await self.llm.generate([{"role": "user", "content": prompt}])

            # 재작성된 쿼리 파싱
            expanded_queries = self._parse_queries(response, num_variations)

            logger.info(
                f"Multi-query expansion generated {len(expanded_queries)} variations "
                f"for query: {query[:50]}..."
            )

            return [query] + expanded_queries

        except Exception as e:
            logger.error(f"Multi-query expansion failed: {e}")
            # 실패 시 원본 쿼리만 반환
            return [query]

    async def semantic_expansion(self, query: str, language: str = "auto") -> List[str]:
        """
        의미 기반 쿼리 확장 (동의어, 관련어)

        Args:
            query: 원본 쿼리
            language: "ko", "en", or "auto"

        Returns:
            [원본 쿼리, 동의어/관련어 포함 쿼리]

        Example:
            원본: "머신러닝"
            확장: ["머신러닝", "기계학습", "machine learning", "ML"]
        """
        try:
            # 언어 자동 감지
            if language == "auto":
                language = self._detect_language(query)

            # 언어별 프롬프트
            if language == "ko":
                prompt = f"""다음 검색어의 동의어와 관련어를 나열하세요.

검색어: {query}

동의어/관련어 (쉼표로 구분):"""
            else:
                prompt = f"""List synonyms and related terms for the following search term.

Search term: {query}

Synonyms/Related terms (comma-separated):"""

            # LLM으로 동의어 생성
            response = await self.llm.generate([{"role": "user", "content": prompt}])

            # 동의어 파싱
            synonyms = self._parse_synonyms(response)

            # 원본 쿼리 + 동의어 결합
            expanded_queries = [query]
            for synonym in synonyms[:3]:  # 상위 3개만 사용
                expanded_queries.append(f"{query} {synonym}")

            logger.info(
                f"Semantic expansion generated {len(synonyms)} synonyms "
                f"for query: {query[:50]}..."
            )

            return expanded_queries

        except Exception as e:
            logger.error(f"Semantic expansion failed: {e}")
            return [query]

    def _detect_language(self, text: str) -> str:
        """
        텍스트 언어 감지 (한글/영어)

        Returns:
            "ko" or "en"
        """
        # 한글 문자 비율 계산
        korean_chars = len(re.findall(r"[가-힣]", text))
        total_chars = len(re.findall(r"[가-힣a-zA-Z]", text))

        if total_chars == 0:
            return "en"

        korean_ratio = korean_chars / total_chars

        return "ko" if korean_ratio > 0.3 else "en"

    def _parse_queries(self, response: str, expected_count: int) -> List[str]:
        """
        LLM 응답에서 재작성된 쿼리 추출

        패턴:
        1. 쿼리1
        2. 쿼리2
        3. 쿼리3
        """
        queries = []

        # 번호 매겨진 항목 찾기
        pattern = r"\d+\.\s*(.+?)(?=\n\d+\.|\Z)"
        matches = re.findall(pattern, response, re.DOTALL)

        for match in matches:
            query = match.strip()
            # 따옴표 제거
            query = query.strip("\"'")
            if query and len(query) > 2:
                queries.append(query)

        # 예상 개수만큼 반환
        return queries[:expected_count]

    def _parse_synonyms(self, response: str) -> List[str]:
        """
        LLM 응답에서 동의어 추출

        패턴: "단어1, 단어2, 단어3"
        """
        # 쉼표로 분리
        synonyms = [s.strip() for s in response.split(",")]

        # 정제
        cleaned_synonyms = []
        for synonym in synonyms:
            # 따옴표, 괄호 제거
            synonym = re.sub(r'["\'\(\)]', "", synonym).strip()
            if synonym and len(synonym) > 1:
                cleaned_synonyms.append(synonym)

        return cleaned_synonyms

    async def expand_query(
        self, query: str, method: str = "hyde", language: str = "auto"
    ) -> List[str]:
        """
        통합 쿼리 확장 인터페이스

        Args:
            query: 원본 쿼리
            method: "hyde", "multi", "semantic", or "all"
            language: "ko", "en", or "auto"

        Returns:
            확장된 쿼리 리스트
        """
        if method == "hyde":
            return await self.hyde_expansion(query, language)
        elif method == "multi":
            return await self.multi_query_expansion(query, language=language)
        elif method == "semantic":
            return await self.semantic_expansion(query, language)
        elif method == "all":
            # 모든 방법 결합
            hyde_queries = await self.hyde_expansion(query, language)
            multi_queries = await self.multi_query_expansion(query, language=language)
            semantic_queries = await self.semantic_expansion(query, language)

            # 중복 제거
            all_queries = list(set(hyde_queries + multi_queries + semantic_queries))
            return all_queries
        else:
            logger.warning(f"Unknown expansion method: {method}")
            return [query]

    def __repr__(self) -> str:
        return "QueryExpansionService(methods=['hyde', 'multi', 'semantic'])"
