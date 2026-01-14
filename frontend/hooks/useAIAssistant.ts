/**
 * AI Assistant Hook
 * 
 * AI assistant for intelligent block recommendations and workflow optimization
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import { Node, Edge } from 'reactflow';

export interface WorkflowContext {
  blocks: Node[];
  edges: Edge[];
  intent: string;
  history: WorkflowPattern[];
  userPreferences: UserPreferences;
  currentSelection?: string;
}

export interface WorkflowPattern {
  id: string;
  name: string;
  description: string;
  blocks: string[];
  connections: Array<{ from: string; to: string }>;
  usage_count: number;
  success_rate: number;
  avg_execution_time: number;
  tags: string[];
}

export interface UserPreferences {
  preferred_llm_models: string[];
  frequently_used_tools: string[];
  workflow_complexity: 'simple' | 'medium' | 'complex';
  domain_expertise: string[];
}

export interface BlockSuggestion {
  id: string;
  block_type: string;
  display_name: string;
  description: string;
  confidence: number;
  reasoning: string;
  estimated_benefit: string;
  configuration_suggestion?: any;
  position_suggestion?: { x: number; y: number };
  connection_suggestions?: Array<{ target: string; type: string }>;
}

export interface OptimizationSuggestion {
  type: 'performance' | 'reliability' | 'cost' | 'maintainability';
  title: string;
  description: string;
  impact: 'low' | 'medium' | 'high';
  effort: 'low' | 'medium' | 'high';
  changes: Array<{
    action: 'add' | 'remove' | 'modify' | 'reorder';
    target: string;
    details: any;
  }>;
}

interface UseAIAssistantOptions {
  enabled?: boolean;
  suggestionLimit?: number;
  autoSuggest?: boolean;
  learningMode?: boolean;
}

export const useAIAssistant = (options: UseAIAssistantOptions = {}) => {
  const {
    enabled = true,
    suggestionLimit = 5,
    autoSuggest = true,
    learningMode = true
  } = options;

  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<BlockSuggestion[]>([]);
  const [optimizations, setOptimizations] = useState<OptimizationSuggestion[]>([]);
  const [workflowPatterns, setWorkflowPatterns] = useState<WorkflowPattern[]>([]);
  const [userPreferences, setUserPreferences] = useState<UserPreferences>({
    preferred_llm_models: ['gpt-4', 'claude-3'],
    frequently_used_tools: [],
    workflow_complexity: 'medium',
    domain_expertise: []
  });

  // Load workflow patterns
  const loadWorkflowPatterns = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/ai-assistant/workflow-patterns');
      if (response.ok) {
        const patterns = await response.json();
        setWorkflowPatterns(patterns);
      }
    } catch (error) {
      console.error('Failed to load workflow patterns:', error);
    }
  }, []);

  // Load user preferences
  const loadUserPreferences = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/ai-assistant/user-preferences');
      if (response.ok) {
        const preferences = await response.json();
        setUserPreferences(preferences);
      }
    } catch (error) {
      console.error('Failed to load user preferences:', error);
    }
  }, []);

  // Suggest next blocks
  const suggestNextBlocks = useCallback(async (context: WorkflowContext): Promise<BlockSuggestion[]> => {
    if (!enabled) return [];

    setIsLoading(true);
    
    try {
      const response = await fetch('/api/v1/ai-assistant/suggest-blocks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          context,
          user_preferences: userPreferences,
          limit: suggestionLimit,
          patterns: workflowPatterns
        })
      });

      if (response.ok) {
        const suggestions = await response.json();
        setSuggestions(suggestions);
        return suggestions;
      }
    } catch (error) {
      console.error('Failed to get block suggestions:', error);
    } finally {
      setIsLoading(false);
    }

    return [];
  }, [enabled, suggestionLimit, userPreferences, workflowPatterns]);

  // Suggest workflow optimizations
  const suggestOptimizations = useCallback(async (context: WorkflowContext): Promise<OptimizationSuggestion[]> => {
    if (!enabled) return [];

    try {
      const response = await fetch('/api/v1/ai-assistant/suggest-optimizations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          context,
          user_preferences: userPreferences,
          patterns: workflowPatterns
        })
      });

      if (response.ok) {
        const optimizations = await response.json();
        setOptimizations(optimizations);
        return optimizations;
      }
    } catch (error) {
      console.error('Failed to get optimization suggestions:', error);
    }

    return [];
  }, [enabled, userPreferences, workflowPatterns]);

  // Analyze workflow pattern
  const analyzeWorkflowPattern = useCallback((context: WorkflowContext) => {
    const { blocks, edges } = context;
    
    // Analyze block types
    const blockTypes = blocks.map(block => block.type || 'unknown');
    const blockTypeCount = blockTypes.reduce((acc, type) => {
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    // Analyze connection patterns
    const connectionPatterns = edges.map(edge => ({
      from: blocks.find(b => b.id === edge.source)?.type || 'unknown',
      to: blocks.find(b => b.id === edge.target)?.type || 'unknown'
    }));

    // Calculate complexity
    const complexity = calculateWorkflowComplexity(blocks, edges);

    // Find similar patterns
    const similarPatterns = findSimilarPatterns(blockTypes, connectionPatterns, workflowPatterns);

    return {
      blockTypeCount,
      connectionPatterns,
      complexity,
      similarPatterns,
      recommendations: generatePatternRecommendations(blockTypes, connectionPatterns, similarPatterns)
    };
  }, [workflowPatterns]);

  // Calculate workflow complexity
  const calculateWorkflowComplexity = (blocks: Node[], edges: Edge[]) => {
    const nodeCount = blocks.length;
    const edgeCount = edges.length;
    const avgConnections = nodeCount > 0 ? edgeCount / nodeCount : 0;
    
    // Calculate branching points (nodes with 2+ outputs)
    const branchingNodes = blocks.filter(block => {
      const outgoingEdges = edges.filter(edge => edge.source === block.id);
      return outgoingEdges.length > 1;
    }).length;

    // Complexity score (0-100)
    const complexityScore = Math.min(100, 
      (nodeCount * 2) + 
      (edgeCount * 1.5) + 
      (branchingNodes * 5) + 
      (avgConnections * 3)
    );

    let level: 'simple' | 'medium' | 'complex';
    if (complexityScore < 20) level = 'simple';
    else if (complexityScore < 50) level = 'medium';
    else level = 'complex';

    return {
      score: complexityScore,
      level,
      nodeCount,
      edgeCount,
      branchingNodes,
      avgConnections
    };
  };

  // Find similar patterns
  const findSimilarPatterns = (
    blockTypes: string[], 
    connectionPatterns: Array<{ from: string; to: string }>,
    patterns: WorkflowPattern[]
  ) => {
    return patterns
      .map(pattern => {
        // Block type similarity
        const blockSimilarity = calculateBlockSimilarity(blockTypes, pattern.blocks);
        
        // Connection pattern similarity
        const connectionSimilarity = calculateConnectionSimilarity(connectionPatterns, pattern.connections);
        
        // Overall similarity
        const overallSimilarity = (blockSimilarity + connectionSimilarity) / 2;
        
        return {
          ...pattern,
          similarity: overallSimilarity
        };
      })
      .filter(pattern => pattern.similarity > 0.3) // Only patterns with 30%+ similarity
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, 5); // Top 5 only
  };

  // Calculate block type similarity
  const calculateBlockSimilarity = (currentBlocks: string[], patternBlocks: string[]) => {
    const currentSet = new Set(currentBlocks);
    const patternSet = new Set(patternBlocks);
    
    const intersection = new Set([...currentSet].filter(x => patternSet.has(x)));
    const union = new Set([...currentSet, ...patternSet]);
    
    return union.size > 0 ? intersection.size / union.size : 0;
  };

  // Calculate connection pattern similarity
  const calculateConnectionSimilarity = (
    currentConnections: Array<{ from: string; to: string }>,
    patternConnections: Array<{ from: string; to: string }>
  ) => {
    if (currentConnections.length === 0 && patternConnections.length === 0) return 1;
    if (currentConnections.length === 0 || patternConnections.length === 0) return 0;

    const currentPatterns = currentConnections.map(c => `${c.from}->${c.to}`);
    const patternPatterns = patternConnections.map(c => `${c.from}->${c.to}`);
    
    const currentSet = new Set(currentPatterns);
    const patternSet = new Set(patternPatterns);
    
    const intersection = new Set([...currentSet].filter(x => patternSet.has(x)));
    const union = new Set([...currentSet, ...patternSet]);
    
    return union.size > 0 ? intersection.size / union.size : 0;
  };

  // Generate pattern-based recommendations
  const generatePatternRecommendations = (
    blockTypes: string[],
    connectionPatterns: Array<{ from: string; to: string }>,
    similarPatterns: any[]
  ) => {
    const recommendations = [];

    // Recommend frequently used next blocks
    if (similarPatterns.length > 0) {
      const topPattern = similarPatterns[0];
      const missingBlocks = topPattern.blocks.filter((block: string) => !blockTypes.includes(block));
      
      if (missingBlocks.length > 0) {
        recommendations.push({
          type: 'missing_blocks',
          title: 'Add blocks to complete pattern',
          blocks: missingBlocks.slice(0, 3),
          confidence: topPattern.similarity
        });
      }
    }

    // Performance optimization recommendation
    if (blockTypes.includes('llm') && !blockTypes.includes('cache')) {
      recommendations.push({
        type: 'performance',
        title: 'Add LLM response caching',
        blocks: ['cache'],
        confidence: 0.8
      });
    }

    return recommendations;
  };

  // Collect learning data
  const recordUserAction = useCallback(async (action: {
    type: 'block_added' | 'block_removed' | 'suggestion_accepted' | 'suggestion_rejected';
    blockType?: string;
    suggestionId?: string;
    context: WorkflowContext;
  }) => {
    if (!learningMode) return;

    try {
      await fetch('/api/v1/ai-assistant/record-action', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(action)
      });
    } catch (error) {
      console.error('Failed to record user action:', error);
    }
  }, [learningMode]);

  // Initialization
  useEffect(() => {
    if (enabled) {
      loadWorkflowPatterns();
      loadUserPreferences();
    }
  }, [enabled, loadWorkflowPatterns, loadUserPreferences]);

  return {
    // State
    isLoading,
    suggestions,
    optimizations,
    workflowPatterns,
    userPreferences,

    // Methods
    suggestNextBlocks,
    suggestOptimizations,
    analyzeWorkflowPattern,
    recordUserAction,
    
    // Utilities
    calculateWorkflowComplexity,
    findSimilarPatterns,

    // Settings
    setUserPreferences
  };
};