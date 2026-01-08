"""Factory for creating memory strategy instances."""

from typing import Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session

from backend.core.memory.base import BaseMemoryStrategy
from backend.core.memory.buffer_memory import BufferMemoryStrategy
from backend.core.memory.summary_memory import SummaryMemoryStrategy
from backend.core.memory.vector_memory import VectorMemoryStrategy
from backend.core.memory.hybrid_memory import HybridMemoryStrategy

class MemoryStrategyFactory:
    """Factory for creating memory strategy instances."""
    
    def create_strategy(
        self,
        memory_type: str,
        session_id: UUID,
        config: Dict[str, Any],
        db_session: Session
    ) -> BaseMemoryStrategy:
        """Create a memory strategy instance based on type."""
        
        if memory_type == 'buffer':
            return BufferMemoryStrategy(session_id, config, db_session)
        elif memory_type == 'summary':
            return SummaryMemoryStrategy(session_id, config, db_session)
        elif memory_type == 'vector':
            return VectorMemoryStrategy(session_id, config, db_session)
        elif memory_type == 'hybrid':
            return HybridMemoryStrategy(session_id, config, db_session)
        else:
            # Default to buffer memory
            return BufferMemoryStrategy(session_id, config, db_session)
    
    def get_available_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available memory strategies."""
        return {
            'buffer': {
                'name': 'Buffer Memory',
                'description': '최근 N개 메시지를 유지하는 단순한 메모리 전략',
                'config_options': {
                    'buffer_size': {
                        'type': 'integer',
                        'default': 20,
                        'min': 5,
                        'max': 100,
                        'description': '유지할 최근 메시지 수'
                    }
                },
                'pros': ['빠른 응답', '간단한 구현', '낮은 리소스 사용'],
                'cons': ['제한된 컨텍스트', '오래된 정보 손실'],
                'best_for': '짧은 대화, 실시간 응답이 중요한 경우'
            },
            'summary': {
                'name': 'Summary Memory',
                'description': '오래된 대화를 요약하여 컨텍스트를 압축하는 전략',
                'config_options': {
                    'summary_threshold': {
                        'type': 'integer',
                        'default': 50,
                        'min': 20,
                        'max': 200,
                        'description': '요약을 시작할 메시지 수'
                    },
                    'summary_interval': {
                        'type': 'integer',
                        'default': 20,
                        'min': 10,
                        'max': 50,
                        'description': '한 번에 요약할 메시지 수'
                    },
                    'buffer_size': {
                        'type': 'integer',
                        'default': 10,
                        'min': 5,
                        'max': 30,
                        'description': '요약과 함께 유지할 최근 메시지 수'
                    }
                },
                'pros': ['긴 대화 지원', '핵심 정보 보존', '효율적인 토큰 사용'],
                'cons': ['요약 지연', '일부 세부사항 손실', 'LLM 호출 필요'],
                'best_for': '긴 대화, 복잡한 주제 토론'
            },
            'vector': {
                'name': 'Vector Memory',
                'description': '의미적 유사성을 기반으로 관련 메시지를 검색하는 전략',
                'config_options': {
                    'vector_top_k': {
                        'type': 'integer',
                        'default': 5,
                        'min': 1,
                        'max': 20,
                        'description': '검색할 관련 메시지 수'
                    },
                    'buffer_size': {
                        'type': 'integer',
                        'default': 5,
                        'min': 3,
                        'max': 15,
                        'description': '최근 메시지 버퍼 크기'
                    }
                },
                'pros': ['의미적 연관성', '주제 점프 지원', '정확한 컨텍스트'],
                'cons': ['높은 계산 비용', '임베딩 생성 시간', '벡터 DB 필요'],
                'best_for': '복잡한 주제, 이전 대화 참조가 많은 경우',
                'status': 'available'
            },
            'hybrid': {
                'name': 'Hybrid Memory',
                'description': '여러 메모리 전략을 조합하여 사용하는 고급 전략',
                'config_options': {
                    'hybrid_weights': {
                        'type': 'object',
                        'default': {'buffer': 0.4, 'summary': 0.3, 'vector': 0.3},
                        'description': '각 전략의 가중치'
                    },
                    'max_context_messages': {
                        'type': 'integer',
                        'default': 20,
                        'min': 10,
                        'max': 50,
                        'description': '최대 컨텍스트 메시지 수'
                    },
                    'enable_smart_selection': {
                        'type': 'boolean',
                        'default': True,
                        'description': '지능형 메시지 선택 활성화'
                    },
                    'buffer_size': {
                        'type': 'integer',
                        'default': 10,
                        'min': 5,
                        'max': 20,
                        'description': '버퍼 메모리 크기'
                    },
                    'summary_threshold': {
                        'type': 'integer',
                        'default': 30,
                        'min': 20,
                        'max': 100,
                        'description': '요약 시작 임계값'
                    },
                    'vector_top_k': {
                        'type': 'integer',
                        'default': 3,
                        'min': 1,
                        'max': 10,
                        'description': '벡터 검색 결과 수'
                    }
                },
                'pros': ['최적의 성능', '상황별 적응', '모든 장점 결합'],
                'cons': ['복잡한 설정', '높은 리소스 사용', '디버깅 어려움'],
                'best_for': '모든 상황, 최고 품질이 필요한 경우',
                'status': 'available'
            }
        }