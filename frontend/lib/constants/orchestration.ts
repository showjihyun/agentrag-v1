/**
 * Agent orchestration related constants and type definitions
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
    name: 'Sequential Execution',
    description: 'Agents execute in order, with the output of the previous agent becoming the input for the next.',
    category: 'core',
    icon: 'ArrowRight',
    color: '#3B82F6',
    complexity: 'simple',
    useCase: 'Tasks requiring step-by-step processing (Data Collection → Analysis → Report Writing)',
    benefits: ['Simple and predictable execution flow', 'Easy debugging', 'Resource efficient'],
    requirements: ['Clear input/output definition between agents', 'Consider order dependencies'],
    estimatedSetupTime: '5-10 min'
  },
  parallel: {
    id: 'parallel',
    name: 'Parallel Execution',
    description: 'Agents execute simultaneously, aggregating all results to generate the final output.',
    category: 'core',
    icon: 'Zap',
    color: '#10B981',
    complexity: 'simple',
    useCase: 'Simultaneous processing of independent tasks (Multiple searches, Translation, Summarization)',
    benefits: ['Fast execution speed', 'High throughput', 'Task distribution'],
    requirements: ['Independent agent tasks', 'Result aggregation logic'],
    estimatedSetupTime: '10-15 min'
  },
  hierarchical: {
    id: 'hierarchical',
    name: 'Hierarchical Management',
    description: 'Manager agent manages worker agents and delegates tasks.',
    category: 'core',
    icon: 'Users',
    color: '#8B5CF6',
    complexity: 'medium',
    useCase: 'Complex project management (Manager → Researcher → Reviewer → Executor)',
    benefits: ['Clear responsibility distribution', 'Scalable structure', 'Quality management'],
    requirements: ['Manager agent setup', 'Role-based agent configuration', 'Delegation rule definition'],
    estimatedSetupTime: '20-30 min'
  },
  adaptive: {
    id: 'adaptive',
    name: 'Adaptive Routing',
    description: 'Dynamically selects agents and adjusts paths based on runtime conditions.',
    category: 'core',
    icon: 'GitBranch',
    color: '#F59E0B',
    complexity: 'medium',
    useCase: 'Tasks requiring situational response (Customer inquiry type-based routing)',
    benefits: ['Flexible execution flow', 'Situation-specific optimization', 'Efficient resource usage'],
    requirements: ['Routing condition definition', 'Situation analysis logic', 'Alternative path setup'],
    estimatedSetupTime: '25-35 min'
  }
};

// 2025 Trend Patterns
export const TRENDS_2025_ORCHESTRATION_TYPES: Record<string, OrchestrationPattern> = {
  consensus_building: {
    id: 'consensus_building',
    name: 'Consensus Building',
    description: 'Agents discuss and negotiate to reach consensus on optimal solutions.',
    category: '2025_trends',
    icon: 'MessageSquare',
    color: '#EF4444',
    complexity: 'complex',
    useCase: 'Complex problems requiring decision-making (Strategy formulation, Policy decisions)',
    benefits: ['High-quality decisions', 'Diverse perspectives reflected', 'Transparent decision-making process'],
    requirements: ['Discussion rules setup', 'Consensus criteria definition', 'Mediation mechanism'],
    estimatedSetupTime: '40-60 min'
  },
  dynamic_routing: {
    id: 'dynamic_routing',
    name: 'Dynamic Routing',
    description: 'Analyzes real-time agent performance and conditions to select optimal execution paths.',
    category: '2025_trends',
    icon: 'Route',
    color: '#06B6D4',
    complexity: 'complex',
    useCase: 'Tasks requiring real-time optimization (Traffic-based routing)',
    benefits: ['Real-time optimization', 'Performance-based selection', 'Automatic load balancing'],
    requirements: ['Performance monitoring', 'Routing algorithm', 'Real-time analysis'],
    estimatedSetupTime: '45-60 min'
  },
  swarm_intelligence: {
    id: 'swarm_intelligence',
    name: 'Swarm Intelligence',
    description: 'Multiple agents collaborate to leverage collective intelligence and search for optimal solutions.',
    category: '2025_trends',
    icon: 'Hexagon',
    color: '#84CC16',
    complexity: 'complex',
    useCase: 'Optimization problem solving (Path optimization, Resource allocation)',
    benefits: ['Collective intelligence utilization', 'Robust solutions', 'Distributed search'],
    requirements: ['Swarm algorithm', 'Information sharing mechanism', 'Convergence conditions'],
    estimatedSetupTime: '50-70 min'
  },
  event_driven: {
    id: 'event_driven',
    name: 'Event Driven',
    description: 'Agents automatically react and process when specific events occur.',
    category: '2025_trends',
    icon: 'Bell',
    color: '#F97316',
    complexity: 'medium',
    useCase: 'Real-time monitoring and response (Alerts, Automated response systems)',
    benefits: ['Real-time reaction', 'Automated response', 'Efficient resource usage'],
    requirements: ['Event definition', 'Trigger conditions', 'Reaction rules'],
    estimatedSetupTime: '30-45 min'
  },
  reflection: {
    id: 'reflection',
    name: 'Self Reflection',
    description: 'Agents analyze their own performance and continuously improve by finding areas for enhancement.',
    category: '2025_trends',
    icon: 'RefreshCw',
    color: '#A855F7',
    complexity: 'complex',
    useCase: 'Tasks requiring continuous improvement (Quality enhancement, Learning optimization)',
    benefits: ['Continuous improvement', 'Self-learning', 'Performance optimization'],
    requirements: ['Performance evaluation criteria', 'Improvement algorithm', 'Feedback loop'],
    estimatedSetupTime: '35-50 min'
  }
};

// 2026 Next-Generation Patterns
export const TRENDS_2026_ORCHESTRATION_TYPES: Record<string, OrchestrationPattern> = {
  neuromorphic: {
    id: 'neuromorphic',
    name: 'Neuromorphic Processing',
    description: 'Mimics brain neural network structure to optimize agent connections and information processing.',
    category: '2026_nextgen',
    icon: 'Brain',
    color: '#EC4899',
    complexity: 'complex',
    useCase: 'Complex pattern recognition and learning (Image analysis, Natural language understanding)',
    benefits: ['Biological efficiency', 'Adaptive learning', 'Parallel processing'],
    requirements: ['Neural network modeling', 'Synaptic weights', 'Learning algorithm'],
    estimatedSetupTime: '60-90 min'
  },
  quantum_enhanced: {
    id: 'quantum_enhanced',
    name: 'Quantum Enhanced',
    description: 'Utilizes quantum computing principles to implement superposition states and entanglement between agents.',
    category: '2026_nextgen',
    icon: 'Atom',
    color: '#6366F1',
    complexity: 'complex',
    useCase: 'Complex optimization problems (Encryption, Simulation)',
    benefits: ['Exponential processing capability', 'Parallel search', 'Quantum advantage'],
    requirements: ['Quantum simulator', 'Entanglement management', 'Measurement strategy'],
    estimatedSetupTime: '90-120 min'
  },
  bio_inspired: {
    id: 'bio_inspired',
    name: 'Bio-Inspired',
    description: 'Mimics biological system principles to construct agent ecosystems.',
    category: '2026_nextgen',
    icon: 'Leaf',
    color: '#059669',
    complexity: 'complex',
    useCase: 'Natural collaboration systems (Ecosystem simulation)',
    benefits: ['Natural collaboration', 'Self-organization', 'Environmental adaptation'],
    requirements: ['Ecosystem modeling', 'Evolutionary algorithm', 'Environmental interaction'],
    estimatedSetupTime: '70-100 min'
  },
  self_evolving: {
    id: 'self_evolving',
    name: 'Self-Evolving',
    description: 'Agents evolve their own structure and algorithms to improve performance.',
    category: '2026_nextgen',
    icon: 'TrendingUp',
    color: '#DC2626',
    complexity: 'complex',
    useCase: 'Systems requiring long-term optimization (Automatic improvement)',
    benefits: ['Automatic optimization', 'Long-term improvement', 'Adaptive evolution'],
    requirements: ['Evolutionary algorithm', 'Fitness function', 'Mutation mechanism'],
    estimatedSetupTime: '80-110 min'
  },
  federated: {
    id: 'federated',
    name: 'Federated Learning',
    description: 'Distributed agents collaborate and learn without sharing data.',
    category: '2026_nextgen',
    icon: 'Network',
    color: '#7C3AED',
    complexity: 'complex',
    useCase: 'Privacy-preserving learning (Medical data, Financial data)',
    benefits: ['Privacy protection', 'Distributed learning', 'Data security'],
    requirements: ['Federated algorithm', 'Encrypted communication', 'Aggregation mechanism'],
    estimatedSetupTime: '60-80 min'
  },
  emotional_ai: {
    id: 'emotional_ai',
    name: 'Emotional AI',
    description: 'Agents recognize emotional states and adjust collaboration methods accordingly.',
    category: '2026_nextgen',
    icon: 'Heart',
    color: '#F43F5E',
    complexity: 'complex',
    useCase: 'Human-AI interaction (Customer service, Education)',
    benefits: ['Emotional intelligence', 'Human-friendly', 'Contextual understanding'],
    requirements: ['Emotion analysis model', 'Response rules', 'Emotional state management'],
    estimatedSetupTime: '50-70 min'
  },
  predictive: {
    id: 'predictive',
    name: 'Predictive Orchestration',
    description: 'Predicts future situations to optimize agent placement and tasks in advance.',
    category: '2026_nextgen',
    icon: 'Crystal',
    color: '#0891B2',
    complexity: 'complex',
    useCase: 'Prediction-based optimization (Demand forecasting, Resource planning)',
    benefits: ['Proactive optimization', 'Prediction-based decisions', 'Risk management'],
    requirements: ['Prediction model', 'Scenario analysis', 'Optimization algorithm'],
    estimatedSetupTime: '65-85 min'
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
    name: 'Manager',
    description: 'Coordinates other agents and delegates tasks',
    color: '#8B5CF6',
    icon: 'Crown'
  },
  worker: {
    name: 'Worker',
    description: 'Execution agent that performs specific tasks',
    color: '#3B82F6',
    icon: 'Wrench'
  },
  critic: {
    name: 'Critic',
    description: 'Reviews results and evaluates quality',
    color: '#EF4444',
    icon: 'Eye'
  },
  synthesizer: {
    name: 'Synthesizer',
    description: 'Integrates multiple results and generates final output',
    color: '#10B981',
    icon: 'Merge'
  },
  coordinator: {
    name: 'Coordinator',
    description: 'Coordinates collaboration and communication between agents',
    color: '#F59E0B',
    icon: 'Users'
  },
  specialist: {
    name: 'Specialist',
    description: 'Provides specialized knowledge in specific domains',
    color: '#06B6D4',
    icon: 'Star'
  }
};

// Communication types
export type CommunicationType = 'direct' | 'broadcast' | 'negotiation' | 'feedback' | 'consensus';

// Communication type definitions
export const COMMUNICATION_TYPES: Record<CommunicationType, { name: string; description: string; color: string }> = {
  direct: {
    name: 'Direct Communication',
    description: 'Direct message exchange between two agents',
    color: '#3B82F6'
  },
  broadcast: {
    name: 'Broadcast',
    description: 'One agent sends messages to all agents',
    color: '#10B981'
  },
  negotiation: {
    name: 'Negotiation',
    description: 'Reaching consensus through negotiation between agents',
    color: '#F59E0B'
  },
  feedback: {
    name: 'Feedback',
    description: 'Feedback and improvement suggestions on results',
    color: '#8B5CF6'
  },
  consensus: {
    name: 'Consensus',
    description: 'Consensus formation among multiple agents',
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
    'Lower priority for agents with poor performance',
    'Agents with errors are retried or replaced',
    'On timeout, proceed to next Agent'
  ],
  performance_thresholds: {
    response_time: 30000, // 30 seconds
    success_rate: 0.8,    // 80%
    token_efficiency: 0.7  // 70%
  }
};