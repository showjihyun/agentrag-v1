/**
 * Agent 오케스트레이션 관련 상수 및 타입 정의
 */

// Orchestration pattern types
export type OrchestrationTypeValue = 
  // Core Patterns
  | 'sequential' | 'parallel' | 'hierarchical' | 'adaptive'
  // 2025 Trends
  | 'consensus_building' | 'dynamic_routing' | 'swarm_intelligence' | 'event_driven' | 'reflection'
  // 2026 Next-Gen
  | 'neuromorphic' | 'quantum_enhanced' | 'bio_inspired' | 'self_evolving' 
  | 'federated' | 'emotional_ai' | 'predictive';

// Orchestration pattern metadata
export interface OrchestrationPattern {
  id: OrchestrationTypeValue;
  name: string;
  description: string;
  category: 'core' | '2025_trends' | '2026_nextgen';
  icon: string;
  color: string;
  complexity: 'simple' | 'medium' | 'complex';
  useCase: string;
  benefits: string[];
  requirements: string[];
  estimatedSetupTime: string;
}

// Core Patterns
export const CORE_ORCHESTRATION_TYPES: Record<string, OrchestrationPattern> = {
  sequential: {
    id: 'sequential',
    name: '순차 실행',
    description: 'Agent들이 순서대로 실행되며, 이전 Agent의 출력이 다음 Agent의 입력이 됩니다.',
    category: 'core',
    icon: 'ArrowRight',
    color: '#3B82F6',
    complexity: 'simple',
    useCase: '단계별 처리가 필요한 작업 (데이터 수집 → 분석 → 보고서 작성)',
    benefits: ['단순하고 예측 가능한 실행 흐름', '디버깅 용이', '리소스 효율적'],
    requirements: ['Agent 간 명확한 입출력 정의', '순서 의존성 고려'],
    estimatedSetupTime: '5-10분'
  },
  parallel: {
    id: 'parallel',
    name: '병렬 실행',
    description: 'Agent들이 동시에 실행되며, 모든 결과를 집계하여 최종 출력을 생성합니다.',
    category: 'core',
    icon: 'Zap',
    color: '#10B981',
    complexity: 'simple',
    useCase: '독립적인 작업의 동시 처리 (다중 검색, 번역, 요약)',
    benefits: ['빠른 실행 속도', '높은 처리량', '작업 분산'],
    requirements: ['독립적인 Agent 작업', '결과 집계 로직'],
    estimatedSetupTime: '10-15분'
  },
  hierarchical: {
    id: 'hierarchical',
    name: '계층적 관리',
    description: '매니저 Agent가 워커 Agent들을 관리하고 작업을 위임합니다.',
    category: 'core',
    icon: 'Users',
    color: '#8B5CF6',
    complexity: 'medium',
    useCase: '복잡한 프로젝트 관리 (매니저 → 연구원 → 검토자 → 실행자)',
    benefits: ['명확한 책임 분담', '확장 가능한 구조', '품질 관리'],
    requirements: ['매니저 Agent 설정', '역할별 Agent 구성', '위임 규칙 정의'],
    estimatedSetupTime: '20-30분'
  },
  adaptive: {
    id: 'adaptive',
    name: '적응형 라우팅',
    description: '실행 중 상황에 따라 동적으로 Agent 선택 및 경로를 조정합니다.',
    category: 'core',
    icon: 'GitBranch',
    color: '#F59E0B',
    complexity: 'medium',
    useCase: '상황별 대응이 필요한 작업 (고객 문의 유형별 라우팅)',
    benefits: ['유연한 실행 흐름', '상황별 최적화', '효율적 리소스 사용'],
    requirements: ['라우팅 조건 정의', '상황 분석 로직', '대체 경로 설정'],
    estimatedSetupTime: '25-35분'
  }
};

