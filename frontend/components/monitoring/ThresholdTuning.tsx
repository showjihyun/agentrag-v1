'use client';

/**
 * Threshold Tuning Component
 * Interface for viewing and adjusting complexity thresholds
 */

import React, { useState, useEffect } from 'react';

interface ThresholdTuningProps {
  isAdmin: boolean;
  autoRefresh: boolean;
  refreshInterval: number;
}

interface ConfigData {
  adaptive_routing: {
    enabled: boolean;
    complexity_threshold_simple: number;
    complexity_threshold_complex: number;
  };
}

interface DashboardData {
  mode_distribution: {
    percentages: Record<string, number>;
  };
  thresholds: {
    current: {
      simple_threshold: number;
      complex_threshold: number;
      timestamp: string;
      reason: string;
    } | null;
    history: Array<{
      simple_threshold: number;
      complex_threshold: number;
      timestamp: string;
      reason: string;
    }>;
  };
}

export default function ThresholdTuning({ isAdmin, autoRefresh, refreshInterval }: ThresholdTuningProps) {
  const [config, setConfig] = useState<ConfigData | null>(null);
  const [metrics, setMetrics] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [simulating, setSimulating] = useState(false);
  
  // Simulation state
  const [simpleThreshold, setSimpleThreshold] = useState(0.35);
  const [complexThreshold, setComplexThreshold] = useState(0.70);
  const [simulationResult, setSimulationResult] = useState<any>(null);

  const fetchData = async () => {
    try {
      setError(null);
      
      // Fetch current configuration
      const configResponse = await fetch('http://localhost:8000/api/config/adaptive');
      if (!configResponse.ok) throw new Error('Failed to fetch configuration');
      const configData = await configResponse.json();
      setConfig(configData);
      
      // Fetch metrics
      const metricsResponse = await fetch('http://localhost:8000/api/metrics/adaptive');
      if (!metricsResponse.ok) throw new Error('Failed to fetch metrics');
      const metricsData = await metricsResponse.json();
      setMetrics(metricsData);
      
      // Set initial threshold values
      if (configData.adaptive_routing) {
        setSimpleThreshold(configData.adaptive_routing.complexity_threshold_simple);
        setComplexThreshold(configData.adaptive_routing.complexity_threshold_complex);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchData, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const simulateThresholds = () => {
    setSimulating(true);
    
    // Simple simulation logic
    // In a real implementation, this would call a backend endpoint
    setTimeout(() => {
      const currentDist = metrics?.mode_distribution.percentages || {};
      
      // Estimate impact based on threshold changes
      const currentSimple = config?.adaptive_routing.complexity_threshold_simple || 0.35;
      const currentComplex = config?.adaptive_routing.complexity_threshold_complex || 0.70;
      
      const simpleDelta = simpleThreshold - currentSimple;
      const complexDelta = complexThreshold - currentComplex;
      
      // Rough estimation: increasing simple threshold reduces fast mode
      const fastChange = -simpleDelta * 20;
      const deepChange = complexDelta * 20;
      const balancedChange = -(fastChange + deepChange);
      
      setSimulationResult({
        estimated_distribution: {
          fast: Math.max(0, Math.min(100, (currentDist.fast || 0) + fastChange)),
          balanced: Math.max(0, Math.min(100, (currentDist.balanced || 0) + balancedChange)),
          deep: Math.max(0, Math.min(100, (currentDist.deep || 0) + deepChange)),
        },
        impact: {
          fast: fastChange,
          balanced: balancedChange,
          deep: deepChange,
        },
      });
      
      setSimulating(false);
    }, 1000);
  };

  const resetThresholds = () => {
    if (config?.adaptive_routing) {
      setSimpleThreshold(config.adaptive_routing.complexity_threshold_simple);
      setComplexThreshold(config.adaptive_routing.complexity_threshold_complex);
      setSimulationResult(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading threshold configuration...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center gap-3">
          <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <h3 className="text-red-800 font-medium">Error loading configuration</h3>
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        </div>
        <button
          onClick={fetchData}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!config || !metrics) return null;

  const targetDistribution = {
    fast: { min: 40, max: 50 },
    balanced: { min: 30, max: 40 },
    deep: { min: 20, max: 30 },
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-900">Threshold Tuning</h2>
        {!isAdmin && (
          <span className="text-sm text-yellow-600 bg-yellow-50 px-3 py-1 rounded">
            View Only (Admin access required to modify)
          </span>
        )}
      </div>

      {/* Current Configuration */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Thresholds</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Simple/Medium Threshold
            </label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="0.1"
                max="0.6"
                step="0.05"
                value={simpleThreshold}
                onChange={(e) => setSimpleThreshold(parseFloat(e.target.value))}
                disabled={!isAdmin}
                className="flex-1"
              />
              <span className="text-lg font-semibold text-gray-900 w-16">
                {simpleThreshold.toFixed(2)}
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Queries with complexity &lt; {simpleThreshold.toFixed(2)} use Fast mode
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Medium/Complex Threshold
            </label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="0.5"
                max="0.9"
                step="0.05"
                value={complexThreshold}
                onChange={(e) => setComplexThreshold(parseFloat(e.target.value))}
                disabled={!isAdmin}
                className="flex-1"
              />
              <span className="text-lg font-semibold text-gray-900 w-16">
                {complexThreshold.toFixed(2)}
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Queries with complexity &gt; {complexThreshold.toFixed(2)} use Deep mode
            </p>
          </div>
        </div>

        {isAdmin && (
          <div className="flex gap-3 mt-6">
            <button
              onClick={simulateThresholds}
              disabled={simulating}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {simulating ? 'Simulating...' : 'Simulate Impact'}
            </button>
            <button
              onClick={resetThresholds}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            >
              Reset
            </button>
          </div>
        )}
      </div>

      {/* Simulation Results */}
      {simulationResult && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-4">Simulation Results</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {['fast', 'balanced', 'deep'].map(mode => {
              const current = metrics.mode_distribution.percentages[mode] || 0;
              const estimated = simulationResult.estimated_distribution[mode];
              const impact = simulationResult.impact[mode];
              const target = targetDistribution[mode as keyof typeof targetDistribution];
              const inTarget = estimated >= target.min && estimated <= target.max;
              
              return (
                <div key={mode} className="bg-white rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-700 capitalize mb-2">{mode} Mode</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Current:</span>
                      <span className="font-medium">{current.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Estimated:</span>
                      <span className={`font-medium ${inTarget ? 'text-green-600' : 'text-yellow-600'}`}>
                        {estimated.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Change:</span>
                      <span className={`font-medium ${impact > 0 ? 'text-green-600' : impact < 0 ? 'text-red-600' : 'text-gray-600'}`}>
                        {impact > 0 ? '+' : ''}{impact.toFixed(1)}%
                      </span>
                    </div>
                    <div className="pt-2 border-t border-gray-200">
                      <span className="text-xs text-gray-500">
                        Target: {target.min}-{target.max}%
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          
          {isAdmin && (
            <div className="mt-6">
              <button
                className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                onClick={() => alert('Apply thresholds functionality would be implemented here')}
              >
                Apply Thresholds
              </button>
              <p className="text-xs text-gray-600 mt-2">
                Note: Applying thresholds will update the system configuration
              </p>
            </div>
          )}
        </div>
      )}

      {/* Current Distribution vs Target */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Current vs Target Distribution</h3>
        <div className="space-y-4">
          {['fast', 'balanced', 'deep'].map(mode => {
            const current = metrics.mode_distribution.percentages[mode] || 0;
            const target = targetDistribution[mode as keyof typeof targetDistribution];
            const inTarget = current >= target.min && current <= target.max;
            
            return (
              <div key={mode}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium text-gray-700 capitalize">{mode} Mode</span>
                  <span className={inTarget ? 'text-green-600' : 'text-yellow-600'}>
                    {current.toFixed(1)}% (Target: {target.min}-{target.max}%)
                  </span>
                </div>
                <div className="relative w-full bg-gray-200 rounded-full h-3">
                  {/* Target range indicator */}
                  <div
                    className="absolute h-3 bg-green-200 rounded-full"
                    style={{
                      left: `${target.min}%`,
                      width: `${target.max - target.min}%`,
                    }}
                  />
                  {/* Current value */}
                  <div
                    className={`absolute h-3 rounded-full ${
                      inTarget ? 'bg-green-500' : 'bg-yellow-500'
                    }`}
                    style={{ width: `${current}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Threshold History */}
      {metrics.thresholds.history.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Threshold Change History</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Timestamp
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Simple Threshold
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Complex Threshold
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Reason
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {metrics.thresholds.history.slice(-10).reverse().map((entry, index) => (
                  <tr key={index}>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {new Date(entry.timestamp).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {entry.simple_threshold.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {entry.complex_threshold.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {entry.reason}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
