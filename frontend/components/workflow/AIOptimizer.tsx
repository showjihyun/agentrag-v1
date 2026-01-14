'use client';

/**
 * AI Workflow Optimizer
 * 
 * Automatic workflow optimization suggestions:
 * - Parallelization opportunities
 * - Caching recommendations
 * - Redundant node detection
 * - Cost optimization
 */

import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Switch } from '@/components/ui/switch';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Sparkles,
  Zap,
  Clock,
  DollarSign,
  GitBranch,
  Database,
  Trash2,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  ChevronDown,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Settings,
  Play,
} from 'lucide-react';

// Types
export interface OptimizationSuggestion {
  id: string;
  type: OptimizationType;
  title: string;
  description: string;
  impact: Impact;
  affectedNodes: string[];
  estimatedSavings?: {
    time?: string;
    cost?: string;
    percentage?: number;
  };
  autoApplicable: boolean;
  applied?: boolean;
  details?: string;
}

export type OptimizationType = 
  | 'parallelization'
  | 'caching'
  | 'redundant_removal'
  | 'batch_processing'
  | 'cost_optimization'
  | 'error_handling'
  | 'timeout_adjustment';

export interface Impact {
  level: 'low' | 'medium' | 'high';
  timeReduction?: number;
  costReduction?: number;
}

export interface WorkflowMetrics {
  totalNodes: number;
  estimatedDuration: string;
  estimatedCost: string;
  parallelizableNodes: number;
  cacheableNodes: number;
  redundantNodes: number;
}

interface AIOptimizerProps {
  workflowId: string;
  suggestions: OptimizationSuggestion[];
  metrics: WorkflowMetrics;
  isAnalyzing?: boolean;
  onApplySuggestion: (suggestionId: string) => Promise<void>;
  onApplyAll: () => Promise<void>;
  onRefresh: () => void;
  className?: string;
}

// Optimization type config
const optimizationConfig: Record<OptimizationType, {
  icon: React.ElementType;
  color: string;
  bgColor: string;
}> = {
  parallelization: { icon: GitBranch, color: 'text-blue-500', bgColor: 'bg-blue-100' },
  caching: { icon: Database, color: 'text-green-500', bgColor: 'bg-green-100' },
  redundant_removal: { icon: Trash2, color: 'text-orange-500', bgColor: 'bg-orange-100' },
  batch_processing: { icon: Zap, color: 'text-purple-500', bgColor: 'bg-purple-100' },
  cost_optimization: { icon: DollarSign, color: 'text-emerald-500', bgColor: 'bg-emerald-100' },
  error_handling: { icon: AlertTriangle, color: 'text-yellow-500', bgColor: 'bg-yellow-100' },
  timeout_adjustment: { icon: Clock, color: 'text-cyan-500', bgColor: 'bg-cyan-100' },
};

// Impact badge
const ImpactBadge: React.FC<{ impact: Impact }> = ({ impact }) => {
  const config = {
    low: { color: 'bg-gray-100 text-gray-600', label: 'Low' },
    medium: { color: 'bg-yellow-100 text-yellow-700', label: 'Medium' },
    high: { color: 'bg-green-100 text-green-700', label: 'High' },
  };

  return (
    <Badge className={cn('text-xs', config[impact.level].color)}>
      Impact: {config[impact.level].label}
    </Badge>
  );
};

