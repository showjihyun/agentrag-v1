'use client';

import React, { useState, useEffect } from 'react';
import { Sparkles, Zap, Scale, Search } from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface ModeRecommendationProps {
  query: string;
  onModeSelect: (mode: 'fast' | 'balanced' | 'deep') => void;
  currentMode: 'fast' | 'balanced' | 'deep';
  autoMode: boolean;
  onAutoModeChange: (enabled: boolean) => void;
}

interface ComplexityAnalysis {
  recommended_mode: 'fast' | 'balanced' | 'deep';
  complexity_level: 'simple' | 'moderate' | 'complex';
  confidence: number;
  reasoning: {
    complexity_score: number;
    factors: string[];
  };
  explanation: string;
}

export default function ModeRecommendation({
  query,
  onModeSelect,
  currentMode,
  autoMode,
  onAutoModeChange
}: ModeRecommendationProps) {
  const [analysis, setAnalysis] = useState<ComplexityAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  // Analyze query complexity when it changes
  useEffect(() => {
    if (!query || query.length < 3 || !autoMode) {
      setAnalysis(null);
      return;
    }

    const timeoutId = setTimeout(async () => {
      setIsAnalyzing(true);
      try {
        const data = await apiClient.analyzeQueryComplexity(query);
        setAnalysis(data);
        
        // Auto-select recommended mode if auto mode is enabled
        if (autoMode && data.recommended_mode !== currentMode) {
          onModeSelect(data.recommended_mode);
        }
      } catch (error) {
        console.error('Failed to analyze query complexity:', error);
      } finally {
        setIsAnalyzing(false);
      }
    }, 500); // Debounce 500ms

    return () => clearTimeout(timeoutId);
  }, [query, autoMode]);

  const getModeIcon = (mode: string) => {
    switch (mode) {
      case 'fast':
        return <Zap className="w-4 h-4" />;
      case 'balanced':
        return <Scale className="w-4 h-4" />;
      case 'deep':
        return <Search className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const getModeColor = (mode: string) => {
    switch (mode) {
      case 'fast':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'balanced':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'deep':
        return 'text-purple-600 bg-purple-50 border-purple-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-orange-600';
  };

  if (!autoMode) {
    return null;
  }

  return (
    <div className="mb-4 space-y-2">
      {/* Auto Mode Toggle */}
      <div className="flex items-center justify-between">
        <label className="flex items-center space-x-2 text-sm text-gray-700 cursor-pointer">
          <input
            type="checkbox"
            checked={autoMode}
            onChange={(e) => onAutoModeChange(e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <Sparkles className="w-4 h-4 text-blue-500" />
          <span>Auto-select mode based on query</span>
        </label>
      </div>

      {/* Recommendation Display */}
      {isAnalyzing && (
        <div className="flex items-center space-x-2 text-sm text-gray-500 animate-pulse">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span>Analyzing query complexity...</span>
        </div>
      )}

      {analysis && !isAnalyzing && (
        <div className={`p-3 rounded-lg border ${getModeColor(analysis.recommended_mode)}`}>
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-2 flex-1">
              {getModeIcon(analysis.recommended_mode)}
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <span className="font-medium text-sm">
                    Recommended: {analysis.recommended_mode.toUpperCase()} mode
                  </span>
                  <span className={`text-xs ${getConfidenceColor(analysis.confidence)}`}>
                    ({Math.round(analysis.confidence * 100)}% confident)
                  </span>
                </div>
                
                <p className="text-xs mt-1 opacity-90">
                  {analysis.explanation.split('.')[0]}.
                </p>

                {/* Complexity Factors */}
                {showDetails && (
                  <div className="mt-2 pt-2 border-t border-current border-opacity-20">
                    <div className="text-xs space-y-1">
                      <div className="font-medium">Analysis:</div>
                      <div className="opacity-80">
                        Complexity: {analysis.complexity_level} 
                        ({Math.round(analysis.reasoning.complexity_score * 100)}%)
                      </div>
                      <ul className="list-disc list-inside opacity-80 space-y-0.5">
                        {analysis.reasoning.factors.map((factor, idx) => (
                          <li key={idx}>{factor}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Toggle Details Button */}
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="text-xs opacity-70 hover:opacity-100 transition-opacity ml-2"
            >
              {showDetails ? 'Less' : 'More'}
            </button>
          </div>

          {/* Override Option */}
          {analysis.recommended_mode !== currentMode && (
            <div className="mt-2 pt-2 border-t border-current border-opacity-20">
              <button
                onClick={() => onModeSelect(analysis.recommended_mode)}
                className="text-xs font-medium hover:underline"
              >
                Use recommended mode →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
