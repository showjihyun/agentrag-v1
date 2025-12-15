import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/queryClient';
import { agentOlympicsApi } from '@/lib/api/agentOlympicsApi';
import { useToast } from '@/hooks/use-toast';

// Queries
export const useAgents = () => {
  return useQuery({
    queryKey: queryKeys.agentOlympics.agents(),
    queryFn: agentOlympicsApi.getAgents,
    staleTime: 30 * 1000, // 30 seconds
  });
};

export const useAgent = (agentId: string) => {
  return useQuery({
    queryKey: [...queryKeys.agentOlympics.agents(), agentId],
    queryFn: () => agentOlympicsApi.getAgent(agentId),
    enabled: !!agentId,
  });
};

export const useCompetitions = () => {
  return useQuery({
    queryKey: queryKeys.agentOlympics.competitions(),
    queryFn: agentOlympicsApi.getCompetitions,
    staleTime: 60 * 1000, // 1 minute
  });
};

export const useCompetition = (competitionId: string) => {
  return useQuery({
    queryKey: [...queryKeys.agentOlympics.competitions(), competitionId],
    queryFn: () => agentOlympicsApi.getCompetition(competitionId),
    enabled: !!competitionId,
  });
};

export const useLiveProgress = (competitionId: string, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.agentOlympics.liveProgress(competitionId),
    queryFn: () => agentOlympicsApi.getLiveProgress(competitionId),
    enabled: !!competitionId && enabled,
    refetchInterval: 1000, // Refetch every second for live updates
    staleTime: 0, // Always consider stale for real-time data
  });
};

export const useLeaderboard = () => {
  return useQuery({
    queryKey: queryKeys.agentOlympics.leaderboard(),
    queryFn: agentOlympicsApi.getLeaderboard,
    staleTime: 30 * 1000, // 30 seconds
  });
};

export const useOlympicsAnalytics = () => {
  return useQuery({
    queryKey: queryKeys.agentOlympics.analytics(),
    queryFn: agentOlympicsApi.getAnalytics,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

export const useOlympicsStatus = () => {
  return useQuery({
    queryKey: [...queryKeys.agentOlympics.all, 'status'],
    queryFn: agentOlympicsApi.getStatus,
    staleTime: 10 * 1000, // 10 seconds
  });
};

export const useCompetitionTypes = () => {
  return useQuery({
    queryKey: [...queryKeys.agentOlympics.all, 'competition-types'],
    queryFn: agentOlympicsApi.getCompetitionTypes,
    staleTime: 5 * 60 * 1000, // 5 minutes - rarely changes
  });
};

// Mutations
export const useCreateCompetition = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: agentOlympicsApi.createCompetition,
    onSuccess: (data) => {
      // Invalidate competitions list
      queryClient.invalidateQueries({ queryKey: queryKeys.agentOlympics.competitions() });
      
      toast({
        title: 'Competition Created',
        description: data.message,
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Failed to Create Competition',
        description: error.message,
        variant: 'destructive',
      });
    },
  });
};

export const useStartCompetition = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: agentOlympicsApi.startCompetition,
    onSuccess: (data, competitionId) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.agentOlympics.competitions() });
      queryClient.invalidateQueries({ queryKey: [...queryKeys.agentOlympics.competitions(), competitionId] });
      
      toast({
        title: 'Competition Started',
        description: data.message,
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Failed to Start Competition',
        description: error.message,
        variant: 'destructive',
      });
    },
  });
};

export const useStopCompetition = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: agentOlympicsApi.stopCompetition,
    onSuccess: (data, competitionId) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.agentOlympics.competitions() });
      queryClient.invalidateQueries({ queryKey: [...queryKeys.agentOlympics.competitions(), competitionId] });
      queryClient.invalidateQueries({ queryKey: queryKeys.agentOlympics.liveProgress(competitionId) });
      
      toast({
        title: 'Competition Stopped',
        description: data.message,
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Failed to Stop Competition',
        description: error.message,
        variant: 'destructive',
      });
    },
  });
};