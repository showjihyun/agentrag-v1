import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/queryClient';
import { workflowDNAApi } from '@/lib/api/workflowDNAApi';
import { useToast } from '@/hooks/use-toast';

// Queries
export const useExperiments = () => {
  return useQuery({
    queryKey: queryKeys.workflowDNA.experiments(),
    queryFn: workflowDNAApi.getExperiments,
    staleTime: 60 * 1000, // 1 minute
  });
};

export const useExperiment = (experimentId: string) => {
  return useQuery({
    queryKey: queryKeys.workflowDNA.experiment(experimentId),
    queryFn: () => workflowDNAApi.getExperiment(experimentId),
    enabled: !!experimentId,
    staleTime: 30 * 1000, // 30 seconds
  });
};

export const usePopulation = (experimentId: string) => {
  return useQuery({
    queryKey: queryKeys.workflowDNA.population(experimentId),
    queryFn: () => workflowDNAApi.getPopulation(experimentId),
    enabled: !!experimentId,
    staleTime: 10 * 1000, // 10 seconds for real-time evolution
  });
};

export const useEvolutionAnalytics = (experimentId: string) => {
  return useQuery({
    queryKey: queryKeys.workflowDNA.analytics(experimentId),
    queryFn: () => workflowDNAApi.getEvolutionAnalytics(experimentId),
    enabled: !!experimentId,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

// Mutations
export const useCreateExperiment = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: workflowDNAApi.createExperiment,
    onSuccess: (data) => {
      // Invalidate experiments list
      queryClient.invalidateQueries({ queryKey: queryKeys.workflowDNA.experiments() });
      
      toast({
        title: 'Experiment Created',
        description: data.message,
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Failed to Create Experiment',
        description: error.message,
        variant: 'destructive',
      });
    },
  });
};

export const useStartEvolution = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: workflowDNAApi.startEvolution,
    onSuccess: (data, experimentId) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.workflowDNA.experiment(experimentId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.workflowDNA.population(experimentId) });
      
      toast({
        title: 'Evolution Started',
        description: data.message,
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Failed to Start Evolution',
        description: error.message,
        variant: 'destructive',
      });
    },
  });
};

export const useStopEvolution = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: workflowDNAApi.stopEvolution,
    onSuccess: (data, experimentId) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.workflowDNA.experiment(experimentId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.workflowDNA.population(experimentId) });
      
      toast({
        title: 'Evolution Stopped',
        description: data.message,
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Failed to Stop Evolution',
        description: error.message,
        variant: 'destructive',
      });
    },
  });
};

export const usePerformCrossover = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: workflowDNAApi.performCrossover,
    onSuccess: (data, variables) => {
      // Invalidate population query
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.workflowDNA.population(variables.experiment_id) 
      });
      
      toast({
        title: 'Crossover Successful',
        description: `Created ${data.offspring.length} offspring`,
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Crossover Failed',
        description: error.message,
        variant: 'destructive',
      });
    },
  });
};

export const usePerformMutation = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: workflowDNAApi.performMutation,
    onSuccess: (data) => {
      // Invalidate population queries
      queryClient.invalidateQueries({ queryKey: queryKeys.workflowDNA.all });
      
      toast({
        title: 'Mutation Applied',
        description: data.message,
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Mutation Failed',
        description: error.message,
        variant: 'destructive',
      });
    },
  });
};

export const useResetExperiment = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: workflowDNAApi.resetExperiment,
    onSuccess: (data, experimentId) => {
      // Invalidate all related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.workflowDNA.experiment(experimentId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.workflowDNA.population(experimentId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.workflowDNA.analytics(experimentId) });
      
      toast({
        title: 'Experiment Reset',
        description: data.message,
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Reset Failed',
        description: error.message,
        variant: 'destructive',
      });
    },
  });
};

export const useUpdateExperimentParameters = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ experimentId, parameters }: { experimentId: string; parameters: any }) =>
      workflowDNAApi.updateExperimentParameters(experimentId, parameters),
    onSuccess: (data, variables) => {
      // Invalidate experiment query
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.workflowDNA.experiment(variables.experimentId) 
      });
      
      toast({
        title: 'Parameters Updated',
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