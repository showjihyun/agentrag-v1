"""
Query Enhancement Service

쿼리 품질 향상을 위한 서비스:
- 쿼리 확장 (동의어, 관련어)
- 쿼리 재작성 (LLM 활용)
- 의도 분석
- 키워드 추출
- 다중 쿼리 생성
"""

import logging
import re
from typing import List, Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)


class QueryEnhancer:
    """
    쿼리 품질 향상 서비스
    
    Features:
    - 의도 분석 (정보검색, 비교, 방법, 정의 등)
    - 키워드 추출
    - 동의어 확장
    - 쿼리 재작성 (LLM)
    - 다중 쿼리 생성
    """
    
    # 의도 패턴
    INTENT_PATTERNS = {
        "정보검색": [
            r"무엇", r"뭐", r"어떤", r"어떻게", r"왜", r"언제", r"어디",
            r"what", r"which", r"when", r"where", r"who", r"why", r"how"
        ],
        "비교": [
            r"차이", r"비교", r"vs", r"대", r"또는", r"아니면",
            r"difference", r"compare", r"versus", r"or"
        ],
        "방법": [
            r"방법", r"어떻게", r"하는법", r"하기", r"설치", r"사용",
            r"how to", r"way to", r"method", r"install", r"use"
        ],
        "정의": [
            r"이란", r"란", r"의미", r"뜻", r"정의",
            r"what is", r"define", r"meaning", r"definition"
        ],
        "문제해결": [
            r"오류", r"에러", r"문제", r"해결", r"안됨", r"안돼",
            r"error", r"problem", r"issue", r"fix", r"solve", r"not working"
        ],
        "추천": [
            r"추천", r"좋은", r"best", r"recommend", r"suggest", r"top"
        ]
    }
    
    # 불용어 (한국어 + 영어)
    STOP_WORDS = {
        # 한국어
        "이", "그", "저", "것", "수", "등", "및", "또는", "그리고",
        "하다", "되다", "있다", "없다", "이다", "아니다",
        # 영어
        "the", "a", "an", "and", "or", "but", "in", "on", "at",
        "to", "for", "of", "with", "by", "from", "is", "are", "was", "were"
    }
    
    def __init__(self, llm_manager=None):
        """
        초기화
        
        Args:
            llm_manager: LLM Manager (쿼리 재작성용, 선택적)
        """
        self.llm_manager = llm_manager
        
        logger.info("QueryEnhancer initialized")
    
    async def enhance_query(
        self,
        query: str,
        enable_llm: bool = True,
        max_expansions: int = 3
    ) -> Dict[str, Any]:
        """
        쿼리 확장 및 재작성
        
        Args:
            query: 원본 쿼리
            enable_llm: LLM 재작성 활성화
            max_expansions: 최대 확장 쿼리 수
            
        Returns:
            {
                "original": "원본 쿼리",
                "expanded": ["확장된", "쿼리", "리스트"],
                "rewritten": "재작성된 쿼리",
                "keywords": ["핵심", "키워드"],
                "intent": "정보검색|비교|방법|정의|문제해결|추천"
            }
        """
        # 1. 의도 분석
        intent = self._analyze_intent(query)
        
        # 2. 키워드 추출
        keywords = self._extract_keywords(query)
        
        # 3. 동의어 확장
        expanded = self._expand_with_synonyms(query, keywords, max_expansions)
        
        # 4. 쿼리 재작성 (LLM 활용)
        rewritten = None
        if enable_llm and self.llm_manager:
            try:
                rewritten = await self._rewrite_query_llm(query, intent)
            except Exception as e:
                logger.warning(f"LLM rewriting failed: {e}")
                rewritten = query
        else:
            rewritten = query
        
        return {
            "original": query,
            "expanded": expanded,
            "rewritten": rewritten,
            "keywords": keywords,
            "intent": intent
        }
    
    def _analyze_intent(self, query: str) -> str:
        """
        쿼리 의도 분석
        
        Returns:
            의도 카테고리
        """
        query_lower = query.lower()
        
        # 각 의도별 패턴 매칭
        intent_scores = {}
        for intent, patterns in self.INTENT_PATTERNS.items():
            score = sum(
                1 for pattern in patterns
                if re.search(pattern, query_lower)
            )
            if score > 0:
                intent_scores[intent] = score
        
        # 가장 높은 점수의 의도 반환
        if intent_scores:
            return max(intent_scores.items(), key=lambda x: x[1])[0]
        
        return "정보검색"  # 기본값
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        키워드 추출 (간단한 방법)
        
        Returns:
            키워드 리스트
        """
        # 토큰화 (공백 기준)
        tokens = query.split()
        
        # 불용어 제거 및 정제
        keywords = []
        for token in tokens:
            # 특수문자 제거
            cleaned = re.sub(r'[^\w\s가-힣]', '', token)
            cleaned = cleaned.strip()
            
            # 불용어 체크
            if cleaned and cleaned.lower() not in self.STOP_WORDS:
                # 길이 체크 (너무 짧은 단어 제외)
                if len(cleaned) >= 2:
                    keywords.append(cleaned)
        
        return keywords
    
    def _expand_with_synonyms(
        self,
        query: str,
        keywords: List[str],
        max_expansions: int
    ) -> List[str]:
        """
        동의어로 쿼리 확장 (간단한 규칙 기반)
        
        Returns:
            확장된 쿼리 리스트
        """
        # 간단한 동의어 사전 (확장 가능)
        synonyms = {
            # 기술 용어
            "python": ["파이썬", "Python"],
            "파이썬": ["python", "Python"],
            "javascript": ["자바스크립트", "JS"],
            "자바스크립트": ["javascript", "JS"],
            
            # 일반 용어
            "방법": ["방식", "how to", "하는법"],
            "오류": ["에러", "error", "문제"],
            "설치": ["install", "인스톨", "설정"],
            "사용": ["use", "활용", "이용"],
            "최신": ["latest", "new", "신규"],
            "비교": ["compare", "차이", "vs"],
            "추천": ["recommend", "best", "좋은"],
        }
        
        expanded = []
        
        # 키워드 기반 확장
        for keyword in keywords[:3]:  # 상위 3개 키워드만
            keyword_lower = keyword.lower()
            if keyword_lower in synonyms:
                for synonym in synonyms[keyword_lower][:2]:  # 동의어 2개까지
                    # 원본 쿼리에서 키워드를 동의어로 교체
                    expanded_query = query.replace(keyword, synonym)
                    if expanded_query != query and expanded_query not in expanded:
                        expanded.append(expanded_query)
                        if len(expanded) >= max_expansions:
                            return expanded
        
        # 의도 기반 확장
        if "최신" not in query and "latest" not in query.lower():
            expanded.append(f"{query} 최신")
        
        if "방법" not in query and "how" not in query.lower():
            expanded.append(f"{query} 방법")
        
        return expanded[:max_expansions]
    
    async def _rewrite_query_llm(self, query: str, intent: str) -> str:
        """
        LLM을 사용한 쿼리 재작성
        
        Args:
            query: 원본 쿼리
            intent: 쿼리 의도
            
        Returns:
            재작성된 쿼리
        """
        if not self.llm_manager:
            return query
        
        # 의도별 프롬프트
        intent_prompts = {
            "정보검색": "다음 검색 쿼리를 더 명확하고 구체적으로 재작성하세요",
            "비교": "다음 비교 쿼리를 더 명확하게 재작성하세요",
            "방법": "다음 방법 질문을 더 구체적으로 재작성하세요",
            "정의": "다음 정의 질문을 더 명확하게 재작성하세요",
            "문제해결": "다음 문제 해결 쿼리를 더 구체적으로 재작성하세요",
            "추천": "다음 추천 요청을 더 명확하게 재작성하세요"
        }
        
        prompt = intent_prompts.get(intent, intent_prompts["정보검색"])
        
        messages = [
            {
                "role": "system",
                "content": (
                    "당신은 검색 쿼리 최적화 전문가입니다. "
                    "사용자의 검색 의도를 파악하여 더 나은 검색 결과를 얻을 수 있도록 "
                    "쿼리를 재작성합니다. 재작성된 쿼리만 출력하세요."
                )
            },
            {
                "role": "user",
                "content": f"{prompt}: {query}"
            }
        ]
        
        try:
            # LLM 호출 (스트리밍 없이)
            response = await self.llm_manager.generate(
                messages,
                stream=False,
                temperature=0.3,
                max_tokens=100
            )
            
            # 응답 추출
            if isinstance(response, dict):
                rewritten = response.get("content", query)
            else:
                rewritten = str(response)
            
            # 정제
            rewritten = rewritten.strip().strip('"').strip("'")
            
            # 너무 길면 원본 사용
            if len(rewritten) > len(query) * 2:
                return query
            
            logger.info(f"Query rewritten: '{query}' -> '{rewritten}'")
            return rewritten
            
        except Exception as e:
            logger.error(f"LLM query rewriting failed: {e}")
            return query
    
    def generate_multi_queries(
        self,
        query: str,
        intent: str,
        num_queries: int = 5
    ) -> List[str]:
        """
        다중 쿼리 생성 (다양한 관점)
        
        Args:
            query: 원본 쿼리
            intent: 쿼리 의도
            num_queries: 생성할 쿼리 수
            
        Returns:
            다양한 쿼리 리스트
        """
        queries = [query]  # 원본 포함
        
        # 의도별 변형 전략
        if intent == "정보검색":
            queries.append(f"{query} 정보")
            queries.append(f"{query} 설명")
            queries.append(f"{query} 개요")
        
        elif intent == "비교":
            queries.append(f"{query} 차이점")
            queries.append(f"{query} 장단점")
            queries.append(f"{query} 비교 분석")
        
        elif intent == "방법":
            queries.append(f"{query} 가이드")
            queries.append(f"{query} 튜토리얼")
            queries.append(f"{query} 단계")
        
        elif intent == "정의":
            queries.append(f"{query} 의미")
            queries.append(f"{query} 개념")
            queries.append(f"{query} 설명")
        
        elif intent == "문제해결":
            queries.append(f"{query} 해결")
            queries.append(f"{query} 해결방법")
            queries.append(f"{query} 원인")
        
        elif intent == "추천":
            queries.append(f"{query} best")
            queries.append(f"{query} 순위")
            queries.append(f"{query} 비교")
        
        # 시간 제약 추가
        queries.append(f"{query} 최신")
        queries.append(f"{query} 2024")
        
        # 신뢰도 제약 추가
        queries.append(f"{query} 공식")
        queries.append(f"{query} 가이드")
        
        # 중복 제거 및 제한
        unique_queries = []
        seen = set()
        for q in queries:
            if q not in seen:
                unique_queries.append(q)
                seen.add(q)
                if len(unique_queries) >= num_queries:
                    break
        
        return unique_queries


# 싱글톤 인스턴스
_query_enhancer = None


def get_query_enhancer(llm_manager=None) -> QueryEnhancer:
    """QueryEnhancer 싱글톤 인스턴스 반환"""
    global _query_enhancer
    if _query_enhancer is None:
        _query_enhancer = QueryEnhancer(llm_manager)
    return _query_enhancer

