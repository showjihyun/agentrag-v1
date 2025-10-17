"""
Multimodal Reranker Service

멀티모달 검색 결과 리랭킹:
- CLIP + ColPali 하이브리드
- 모달리티별 가중치 최적화
- 크로스 모달 점수 통합
- 학습 기반 가중치 조정
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class MultimodalReranker:
    """
    멀티모달 리랭킹 서비스
    
    Features:
    - CLIP + ColPali 점수 통합
    - 모달리티별 가중치
    - 크로스 모달 부스팅
    - 다양성 보장
    """
    
    def __init__(
        self,
        clip_weight: float = 0.4,
        colpali_weight: float = 0.3,
        text_weight: float = 0.3,
        cross_modal_boost: float = 0.1,
        diversity_threshold: float = 0.85
    ):
        """
        초기화
        
        Args:
            clip_weight: CLIP 점수 가중치
            colpali_weight: ColPali 점수 가중치
            text_weight: 텍스트 점수 가중치
            cross_modal_boost: 크로스 모달 부스트
            diversity_threshold: 다양성 임계값
        """
        self.clip_weight = clip_weight
        self.colpali_weight = colpali_weight
        self.text_weight = text_weight
        self.cross_modal_boost = cross_modal_boost
        self.diversity_threshold = diversity_threshold
        
        # 통계
        self.stats = {
            "total_reranks": 0,
            "avg_score_improvement": 0.0,
            "cross_modal_boosts": 0
        }
        
        logger.info(
            f"MultimodalReranker initialized: "
            f"clip={clip_weight}, colpali={colpali_weight}, text={text_weight}"
        )
    
    def rerank(
        self,
        results: Dict[str, List[Dict[str, Any]]],
        query_type: str = 'text',
        top_k: int = 10,
        enable_diversity: bool = True
    ) -> List[Dict[str, Any]]:
        """
        멀티모달 결과 리랭킹
        
        Args:
            results: 모달리티별 검색 결과
                {
                    'text': [...],
                    'images': [...],
                    'audio': [...]
                }
            query_type: 쿼리 타입 ('text', 'image', 'audio')
            top_k: 반환할 결과 수
            enable_diversity: 다양성 보장 활성화
        
        Returns:
            리랭킹된 통합 결과
        """
        self.stats["total_reranks"] += 1
        
        # 1. 모든 결과 수집
        all_results = []
        
        for modality, modality_results in results.items():
            for result in modality_results:
                result['modality'] = modality
                all_results.append(result)
        
        if not all_results:
            return []
        
        # 2. 점수 정규화
        normalized_results = self._normalize_scores(all_results)
        
        # 3. 멀티모달 점수 계산
        scored_results = self._calculate_multimodal_scores(
            normalized_results,
            query_type
        )
        
        # 4. 크로스 모달 부스팅
        boosted_results = self._apply_cross_modal_boost(scored_results, query_type)
        
        # 5. 정렬
        boosted_results.sort(key=lambda x: x['multimodal_score'], reverse=True)
        
        # 6. 다양성 보장
        if enable_diversity:
            final_results = self._ensure_diversity(boosted_results, top_k)
        else:
            final_results = boosted_results[:top_k]
        
        # 7. 통계 업데이트
        self._update_stats(all_results, final_results)
        
        logger.info(
            f"Reranked {len(all_results)} → {len(final_results)} results "
            f"(query_type={query_type})"
        )
        
        return final_results
    
    def _normalize_scores(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        점수 정규화 (모달리티별)
        
        Args:
            results: 검색 결과
        
        Returns:
            정규화된 결과
        """
        # 모달리티별 그룹화
        by_modality = defaultdict(list)
        for result in results:
            modality = result.get('modality', 'text')
            by_modality[modality].append(result)
        
        # 모달리티별 정규화
        normalized = []
        
        for modality, modality_results in by_modality.items():
            scores = [r.get('score', 0.0) for r in modality_results]
            
            if not scores:
                continue
            
            min_score = min(scores)
            max_score = max(scores)
            score_range = max_score - min_score if max_score > min_score else 1.0
            
            for result in modality_results:
                original_score = result.get('score', 0.0)
                normalized_score = (original_score - min_score) / score_range
                
                result['original_score'] = original_score
                result['normalized_score'] = normalized_score
                normalized.append(result)
        
        return normalized
    
    def _calculate_multimodal_scores(
        self,
        results: List[Dict[str, Any]],
        query_type: str
    ) -> List[Dict[str, Any]]:
        """
        멀티모달 점수 계산
        
        Args:
            results: 정규화된 결과
            query_type: 쿼리 타입
        
        Returns:
            멀티모달 점수가 추가된 결과
        """
        # 쿼리 타입별 가중치 조정
        weights = self._get_adaptive_weights(query_type)
        
        for result in results:
            modality = result.get('modality', 'text')
            normalized_score = result.get('normalized_score', 0.0)
            
            # 모달리티별 가중치 적용
            if modality == 'text':
                weighted_score = normalized_score * weights['text']
            elif modality == 'image':
                # CLIP vs ColPali 구분 (메타데이터 확인)
                method = result.get('metadata', {}).get('method', 'clip')
                if method == 'colpali':
                    weighted_score = normalized_score * weights['colpali']
                else:
                    weighted_score = normalized_score * weights['clip']
            elif modality == 'audio':
                weighted_score = normalized_score * weights['audio']
            else:
                weighted_score = normalized_score * 0.1  # 기타
            
            result['weighted_score'] = weighted_score
            result['multimodal_score'] = weighted_score  # 초기값
        
        return results
    
    def _get_adaptive_weights(self, query_type: str) -> Dict[str, float]:
        """
        쿼리 타입별 적응형 가중치
        
        Args:
            query_type: 쿼리 타입
        
        Returns:
            모달리티별 가중치
        """
        if query_type == 'text':
            return {
                'text': 0.4,
                'clip': 0.3,
                'colpali': 0.2,
                'audio': 0.1
            }
        elif query_type == 'image':
            return {
                'text': 0.2,
                'clip': 0.3,
                'colpali': 0.4,
                'audio': 0.1
            }
        elif query_type == 'audio':
            return {
                'text': 0.3,
                'clip': 0.1,
                'colpali': 0.1,
                'audio': 0.5
            }
        else:
            # 기본 균등 가중치
            return {
                'text': 0.3,
                'clip': 0.3,
                'colpali': 0.2,
                'audio': 0.2
            }
    
    def _apply_cross_modal_boost(
        self,
        results: List[Dict[str, Any]],
        query_type: str
    ) -> List[Dict[str, Any]]:
        """
        크로스 모달 부스팅
        
        쿼리와 다른 모달리티의 결과에 부스트 적용
        
        Args:
            results: 점수가 계산된 결과
            query_type: 쿼리 타입
        
        Returns:
            부스팅된 결과
        """
        for result in results:
            modality = result.get('modality', 'text')
            
            # 크로스 모달 여부 확인
            is_cross_modal = (
                (query_type == 'text' and modality in ['image', 'audio']) or
                (query_type == 'image' and modality in ['text', 'audio']) or
                (query_type == 'audio' and modality in ['text', 'image'])
            )
            
            if is_cross_modal:
                # 크로스 모달 부스트 적용
                boost = self.cross_modal_boost * result['normalized_score']
                result['multimodal_score'] += boost
                result['cross_modal_boosted'] = True
                self.stats["cross_modal_boosts"] += 1
            else:
                result['cross_modal_boosted'] = False
        
        return results
    
    def _ensure_diversity(
        self,
        results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        다양성 보장 (MMR 스타일)
        
        Args:
            results: 정렬된 결과
            top_k: 선택할 결과 수
        
        Returns:
            다양성이 보장된 결과
        """
        if len(results) <= top_k:
            return results
        
        selected = []
        remaining = results.copy()
        
        # 모달리티별 최소 개수 보장
        modality_counts = defaultdict(int)
        min_per_modality = max(1, top_k // 4)  # 최소 25%
        
        # 1단계: 각 모달리티에서 최소 개수 선택
        for modality in ['text', 'image', 'audio']:
            modality_results = [r for r in remaining if r.get('modality') == modality]
            
            for result in modality_results[:min_per_modality]:
                if len(selected) < top_k:
                    selected.append(result)
                    remaining.remove(result)
                    modality_counts[modality] += 1
        
        # 2단계: 나머지는 점수 기반 + 다양성
        while len(selected) < top_k and remaining:
            best_idx = 0
            best_score = -float('inf')
            
            for idx, candidate in enumerate(remaining):
                # 기본 점수
                score = candidate['multimodal_score']
                
                # 모달리티 다양성 보너스
                modality = candidate.get('modality', 'text')
                if modality_counts[modality] < len(selected) / 3:
                    score *= 1.2  # 20% 보너스
                
                # 콘텐츠 유사도 페널티 (간단한 버전)
                similarity_penalty = self._calculate_similarity_penalty(
                    candidate,
                    selected
                )
                score *= (1.0 - similarity_penalty)
                
                if score > best_score:
                    best_score = score
                    best_idx = idx
            
            # 선택
            selected_result = remaining.pop(best_idx)
            selected.append(selected_result)
            modality_counts[selected_result.get('modality', 'text')] += 1
        
        return selected
    
    def _calculate_similarity_penalty(
        self,
        candidate: Dict[str, Any],
        selected: List[Dict[str, Any]]
    ) -> float:
        """
        유사도 페널티 계산
        
        Args:
            candidate: 후보 결과
            selected: 이미 선택된 결과
        
        Returns:
            페널티 (0.0 ~ 1.0)
        """
        if not selected:
            return 0.0
        
        # 같은 문서 ID 확인
        candidate_doc_id = candidate.get('document_id')
        if candidate_doc_id:
            for result in selected:
                if result.get('document_id') == candidate_doc_id:
                    return 0.5  # 같은 문서면 50% 페널티
        
        # 콘텐츠 유사도 (간단한 버전)
        candidate_text = str(candidate.get('content', ''))[:200]
        max_similarity = 0.0
        
        for result in selected:
            result_text = str(result.get('content', ''))[:200]
            similarity = self._text_similarity(candidate_text, result_text)
            max_similarity = max(max_similarity, similarity)
        
        # 임계값 이상이면 페널티
        if max_similarity > self.diversity_threshold:
            return 0.3  # 30% 페널티
        
        return 0.0
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """간단한 텍스트 유사도"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _update_stats(
        self,
        original_results: List[Dict[str, Any]],
        final_results: List[Dict[str, Any]]
    ):
        """통계 업데이트"""
        if not original_results or not final_results:
            return
        
        # 평균 점수 개선 계산
        original_avg = np.mean([r.get('score', 0.0) for r in original_results[:len(final_results)]])
        final_avg = np.mean([r.get('multimodal_score', 0.0) for r in final_results])
        
        improvement = final_avg - original_avg
        
        # 이동 평균
        alpha = 0.1
        self.stats["avg_score_improvement"] = (
            alpha * improvement +
            (1 - alpha) * self.stats["avg_score_improvement"]
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        return {
            **self.stats,
            "weights": {
                "clip": self.clip_weight,
                "colpali": self.colpali_weight,
                "text": self.text_weight
            },
            "cross_modal_boost": self.cross_modal_boost,
            "diversity_threshold": self.diversity_threshold
        }


# Global instance
_multimodal_reranker: Optional[MultimodalReranker] = None


def get_multimodal_reranker(
    clip_weight: float = 0.4,
    colpali_weight: float = 0.3,
    text_weight: float = 0.3
) -> MultimodalReranker:
    """Get global multimodal reranker instance"""
    global _multimodal_reranker
    
    if _multimodal_reranker is None:
        _multimodal_reranker = MultimodalReranker(
            clip_weight=clip_weight,
            colpali_weight=colpali_weight,
            text_weight=text_weight
        )
    
    return _multimodal_reranker
