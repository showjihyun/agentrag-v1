/**
 * Orchestration Types Constants
 * 
 * Defines all available orchestration patterns for AgentWorkflows
 * including 2025 and 2026 trend patterns.
 */

import {
  GitMerge,
  Layers,
  Network,
  Zap,
  Users,
  Route,
  Waves,
  Radio,
  RotateCcw,
  Brain,
  Atom,
  Dna,
  TrendingUp,
  Globe,
  Heart,
  Target,
  LucideIcon
} from 'lucide-react';

export type OrchestrationTypeValue = 
  // Core patterns (existing)
  | 'sequential' 
  | 'parallel' 
  | 'hierarchical' 
  | 'adaptive'
  // 2025 Trends - Advanced patterns
  | 'consensus_building'
  | 'dynamic_routing'
  | 'swarm_intelligence'
  | 'event_driven'
  | 'reflection'
  // 2026 Trends - Next-generation patterns
  | 'neuromorphic'
  | 'quantum_enhanced'
  | 'bio_inspired'
  | 'self_evolving'
  | 'federated'
  | 'emotional_ai'
  | 'predictive';

export interface OrchestrationTypeInfo {
  id: OrchestrationTypeValue;
  name: string;
  description: string;
  icon: LucideIcon;
  category: 'core' | '2025_trends' | '2026_trends';
  complexity: 'basic' | 'intermediate' | 'advanced' | 'experimental';
  useCases: string[];
  benefits: string[];
  requirements?: string[];
  maturity: 'stable' | 'beta' | 'experimental';
}