// 2025 Trend Patterns
export const TRENDS_2025_ORCHESTRATION_TYPES: Record<string, OrchestrationPattern> = {
  consensus_building: {
    id: 'consensus_building',
    name: '합의 구축',
    description: 'Agent들이 토론하고 협상하여 최적의 해결책에 대한 합의를 도출합니다.',
    category: '2025_trends',
    icon: 'MessageSquare',
    color: '#EF4444',
    complexity: 'complex',
    useCase: '의사결정이 필요한 복잡한 문제 (전략 수립, 정책 결정)',
    benefits: ['높은 품질의 결정', '다양한 관점 반영', '투명한 의사결정 과정'],
    requirements: ['토론 규칙 설정', '합의 기준 정의', '중재 메커니즘'],
    estimatedSetupTime: '40-60분'
  },
  dynamic_routing: {
    id: 'dynamic_routing',
    name: '동적 라우팅',
    description: '실시간 Agent 성능과 상황을 분석하여 최적의 실행 경로를 선택합니다.',
    category: '2025_trends',
    icon: 'Route',
    color: '#06B6D4',
    complexity: 'complex',
    useCase: '실시간 최적화가 필요한 작업 (트래픽 기반 라우팅)',
    benefits: ['실시간 최적화', '성능 기반 선택', '자동 부하 분산'],
    requirements: ['성능 모니터링', '라우팅 알고리즘', '실시간 분석'],
    estimatedSetupTime: '45-60분'
  },
  swarm_intelligence: {
    id: 'swarm_intelligence',
    name: '군집 지능',
    description: '다수의 Agent가 협력하여 집단 지능을 발휘하고 최적해를 탐색합니다.',
    category: '2025_trends',
    icon: 'Hexagon',
    color: '#84CC16',
    complexity: 'complex',
    useCase: '최적화 문제 해결 (경로 최적화, 리소스 배치)',
    benefits: ['집단 지능 활용', '강건한 해결책', '분산 탐색'],
    requirements: ['군집 알고리즘', '정보 공유 메커니즘', '수렴 조건'],
    estimatedSetupTime: '50-70분'
  },
  event_driven: {
    id: 'event_driven',
    name: '이벤트 기반',
    description: '특정 이벤트 발생 시 해당 Agent가 자동으로 반응하고 처리합니다.',
    category: '2025_trends',
    icon: 'Bell',
    color: '#F97316',
    complexity: 'medium',
    useCase: '실시간 모니터링 및 대응 (알림, 자동 대응 시스템)',
    benefits: ['실시간 반응', '자동화된 대응', '효율적 리소스 사용'],
    requirements: ['이벤트 정의', '트리거 조건', '반응 규칙'],
    estimatedSetupTime: '30-45분'
  },
  reflection: {
    id: 'reflection',
    name: '자기 성찰',
    description: 'Agent들이 자신의 성과를 분석하고 개선점을 찾아 지속적으로 발전합니다.',
    category: '2025_trends',
    icon: 'RefreshCw',
    color: '#A855F7',
    complexity: 'complex',
    useCase: '지속적 개선이 필요한 작업 (품질 향상, 학습 최적화)',
    benefits: ['지속적 개선', '자가 학습', '성능 최적화'],
    requirements: ['성과 평가 기준', '개선 알고리즘', '피드백 루프'],
    estimatedSetupTime: '35-50분'
  }
};

