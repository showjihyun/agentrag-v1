'use client';

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { VirtualizedList } from '@/components/ui/virtualized-list';
import { 
  AnimatedDiv, 
  AnimatedCard, 
  AnimatedList, 
  AnimatedListItem, 
  AnimatedProgress, 
  PulseIndicator
} from '@/components/ui/animated-components';
import { 
  Dna, 
  Shuffle, 
  TrendingUp, 
  Zap, 
  Target, 
  GitBranch,
  Activity,
  Beaker,
  Microscope,
  FlaskConical,
  Atom,
  Sparkles,
  RotateCcw,
  Play,
  Pause,
  RefreshCw,
  Eye,
  Settings,
  Award,
  TreePine
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { useExperiments, useExperiment, usePopulation, useEvolutionAnalytics, useStartEvolution, useStopEvolution, usePerformCrossover, useResetExperiment, useUpdateExperimentParameters } from '@/hooks/queries/useWorkflowDNA';
import { useWorkflowDNAStore } from '@/lib/stores/workflowDNAStore';
import type { WorkflowGene, WorkflowDNA, EvolutionExperiment } from '@/lib/api/workflowDNAApi';

// Types are now imported from API

interface WorkflowDNABlockProps {
  onConfigChange?: (config: any) => void;
  initialConfig?: any;
}

const WorkflowDNABlock: React.FC<WorkflowDNABlockProps> = ({
  onConfigChange
}) => {
  // Zustand store
  const { 
    currentExperiment, 
    selectedWorkflow, 
    isEvolving, 
    evolutionSpeed, 
    viewMode, 
    crossoverLab,
    setCurrentExperiment,
    setSelectedWorkflow,
    setIsEvolving,
    setEvolutionSpeed,
    setViewMode,
    setCrossoverParent1,
    setCrossoverParent2,
    resetCrossoverLab,
    updateExperimentParameters
  } = useWorkflowDNAStore();

  // React Query hooks
  const experimentId = 'exp_1'; // Mock experiment ID
  
  const { data: experimentsData, isLoading: experimentsLoading } = useExperiments();
  const { data: experimentData, isLoading: experimentLoading } = useExperiment(experimentId);
  const { data: populationData, isLoading: populationLoading } = usePopulation(experimentId);
  const { data: analyticsData } = useEvolutionAnalytics(experimentId);

  // Mutations
  const startEvolutionMutation = useStartEvolution();
  const stopEvolutionMutation = useStopEvolution();
  const performCrossoverMutation = usePerformCrossover();
  const resetExperimentMutation = useResetExperiment();
  const updateParametersMutation = useUpdateExperimentParameters();

  // Animation refs
  const evolutionRef = useRef<number | null>(null);
  const helixRef = useRef<HTMLCanvasElement>(null);

  // Memoized data
  const experiments = useMemo(() => experimentsData?.experiments || [], [experimentsData]);
  const population = useMemo(() => populationData?.population || [], [populationData]);
  const analytics = useMemo(() => analyticsData?.analytics || {}, [analyticsData]);

  // Update store when data changes
  useEffect(() => {
    if (experimentData?.experiment) {
      setCurrentExperiment(experimentData.experiment);
    }
  }, [experimentData, setCurrentExperiment]);

  useEffect(() => {
    if (population.length > 0 && !selectedWorkflow) {
      setSelectedWorkflow(population[0] || null);
    }
  }, [population, selectedWorkflow, setSelectedWorkflow]);

  useEffect(() => {
    if (isEvolving) {
      startEvolution();
    }
    return () => {
      if (evolutionRef.current) {
        cancelAnimationFrame(evolutionRef.current);
      }
    };
  }, [isEvolving]);

  // Evolution control functions
  const handleStartEvolution = () => {
    if (currentExperiment) {
      startEvolutionMutation.mutate(currentExperiment.id);
      setIsEvolving(true);
    }
  };

  const handleStopEvolution = () => {
    if (currentExperiment) {
      stopEvolutionMutation.mutate(currentExperiment.id);
      setIsEvolving(false);
      if (evolutionRef.current) {
        cancelAnimationFrame(evolutionRef.current);
      }
    }
  };

  const handleResetExperiment = () => {
    if (currentExperiment) {
      resetExperimentMutation.mutate(currentExperiment.id);
      setIsEvolving(false);
    }
  };

  const calculateFitness = (genes: WorkflowGene[]): number => {
    // Multi-objective fitness function
    const weights = {
      performance: 0.3,
      reliability: 0.25,
      efficiency: 0.2,
      adaptability: 0.15,
      creativity: 0.1
    };

    let fitness = 0;
    genes.forEach(gene => {
      const weight = weights[gene.type] || 0.1;
      fitness += gene.value * gene.expression_level * weight;
    });

    return Math.min(1, fitness);
  };

  const calculateDiversityIndex = (population: WorkflowDNA[]): number => {
    if (population.length === 0 || !population[0]) return 0;
    
    // Calculate genetic diversity using Shannon diversity index
    const geneVariances = population[0].genes.map((_, geneIndex) => {
      const values = population.map(w => w.genes[geneIndex]?.value || 0);
      const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
      const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
      return variance;
    });

    return geneVariances.reduce((sum, variance) => sum + variance, 0) / geneVariances.length;
  };

  const startEvolution = () => {
    if (!currentExperiment) return;

    const evolve = () => {
      if (!currentExperiment || currentExperiment.current_generation >= currentExperiment.max_generations) {
        setIsEvolving(false);
        return;
      }

      // Perform one generation of evolution
      const newPopulation = performEvolutionStep(currentExperiment.population, currentExperiment);
      const newGeneration = currentExperiment.current_generation + 1;

      const bestFitness = Math.max(...newPopulation.map(w => w.fitness_score));
      const averageFitness = newPopulation.reduce((sum, w) => sum + w.fitness_score, 0) / newPopulation.length;
      const diversityIndex = calculateDiversityIndex(newPopulation);

      const newHistory = [...currentExperiment.evolution_history, {
        generation: newGeneration,
        best_fitness: bestFitness,
        average_fitness: averageFitness,
        diversity_index: diversityIndex,
        extinction_events: diversityIndex < 0.01 ? 1 : 0
      }];

      const updatedExperiment = {
        ...currentExperiment,
        current_generation: newGeneration,
        population: newPopulation,
        evolution_history: newHistory
      };

      setCurrentExperiment(updatedExperiment);

      if (isEvolving) {
        setTimeout(() => {
          evolutionRef.current = requestAnimationFrame(evolve);
        }, 1000 / evolutionSpeed);
      }
    };

    evolve();
  };

  const performEvolutionStep = (population: WorkflowDNA[], experiment: EvolutionExperiment): WorkflowDNA[] => {
    // Selection
    const selected = tournamentSelection(population, experiment.population_size);
    
    // Crossover and Mutation
    const newPopulation: WorkflowDNA[] = [];
    
    for (let i = 0; i < selected.length; i += 2) {
      const parent1 = selected[i];
      const parent2 = selected[i + 1] || selected[0];
      
      if (!parent1 || !parent2) continue;
      
      if (Math.random() < experiment.crossover_rate) {
        const [child1, child2] = crossover(parent1, parent2, experiment.current_generation + 1);
        newPopulation.push(mutate(child1, experiment.mutation_rate));
        if (newPopulation.length < experiment.population_size) {
          newPopulation.push(mutate(child2, experiment.mutation_rate));
        }
      } else {
        newPopulation.push(mutate({ ...parent1 }, experiment.mutation_rate));
        if (newPopulation.length < experiment.population_size) {
          newPopulation.push(mutate({ ...parent2 }, experiment.mutation_rate));
        }
      }
    }

    return newPopulation.slice(0, experiment.population_size);
  };

  const tournamentSelection = (population: WorkflowDNA[], size: number): WorkflowDNA[] => {
    if (population.length === 0) return [];
    
    const selected: WorkflowDNA[] = [];
    const tournamentSize = 3;

    for (let i = 0; i < size; i++) {
      const tournament: WorkflowDNA[] = [];
      for (let j = 0; j < tournamentSize; j++) {
        const randomIndex = Math.floor(Math.random() * population.length);
        const selectedWorkflow = population[randomIndex];
        if (selectedWorkflow) {
          tournament.push(selectedWorkflow);
        }
      }
      if (tournament.length > 0) {
        tournament.sort((a, b) => b.fitness_score - a.fitness_score);
        const winner = tournament[0];
        if (winner) {
          selected.push(winner);
        }
      }
    }

    return selected;
  };

  const crossover = (parent1: WorkflowDNA, parent2: WorkflowDNA, generation: number): [WorkflowDNA, WorkflowDNA] => {
    const child1Genes = parent1.genes.map((gene, index) => {
      const parent2Gene = parent2.genes[index];
      return {
        ...gene,
        value: Math.random() < 0.5 ? gene.value : (parent2Gene?.value ?? gene.value),
        expression_level: parent2Gene ? (gene.expression_level + parent2Gene.expression_level) / 2 : gene.expression_level
      };
    });

    const child2Genes = parent1.genes.map((gene, index) => {
      const parent2Gene = parent2.genes[index];
      return {
        ...gene,
        value: Math.random() < 0.5 ? (parent2Gene?.value ?? gene.value) : gene.value,
        expression_level: parent2Gene ? (gene.expression_level + parent2Gene.expression_level) / 2 : gene.expression_level
      };
    });

    const child1: WorkflowDNA = {
      id: `workflow_${Date.now()}_1`,
      name: `Hybrid ${parent1.name.split(' ')[2]} × ${parent2.name.split(' ')[2]}`,
      generation,
      genes: child1Genes,
      fitness_score: calculateFitness(child1Genes),
      performance_metrics: {
        speed: child1Genes.find(g => g.id === 'speed_gene')?.value || 0,
        accuracy: child1Genes.find(g => g.id === 'accuracy_gene')?.value || 0,
        efficiency: child1Genes.find(g => g.id === 'efficiency_gene')?.value || 0,
        adaptability: child1Genes.find(g => g.id === 'adaptability_gene')?.value || 0,
        innovation: child1Genes.find(g => g.id === 'creativity_gene')?.value || 0
      },
      parent_ids: [parent1.id, parent2.id],
      mutation_history: [],
      survival_probability: Math.random(),
      age: 0
    };

    const child2: WorkflowDNA = {
      ...child1,
      id: `workflow_${Date.now()}_2`,
      genes: child2Genes,
      fitness_score: calculateFitness(child2Genes),
      performance_metrics: {
        speed: child2Genes.find(g => g.id === 'speed_gene')?.value || 0,
        accuracy: child2Genes.find(g => g.id === 'accuracy_gene')?.value || 0,
        efficiency: child2Genes.find(g => g.id === 'efficiency_gene')?.value || 0,
        adaptability: child2Genes.find(g => g.id === 'adaptability_gene')?.value || 0,
        innovation: child2Genes.find(g => g.id === 'creativity_gene')?.value || 0
      }
    };

    return [child1, child2];
  };

  const mutate = (workflow: WorkflowDNA, mutationRate: number): WorkflowDNA => {
    const mutatedGenes = workflow.genes.map(gene => {
      if (Math.random() < mutationRate) {
        const oldValue = gene.value;
        const newValue = Math.max(0, Math.min(1, gene.value + (Math.random() - 0.5) * 0.2));
        
        workflow.mutation_history.push({
          generation: workflow.generation,
          gene_id: gene.id,
          old_value: oldValue,
          new_value: newValue,
          impact: Math.abs(newValue - oldValue)
        });

        return {
          ...gene,
          value: newValue
        };
      }
      return gene;
    });

    return {
      ...workflow,
      genes: mutatedGenes,
      fitness_score: calculateFitness(mutatedGenes)
    };
  };

  const handlePerformCrossover = () => {
    if (!crossoverLab.parent1 || !crossoverLab.parent2 || !currentExperiment) return;

    performCrossoverMutation.mutate({
      parent1_id: crossoverLab.parent1.id,
      parent2_id: crossoverLab.parent2.id,
      experiment_id: currentExperiment.id
    }, {
      onSuccess: () => {
        resetCrossoverLab();
      }
    });
  };

  const getGeneColor = (geneType: string) => {
    const colorMap: Record<string, string> = {
      performance: '#ef4444',
      reliability: '#3b82f6',
      efficiency: '#10b981',
      adaptability: '#f59e0b',
      creativity: '#8b5cf6'
    };
    return colorMap[geneType] || '#6b7280';
  };

  const getFitnessLevel = (fitness: number) => {
    if (fitness >= 0.8) return { level: 'Elite', color: 'text-purple-600 bg-purple-100' };
    if (fitness >= 0.6) return { level: 'Strong', color: 'text-green-600 bg-green-100' };
    if (fitness >= 0.4) return { level: 'Average', color: 'text-blue-600 bg-blue-100' };
    if (fitness >= 0.2) return { level: 'Weak', color: 'text-yellow-600 bg-yellow-100' };
    return { level: 'Poor', color: 'text-red-600 bg-red-100' };
  };

  // Loading states
  if (experimentsLoading || experimentLoading || populationLoading) {
    return (
      <div className="w-full space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-32 bg-gray-200 rounded mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="h-64 bg-gray-200 rounded"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <AnimatedDiv className="w-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Dna className="h-6 w-6 text-purple-600" />
            Workflow DNA Evolution System
          </h2>
          <p className="text-gray-600 mt-1">
            Genetic algorithms for evolving optimal workflow configurations
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={viewMode} onValueChange={(value: any) => setViewMode(value)}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="helix">🧬 DNA Helix</SelectItem>
              <SelectItem value="tree">🌳 Evolution Tree</SelectItem>
              <SelectItem value="landscape">🏔️ Fitness Landscape</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="sm"
            onClick={isEvolving ? handleStopEvolution : handleStartEvolution}
          >
            {isEvolving ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            {isEvolving ? 'Pause' : 'Start'} Evolution
          </Button>
        </div>
      </div>

      {/* Evolution Status */}
      {currentExperiment && (
        <AnimatedCard className="border-2 border-purple-200 bg-gradient-to-r from-purple-50 to-pink-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-lg flex items-center gap-2">
                  <Beaker className="h-5 w-5 text-purple-600" />
                  {currentExperiment.name}
                </h3>
                <div className="flex items-center gap-4 mt-2">
                  <Badge className={isEvolving ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}>
                    {currentExperiment.status.toUpperCase()}
                  </Badge>
                  <span className="text-sm">
                    Generation: {currentExperiment.current_generation}/{currentExperiment.max_generations}
                  </span>
                  <span className="text-sm">
                    Population: {currentExperiment.population.length}
                  </span>
                  <span className="text-sm">
                    Best Fitness: {(Math.max(...currentExperiment.population.map(w => w.fitness_score)) * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-purple-600">
                  {isEvolving ? <Activity className="h-8 w-8 animate-pulse" /> : <Microscope className="h-8 w-8" />}
                </div>
                <p className="text-sm text-gray-600">
                  {isEvolving ? 'Evolving...' : 'Ready'}
                </p>
              </div>
            </div>
            
            {/* Evolution Progress */}
            <div className="mt-4">
              <Progress 
                value={(currentExperiment.current_generation / currentExperiment.max_generations) * 100} 
                className="h-2"
              />
            </div>
          </CardContent>
        </AnimatedCard>
      )}

      {/* Main Content */}
      <Tabs defaultValue="population" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="population">🧬 Population</TabsTrigger>
          <TabsTrigger value="genetics">🔬 Gene Lab</TabsTrigger>
          <TabsTrigger value="crossover">⚗️ Crossover Lab</TabsTrigger>
          <TabsTrigger value="evolution">📈 Evolution</TabsTrigger>
          <TabsTrigger value="analysis">📊 Analysis</TabsTrigger>
        </TabsList>

        {/* Population Tab */}
        <TabsContent value="population" className="space-y-4">
          {population.length > 0 && (
            <AnimatedList className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {population
                .sort((a, b) => b.fitness_score - a.fitness_score)
                .slice(0, 12)
                .map((workflow, index) => (
                <AnimatedListItem key={workflow.id}>
                  <div 
                    className={`cursor-pointer transition-all hover:shadow-md ${
                      selectedWorkflow?.id === workflow.id ? 'ring-2 ring-purple-500' : ''
                    }`}
                    onClick={() => setSelectedWorkflow(workflow)}
                  >
                    <AnimatedCard>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <Badge className="bg-purple-100 text-purple-800">
                          #{index + 1}
                        </Badge>
                        {workflow.name}
                      </span>
                      <Badge className={getFitnessLevel(workflow.fitness_score).color}>
                        {getFitnessLevel(workflow.fitness_score).level}
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {/* DNA Visualization */}
                    <div className="flex items-center gap-1 mb-3">
                      {workflow.genes.map((gene, geneIndex) => (
                        <div
                          key={gene.id}
                          className="w-4 h-8 rounded-sm"
                          style={{ 
                            backgroundColor: getGeneColor(gene.type),
                            opacity: gene.expression_level
                          }}
                          title={`${gene.name}: ${(gene.value * 100).toFixed(0)}%`}
                        />
                      ))}
                    </div>

                    {/* Performance Metrics */}
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between">
                        <span>Fitness Score</span>
                        <span className="font-bold">{(workflow.fitness_score * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Generation</span>
                        <span>{workflow.generation}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Mutations</span>
                        <span>{workflow.mutation_history.length}</span>
                      </div>
                    </div>

                    {/* Parent Information */}
                    {workflow.parent_ids.length > 0 && (
                      <div className="mt-2 pt-2 border-t">
                        <div className="text-xs text-gray-600">
                          Parents: {workflow.parent_ids.length}
                        </div>
                      </div>
                    )}
                  </CardContent>
                  </AnimatedCard>
                  </div>
                </AnimatedListItem>
              ))}
            </AnimatedList>
          )}
        </TabsContent>

        {/* Gene Lab Tab */}
        <TabsContent value="genetics" className="space-y-4">
          {selectedWorkflow && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Gene Details */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FlaskConical className="h-5 w-5" />
                    Genetic Analysis: {selectedWorkflow.name}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {selectedWorkflow.genes.map((gene) => (
                      <div key={gene.id} className="border rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium">{gene.name}</span>
                          <Badge 
                            style={{ backgroundColor: getGeneColor(gene.type) }}
                            className="text-white"
                          >
                            {gene.type}
                          </Badge>
                        </div>
                        
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span>Value</span>
                            <span>{(gene.value * 100).toFixed(1)}%</span>
                          </div>
                          <Progress value={gene.value * 100} className="h-2" />
                          
                          <div className="flex justify-between text-sm">
                            <span>Expression Level</span>
                            <span>{(gene.expression_level * 100).toFixed(1)}%</span>
                          </div>
                          <Progress value={gene.expression_level * 100} className="h-2" />
                          
                          <div className="flex justify-between text-sm">
                            <span>Dominance</span>
                            <span>{(gene.dominance * 100).toFixed(1)}%</span>
                          </div>
                          <Progress value={gene.dominance * 100} className="h-2" />
                        </div>

                        {gene.interactions.length > 0 && (
                          <div className="mt-2 pt-2 border-t">
                            <div className="text-xs text-gray-600">
                              Interactions: {gene.interactions.join(', ')}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Performance Radar */}
              <Card>
                <CardHeader>
                  <CardTitle>Performance Profile</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={[
                        { metric: 'Speed', value: selectedWorkflow.performance_metrics.speed * 100 },
                        { metric: 'Accuracy', value: selectedWorkflow.performance_metrics.accuracy * 100 },
                        { metric: 'Efficiency', value: selectedWorkflow.performance_metrics.efficiency * 100 },
                        { metric: 'Adaptability', value: selectedWorkflow.performance_metrics.adaptability * 100 },
                        { metric: 'Innovation', value: selectedWorkflow.performance_metrics.innovation * 100 }
                      ]}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="metric" />
                        <PolarRadiusAxis angle={90} domain={[0, 100]} />
                        <Radar
                          name="Performance"
                          dataKey="value"
                          stroke="#8b5cf6"
                          fill="#8b5cf6"
                          fillOpacity={0.3}
                        />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Mutation History */}
                  {selectedWorkflow.mutation_history.length > 0 && (
                    <div className="mt-4">
                      <h4 className="font-medium mb-2">Recent Mutations</h4>
                      <div className="space-y-1 max-h-32 overflow-y-auto">
                        {selectedWorkflow.mutation_history.slice(-5).map((mutation, index) => (
                          <div key={index} className="text-xs p-2 bg-gray-50 rounded">
                            <span className="font-medium">{mutation.gene_id}</span>: 
                            {(mutation.old_value * 100).toFixed(1)}% → {(mutation.new_value * 100).toFixed(1)}%
                            <span className="text-gray-500 ml-2">
                              (Impact: {(mutation.impact * 100).toFixed(1)}%)
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Crossover Lab Tab */}
        <TabsContent value="crossover" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Atom className="h-5 w-5" />
                Genetic Crossover Laboratory
              </CardTitle>
              <CardDescription>
                Experiment with genetic crossover between different workflow organisms
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Parent 1 Selection */}
                <div className="space-y-2">
                  <Label>Parent 1</Label>
                  <Select 
                    value={crossoverLab.parent1?.id || ''} 
                    onValueChange={(value) => {
                      const parent = population.find(w => w.id === value);
                      setCrossoverParent1(parent || null);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select Parent 1" />
                    </SelectTrigger>
                    <SelectContent>
                      {currentExperiment?.population.map((workflow) => (
                        <SelectItem key={workflow.id} value={workflow.id}>
                          {workflow.name} (Fitness: {(workflow.fitness_score * 100).toFixed(1)}%)
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  
                  {crossoverLab.parent1 && (
                    <div className="p-2 border rounded">
                      <div className="flex items-center gap-1 mb-2">
                        {crossoverLab.parent1.genes.map((gene) => (
                          <div
                            key={gene.id}
                            className="w-3 h-6 rounded-sm"
                            style={{ 
                              backgroundColor: getGeneColor(gene.type),
                              opacity: gene.expression_level
                            }}
                          />
                        ))}
                      </div>
                      <div className="text-xs text-gray-600">
                        Fitness: {(crossoverLab.parent1.fitness_score * 100).toFixed(1)}%
                      </div>
                    </div>
                  )}
                </div>

                {/* Crossover Operation */}
                <div className="flex flex-col items-center justify-center space-y-4">
                  <Shuffle className="h-8 w-8 text-purple-600" />
                  <Button
                    onClick={handlePerformCrossover}
                    disabled={!crossoverLab.parent1 || !crossoverLab.parent2}
                    className="w-full"
                  >
                    <Sparkles className="h-4 w-4 mr-2" />
                    Create Offspring
                  </Button>
                </div>

                {/* Parent 2 Selection */}
                <div className="space-y-2">
                  <Label>Parent 2</Label>
                  <Select 
                    value={crossoverLab.parent2?.id || ''} 
                    onValueChange={(value) => {
                      const parent = population.find(w => w.id === value);
                      setCrossoverParent2(parent || null);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select Parent 2" />
                    </SelectTrigger>
                    <SelectContent>
                      {currentExperiment?.population.map((workflow) => (
                        <SelectItem key={workflow.id} value={workflow.id}>
                          {workflow.name} (Fitness: {(workflow.fitness_score * 100).toFixed(1)}%)
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  
                  {crossoverLab.parent2 && (
                    <div className="p-2 border rounded">
                      <div className="flex items-center gap-1 mb-2">
                        {crossoverLab.parent2.genes.map((gene) => (
                          <div
                            key={gene.id}
                            className="w-3 h-6 rounded-sm"
                            style={{ 
                              backgroundColor: getGeneColor(gene.type),
                              opacity: gene.expression_level
                            }}
                          />
                        ))}
                      </div>
                      <div className="text-xs text-gray-600">
                        Fitness: {(crossoverLab.parent2.fitness_score * 100).toFixed(1)}%
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Crossover Parameters */}
              <div className="mt-6 space-y-4">
                <div>
                  <Label>Crossover Rate: {currentExperiment?.crossover_rate || 0.7}</Label>
                  <Slider
                    value={[currentExperiment?.crossover_rate || 0.7]}
                    onValueChange={([value]) => {
                      if (value !== undefined) {
                        updateExperimentParameters({ crossover_rate: value });
                      }
                    }}
                    max={1}
                    min={0}
                    step={0.1}
                    className="mt-2"
                  />
                </div>
                <div>
                  <Label>Mutation Rate: {currentExperiment?.mutation_rate || 0.1}</Label>
                  <Slider
                    value={[currentExperiment?.mutation_rate || 0.1]}
                    onValueChange={([value]) => {
                      if (value !== undefined) {
                        updateExperimentParameters({ mutation_rate: value });
                      }
                    }}
                    max={0.5}
                    min={0}
                    step={0.05}
                    className="mt-2"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Evolution Tab */}
        <TabsContent value="evolution" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Evolution History Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Evolution Progress
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={currentExperiment?.evolution_history || []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="generation" />
                      <YAxis />
                      <Tooltip />
                      <Line 
                        type="monotone" 
                        dataKey="best_fitness" 
                        stroke="#8b5cf6" 
                        strokeWidth={2}
                        name="Best Fitness"
                      />
                      <Line 
                        type="monotone" 
                        dataKey="average_fitness" 
                        stroke="#06b6d4" 
                        strokeWidth={2}
                        name="Average Fitness"
                      />
                      <Line 
                        type="monotone" 
                        dataKey="diversity_index" 
                        stroke="#10b981" 
                        strokeWidth={2}
                        name="Diversity Index"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Evolution Controls */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  Evolution Parameters
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Evolution Speed: {evolutionSpeed}x</Label>
                  <Slider
                    value={[evolutionSpeed]}
                    onValueChange={([value]) => {
                      if (value !== undefined) {
                        setEvolutionSpeed(value);
                      }
                    }}
                    max={10}
                    min={0.1}
                    step={0.1}
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label>Selection Pressure: {currentExperiment?.selection_pressure || 0.8}</Label>
                  <Slider
                    value={[currentExperiment?.selection_pressure || 0.8]}
                    onValueChange={([value]) => {
                      if (value !== undefined) {
                        updateExperimentParameters({ selection_pressure: value });
                      }
                    }}
                    max={1}
                    min={0.1}
                    step={0.1}
                    className="mt-2"
                  />
                </div>

                <div>
                  <Label>Population Size: {currentExperiment?.population_size || 20}</Label>
                  <Slider
                    value={[currentExperiment?.population_size || 20]}
                    onValueChange={([value]) => {
                      if (value !== undefined) {
                        updateExperimentParameters({ population_size: value });
                      }
                    }}
                    max={100}
                    min={10}
                    step={5}
                    className="mt-2"
                  />
                </div>

                <div className="pt-4 border-t">
                  <Button
                    onClick={handleResetExperiment}
                    variant="outline"
                    className="w-full"
                  >
                    <RotateCcw className="h-4 w-4 mr-2" />
                    Reset Experiment
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Analysis Tab */}
        <TabsContent value="analysis" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Statistics Cards */}
            <AnimatedCard>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <Award className="h-8 w-8 text-yellow-600" />
                  <div>
                    <p className="text-sm text-gray-600">Elite Organisms</p>
                    <p className="text-xl font-bold">
                      {population.filter(w => w.fitness_score >= 0.8).length || 0}
                    </p>
                  </div>
                </div>
              </CardContent>
            </AnimatedCard>

            <AnimatedCard>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <TreePine className="h-8 w-8 text-green-600" />
                  <div>
                    <p className="text-sm text-gray-600">Genetic Diversity</p>
                    <p className="text-xl font-bold">
                      {population.length > 0 ? (calculateDiversityIndex(population) * 100).toFixed(1) : 0}%
                    </p>
                  </div>
                </div>
              </CardContent>
            </AnimatedCard>

            <AnimatedCard>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <Zap className="h-8 w-8 text-purple-600" />
                  <div>
                    <p className="text-sm text-gray-600">Avg Fitness</p>
                    <p className="text-xl font-bold">
                      {population.length > 0 ? 
                        ((population.reduce((sum, w) => sum + w.fitness_score, 0) / population.length) * 100).toFixed(1) 
                        : 0}%
                    </p>
                  </div>
                </div>
              </CardContent>
            </AnimatedCard>
          </div>

          {/* Insights */}
          <Card>
            <CardHeader>
              <CardTitle>Evolution Insights</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <Alert>
                  <TrendingUp className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Convergence Trend:</strong> Population is showing signs of convergence around high-performance traits.
                  </AlertDescription>
                </Alert>
                <Alert>
                  <Dna className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Genetic Bottleneck:</strong> Consider introducing new genetic material to maintain diversity.
                  </AlertDescription>
                </Alert>
                <Alert>
                  <Sparkles className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Optimal Traits:</strong> High efficiency and adaptability genes are dominating the population.
                  </AlertDescription>
                </Alert>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
      </AnimatedDiv>
    </ErrorBoundary>
  );
};

export default WorkflowDNABlock;