export const ORCHESTRATION_TYPES: Record<OrchestrationTypeValue, OrchestrationTypeInfo> = {
  // ============================================================================
  // CORE PATTERNS (Existing)
  // ============================================================================
  sequential: {
    id: 'sequential',
    name: '순차 실행',
    description: '에이전트들이 순서대로 실행되는 기본 패턴입니다. 각 에이전트의 출력이 다음 에이전트의 입력이 됩니다.',
    icon: GitMerge,
    category: 'core',
    complexity: 'basic',
    useCases: ['문서 처리 파이프라인', '단계별 승인 프로세스', '데이터 변환 워크플로우'],
    benefits: ['단순하고 이해하기 쉬움', '디버깅 용이', '예측 가능한 실행 순서'],
    maturity: 'stable'
  },
  
  parallel: {
    id: 'parallel',
    name: '병렬 실행',
    description: '여러 에이전트가 동시에 실행되어 처리 속도를 향상시킵니다. 독립적인 작업에 최적화되어 있습니다.',
    icon: Layers,
    category: 'core',
    complexity: 'basic',
    useCases: ['대용량 데이터 처리', '다중 API 호출', '독립적 분석 작업'],
    benefits: ['빠른 처리 속도', '리소스 효율성', '확장성'],
    maturity: 'stable'
  },
  
  hierarchical: {
    id: 'hierarchical',
    name: '계층적 실행',
    description: '슈퍼바이저 에이전트가 하위 에이전트들을 관리하고 조정하는 계층 구조입니다.',
    icon: Network,
    category: 'core',
    complexity: 'intermediate',
    useCases: ['복잡한 의사결정', '팀 관리 시뮬레이션', '다단계 승인'],
    benefits: ['중앙 집중식 제어', '복잡한 로직 처리', '역할 분담'],
    maturity: 'stable'
  },
  
  adaptive: {
    id: 'adaptive',
    name: '적응형 실행',
    description: '실행 중 상황에 따라 전략을 동적으로 변경하는 지능형 패턴입니다.',
    icon: Zap,
    category: 'core',
    complexity: 'advanced',
    useCases: ['동적 환경 대응', '실시간 최적화', '상황 인식 시스템'],
    benefits: ['유연성', '자동 최적화', '환경 적응'],
    maturity: 'stable'
  },

  // ============================================================================
  // 2025 TRENDS - Advanced Patterns
  // ============================================================================
  consensus_building: {
    id: 'consensus_building',
    name: '합의 기반 실행',
    description: '여러 에이전트가 동일한 작업을 수행하고 결과를 비교하여 최적의 답을 도출합니다.',
    icon: Users,
    category: '2025_trends',
    complexity: 'advanced',
    useCases: ['고위험 의사결정', '품질 검증', '다중 검토 시스템'],
    benefits: ['높은 정확도', '오류 감소', '신뢰성 향상'],
    requirements: ['3개 이상의 에이전트', '투표 메커니즘'],
    maturity: 'beta'
  },

  dynamic_routing: {
    id: 'dynamic_routing',
    name: '동적 라우팅',
    description: '입력 분석을 통해 가장 적합한 전문 에이전트로 작업을 자동 라우팅합니다.',
    icon: Route,
    category: '2025_trends',
    complexity: 'intermediate',
    useCases: ['고객 지원', '전문가 시스템', '멀티도메인 처리'],
    benefits: ['효율성 향상', '전문화', '자동 분류'],
    requirements: ['분류 모델', '전문 에이전트'],
    maturity: 'beta'
  },

  swarm_intelligence: {
    id: 'swarm_intelligence',
    name: '군집 지능',
    description: '많은 단순한 에이전트들이 협력하여 복잡한 문제를 해결하는 생체 모방 패턴입니다.',
    icon: Waves,
    category: '2025_trends',
    complexity: 'advanced',
    useCases: ['최적화 문제', '대규모 탐색', '분산 처리'],
    benefits: ['확장성', '내결함성', '창발적 지능'],
    requirements: ['다수의 에이전트', '통신 프로토콜'],
    maturity: 'beta'
  },

  event_driven: {
    id: 'event_driven',
    name: '이벤트 기반',
    description: '이벤트 발생에 따라 에이전트들이 반응하고 협력하는 비동기 패턴입니다.',
    icon: Radio,
    category: '2025_trends',
    complexity: 'intermediate',
    useCases: ['실시간 모니터링', 'IoT 시스템', '알림 처리'],
    benefits: ['반응성', '확장성', '느슨한 결합'],
    requirements: ['이벤트 버스', '비동기 처리'],
    maturity: 'beta'
  },

  reflection: {
    id: 'reflection',
    name: '성찰 및 개선',
    description: '에이전트가 자신의 출력을 분석하고 개선하는 자기 성찰 패턴입니다.',
    icon: RotateCcw,
    category: '2025_trends',
    complexity: 'advanced',
    useCases: ['코드 생성', '품질 개선', '자가 학습'],
    benefits: ['품질 향상', '자동 개선', '학습 능력'],
    requirements: ['평가 모델', '피드백 루프'],
    maturity: 'beta'
  },

  // ============================================================================
  // 2026 TRENDS - Next-Generation Patterns
  // ============================================================================
  neuromorphic: {
    id: 'neuromorphic',
    name: '뉴로모픽 오케스트레이션',
    description: '인간 뇌의 신경망을 모방한 에너지 효율적인 에이전트 조정 패턴입니다.',
    icon: Brain,
    category: '2026_trends',
    complexity: 'experimental',
    useCases: ['에지 컴퓨팅', '실시간 처리', '저전력 시스템'],
    benefits: ['90% 에너지 절약', '실시간 적응', '병렬 처리'],
    requirements: ['뉴로모픽 하드웨어', '시냅스 모델'],
    maturity: 'experimental'
  },

  quantum_enhanced: {
    id: 'quantum_enhanced',
    name: '양자 강화 워크플로우',
    description: '양자 컴퓨팅 원리를 활용하여 복잡한 최적화 문제를 해결하는 차세대 패턴입니다.',
    icon: Atom,
    category: '2026_trends',
    complexity: 'experimental',
    useCases: ['금융 모델링', '신약 개발', '최적화 문제'],
    benefits: ['1000배 빠른 최적화', '복잡한 문제 해결', '동시 탐색'],
    requirements: ['양자 시뮬레이터', '양자 알고리즘'],
    maturity: 'experimental'
  },

  bio_inspired: {
    id: 'bio_inspired',
    name: '생체 모방 조정',
    description: '개미, 벌 등 자연의 집단 지능을 AI 에이전트에 적용한 생체 모방 패턴입니다.',
    icon: Dna,
    category: '2026_trends',
    complexity: 'advanced',
    useCases: ['경로 최적화', '자원 할당', '집단 의사결정'],
    benefits: ['자가 조직화', '적응성', '견고성'],
    requirements: ['페로몬 모델', '진화 알고리즘'],
    maturity: 'experimental'
  },

  self_evolving: {
    id: 'self_evolving',
    name: '자가 진화',
    description: '에이전트가 스스로 학습하고 진화하여 성능을 지속적으로 개선하는 패턴입니다.',
    icon: TrendingUp,
    category: '2026_trends',
    complexity: 'experimental',
    useCases: ['지속적 개선', '자동 최적화', '적응형 시스템'],
    benefits: ['자동 진화', '성능 향상', '자율성'],
    requirements: ['진화 엔진', '성능 메트릭'],
    maturity: 'experimental'
  },

  federated: {
    id: 'federated',
    name: '연합 네트워크',
    description: '여러 조직의 에이전트가 데이터 공유 없이 협업하는 프라이버시 보장 패턴입니다.',
    icon: Globe,
    category: '2026_trends',
    complexity: 'advanced',
    useCases: ['의료 연합', '금융 컨소시엄', '크로스 도메인 협업'],
    benefits: ['프라이버시 보장', '분산 협업', '확장성'],
    requirements: ['연합 학습', '암호화 통신'],
    maturity: 'experimental'
  },

  emotional_ai: {
    id: 'emotional_ai',
    name: '감정 AI 오케스트레이션',
    description: '인간의 감정 상태를 인식하고 반응하는 감정 지능 기반 에이전트 조정입니다.',
    icon: Heart,
    category: '2026_trends',
    complexity: 'advanced',
    useCases: ['고객 서비스', '교육', '헬스케어'],
    benefits: ['감정 인식', '맞춤형 대응', '사용자 경험 향상'],
    requirements: ['감정 분석 모델', '멀티모달 입력'],
    maturity: 'experimental'
  },

  predictive: {
    id: 'predictive',
    name: '예측적 오케스트레이션',
    description: 'AI가 미래 상황을 예측하여 사전에 워크플로우를 준비하고 최적화하는 패턴입니다.',
    icon: Target,
    category: '2026_trends',
    complexity: 'advanced',
    useCases: ['예방 정비', '리소스 예측', '수요 예측'],
    benefits: ['사전 대응', '효율성', '비용 절약'],
    requirements: ['예측 모델', '시계열 분석'],
    maturity: 'experimental'
  }
};