// 2026 Next-Generation Patterns
export const TRENDS_2026_ORCHESTRATION_TYPES: Record<string, OrchestrationPattern> = {
  neuromorphic: {
    id: 'neuromorphic',
    name: '뇌 모방 처리',
    description: '뇌의 신경망 구조를 모방하여 Agent 간 연결과 정보 처리를 최적화합니다.',
    category: '2026_nextgen',
    icon: 'Brain',
    color: '#EC4899',
    complexity: 'complex',
    useCase: '복잡한 패턴 인식 및 학습 (이미지 분석, 자연어 이해)',
    benefits: ['생물학적 효율성', '적응적 학습', '병렬 처리'],
    requirements: ['신경망 모델링', '시냅스 가중치', '학습 알고리즘'],
    estimatedSetupTime: '60-90분'
  },
  quantum_enhanced: {
    id: 'quantum_enhanced',
    name: '양자 강화',
    description: '양자 컴퓨팅 원리를 활용하여 Agent 간 중첩 상태와 얽힘을 구현합니다.',
    category: '2026_nextgen',
    icon: 'Atom',
    color: '#6366F1',
    complexity: 'complex',
    useCase: '복잡한 최적화 문제 (암호화, 시뮬레이션)',
    benefits: ['지수적 처리 능력', '병렬 탐색', '양자 우위'],
    requirements: ['양자 시뮬레이터', '얽힘 관리', '측정 전략'],
    estimatedSetupTime: '90-120분'
  },
  bio_inspired: {
    id: 'bio_inspired',
    name: '생물학적 영감',
    description: '생물학적 시스템의 원리를 모방하여 Agent 생태계를 구성합니다.',
    category: '2026_nextgen',
    icon: 'Leaf',
    color: '#059669',
    complexity: 'complex',
    useCase: '자연스러운 협력 시스템 (생태계 시뮬레이션)',
    benefits: ['자연스러운 협력', '자가 조직화', '환경 적응'],
    requirements: ['생태계 모델링', '진화 알고리즘', '환경 상호작용'],
    estimatedSetupTime: '70-100분'
  },
  self_evolving: {
    id: 'self_evolving',
    name: '자가 진화',
    description: 'Agent들이 스스로 구조와 알고리즘을 진화시켜 성능을 향상시킵니다.',
    category: '2026_nextgen',
    icon: 'TrendingUp',
    color: '#DC2626',
    complexity: 'complex',
    useCase: '장기적 최적화가 필요한 시스템 (자동 개선)',
    benefits: ['자동 최적화', '장기적 개선', '적응적 진화'],
    requirements: ['진화 알고리즘', '적합도 함수', '변이 메커니즘'],
    estimatedSetupTime: '80-110분'
  },
  federated: {
    id: 'federated',
    name: '연합 학습',
    description: '분산된 Agent들이 데이터를 공유하지 않고도 협력하여 학습합니다.',
    category: '2026_nextgen',
    icon: 'Network',
    color: '#7C3AED',
    complexity: 'complex',
    useCase: '프라이버시 보호 학습 (의료 데이터, 금융 데이터)',
    benefits: ['프라이버시 보호', '분산 학습', '데이터 보안'],
    requirements: ['연합 알고리즘', '암호화 통신', '집계 메커니즘'],
    estimatedSetupTime: '60-80분'
  },
  emotional_ai: {
    id: 'emotional_ai',
    name: '감정 인식 AI',
    description: 'Agent들이 감정 상태를 인식하고 이를 바탕으로 협력 방식을 조정합니다.',
    category: '2026_nextgen',
    icon: 'Heart',
    color: '#F43F5E',
    complexity: 'complex',
    useCase: '인간-AI 상호작용 (고객 서비스, 교육)',
    benefits: ['감정적 지능', '인간 친화적', '맥락적 이해'],
    requirements: ['감정 분석 모델', '반응 규칙', '감정 상태 관리'],
    estimatedSetupTime: '50-70분'
  },
  predictive: {
    id: 'predictive',
    name: '예측적 오케스트레이션',
    description: '미래 상황을 예측하여 사전에 Agent 배치와 작업을 최적화합니다.',
    category: '2026_nextgen',
    icon: 'Crystal',
    color: '#0891B2',
    complexity: 'complex',
    useCase: '예측 기반 최적화 (수요 예측, 리소스 계획)',
    benefits: ['사전 최적화', '예측 기반 결정', '리스크 관리'],
    requirements: ['예측 모델', '시나리오 분석', '최적화 알고리즘'],
    estimatedSetupTime: '65-85분'
  }
};

