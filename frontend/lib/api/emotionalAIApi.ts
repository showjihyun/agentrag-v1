import { apiClient } from './client';

export interface EmotionState {
  primary: string;
  intensity: number;
  confidence: number;
  timestamp: string;
  triggers: string[];
  context: string;
}

export interface UserMood {
  user_id: string;
  name: string;
  current_emotion: EmotionState;
  emotion_history: EmotionState[];
  stress_level: number;
  energy_level: number;
  focus_level: number;
  wellness_score: number;
  preferences: {
    communication_style: string;
    work_pace: string;
    feedback_type: string;
  };
}

export interface TeamEmotionalDynamics {
  team_id: string;
  team_name: string;
  overall_mood: string;
  cohesion_score: number;
  stress_indicators: string[];
  productivity_correlation: number;
  conflict_risk: number;
  burnout_risk: number;
  recommendations: string[];
}

export interface EmotionAnalysisRequest {
  user_id: string;
  input_type: 'text' | 'voice' | 'video' | 'biometric';
  data: any;
}

export interface WellnessInsight {
  id: string;
  type: 'recommendation' | 'alert' | 'insight';
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high';
  timestamp: string;
}

// API functions
export const emotionalAIApi = {
  // Get current user mood
  getUserMood: async (userId: string): Promise<{ user_mood: UserMood }> => {
    const response = await apiClient.get(`/emotional-ai/users/${userId}/mood`);
    return response.data;
  },

  // Analyze emotion from input
  analyzeEmotion: async (request: EmotionAnalysisRequest): Promise<{ emotion_state: EmotionState }> => {
    const response = await apiClient.post('/emotional-ai/analyze', request);
    return response.data;
  },

  // Get team dynamics
  getTeamDynamics: async (teamId: string): Promise<{ team_dynamics: TeamEmotionalDynamics }> => {
    const response = await apiClient.get(`/emotional-ai/teams/${teamId}/dynamics`);
    return response.data;
  },

  // Get emotion history
  getEmotionHistory: async (userId: string, hours = 24): Promise<{ emotion_history: EmotionState[] }> => {
    const response = await apiClient.get(`/emotional-ai/users/${userId}/history?hours=${hours}`);
    return response.data;
  },

  // Get wellness insights
  getWellnessInsights: async (userId: string): Promise<{ insights: WellnessInsight[] }> => {
    const response = await apiClient.get(`/emotional-ai/users/${userId}/wellness-insights`);
    return response.data;
  },

  // Update user preferences
  updateUserPreferences: async (userId: string, preferences: any): Promise<{ message: string }> => {
    const response = await apiClient.put(`/emotional-ai/users/${userId}/preferences`, preferences);
    return response.data;
  },

  // Get emotion analytics
  getEmotionAnalytics: async (userId: string): Promise<{ analytics: any }> => {
    const response = await apiClient.get(`/emotional-ai/users/${userId}/analytics`);
    return response.data;
  },

  // Start real-time emotion monitoring
  startEmotionMonitoring: async (userId: string): Promise<{ message: string; session_id: string }> => {
    const response = await apiClient.post(`/emotional-ai/users/${userId}/start-monitoring`);
    return response.data;
  },

  // Stop real-time emotion monitoring
  stopEmotionMonitoring: async (sessionId: string): Promise<{ message: string }> => {
    const response = await apiClient.post(`/emotional-ai/sessions/${sessionId}/stop-monitoring`);
    return response.data;
  },
};