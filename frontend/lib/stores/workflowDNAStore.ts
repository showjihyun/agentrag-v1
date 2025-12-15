import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';

interface WorkflowGene {
  id: string;
  name: string;
  type: 'performance' | 'reliability' | 'efficiency' | 'adaptability' | 'creativity';
  value: number;
  dominance: number;
  mutation_rate: number;
  expression_level: number;
  interactions: string[];
}

interface WorkflowDNA {
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

interface EvolutionExperiment {
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

interface CrossoverLab {
  parent1: WorkflowDNA | null;
  parent2: WorkflowDNA | null;
}

interface WorkflowDNAState {
  // State
  currentExperiment: EvolutionExperiment | null;
  selectedWorkflow: WorkflowDNA | null;
  isEvolving: boolean;
  evolutionSpeed: number;
  viewMode: 'helix' | 'tree' | 'landscape';
  crossoverLab: CrossoverLab;
  
  // Actions
  setCurrentExperiment: (experiment: EvolutionExperiment | null) => void;
  setSelectedWorkflow: (workflow: WorkflowDNA | null) => void;
  setIsEvolving: (evolving: boolean) => void;
  setEvolutionSpeed: (speed: number) => void;
  setViewMode: (mode: 'helix' | 'tree' | 'landscape') => void;
  setCrossoverParent1: (parent: WorkflowDNA | null) => void;
  setCrossoverParent2: (parent: WorkflowDNA | null) => void;
  resetCrossoverLab: () => void;
  updateExperimentGeneration: (generation: number) => void;
  addToPopulation: (workflows: WorkflowDNA[]) => void;
  updateExperimentParameters: (parameters: Partial<EvolutionExperiment>) => void;
}

export const useWorkflowDNAStore = create<WorkflowDNAState>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // Initial state
      currentExperiment: null,
      selectedWorkflow: null,
      isEvolving: false,
      evolutionSpeed: 1,
      viewMode: 'helix',
      crossoverLab: {
        parent1: null,
        parent2: null,
      },

      // Actions
      setCurrentExperiment: (experiment) => 
        set({ currentExperiment: experiment }, false, 'setCurrentExperiment'),
      
      setSelectedWorkflow: (workflow) => 
        set({ selectedWorkflow: workflow }, false, 'setSelectedWorkflow'),
      
      setIsEvolving: (evolving) => 
        set({ isEvolving: evolving }, false, 'setIsEvolving'),
      
      setEvolutionSpeed: (speed) => 
        set({ evolutionSpeed: speed }, false, 'setEvolutionSpeed'),
      
      setViewMode: (mode) => 
        set({ viewMode: mode }, false, 'setViewMode'),
      
      setCrossoverParent1: (parent) =>
        set(
          (state) => ({
            crossoverLab: { ...state.crossoverLab, parent1: parent },
          }),
          false,
          'setCrossoverParent1'
        ),
      
      setCrossoverParent2: (parent) =>
        set(
          (state) => ({
            crossoverLab: { ...state.crossoverLab, parent2: parent },
          }),
          false,
          'setCrossoverParent2'
        ),
      
      resetCrossoverLab: () =>
        set(
          { crossoverLab: { parent1: null, parent2: null } },
          false,
          'resetCrossoverLab'
        ),
      
      updateExperimentGeneration: (generation) =>
        set(
          (state) => {
            if (!state.currentExperiment) return state;
            return {
              currentExperiment: {
                ...state.currentExperiment,
                current_generation: generation,
              },
            };
          },
          false,
          'updateExperimentGeneration'
        ),
      
      addToPopulation: (workflows) =>
        set(
          (state) => {
            if (!state.currentExperiment) return state;
            return {
              currentExperiment: {
                ...state.currentExperiment,
                population: [...state.currentExperiment.population, ...workflows],
              },
            };
          },
          false,
          'addToPopulation'
        ),
      
      updateExperimentParameters: (parameters) =>
        set(
          (state) => {
            if (!state.currentExperiment) return state;
            return {
              currentExperiment: {
                ...state.currentExperiment,
                ...parameters,
              },
            };
          },
          false,
          'updateExperimentParameters'
        ),
    })),
    {
      name: 'workflow-dna-store',
    }
  )
);