// All orchestration types
export const ORCHESTRATION_TYPES: Record<string, OrchestrationPattern> = {
  ...CORE_ORCHESTRATION_TYPES,
  ...TRENDS_2025_ORCHESTRATION_TYPES,
  ...TRENDS_2026_ORCHESTRATION_TYPES
};

// Category colors
export const CATEGORY_COLORS = {
  core: '#3B82F6',
  '2025_trends': '#10B981',
  '2026_nextgen': '#8B5CF6'
};

// Agent role types
export type AgentRole = 'manager' | 'worker' | 'critic' | 'synthesizer' | 'coordinator' | 'specialist';

// Agent role definitions
export const AGENT_ROLES: Record<AgentRole, { name: string; description: string; color: string; icon: string }> = {
  manager: {
    name: '매니저',
    description: '다른 Agent들을 조정하고 작업을 위임합니다',
    color: '#8B5CF6',
    icon: 'Crown'
  },
  worker: {
    name: '워커',
    description: '구체적인 작업을 수행하는 실행 Agent입니다',
    color: '#3B82F6',
    icon: 'Wrench'
  },
  critic: {
    name: '비평가',
    description: '결과를 검토하고 품질을 평가합니다',
    color: '#EF4444',
    icon: 'Eye'
  },
  synthesizer: {
    name: '종합자',
    description: '여러 결과를 통합하고 최종 출력을 생성합니다',
    color: '#10B981',
    icon: 'Merge'
  },
  coordinator: {
    name: '조정자',
    description: 'Agent 간 협력과 통신을 조정합니다',
    color: '#F59E0B',
    icon: 'Users'
  },
  specialist: {
    name: '전문가',
    description: '특정 도메인의 전문 지식을 제공합니다',
    color: '#06B6D4',
    icon: 'Star'
  }
};

// Communication types
export type CommunicationType = 'direct' | 'broadcast' | 'negotiation' | 'feedback' | 'consensus';

// Communication type definitions
export const COMMUNICATION_TYPES: Record<CommunicationType, { name: string; description: string; color: string }> = {
  direct: {
    name: '직접 통신',
    description: '두 Agent 간 직접적인 메시지 교환',
    color: '#3B82F6'
  },
  broadcast: {
    name: '브로드캐스트',
    description: '한 Agent가 모든 Agent에게 메시지 전송',
    color: '#10B981'
  },
  negotiation: {
    name: '협상',
    description: 'Agent 간 협상을 통한 합의 도출',
    color: '#F59E0B'
  },
  feedback: {
    name: '피드백',
    description: '결과에 대한 피드백 및 개선 제안',
    color: '#8B5CF6'
  },
  consensus: {
    name: '합의',
    description: '다수 Agent 간 합의 형성',
    color: '#EF4444'
  }
};

// Supervisor configuration types
export interface SupervisorConfig {
  enabled: boolean;
  llm_provider: string;
  llm_model: string;
  max_iterations: number;
  decision_strategy: 'llm_based' | 'consensus' | 'weighted_voting' | 'expert_system';
  fallback_agent_id?: string;
  coordination_rules?: string[];
  performance_thresholds?: Record<string, number>;
}

// Default supervisor configuration
export const DEFAULT_SUPERVISOR_CONFIG: SupervisorConfig = {
  enabled: false,
  llm_provider: 'ollama',
  llm_model: 'llama3.1',
  max_iterations: 10,
  decision_strategy: 'llm_based',
  coordination_rules: [
    '성능이 낮은 Agent는 우선순위를 낮춘다',
    'Agents with errors are retried or replaced',
    'On timeout, proceed to next Agent'
  ],
  performance_thresholds: {
    response_time: 30000, // 30 seconds
    success_rate: 0.8,    // 80%
    token_efficiency: 0.7  // 70%
  }
};