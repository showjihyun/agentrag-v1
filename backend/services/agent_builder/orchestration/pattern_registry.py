"""
Pattern Registry
오케스트레이션 패턴 정보 및 메타데이터 관리
"""

from typing import Dict, List, Any, Optional


class PatternRegistry:
    """오케스트레이션 패턴 레지스트리"""
    
    # 패턴 정보 정의 (frontend의 orchestration.ts와 동기화)
    _patterns = {
        # 핵심 패턴
        "sequential": {
            "name": "순차 실행",
            "description": "Agent들이 순서대로 실행되며, 이전 Agent의 출력이 다음 Agent의 입력이 됩니다.",
            "category": "core",
            "complexity": "simple",
            "use_case": "단계별 처리가 필요한 작업 (데이터 수집 → 분석 → 보고서 작성)",
            "benefits": ["단순하고 예측 가능한 실행 흐름", "디버깅 용이", "리소스 효율적"],
            "requirements": ["Agent 간 명확한 입출력 정의", "순서 의존성 고려"],
            "estimated_setup_time": "5-10분"
        },
        "parallel": {
            "name": "병렬 실행",
            "description": "Agent들이 동시에 실행되며, 모든 결과를 집계하여 최종 출력을 생성합니다.",
            "category": "core",
            "complexity": "simple",
            "use_case": "독립적인 작업의 동시 처리 (다중 검색, 번역, 요약)",
            "benefits": ["빠른 실행 속도", "높은 처리량", "작업 분산"],
            "requirements": ["독립적인 Agent 작업", "결과 집계 로직"],
            "estimated_setup_time": "10-15분"
        },
        "hierarchical": {
            "name": "계층적 관리",
            "description": "매니저 Agent가 워커 Agent들을 관리하고 작업을 위임합니다.",
            "category": "core",
            "complexity": "medium",
            "use_case": "복잡한 프로젝트 관리 (매니저 → 연구원 → 검토자 → 실행자)",
            "benefits": ["명확한 책임 분담", "확장 가능한 구조", "품질 관리"],
            "requirements": ["매니저 Agent 설정", "역할별 Agent 구성", "위임 규칙 정의"],
            "estimated_setup_time": "20-30분"
        },
        "adaptive": {
            "name": "적응형 라우팅",
            "description": "실행 중 상황에 따라 동적으로 Agent 선택 및 경로를 조정합니다.",
            "category": "core",
            "complexity": "medium",
            "use_case": "상황별 대응이 필요한 작업 (고객 문의 유형별 라우팅)",
            "benefits": ["유연한 실행 흐름", "상황별 최적화", "효율적 리소스 사용"],
            "requirements": ["라우팅 조건 정의", "상황 분석 로직", "대체 경로 설정"],
            "estimated_setup_time": "25-35분"
        },
        
        # 2025년 트렌드 패턴
        "consensus_building": {
            "name": "합의 구축",
            "description": "Agent들이 토론하고 협상하여 최적의 해결책에 대한 합의를 도출합니다.",
            "category": "2025_trends",
            "complexity": "complex",
            "use_case": "의사결정이 필요한 복잡한 문제 (전략 수립, 정책 결정)",
            "benefits": ["높은 품질의 결정", "다양한 관점 반영", "투명한 의사결정 과정"],
            "requirements": ["토론 규칙 설정", "합의 기준 정의", "중재 메커니즘"],
            "estimated_setup_time": "40-60분"
        },
        "dynamic_routing": {
            "name": "동적 라우팅",
            "description": "실시간 Agent 성능과 상황을 분석하여 최적의 실행 경로를 선택합니다.",
            "category": "2025_trends",
            "complexity": "complex",
            "use_case": "실시간 최적화가 필요한 작업 (트래픽 기반 라우팅)",
            "benefits": ["실시간 최적화", "성능 기반 선택", "자동 부하 분산"],
            "requirements": ["성능 모니터링", "라우팅 알고리즘", "실시간 분석"],
            "estimated_setup_time": "45-60분"
        },
        "swarm_intelligence": {
            "name": "군집 지능",
            "description": "다수의 Agent가 협력하여 집단 지능을 발휘하고 최적해를 탐색합니다.",
            "category": "2025_trends",
            "complexity": "complex",
            "use_case": "최적화 문제 해결 (경로 최적화, 리소스 배치)",
            "benefits": ["집단 지능 활용", "강건한 해결책", "분산 탐색"],
            "requirements": ["군집 알고리즘", "정보 공유 메커니즘", "수렴 조건"],
            "estimated_setup_time": "50-70분"
        },
        "event_driven": {
            "name": "이벤트 기반",
            "description": "특정 이벤트 발생 시 해당 Agent가 자동으로 반응하고 처리합니다.",
            "category": "2025_trends",
            "complexity": "medium",
            "use_case": "실시간 모니터링 및 대응 (알림, 자동 대응 시스템)",
            "benefits": ["실시간 반응", "자동화된 대응", "효율적 리소스 사용"],
            "requirements": ["이벤트 정의", "트리거 조건", "반응 규칙"],
            "estimated_setup_time": "30-45분"
        },
        "reflection": {
            "name": "자기 성찰",
            "description": "Agent들이 자신의 성과를 분석하고 개선점을 찾아 지속적으로 발전합니다.",
            "category": "2025_trends",
            "complexity": "complex",
            "use_case": "지속적 개선이 필요한 작업 (품질 향상, 학습 최적화)",
            "benefits": ["지속적 개선", "자가 학습", "성능 최적화"],
            "requirements": ["성과 평가 기준", "개선 알고리즘", "피드백 루프"],
            "estimated_setup_time": "35-50분"
        },
        
        # 2026년 차세대 패턴
        "neuromorphic": {
            "name": "뇌 모방 처리",
            "description": "뇌의 신경망 구조를 모방하여 Agent 간 연결과 정보 처리를 최적화합니다.",
            "category": "2026_nextgen",
            "complexity": "complex",
            "use_case": "복잡한 패턴 인식 및 학습 (이미지 분석, 자연어 이해)",
            "benefits": ["생물학적 효율성", "적응적 학습", "병렬 처리"],
            "requirements": ["신경망 모델링", "시냅스 가중치", "학습 알고리즘"],
            "estimated_setup_time": "60-90분"
        },
        "quantum_enhanced": {
            "name": "양자 강화",
            "description": "양자 컴퓨팅 원리를 활용하여 Agent 간 중첩 상태와 얽힘을 구현합니다.",
            "category": "2026_nextgen",
            "complexity": "complex",
            "use_case": "복잡한 최적화 문제 (암호화, 시뮬레이션)",
            "benefits": ["지수적 처리 능력", "병렬 탐색", "양자 우위"],
            "requirements": ["양자 시뮬레이터", "얽힘 관리", "측정 전략"],
            "estimated_setup_time": "90-120분"
        },
        "bio_inspired": {
            "name": "생물학적 영감",
            "description": "생물학적 시스템의 원리를 모방하여 Agent 생태계를 구성합니다.",
            "category": "2026_nextgen",
            "complexity": "complex",
            "use_case": "자연스러운 협력 시스템 (생태계 시뮬레이션)",
            "benefits": ["자연스러운 협력", "자가 조직화", "환경 적응"],
            "requirements": ["생태계 모델링", "진화 알고리즘", "환경 상호작용"],
            "estimated_setup_time": "70-100분"
        },
        "self_evolving": {
            "name": "자가 진화",
            "description": "Agent들이 스스로 구조와 알고리즘을 진화시켜 성능을 향상시킵니다.",
            "category": "2026_nextgen",
            "complexity": "complex",
            "use_case": "장기적 최적화가 필요한 시스템 (자동 개선)",
            "benefits": ["자동 최적화", "장기적 개선", "적응적 진화"],
            "requirements": ["진화 알고리즘", "적합도 함수", "변이 메커니즘"],
            "estimated_setup_time": "80-110분"
        },
        "federated": {
            "name": "연합 학습",
            "description": "분산된 Agent들이 데이터를 공유하지 않고도 협력하여 학습합니다.",
            "category": "2026_nextgen",
            "complexity": "complex",
            "use_case": "프라이버시 보호 학습 (의료 데이터, 금융 데이터)",
            "benefits": ["프라이버시 보호", "분산 학습", "데이터 보안"],
            "requirements": ["연합 알고리즘", "암호화 통신", "집계 메커니즘"],
            "estimated_setup_time": "60-80분"
        },
        "emotional_ai": {
            "name": "감정 인식 AI",
            "description": "Agent들이 감정 상태를 인식하고 이를 바탕으로 협력 방식을 조정합니다.",
            "category": "2026_nextgen",
            "complexity": "complex",
            "use_case": "인간-AI 상호작용 (고객 서비스, 교육)",
            "benefits": ["감정적 지능", "인간 친화적", "맥락적 이해"],
            "requirements": ["감정 분석 모델", "반응 규칙", "감정 상태 관리"],
            "estimated_setup_time": "50-70분"
        },
        "predictive": {
            "name": "예측적 오케스트레이션",
            "description": "미래 상황을 예측하여 사전에 Agent 배치와 작업을 최적화합니다.",
            "category": "2026_nextgen",
            "complexity": "complex",
            "use_case": "예측 기반 최적화 (수요 예측, 리소스 계획)",
            "benefits": ["사전 최적화", "예측 기반 결정", "리스크 관리"],
            "requirements": ["예측 모델", "시나리오 분석", "최적화 알고리즘"],
            "estimated_setup_time": "65-85분"
        }
    }
    
    # 패턴별 추천 Agent 역할
    _recommended_agents = {
        "sequential": [
            {"name": "데이터 수집가", "role": "worker", "priority": 1},
            {"name": "분석가", "role": "worker", "priority": 2},
            {"name": "보고서 작성자", "role": "synthesizer", "priority": 3}
        ],
        "parallel": [
            {"name": "검색 전문가", "role": "specialist", "priority": 1},
            {"name": "번역가", "role": "specialist", "priority": 1},
            {"name": "요약 전문가", "role": "specialist", "priority": 1},
            {"name": "결과 통합자", "role": "synthesizer", "priority": 2}
        ],
        "hierarchical": [
            {"name": "프로젝트 매니저", "role": "manager", "priority": 1},
            {"name": "연구원 A", "role": "worker", "priority": 2},
            {"name": "연구원 B", "role": "worker", "priority": 2},
            {"name": "품질 검토자", "role": "critic", "priority": 3}
        ],
        "consensus_building": [
            {"name": "전문가 A", "role": "specialist", "priority": 1},
            {"name": "전문가 B", "role": "specialist", "priority": 1},
            {"name": "전문가 C", "role": "specialist", "priority": 1},
            {"name": "중재자", "role": "coordinator", "priority": 2}
        ],
        "swarm_intelligence": [
            {"name": "탐색자 1", "role": "worker", "priority": 1},
            {"name": "탐색자 2", "role": "worker", "priority": 1},
            {"name": "탐색자 3", "role": "worker", "priority": 1},
            {"name": "조율자", "role": "coordinator", "priority": 2}
        ]
    }
    
    # 패턴별 설정 템플릿
    _configuration_templates = {
        "sequential": {
            "supervisor_config": {
                "enabled": False,
                "llm_provider": "ollama",
                "llm_model": "llama3.1",
                "max_iterations": 5,
                "decision_strategy": "llm_based"
            },
            "communication_rules": {
                "allow_direct_communication": True,
                "enable_broadcast": False,
                "require_consensus": False,
                "max_negotiation_rounds": 1
            },
            "performance_thresholds": {
                "max_execution_time": 180000,  # 3분
                "min_success_rate": 0.9,
                "max_token_usage": 5000
            }
        },
        "parallel": {
            "supervisor_config": {
                "enabled": False,
                "llm_provider": "ollama",
                "llm_model": "llama3.1",
                "max_iterations": 3,
                "decision_strategy": "llm_based"
            },
            "communication_rules": {
                "allow_direct_communication": False,
                "enable_broadcast": True,
                "require_consensus": False,
                "max_negotiation_rounds": 1
            },
            "performance_thresholds": {
                "max_execution_time": 120000,  # 2분
                "min_success_rate": 0.8,
                "max_token_usage": 8000
            }
        },
        "hierarchical": {
            "supervisor_config": {
                "enabled": True,
                "llm_provider": "ollama",
                "llm_model": "llama3.1",
                "max_iterations": 10,
                "decision_strategy": "llm_based"
            },
            "communication_rules": {
                "allow_direct_communication": True,
                "enable_broadcast": False,
                "require_consensus": False,
                "max_negotiation_rounds": 2
            },
            "performance_thresholds": {
                "max_execution_time": 300000,  # 5분
                "min_success_rate": 0.85,
                "max_token_usage": 12000
            }
        },
        "consensus_building": {
            "supervisor_config": {
                "enabled": True,
                "llm_provider": "ollama",
                "llm_model": "llama3.1",
                "max_iterations": 15,
                "decision_strategy": "consensus"
            },
            "communication_rules": {
                "allow_direct_communication": True,
                "enable_broadcast": True,
                "require_consensus": True,
                "max_negotiation_rounds": 5
            },
            "performance_thresholds": {
                "max_execution_time": 600000,  # 10분
                "min_success_rate": 0.75,
                "max_token_usage": 20000
            }
        }
    }
    
    @classmethod
    def get_all_patterns(cls) -> Dict[str, Dict[str, Any]]:
        """모든 패턴 정보 반환"""
        return cls._patterns.copy()
    
    @classmethod
    def get_pattern(cls, pattern_type: str) -> Optional[Dict[str, Any]]:
        """특정 패턴 정보 반환"""
        return cls._patterns.get(pattern_type)
    
    @classmethod
    def get_recommended_agents(cls, pattern_type: str) -> List[Dict[str, Any]]:
        """패턴별 추천 Agent 역할 반환"""
        return cls._recommended_agents.get(pattern_type, [
            {"name": "범용 에이전트", "role": "worker", "priority": 1},
            {"name": "전문가", "role": "specialist", "priority": 2},
            {"name": "조율자", "role": "coordinator", "priority": 3}
        ])
    
    @classmethod
    def get_configuration_template(cls, pattern_type: str) -> Dict[str, Any]:
        """패턴별 설정 템플릿 반환"""
        return cls._configuration_templates.get(pattern_type, cls._configuration_templates["sequential"])
    
    @classmethod
    def get_example_workflows(cls, pattern_type: str) -> List[Dict[str, Any]]:
        """패턴별 예제 워크플로우 반환"""
        examples = {
            "sequential": [
                {
                    "name": "문서 처리 파이프라인",
                    "description": "PDF 추출 → 텍스트 분석 → 요약 생성",
                    "agents": ["PDF 추출기", "텍스트 분석기", "요약 생성기"]
                },
                {
                    "name": "고객 문의 처리",
                    "description": "문의 분류 → 정보 검색 → 답변 생성",
                    "agents": ["분류기", "검색기", "답변 생성기"]
                }
            ],
            "parallel": [
                {
                    "name": "다중 소스 정보 수집",
                    "description": "여러 API에서 동시에 데이터 수집 후 통합",
                    "agents": ["뉴스 수집기", "소셜미디어 수집기", "학술 논문 수집기", "통합기"]
                },
                {
                    "name": "다국어 번역",
                    "description": "하나의 텍스트를 여러 언어로 동시 번역",
                    "agents": ["영어 번역기", "중국어 번역기", "일본어 번역기", "품질 검증기"]
                }
            ],
            "hierarchical": [
                {
                    "name": "연구 프로젝트 관리",
                    "description": "연구 매니저가 여러 연구원에게 작업 할당 및 관리",
                    "agents": ["연구 매니저", "데이터 연구원", "분석 연구원", "보고서 작성자", "품질 검토자"]
                }
            ]
        }
        
        return examples.get(pattern_type, [])
    
    @classmethod
    def get_patterns_by_category(cls, category: str) -> Dict[str, Dict[str, Any]]:
        """카테고리별 패턴 반환"""
        return {
            pattern_id: pattern_info 
            for pattern_id, pattern_info in cls._patterns.items() 
            if pattern_info["category"] == category
        }
    
    @classmethod
    def get_patterns_by_complexity(cls, complexity: str) -> Dict[str, Dict[str, Any]]:
        """복잡도별 패턴 반환"""
        return {
            pattern_id: pattern_info 
            for pattern_id, pattern_info in cls._patterns.items() 
            if pattern_info["complexity"] == complexity
        }
    
    @classmethod
    def register_pattern(
        cls, 
        pattern_id: str, 
        pattern_info: Dict[str, Any],
        recommended_agents: Optional[List[Dict[str, Any]]] = None,
        configuration_template: Optional[Dict[str, Any]] = None
    ):
        """새로운 패턴 등록"""
        cls._patterns[pattern_id] = pattern_info
        
        if recommended_agents:
            cls._recommended_agents[pattern_id] = recommended_agents
        
        if configuration_template:
            cls._configuration_templates[pattern_id] = configuration_template