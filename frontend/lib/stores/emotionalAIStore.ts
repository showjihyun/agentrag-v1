import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface EmotionState {
  primary: string;
  intensity: number;
  confidence: number;
  timestamp: Date;
  triggers: string[];
  context: string;
}

interface UserMood {
  userId: string;
  name: string;
  currentEmotion: EmotionState;
  emotionHistory: EmotionState[];
  stressLevel: number;
  energyLevel: number;
  focusLevel: number;
  wellnessScore: number;
  preferences: {
    communicationStyle: string;
    workPace: string;
    feedbackType: string;
  };
}

interface TeamEmotionalDynamics {
  teamId: string;
  teamName: string;
  overallMood: string;
  cohesionScore: number;
  stressIndicators: string[];
  productivityCorrelation: number;
  conflictRisk: number;
  burnoutRisk: number;
  recommendations: string[];
}

interface EmotionalAIState {
  // State
  currentUser: UserMood | null;
  teamDynamics: TeamEmotionalDynamics | null;
  emotionHistory: EmotionState[];
  adaptiveMode: boolean;
  emotionalTheme: string;
  wellnessInsights: any[];
  
  // Actions
  setCurrentUser: (user: UserMood | null) => void;
  updateUserEmotion: (emotion: EmotionState) => void;
  setTeamDynamics: (dynamics: TeamEmotionalDynamics | null) => void;
  setAdaptiveMode: (enabled: boolean) => void;
  setEmotionalTheme: (theme: string) => void;
  addEmotionToHistory: (emotion: EmotionState) => void;
  updateWellnessMetrics: (metrics: Partial<Pick<UserMood, 'stressLevel' | 'energyLevel' | 'focusLevel' | 'wellnessScore'>>) => void;
}

export const useEmotionalAIStore = create<EmotionalAIState>()(
  devtools(
    (set, get) => ({
      // Initial state
      currentUser: null,
      teamDynamics: null,
      emotionHistory: [],
      adaptiveMode: true,
      emotionalTheme: 'default',
      wellnessInsights: [],

      // Actions
      setCurrentUser: (user) => set({ currentUser: user }, false, 'setCurrentUser'),
      
      updateUserEmotion: (emotion) =>
        set(
          (state) => {
            if (!state.currentUser) return state;
            return {
              currentUser: {
                ...state.currentUser,
                currentEmotion: emotion,
                emotionHistory: [...state.currentUser.emotionHistory, emotion].slice(-24), // Keep last 24 hours
              },
            };
          },
          false,
          'updateUserEmotion'
        ),

      setTeamDynamics: (dynamics) => set({ teamDynamics: dynamics }, false, 'setTeamDynamics'),
      
      setAdaptiveMode: (enabled) => set({ adaptiveMode: enabled }, false, 'setAdaptiveMode'),
      
      setEmotionalTheme: (theme) => set({ emotionalTheme: theme }, false, 'setEmotionalTheme'),
      
      addEmotionToHistory: (emotion) =>
        set(
          (state) => ({
            emotionHistory: [...state.emotionHistory, emotion].slice(-100), // Keep last 100 entries
          }),
          false,
          'addEmotionToHistory'
        ),

      updateWellnessMetrics: (metrics) =>
        set(
          (state) => {
            if (!state.currentUser) return state;
            return {
              currentUser: {
                ...state.currentUser,
                ...metrics,
              },
            };
          },
          false,
          'updateWellnessMetrics'
        ),
    }),
    {
      name: 'emotional-ai-store',
    }
  )
);