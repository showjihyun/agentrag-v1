import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/queryClient';
import { emotionalAIApi } from '@/lib/api/emotionalAIApi';
import { useToast } from '@/hooks/use-toast';

// Queries
export const useUserMood = (userId: string) => {
  return useQuery({
    queryKey: queryKeys.emotionalAI.userMood(userId),
    queryFn: () => emotionalAIApi.getUserMood(userId),
    enabled: !!userId,
    staleTime: 30 * 1000, // 30 seconds
  });
};

export const useTeamDynamics = (teamId: string) => {
  return useQuery({
    queryKey: queryKeys.emotionalAI.teamDynamics(teamId),
    queryFn: () => emotionalAIApi.getTeamDynamics(teamId),
    enabled: !!teamId,
    staleTime: 60 * 1000, // 1 minute
  });
};

export const useEmotionHistory = (userId: string, hours = 24) => {
  return useQuery({
    queryKey: queryKeys.emotionalAI.emotionHistory(userId, hours),
    queryFn: () => emotionalAIApi.getEmotionHistory(userId, hours),
    enabled: !!userId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

export const useWellnessInsights = (userId: string) => {
  return useQuery({
    queryKey: queryKeys.emotionalAI.wellnessInsights(userId),
    queryFn: () => emotionalAIApi.getWellnessInsights(userId),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useEmotionAnalytics = (userId: string) => {
  return useQuery({
    queryKey: queryKeys.emotionalAI.analytics(userId),
    queryFn: () => emotionalAIApi.getEmotionAnalytics(userId),
    enabled: !!userId,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Mutations
export const useAnalyzeEmotion = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: emotionalAIApi.analyzeEmotion,
    onSuccess: (data, variables) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.emotionalAI.userMood(variables.user_id) 
      });
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.emotionalAI.emotionHistory(variables.user_id) 
      });
      
      toast({
        title: 'Emotion Analyzed',
        description: `Detected: ${data.emotion_state.primary} (${(data.emotion_state.confidence * 100).toFixed(0)}% confidence)`,
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Analysis Failed',
        description: error.message,
        variant: 'destructive',
      });
    },
  });
};

export const useUpdateUserPreferences = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ userId, preferences }: { userId: string; preferences: any }) =>
      emotionalAIApi.updateUserPreferences(userId, preferences),
    onSuccess: (data, variables) => {
      // Invalidate user mood query
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.emotionalAI.userMood(variables.userId) 
      });
      
      toast({
        title: 'Preferences Updated',
        description: data.message,
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Update Failed',
        description: error.message,
        variant: 'destructive',
      });
    },
  });
};

export const useStartEmotionMonitoring = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: emotionalAIApi.startEmotionMonitoring,
    onSuccess: (data, userId) => {
      // Start polling for real-time updates
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.emotionalAI.userMood(userId) 
      });
      
      toast({
        title: 'Monitoring Started',
        description: data.message,
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Failed to Start Monitoring',
        description: error.message,
        variant: 'destructive',
      });
    },
  });
};

export const useStopEmotionMonitoring = () => {
  const { toast } = useToast();

  return useMutation({
    mutationFn: emotionalAIApi.stopEmotionMonitoring,
    onSuccess: (data) => {
      toast({
        title: 'Monitoring Stopped',
        description: data.message,
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Failed to Stop Monitoring',
        description: error.message,
        variant: 'destructive',
      });
    },
  });
};