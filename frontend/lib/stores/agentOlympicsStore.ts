import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';

interface Agent {
  id: string;
  name: string;
  type: string;
  avatar: string;
  performance: {
    speed: number;
    accuracy: number;
    efficiency: number;
    creativity: number;
    collaboration: number;
  };
  stats: {
    wins: number;
    losses: number;
    draws: number;
    totalCompetitions: number;
    ranking: number;
    points: number;
  };
  status: 'competing' | 'idle' | 'training' | 'offline';
  currentPosition?: number;
  progress?: number;
}

interface Competition {
  id: string;
  name: string;
  type: 'speed' | 'accuracy' | 'collaboration' | 'creativity' | 'endurance';
  status: 'upcoming' | 'active' | 'completed';
  participants: Agent[];
  startTime: Date;
  duration: number;
  prize: number;
  spectators: number;
  description: string;
}

interface AgentOlympicsState {
  // State
  agents: Agent[];
  competitions: Competition[];
  activeCompetition: Competition | null;
  leaderboard: Agent[];
  isLive: boolean;
  raceProgress: Record<string, number>;
  
  // Actions
  setAgents: (agents: Agent[]) => void;
  updateAgent: (agentId: string, updates: Partial<Agent>) => void;
  setCompetitions: (competitions: Competition[]) => void;
  setActiveCompetition: (competition: Competition | null) => void;
  updateRaceProgress: (progress: Record<string, number>) => void;
  startCompetition: () => void;
  stopCompetition: () => void;
  updateLeaderboard: () => void;
}

export const useAgentOlympicsStore = create<AgentOlympicsState>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // Initial state
      agents: [],
      competitions: [],
      activeCompetition: null,
      leaderboard: [],
      isLive: false,
      raceProgress: {},

      // Actions
      setAgents: (agents) => set({ agents }, false, 'setAgents'),
      
      updateAgent: (agentId, updates) =>
        set(
          (state) => ({
            agents: state.agents.map((agent) =>
              agent.id === agentId ? { ...agent, ...updates } : agent
            ),
          }),
          false,
          'updateAgent'
        ),

      setCompetitions: (competitions) => set({ competitions }, false, 'setCompetitions'),
      
      setActiveCompetition: (competition) => set({ activeCompetition: competition }, false, 'setActiveCompetition'),
      
      updateRaceProgress: (progress) => set({ raceProgress: progress }, false, 'updateRaceProgress'),
      
      startCompetition: () => set({ isLive: true }, false, 'startCompetition'),
      
      stopCompetition: () => set({ isLive: false }, false, 'stopCompetition'),
      
      updateLeaderboard: () => {
        const { agents } = get();
        const sortedAgents = [...agents].sort((a, b) => b.stats.points - a.stats.points);
        set({ leaderboard: sortedAgents }, false, 'updateLeaderboard');
      },
    })),
    {
      name: 'agent-olympics-store',
    }
  )
);