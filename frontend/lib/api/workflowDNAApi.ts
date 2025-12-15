import { apiClient } from './client';

export interface WorkflowGene {
  id: string;
  name: string;
  type: 'performance' | 'reliability' | 'efficiency' | 'adaptability' | 'creativity';
  value: number;
  dominance: number;
  mutation_rate: number;
  expression_level: number;
  interactions: string[];
}

export interface WorkflowDNA {
  id: string;
  name: string;
  generation: number;
  genes: WorkflowGene[];
  fitness_score: number;
  performance_metrics: {
    speed: number;
    accuracy: number;
    efficiency: number;
    adaptability: number;
    innovation: number;
  };
  parent_ids: string[];
  mutation_history: Array<{
    generation: number;
    gene_id: string;
    old_value: number;
    new_value: number;
    impact: number;
  }>;
  survival_probability: number;
  age: number;
}

export interface EvolutionExperiment {
  id: string;
  name: string;
  population_size: number;
  current_generation: number;
  max_generations: number;
  mutation_rate: number;
  crossover_rate: number;
  selection_pressure: number;
  fitness_function: string;
  population: WorkflowDNA[];
  evolution_history: Array<{
    generation: number;
    best_fitness: number;
    average_fitness: number;
    diversity_index: number;
    extinction_events: number;
  }>;
  status: 'running' | 'paused' | 'completed' | 'extinct';
}

export interface CrossoverRequest {
  parent1_id: string;
  parent2_id: string;
  experiment_id: string;
}

export interface MutationRequest {
  workflow_id: string;
  mutation_rate: number;
}

// API functions
export const workflowDNAApi = {
  // Get experiments
  getExperiments: async (): Promise<{ experiments: EvolutionExperiment[] }> => {
    const response = await apiClient.get('/workflow-dna/experiments');
    return response.data;
  },

  // Get specific experiment
  getExperiment: async (experimentId: string): Promise<{ experiment: EvolutionExperiment }> => {
    const response = await apiClient.get(`/workflow-dna/experiments/${experimentId}`);
    return response.data;
  },

  // Create new experiment
  createExperiment: async (config: Partial<EvolutionExperiment>): Promise<{ experiment: EvolutionExperiment; message: string }> => {
    const response = await apiClient.post('/workflow-dna/experiments', config);
    return response.data;
  },

  // Start evolution
  startEvolution: async (experimentId: string): Promise<{ message: string }> => {
    const response = await apiClient.post(`/workflow-dna/experiments/${experimentId}/start`);
    return response.data;
  },

  // Stop evolution
  stopEvolution: async (experimentId: string): Promise<{ message: string }> => {
    const response = await apiClient.post(`/workflow-dna/experiments/${experimentId}/stop`);
    return response.data;
  },

  // Get population
  getPopulation: async (experimentId: string): Promise<{ population: WorkflowDNA[] }> => {
    const response = await apiClient.get(`/workflow-dna/experiments/${experimentId}/population`);
    return response.data;
  },

  // Perform crossover
  performCrossover: async (request: CrossoverRequest): Promise<{ offspring: WorkflowDNA[]; message: string }> => {
    const response = await apiClient.post('/workflow-dna/crossover', request);
    return response.data;
  },

  // Perform mutation
  performMutation: async (request: MutationRequest): Promise<{ mutated_workflow: WorkflowDNA; message: string }> => {
    const response = await apiClient.post('/workflow-dna/mutate', request);
    return response.data;
  },

  // Get evolution analytics
  getEvolutionAnalytics: async (experimentId: string): Promise<{ analytics: any }> => {
    const response = await apiClient.get(`/workflow-dna/experiments/${experimentId}/analytics`);
    return response.data;
  },

  // Reset experiment
  resetExperiment: async (experimentId: string): Promise<{ message: string }> => {
    const response = await apiClient.post(`/workflow-dna/experiments/${experimentId}/reset`);
    return response.data;
  },

  // Update experiment parameters
  updateExperimentParameters: async (experimentId: string, parameters: Partial<EvolutionExperiment>): Promise<{ message: string }> => {
    const response = await apiClient.put(`/workflow-dna/experiments/${experimentId}/parameters`, parameters);
    return response.data;
  },
};