// Helper functions and derived constants
export const ORCHESTRATION_ICONS = Object.fromEntries(
  Object.entries(ORCHESTRATION_TYPES).map(([key, value]) => [key, value.icon])
) as Record<OrchestrationTypeValue, LucideIcon>;

export const ORCHESTRATION_LABELS = Object.fromEntries(
  Object.entries(ORCHESTRATION_TYPES).map(([key, value]) => [key, value.name])
) as Record<OrchestrationTypeValue, string>;

export const ORCHESTRATION_DESCRIPTIONS = Object.fromEntries(
  Object.entries(ORCHESTRATION_TYPES).map(([key, value]) => [key, value.description])
) as Record<OrchestrationTypeValue, string>;

// Categorized lists
export const CORE_ORCHESTRATION_TYPES = Object.values(ORCHESTRATION_TYPES).filter(
  type => type.category === 'core'
);

export const TRENDS_2025_ORCHESTRATION_TYPES = Object.values(ORCHESTRATION_TYPES).filter(
  type => type.category === '2025_trends'
);

export const TRENDS_2026_ORCHESTRATION_TYPES = Object.values(ORCHESTRATION_TYPES).filter(
  type => type.category === '2026_trends'
);

// Complexity-based lists
export const BASIC_ORCHESTRATION_TYPES = Object.values(ORCHESTRATION_TYPES).filter(
  type => type.complexity === 'basic'
);

export const INTERMEDIATE_ORCHESTRATION_TYPES = Object.values(ORCHESTRATION_TYPES).filter(
  type => type.complexity === 'intermediate'
);

export const ADVANCED_ORCHESTRATION_TYPES = Object.values(ORCHESTRATION_TYPES).filter(
  type => type.complexity === 'advanced'
);

export const EXPERIMENTAL_ORCHESTRATION_TYPES = Object.values(ORCHESTRATION_TYPES).filter(
  type => type.complexity === 'experimental'
);

// Maturity-based lists
export const STABLE_ORCHESTRATION_TYPES = Object.values(ORCHESTRATION_TYPES).filter(
  type => type.maturity === 'stable'
);

export const BETA_ORCHESTRATION_TYPES = Object.values(ORCHESTRATION_TYPES).filter(
  type => type.maturity === 'beta'
);

export const EXPERIMENTAL_MATURITY_ORCHESTRATION_TYPES = Object.values(ORCHESTRATION_TYPES).filter(
  type => type.maturity === 'experimental'
);

// Category colors for UI
export const CATEGORY_COLORS = {
  core: 'blue',
  '2025_trends': 'purple',
  '2026_trends': 'emerald'
} as const;

// Complexity colors for UI
export const COMPLEXITY_COLORS = {
  basic: 'green',
  intermediate: 'yellow',
  advanced: 'orange',
  experimental: 'red'
} as const;

// Maturity colors for UI
export const MATURITY_COLORS = {
  stable: 'green',
  beta: 'yellow',
  experimental: 'red'
} as const;