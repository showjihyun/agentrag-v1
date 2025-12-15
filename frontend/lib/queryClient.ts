import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000, // 30 seconds
      gcTime: 5 * 60 * 1000, // 5 minutes (formerly cacheTime)
      retry: (failureCount, error: any) => {
        // Don't retry on 4xx errors
        if (error?.status >= 400 && error?.status < 500) {
          return false;
        }
        return failureCount < 3;
      },
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
});

// Query keys factory for consistent cache management
export const queryKeys = {
  // Agent Olympics
  agentOlympics: {
    all: ['agent-olympics'] as const,
    agents: () => [...queryKeys.agentOlympics.all, 'agents'] as const,
    competitions: () => [...queryKeys.agentOlympics.all, 'competitions'] as const,
    leaderboard: () => [...queryKeys.agentOlympics.all, 'leaderboard'] as const,
    liveProgress: (competitionId: string) => 
      [...queryKeys.agentOlympics.all, 'live-progress', competitionId] as const,
    analytics: () => [...queryKeys.agentOlympics.all, 'analytics'] as const,
  },
  
  // Emotional AI
  emotionalAI: {
    all: ['emotional-ai'] as const,
    userMood: (userId: string) => 
      [...queryKeys.emotionalAI.all, 'user-mood', userId] as const,
    emotionHistory: (userId: string, hours?: number) => 
      [...queryKeys.emotionalAI.all, 'emotion-history', userId, hours] as const,
    teamDynamics: (teamId: string) => 
      [...queryKeys.emotionalAI.all, 'team-dynamics', teamId] as const,
    wellnessInsights: (userId: string) => 
      [...queryKeys.emotionalAI.all, 'wellness-insights', userId] as const,
    analytics: (userId: string) => 
      [...queryKeys.emotionalAI.all, 'analytics', userId] as const,
    adaptiveTheme: (userId: string) => 
      [...queryKeys.emotionalAI.all, 'adaptive-theme', userId] as const,
  },
  
  // Workflow DNA
  workflowDNA: {
    all: ['workflow-dna'] as const,
    experiments: () => [...queryKeys.workflowDNA.all, 'experiments'] as const,
    experiment: (experimentId: string) => 
      [...queryKeys.workflowDNA.all, 'experiment', experimentId] as const,
    population: (experimentId: string) => 
      [...queryKeys.workflowDNA.all, 'population', experimentId] as const,
    analytics: (experimentId: string) => 
      [...queryKeys.workflowDNA.all, 'analytics', experimentId] as const,
  },
  
  // Performance
  performance: {
    all: ['performance'] as const,
    metrics: () => [...queryKeys.performance.all, 'metrics'] as const,
    cacheStats: () => [...queryKeys.performance.all, 'cache-stats'] as const,
    recommendations: () => [...queryKeys.performance.all, 'recommendations'] as const,
  },
} as const;