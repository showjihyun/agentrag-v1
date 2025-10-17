'use client';

/**
 * Query Complexity Indicator Component
 * 
 * Shows real-time query complexity analysis with:
 * - Complexity level (simple, moderate, complex)
 * - Estimated processing time
 * - Recommended mode
 */

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

interface ComplexityAnalysis {
  complexity: 'simple' | 'moderate' | 'complex';
  reasoning: string;
  recommended_mode: 'fast' | 'balanced' | 'deep';
  estimated_time: number;
}

interface Props {
  query: string;
  onAnalysisComplete?: (analysis: ComplexityAnalysis) => void;
  className?: string;
}

export default function QueryComplexityIndicator({ 
  query, 
  onAnalysisComplete,
  className = ''
}: Props) {
  const [analysis, setAnalysis] = useState<ComplexityAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  useEffect(() => {
    // Only analyze queries longer than 10 characters
    if (query.length > 10) {
      // Debounce: wait 500ms after user stops typing
      const timer = setTimeout(() => {
        analyzeQuery();
      }, 500);

      return () => clearTimeout(timer);
    } else {
      setAnalysis(null);
    }
  }, [query]);

  const analyzeQuery = async () => {
    setIsAnalyzing(true);
    try {
      const result = await apiClient.analyzeQueryComplexity(query);
      setAnalysis(result);
      onAnalysisComplete?.(result);
    } catch (error) {
      console.error('Query complexity analysis failed:', error);
      // Fail silently - this is a nice-to-have feature
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (!analysis && !isAnalyzing) return null;

  if (isAnalyzing) {
    return (
      <div className={`flex items-center gap-2 text-sm text-gray-500 ${className}`}>
        <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-gray-400"></div>
        <span>Analyzing query...</span>
      </div>
    );
  }

  if (!analysis) return null;

  const complexityConfig = {
    simple: {
      color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
      icon: '⚡',
      label: 'Simple'
    },
    moderate: {
      color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
      icon: '💡',
      label: 'Moderate'
    },
    complex: {
      color: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
      icon: '🔬',
      label: 'Complex'
    }
  };

  const config = complexityConfig[analysis.complexity] || complexityConfig.moderate;

  return (
    <div className={`flex items-center gap-2 text-sm ${className}`}>
      {/* Complexity Badge */}
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full font-medium ${config.color}`}>
        <span>{config.icon}</span>
        <span>{config.label}</span>
      </span>

      {/* Estimated Time */}
      <span className="text-gray-600 dark:text-gray-400">
        ~{analysis.estimated_time}s
      </span>

      {/* Separator */}
      <span className="text-gray-300 dark:text-gray-600">•</span>

      {/* Recommended Mode */}
      <span className="text-gray-600 dark:text-gray-400 capitalize">
        {analysis.recommended_mode} mode
      </span>

      {/* Info Tooltip (optional) */}
      {analysis.reasoning && (
        <span 
          className="text-gray-400 hover:text-gray-600 cursor-help"
          title={analysis.reasoning}
        >
          ℹ️
        </span>
      )}
    </div>
  );
}
