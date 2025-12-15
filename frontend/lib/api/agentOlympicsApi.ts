import { queryKeys } from '@/lib/queryClient';

const API_BASE = '/api/agent-builder/agent-olympics';

export interface Agent {
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
    total_competitions: number;
    ranking: number;
    points: number;
    win_rate: number;
  };
  status: 'competing' | 'idle' | 'training' | 'offline';
  current_position?: number;
  progress?: number;
  created_at: string;
}

export interface Competition {
  id: string;
  name: string;
  type: 'speed' | 'accuracy' | 'collaboration' | 'creativity' | 'endurance' | 'efficiency';
  status: 'upcoming' | 'active' | 'completed' | 'cancelled';
  participants: Agent[];
  start_time: string;
  duration: number;
  prize: number;
  spectators: number;
  description: string;
  results?: any;
  created_at: string;
}

export interface LiveProgress {
  competition_id: string;
  progress: Record<string, number>;
  rankings: Array<{
    agent_id: string;
    name: string;
    avatar: string;
    progress: number;
    position: number;
  }>;
  spectators: number;
  is_completed: boolean;
}

export interface Analytics {
  elite_organisms: number;
  genetic_diversity: number;
  average_fitness: number;
  evolution_trends: Record<string, number[]>;
  gene_distribution: Record<string, Record<string, number>>;
  convergence_analysis: Record<string, any>;
}

// API functions
export const agentOlympicsApi = {
  // Agents
  async getAgents(): Promise<{ agents: Agent[]; total_count: number; active_count: number; top_performer: Agent | null }> {
    const response = await fetch(`${API_BASE}/agents`);
    if (!response.ok) throw new Error('Failed to fetch agents');
    return response.json();
  },

  async getAgent(agentId: string): Promise<Agent> {
    const response = await fetch(`${API_BASE}/agents/${agentId}`);
    if (!response.ok) throw new Error('Failed to fetch agent');
    return response.json();
  },

  // Competitions
  async getCompetitions(): Promise<{ competitions: Competition[]; active_competitions: Competition[]; total_count: number; upcoming_count: number }> {
    const response = await fetch(`${API_BASE}/competitions`);
    if (!response.ok) throw new Error('Failed to fetch competitions');
    return response.json();
  },

  async getCompetition(competitionId: string): Promise<Competition> {
    const response = await fetch(`${API_BASE}/competitions/${competitionId}`);
    if (!response.ok) throw new Error('Failed to fetch competition');
    return response.json();
  },

  async getLiveProgress(competitionId: string): Promise<LiveProgress> {
    const response = await fetch(`${API_BASE}/competitions/${competitionId}/progress`);
    if (!response.ok) throw new Error('Failed to fetch live progress');
    return response.json();
  },

  // Leaderboard
  async getLeaderboard(): Promise<{ leaderboard: Agent[]; total_agents: number; ranking_updated_at: string }> {
    const response = await fetch(`${API_BASE}/leaderboard`);
    if (!response.ok) throw new Error('Failed to fetch leaderboard');
    return response.json();
  },

  // Analytics
  async getAnalytics(): Promise<Analytics> {
    const response = await fetch(`${API_BASE}/analytics`);
    if (!response.ok) throw new Error('Failed to fetch analytics');
    return response.json();
  },

  // Competition management
  async createCompetition(data: {
    name: string;
    type: string;
    participant_ids: string[];
    duration?: number;
    prize?: number;
    description?: string;
  }): Promise<{ success: boolean; competition_id: string; message: string }> {
    const response = await fetch(`${API_BASE}/competitions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create competition');
    return response.json();
  },

  async startCompetition(competitionId: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE}/competitions/${competitionId}/start`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to start competition');
    return response.json();
  },

  async stopCompetition(competitionId: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE}/competitions/${competitionId}/stop`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to stop competition');
    return response.json();
  },

  // Status
  async getStatus(): Promise<{
    total_agents: number;
    active_agents: number;
    total_competitions: number;
    active_competitions: number;
    upcoming_competitions: number;
    completed_competitions: number;
    total_spectators: number;
    system_status: string;
    last_updated: string;
  }> {
    const response = await fetch(`${API_BASE}/status`);
    if (!response.ok) throw new Error('Failed to fetch status');
    return response.json();
  },

  async getCompetitionTypes(): Promise<{
    competition_types: Array<{
      type: string;
      name: string;
      description: string;
    }>;
    total_types: number;
  }> {
    const response = await fetch(`${API_BASE}/competition-types`);
    if (!response.ok) throw new Error('Failed to fetch competition types');
    return response.json();
  },
};