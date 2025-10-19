"""
Web Search Enhancement Components

검색 결과의 품질과 정확도를 향상시키는 컴포넌트들
"""

import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urlparse
import hashlib

logger = logging.getLogger(__name__)


class SourceCredibilityScorer:
    """
    소스 신뢰도 평가
    
    Features:
    - 도메인 신뢰도 평가
    - HTTPS 확인
    - 콘텐츠 품질 평가
    - 최신성 평가
    """
    
    # 신뢰할 수 있는 도메인 (화이트리스트)
    TRUSTED_DOMAINS = {
        # 정부 및 교육기관
        'gov.kr': 0.95,
        'go.kr': 0.95,
        'edu': 0.85,
        'ac.kr': 0.85,
        
        # 국제 신뢰 기관
        'wikipedia.org': 0.9,
        'who.int': 0.95,
        'un.org': 0.95,
        
        # 기술 문서
        'github.com': 0.8,
        'stackoverflow.com': 0.8,
        'docs.python.org': 0.9,
        'developer.mozilla.org': 0.9,
        
        # 뉴스 (주요 언론)
        'naver.com': 0.7,
        'daum.net': 0.7,
        'chosun.com': 0.75,
        'joins.com': 0.75,
        'donga.com': 0.75,
        
        # 학술
        'scholar.google.com': 0.9,
        'arxiv.org': 0.85,
        'pubmed.ncbi.nlm.nih.gov': 0.9,
    }
    
    # 의심스러운 도메인 (블랙리스트)
    SUSPICIOUS_DOMAINS = {
        'blogspot.com': 0.3,
        'wordpress.com': 0.4,
        'tistory.com': 0.5,
        'medium.com': 0.6,  # 개인 블로그 플랫폼
    }
    
    # 광고 관련 키워드
    AD_MARKERS = [
        '광고', 'ad', 'sponsored', '협찬', '제휴',
        '쿠폰', 'coupon', '할인', 'discount'
    ]
    
    def score_source(
        self,
        url: str,
        title: str = "",
        snippet: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        소스 신뢰도 점수 계산 (0.0 ~ 1.0)
        
        Args:
            url: 소스 URL
            title: 제목
            snippet: 스니펫
            metadata: 추가 메타데이터
            
        Returns:
            신뢰도 점수 (0.0 ~ 1.0)
        """
        score = 0.5  # 기본 점수
        
        try:
            # 1. 도메인 신뢰도 (가중치: 0.3)
            domain = self._extract_domain(url)
            
            # 정확한 도메인 매칭
            if domain in self.TRUSTED_DOMAINS:
                score += self.TRUSTED_DOMAINS[domain] * 0.3
            elif domain in self.SUSPICIOUS_DOMAINS:
                score -= (1 - self.SUSPICIOUS_DOMAINS[domain]) * 0.3
            else:
                # 부분 매칭 (예: *.edu, *.gov)
                for trusted_domain, trust_score in self.TRUSTED_DOMAINS.items():
                    if domain.endswith(trusted_domain):
                        score += trust_score * 0.25
                        break
            
            # 2. HTTPS 사용 (가중치: 0.1)
            if url.startswith('https://'):
                score += 0.1
            
            # 3. 콘텐츠 품질 (가중치: 0.3)
            content = f"{title} {snippet}"
            
            # 충분한 내용
            if len(content) > 200:
                score += 0.1
            
            # 인용 포함 (학술적)
            if self._has_citations(content):
                score += 0.1
            
            # 광고 없음
            if not self._has_ads_markers(content):
                score += 0.1
            
            # 4. 최신성 (가중치: 0.1)
            date = self._extract_date(url, metadata)
            if date and self._is_recent(date, days=365):
                score += 0.1
            
            # 5. URL 품질 (가중치: 0.1)
            if self._is_clean_url(url):
                score += 0.05
            if not self._has_suspicious_patterns(url):
                score += 0.05
            
        except Exception as e:
            logger.warning(f"Error scoring source {url}: {e}")
        
        return min(1.0, max(0.0, score))
    
    def filter_by_credibility(
        self,
        results: List[Dict[str, Any]],
        min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        신뢰도 기준으로 필터링
        
        Args:
            results: 검색 결과 리스트
            min_score: 최소 신뢰도 점수
            
        Returns:
            필터링된 결과
        """
        filtered = []
        
        for result in results:
            score = self.score_source(
                url=result.get('url', ''),
                title=result.get('title', ''),
                snippet=result.get('snippet', ''),
                metadata=result.get('metadata')
            )
            
            result['credibility_score'] = score
            
            if score >= min_score:
                filtered.append(result)
            else:
                logger.debug(
                    f"Filtered out low credibility source: "
                    f"{result.get('url', '')} (score={score:.2f})"
                )
        
        logger.info(
            f"Credibility filtering: {len(results)} -> {len(filtered)} "
            f"(removed {len(results) - len(filtered)})"
        )
        
        return filtered
    
    def _extract_domain(self, url: str) -> str:
        """URL에서 도메인 추출"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # www. 제거
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ""
    
    def _has_citations(self, content: str) -> bool:
        """인용 포함 여부 확인"""
        citation_patterns = [
            r'\[\d+\]',  # [1], [2]
            r'\(\d{4}\)',  # (2023)
            r'et al\.',  # et al.
            r'doi:',  # DOI
            r'http[s]?://doi\.org',  # DOI URL
        ]
        
        for pattern in citation_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False
    
    def _has_ads_markers(self, content: str) -> bool:
        """광고 마커 포함 여부 확인"""
        content_lower = content.lower()
        return any(marker in content_lower for marker in self.AD_MARKERS)
    
    def _extract_date(
        self,
        url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[datetime]:
        """URL이나 메타데이터에서 날짜 추출"""
        # 메타데이터에서 날짜 확인
        if metadata:
            date_fields = ['dateLastCrawled', 'publishedDate', 'date']
            for field in date_fields:
                if field in metadata:
                    try:
                        return datetime.fromisoformat(
                            metadata[field].replace('Z', '+00:00')
                        )
                    except:
                        pass
        
        # URL에서 날짜 패턴 추출 (예: /2023/12/31/)
        date_pattern = r'/(\d{4})/(\d{1,2})/(\d{1,2})/'
        match = re.search(date_pattern, url)
        if match:
            try:
                year, month, day = match.groups()
                return datetime(int(year), int(month), int(day))
            except:
                pass
        
        return None
    
    def _is_recent(self, date: datetime, days: int = 365) -> bool:
        """최근 날짜인지 확인"""
        # 타임존 처리
        now = datetime.now()
        if date.tzinfo is not None:
            from datetime import timezone
            now = datetime.now(timezone.utc)
            if date.tzinfo != timezone.utc:
                date = date.astimezone(timezone.utc)
        age = now - date
        return age.days <= days
    
    def _is_clean_url(self, url: str) -> bool:
        """깨끗한 URL인지 확인 (쿼리 파라미터 적음)"""
        parsed = urlparse(url)
        # 쿼리 파라미터가 3개 이하
        if parsed.query:
            params = parsed.query.split('&')
            return len(params) <= 3
        return True
    
    def _has_suspicious_patterns(self, url: str) -> bool:
        """의심스러운 패턴 포함 여부"""
        suspicious = [
            'click',
            'redirect',
            'affiliate',
            'ref=',
            'utm_',
            'track',
        ]
        
        url_lower = url.lower()
        return any(pattern in url_lower for pattern in suspicious)


class ResultDeduplicator:
    """
    검색 결과 중복 제거
    
    Features:
    - URL 기반 중복 제거
    - 콘텐츠 유사도 기반 중복 제거
    - 도메인 다양성 확보
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        초기화
        
        Args:
            similarity_threshold: 중복으로 간주할 유사도 임계값
        """
        self.similarity_threshold = similarity_threshold
    
    def deduplicate(
        self,
        results: List[Dict[str, Any]],
        method: str = "url"
    ) -> List[Dict[str, Any]]:
        """
        중복 제거
        
        Args:
            results: 검색 결과 리스트
            method: 중복 제거 방법 ("url", "content", "both")
            
        Returns:
            중복 제거된 결과
        """
        if not results:
            return []
        
        if method == "url":
            return self._deduplicate_by_url(results)
        elif method == "content":
            return self._deduplicate_by_content(results)
        elif method == "both":
            # URL 중복 제거 후 콘텐츠 중복 제거
            url_deduped = self._deduplicate_by_url(results)
            return self._deduplicate_by_content(url_deduped)
        else:
            raise ValueError(f"Unknown deduplication method: {method}")
    
    def _deduplicate_by_url(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """URL 기반 중복 제거"""
        seen_urls = set()
        seen_domains = {}
        unique = []
        
        for result in results:
            url = result.get('url', '')
            if not url:
                continue
            
            # 정규화된 URL
            normalized_url = self._normalize_url(url)
            
            # URL 중복 체크
            if normalized_url in seen_urls:
                logger.debug(f"Duplicate URL: {url}")
                continue
            
            seen_urls.add(normalized_url)
            
            # 도메인 다양성 확보 (같은 도메인 최대 3개)
            domain = self._extract_domain(url)
            if domain:
                domain_count = seen_domains.get(domain, 0)
                if domain_count >= 3:
                    logger.debug(f"Too many from domain {domain}: {url}")
                    continue
                seen_domains[domain] = domain_count + 1
            
            unique.append(result)
        
        logger.info(
            f"URL deduplication: {len(results)} -> {len(unique)} "
            f"(removed {len(results) - len(unique)})"
        )
        
        return unique
    
    def _deduplicate_by_content(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """콘텐츠 유사도 기반 중복 제거 (간단한 해시 기반)"""
        seen_hashes = set()
        unique = []
        
        for result in results:
            # 제목 + 스니펫으로 해시 생성
            content = f"{result.get('title', '')} {result.get('snippet', '')}"
            content_hash = self._content_hash(content)
            
            if content_hash in seen_hashes:
                logger.debug(f"Duplicate content: {result.get('title', '')[:50]}")
                continue
            
            seen_hashes.add(content_hash)
            unique.append(result)
        
        logger.info(
            f"Content deduplication: {len(results)} -> {len(unique)} "
            f"(removed {len(results) - len(unique)})"
        )
        
        return unique
    
    def _normalize_url(self, url: str) -> str:
        """URL 정규화 (쿼리 파라미터 제거 등)"""
        try:
            parsed = urlparse(url)
            # 스킴, 도메인, 경로만 사용 (쿼리 파라미터 제거)
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            # 끝의 / 제거
            return normalized.rstrip('/')
        except:
            return url
    
    def _extract_domain(self, url: str) -> str:
        """도메인 추출"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ""
    
    def _content_hash(self, content: str) -> str:
        """콘텐츠 해시 생성 (정규화 후)"""
        # 소문자 변환, 공백 정규화
        normalized = re.sub(r'\s+', ' ', content.lower().strip())
        # 해시 생성
        return hashlib.md5(normalized.encode()).hexdigest()


class TemporalFilter:
    """
    시간 기반 필터링
    
    Features:
    - 최신성 평가
    - 날짜 기반 필터링
    - 최신성 점수 부여
    """
    
    def filter_by_recency(
        self,
        results: List[Dict[str, Any]],
        prefer_recent: bool = True,
        max_age_days: Optional[int] = None,
        boost_recent: bool = True
    ) -> List[Dict[str, Any]]:
        """
        최신성 기반 필터링 및 점수 부여
        
        Args:
            results: 검색 결과 리스트
            prefer_recent: 최신 결과 우선
            max_age_days: 최대 나이 (일)
            boost_recent: 최신 결과에 점수 부스트
            
        Returns:
            필터링 및 정렬된 결과
        """
        filtered = []
        
        for result in results:
            # URL이나 메타데이터에서 날짜 추출
            date = self._extract_date(result)
            
            if date:
                # 타임존 처리
                now = datetime.now()
                if date.tzinfo is not None:
                    # date가 timezone-aware면 now도 aware로
                    from datetime import timezone
                    now = datetime.now(timezone.utc)
                    if date.tzinfo != timezone.utc:
                        date = date.astimezone(timezone.utc)
                age_days = (now - date).days
                
                # 최대 나이 제한
                if max_age_days and age_days > max_age_days:
                    logger.debug(
                        f"Filtered out old result: {result.get('title', '')[:50]} "
                        f"(age={age_days} days)"
                    )
                    continue
                
                # 최신성 점수 추가
                if boost_recent:
                    # 지수 감쇠: 1년 후 0.5, 2년 후 0.25
                    recency_score = 1.0 / (1.0 + age_days / 365.0)
                    result['recency_score'] = recency_score
                    result['age_days'] = age_days
            else:
                # 날짜 정보 없으면 중간 점수
                if boost_recent:
                    result['recency_score'] = 0.5
            
            filtered.append(result)
        
        # 최신성 점수로 정렬
        if prefer_recent and boost_recent:
            filtered.sort(
                key=lambda x: x.get('recency_score', 0),
                reverse=True
            )
        
        logger.info(
            f"Temporal filtering: {len(results)} -> {len(filtered)} "
            f"(removed {len(results) - len(filtered)})"
        )
        
        return filtered
    
    def _extract_date(
        self,
        result: Dict[str, Any]
    ) -> Optional[datetime]:
        """결과에서 날짜 추출"""
        # 메타데이터에서 날짜 확인
        metadata = result.get('metadata', {})
        if metadata:
            date_fields = ['dateLastCrawled', 'publishedDate', 'date', 'lastModified']
            for field in date_fields:
                if field in metadata:
                    try:
                        date_str = metadata[field]
                        # ISO 형식 파싱
                        return datetime.fromisoformat(
                            date_str.replace('Z', '+00:00')
                        )
                    except:
                        pass
        
        # URL에서 날짜 패턴 추출
        url = result.get('url', '')
        if url:
            date_pattern = r'/(\d{4})/(\d{1,2})/(\d{1,2})/'
            match = re.search(date_pattern, url)
            if match:
                try:
                    year, month, day = match.groups()
                    return datetime(int(year), int(month), int(day))
                except:
                    pass
        
        return None


# 싱글톤 인스턴스
_credibility_scorer = None
_deduplicator = None
_temporal_filter = None


def get_credibility_scorer() -> SourceCredibilityScorer:
    """SourceCredibilityScorer 싱글톤 인스턴스 반환"""
    global _credibility_scorer
    if _credibility_scorer is None:
        _credibility_scorer = SourceCredibilityScorer()
    return _credibility_scorer


def get_deduplicator(similarity_threshold: float = 0.85) -> ResultDeduplicator:
    """ResultDeduplicator 싱글톤 인스턴스 반환"""
    global _deduplicator
    if _deduplicator is None:
        _deduplicator = ResultDeduplicator(similarity_threshold)
    return _deduplicator


def get_temporal_filter() -> TemporalFilter:
    """TemporalFilter 싱글톤 인스턴스 반환"""
    global _temporal_filter
    if _temporal_filter is None:
        _temporal_filter = TemporalFilter()
    return _temporal_filter