// Suggestion card
const SuggestionCard: React.FC<{
  suggestion: OptimizationSuggestion;
  onApply: () => void;
  isApplying?: boolean;
}> = ({ suggestion, onApply, isApplying }) => {
  const [expanded, setExpanded] = useState(false);
  const config = optimizationConfig[suggestion.type];
  const Icon = config.icon;

  return (
    <Card className={cn(
      'transition-all',
      suggestion.applied && 'opacity-60 bg-muted/30'
    )}>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className={cn('p-2 rounded-lg', config.bgColor)}>
            <Icon className={cn('w-5 h-5', config.color)} />
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="font-medium text-sm">{suggestion.title}</h4>
              <ImpactBadge impact={suggestion.impact} />
              {suggestion.applied && (
                <Badge variant="outline" className="text-xs text-green-600">
                  <CheckCircle2 className="w-3 h-3 mr-1" />
                  Applied
                </Badge>
              )}
            </div>
            
            <p className="text-sm text-muted-foreground">{suggestion.description}</p>
            
            {/* Estimated savings */}
            {suggestion.estimatedSavings && (
              <div className="flex items-center gap-4 mt-2">
                {suggestion.estimatedSavings.time && (
                  <span className="text-xs flex items-center gap-1 text-green-600">
                    <Clock className="w-3 h-3" />
                    {suggestion.estimatedSavings.time} saved
                  </span>
                )}
                {suggestion.estimatedSavings.cost && (
                  <span className="text-xs flex items-center gap-1 text-green-600">
                    <DollarSign className="w-3 h-3" />
                    {suggestion.estimatedSavings.cost} saved
                  </span>
                )}
                {suggestion.estimatedSavings.percentage && (
                  <span className="text-xs flex items-center gap-1 text-green-600">
                    <TrendingDown className="w-3 h-3" />
                    {suggestion.estimatedSavings.percentage}% reduction
                  </span>
                )}
              </div>
            )}
            
            {/* Affected nodes */}
            {suggestion.affectedNodes.length > 0 && (
              <div className="mt-2">
                <button
                  className="text-xs text-muted-foreground flex items-center gap-1 hover:text-foreground"
                  onClick={() => setExpanded(!expanded)}
                >
                  {expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                  Affected nodes ({suggestion.affectedNodes.length})
                </button>
                {expanded && (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {suggestion.affectedNodes.map((node, i) => (
                      <Badge key={i} variant="outline" className="text-xs">
                        {node}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            )}
            
            {/* Details */}
            {expanded && suggestion.details && (
              <div className="mt-2 p-2 bg-muted/50 rounded text-xs">
                {suggestion.details}
              </div>
            )}
          </div>
          
          {/* Apply button */}
          {!suggestion.applied && (
            <Button
              size="sm"
              variant={suggestion.autoApplicable ? 'default' : 'outline'}
              onClick={onApply}
              disabled={isApplying}
            >
              {isApplying ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4 mr-1" />
                  Apply
                </>
              )}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// Main component
export function AIOptimizer({
  workflowId,
  suggestions,
  metrics,
  isAnalyzing = false,
  onApplySuggestion,
  onApplyAll,
  onRefresh,
  className,
}: AIOptimizerProps) {
  const [applyingId, setApplyingId] = useState<string | null>(null);
  const [isApplyingAll, setIsApplyingAll] = useState(false);
  const [autoOptimize, setAutoOptimize] = useState(false);

  const pendingSuggestions = suggestions.filter(s => !s.applied);
  const appliedSuggestions = suggestions.filter(s => s.applied);
  
  const totalSavings = {
    time: pendingSuggestions.reduce((acc, s) => {
      const match = s.estimatedSavings?.time?.match(/(\d+)/);
      return acc + (match ? parseInt(match[1]) : 0);
    }, 0),
    cost: pendingSuggestions.reduce((acc, s) => {
      const match = s.estimatedSavings?.cost?.match(/\$?([\d.]+)/);
      return acc + (match ? parseFloat(match[1]) : 0);
    }, 0),
  };

  const handleApply = async (suggestionId: string) => {
    setApplyingId(suggestionId);
    try {
      await onApplySuggestion(suggestionId);
    } finally {
      setApplyingId(null);
    }
  };

  const handleApplyAll = async () => {
    setIsApplyingAll(true);
    try {
      await onApplyAll();
    } finally {
      setIsApplyingAll(false);
    }
  };

  return (
    <div className={cn('flex flex-col h-full bg-background', className)}>
      {/* Header */}
      <div className="p-4 border-b bg-gradient-to-r from-purple-500/10 to-blue-500/10">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold">AI Optimization</h3>
              <p className="text-xs text-muted-foreground">
                {pendingSuggestions.length} optimization suggestions
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" onClick={onRefresh} disabled={isAnalyzing}>
              <RefreshCw className={cn('w-4 h-4', isAnalyzing && 'animate-spin')} />
            </Button>
          </div>
        </div>

        {/* Metrics summary */}
        <div className="grid grid-cols-4 gap-2">
          <div className="p-2 bg-background rounded-lg text-center">
            <div className="text-lg font-bold">{metrics.totalNodes}</div>
            <div className="text-xs text-muted-foreground">Nodes</div>
          </div>
          <div className="p-2 bg-background rounded-lg text-center">
            <div className="text-lg font-bold">{metrics.estimatedDuration}</div>
            <div className="text-xs text-muted-foreground">Est. Time</div>
          </div>
          <div className="p-2 bg-background rounded-lg text-center">
            <div className="text-lg font-bold">{metrics.estimatedCost}</div>
            <div className="text-xs text-muted-foreground">Est. Cost</div>
          </div>
          <div className="p-2 bg-background rounded-lg text-center">
            <div className="text-lg font-bold text-green-600">
              {pendingSuggestions.length}
            </div>
            <div className="text-xs text-muted-foreground">Optimizable</div>
          </div>
        </div>
      </div>

      {/* Potential savings */}
      {pendingSuggestions.length > 0 && (
        <div className="p-4 border-b bg-green-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-green-800">Estimated Savings</p>
              <div className="flex items-center gap-4 mt-1">
                {totalSavings.time > 0 && (
                  <span className="text-sm text-green-700 flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    ~{totalSavings.time}s
                  </span>
                )}
                {totalSavings.cost > 0 && (
                  <span className="text-sm text-green-700 flex items-center gap-1">
                    <DollarSign className="w-4 h-4" />
                    ~${totalSavings.cost.toFixed(2)}
                  </span>
                )}
              </div>
            </div>
            <Button
              size="sm"
              onClick={handleApplyAll}
              disabled={isApplyingAll || pendingSuggestions.length === 0}
            >
              {isApplyingAll ? (
                <Loader2 className="w-4 h-4 mr-1 animate-spin" />
              ) : (
                <Play className="w-4 h-4 mr-1" />
              )}
              Apply All
            </Button>
          </div>
        </div>
      )}

      {/* Suggestions list */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-3">
          {isAnalyzing ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary mb-3" />
              <p className="text-sm text-muted-foreground">Analyzing workflow...</p>
            </div>
          ) : pendingSuggestions.length === 0 && appliedSuggestions.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <CheckCircle2 className="w-12 h-12 text-green-500 mb-3" />
              <p className="font-medium">Workflow is optimized!</p>
              <p className="text-sm text-muted-foreground mt-1">
                No additional optimization suggestions.
              </p>
            </div>
          ) : (
            <>
              {/* Pending suggestions */}
              {pendingSuggestions.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-sm font-medium text-muted-foreground">
                    Optimization Suggestions ({pendingSuggestions.length})
                  </h4>
                  {pendingSuggestions.map(suggestion => (
                    <SuggestionCard
                      key={suggestion.id}
                      suggestion={suggestion}
                      onApply={() => handleApply(suggestion.id)}
                      isApplying={applyingId === suggestion.id}
                    />
                  ))}
                </div>
              )}

              {/* Applied suggestions */}
              {appliedSuggestions.length > 0 && (
                <div className="space-y-3 mt-6">
                  <h4 className="text-sm font-medium text-muted-foreground">
                    Applied Optimizations ({appliedSuggestions.length})
                  </h4>
                  {appliedSuggestions.map(suggestion => (
                    <SuggestionCard
                      key={suggestion.id}
                      suggestion={suggestion}
                      onApply={() => {}}
                    />
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </ScrollArea>

      {/* Auto-optimize toggle */}
      <div className="p-4 border-t bg-muted/30">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">Auto Optimization</p>
            <p className="text-xs text-muted-foreground">
              Automatically apply optimizations on save
            </p>
          </div>
          <Switch
            checked={autoOptimize}
            onCheckedChange={setAutoOptimize}
          />
        </div>
      </div>
    </div>
  );
}

export default AIOptimizer;
