/**
 * AI Insights Engine
 * Real-time data analysis and insight generation
 */

export type InsightType =
  | 'performance'
  | 'cost'
  | 'quality'
  | 'security'
  | 'optimization'
  | 'anomaly'
  | 'prediction'
  | 'recommendation'
  | 'alert'
  | 'trend';

export type InsightSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';

export type InsightCategory =
  | 'agent_performance'
  | 'workflow_efficiency'
  | 'cost_optimization'
  | 'quality_improvement'
  | 'security_risk'
  | 'user_experience'
  | 'system_health';

export interface InsightAction {
  id: string;
  label: string;
  type: 'primary' | 'secondary' | 'danger';
  handler: () => Promise<void>;
  requiresConfirmation: boolean;
  estimatedImpact?: {
    metric: string;
    value: number;
    unit: string;
  };
}

export interface Insight {
  id: string;
  type: InsightType;
  severity: InsightSeverity;
  category: InsightCategory;
  title: string;
  description: string;
  impact?: {
    metric: string;
    current: number;
    predicted: number;
    change: number;
    changePercent: number;
  };
  actions: InsightAction[];
  relatedData?: any;
  confidence: number; // 0-100
  timestamp: string;
  expiresAt?: string;
  tags: string[];
}

export interface ExecutionData {
  id: string;
  agent_id: string;
  status: string;
  duration: number;
  cost: number;
  tokens: number;
  timestamp: string;
  error?: string;
}

export interface MetricsData {
  response_times: number[];
  error_rates: number[];
  costs: number[];
  success_rates: number[];
  timestamps: string[];
}

export class InsightEngine {
  private insights: Insight[] = [];
  private historicalData: Map<string, any[]> = new Map();

  /**
   * Real-time data analysis
   */
  analyzeRealtime(executions: ExecutionData[]): Insight[] {
    const insights: Insight[] = [];

    // Performance analysis
    insights.push(...this.analyzePerformance(executions));

    // Cost analysis
    insights.push(...this.analyzeCost(executions));

    // Error analysis
    insights.push(...this.analyzeErrors(executions));

    // Anomaly detection
    insights.push(...this.detectAnomalies(executions));

    return insights.sort((a, b) => {
      const severityOrder = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
      return severityOrder[a.severity] - severityOrder[b.severity];
    });
  }

  /**
   * Performance analysis
   */
  private analyzePerformance(executions: ExecutionData[]): Insight[] {
    const insights: Insight[] = [];

    if (executions.length < 10) return insights;

    const recentExecutions = executions.slice(-20);
    const avgDuration = recentExecutions.reduce((sum, e) => sum + e.duration, 0) / recentExecutions.length;

    // Detect slow executions
    const slowExecutions = recentExecutions.filter(e => e.duration > avgDuration * 2);
    if (slowExecutions.length > 5) {
      insights.push({
        id: `perf-slow-${Date.now()}`,
        type: 'performance',
        severity: 'high',
        category: 'agent_performance',
        title: 'Response Time Degradation Detected',
        description: `${slowExecutions.length} recent executions are 2x slower than average. Average: ${avgDuration.toFixed(2)}s`,
        impact: {
          metric: 'response_time',
          current: avgDuration,
          predicted: avgDuration * 1.5,
          change: avgDuration * 0.5,
          changePercent: 50,
        },
        actions: [
          {
            id: 'optimize-prompt',
            label: 'Optimize Prompt',
            type: 'primary',
            handler: async () => {
              // Prompt optimization logic
            },
            requiresConfirmation: false,
            estimatedImpact: {
              metric: 'response_time',
              value: -30,
              unit: '%',
            },
          },
          {
            id: 'view-details',
            label: 'View Details',
            type: 'secondary',
            handler: async () => {
              // Open detailed analysis modal
            },
            requiresConfirmation: false,
          },
        ],
        confidence: 92,
        timestamp: new Date().toISOString(),
        tags: ['performance', 'response-time', 'degradation'],
      });
    }

    // P95 analysis
    const sortedDurations = [...recentExecutions.map(e => e.duration)].sort((a, b) => a - b);
    const p95Index = Math.floor(sortedDurations.length * 0.95);
    const p95 = sortedDurations[p95Index];

    if (p95 !== undefined && p95 > avgDuration * 3) {
      insights.push({
        id: `perf-p95-${Date.now()}`,
        type: 'performance',
        severity: 'medium',
        category: 'agent_performance',
        title: 'High P95 Response Time',
        description: `Top 5% of executions are 3x slower than average. P95: ${p95.toFixed(2)}s`,
        confidence: 88,
        timestamp: new Date().toISOString(),
        actions: [
          {
            id: 'investigate',
            label: 'Investigate Cause',
            type: 'primary',
            handler: async () => {},
            requiresConfirmation: false,
          },
        ],
        tags: ['performance', 'p95', 'outliers'],
      });
    }

    return insights;
  }

  /**
   * Cost analysis
   */
  private analyzeCost(executions: ExecutionData[]): Insight[] {
    const insights: Insight[] = [];

    if (executions.length < 10) return insights;

    const recentExecutions = executions.slice(-50);
    const totalCost = recentExecutions.reduce((sum, e) => sum + e.cost, 0);
    const avgCost = totalCost / recentExecutions.length;

    // Detect cost spikes
    const last10 = recentExecutions.slice(-10);
    const prev10 = recentExecutions.slice(-20, -10);
    const recentAvg = last10.reduce((sum, e) => sum + e.cost, 0) / 10;
    const prevAvg = prev10.reduce((sum, e) => sum + e.cost, 0) / 10;

    if (recentAvg > prevAvg * 1.5) {
      const increase = ((recentAvg - prevAvg) / prevAvg) * 100;
      insights.push({
        id: `cost-spike-${Date.now()}`,
        type: 'cost',
        severity: 'high',
        category: 'cost_optimization',
        title: 'Cost Spike Detected',
        description: `Recent execution costs increased by ${increase.toFixed(1)}%. Current average: $${recentAvg.toFixed(4)}`,
        impact: {
          metric: 'cost',
          current: recentAvg,
          predicted: recentAvg * 1.3,
          change: recentAvg * 0.3,
          changePercent: 30,
        },
        actions: [
          {
            id: 'optimize-model',
            label: 'Optimize Model',
            type: 'primary',
            handler: async () => {},
            requiresConfirmation: true,
            estimatedImpact: {
              metric: 'cost',
              value: -40,
              unit: '%',
            },
          },
          {
            id: 'enable-caching',
            label: 'Enable Caching',
            type: 'secondary',
            handler: async () => {},
            requiresConfirmation: false,
            estimatedImpact: {
              metric: 'cost',
              value: -25,
              unit: '%',
            },
          },
        ],
        confidence: 95,
        timestamp: new Date().toISOString(),
        tags: ['cost', 'spike', 'optimization'],
      });
    }

    return insights;
  }

  /**
   * Error analysis
   */
  private analyzeErrors(executions: ExecutionData[]): Insight[] {
    const insights: Insight[] = [];

    const recentExecutions = executions.slice(-50);
    const errors = recentExecutions.filter(e => e.status === 'failed');
    const errorRate = (errors.length / recentExecutions.length) * 100;

    if (errorRate > 10) {
      // Error pattern analysis
      const errorTypes = new Map<string, number>();
      errors.forEach(e => {
        if (e.error) {
          const errorType = e.error.split(':')[0];
          if (errorType) {
            errorTypes.set(errorType, (errorTypes.get(errorType) || 0) + 1);
          }
        }
      });

      const mostCommonError = Array.from(errorTypes.entries())
        .sort((a, b) => b[1] - a[1])[0];

      insights.push({
        id: `error-rate-${Date.now()}`,
        type: 'alert',
        severity: errorRate > 20 ? 'critical' : 'high',
        category: 'system_health',
        title: 'High Error Rate Detected',
        description: `Error rate is ${errorRate.toFixed(1)}%. Most common error: ${mostCommonError?.[0] || 'Unknown'}`,
        impact: {
          metric: 'error_rate',
          current: errorRate,
          predicted: errorRate * 1.2,
          change: errorRate * 0.2,
          changePercent: 20,
        },
        actions: [
          {
            id: 'auto-fix',
            label: 'Attempt Auto-Fix',
            type: 'primary',
            handler: async () => {},
            requiresConfirmation: true,
          },
          {
            id: 'view-logs',
            label: 'View Logs',
            type: 'secondary',
            handler: async () => {},
            requiresConfirmation: false,
          },
        ],
        confidence: 98,
        timestamp: new Date().toISOString(),
        tags: ['error', 'reliability', 'critical'],
      });
    }

    return insights;
  }

  /**
   * Anomaly detection (Statistical Anomaly Detection)
   */
  private detectAnomalies(executions: ExecutionData[]): Insight[] {
    const insights: Insight[] = [];

    if (executions.length < 30) return insights;

    const durations = executions.map(e => e.duration);
    const mean = durations.reduce((a, b) => a + b, 0) / durations.length;
    const variance = durations.reduce((sum, d) => sum + Math.pow(d - mean, 2), 0) / durations.length;
    const stdDev = Math.sqrt(variance);

    // 3-sigma rule
    const anomalies = executions.filter(e => Math.abs(e.duration - mean) > 3 * stdDev);

    if (anomalies.length > 0) {
      insights.push({
        id: `anomaly-${Date.now()}`,
        type: 'anomaly',
        severity: 'medium',
        category: 'system_health',
        title: 'Anomalous Execution Pattern Detected',
        description: `${anomalies.length} executions are outside normal range (3σ threshold)`,
        actions: [
          {
            id: 'investigate-anomalies',
            label: 'Investigate Anomalies',
            type: 'primary',
            handler: async () => {},
            requiresConfirmation: false,
          },
        ],
        confidence: 85,
        timestamp: new Date().toISOString(),
        tags: ['anomaly', 'outlier', 'investigation'],
      });
    }

    return insights;
  }

  /**
   * Trend prediction
   */
  predictTrends(historicalData: MetricsData): Insight[] {
    const insights: Insight[] = [];

    // Simple trend prediction using linear regression
    const costs = historicalData.costs;
    if (costs.length < 7) return insights;

    const n = costs.length;
    const sumX = costs.reduce((sum, _, i) => sum + i, 0);
    const sumY = costs.reduce((sum, y) => sum + y, 0);
    const sumXY = costs.reduce((sum, y, i) => sum + i * y, 0);
    const sumX2 = costs.reduce((sum, _, i) => sum + i * i, 0);

    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);

    if (slope > 0 && costs.length > 0) {
      const lastCost = costs[costs.length - 1];
      if (lastCost !== undefined) {
        const predicted7Days = lastCost + slope * 7;
        const increase = ((predicted7Days - lastCost) / lastCost) * 100;

        if (increase > 20) {
          insights.push({
            id: `trend-cost-${Date.now()}`,
            type: 'prediction',
            severity: 'medium',
            category: 'cost_optimization',
            title: 'Cost Increase Trend Predicted',
            description: `Current trend suggests ${increase.toFixed(1)}% cost increase in 7 days`,
            impact: {
              metric: 'cost',
              current: lastCost,
              predicted: predicted7Days,
              change: predicted7Days - lastCost,
              changePercent: increase,
            },
            actions: [
              {
                id: 'set-budget-alert',
                label: 'Set Budget Alert',
                type: 'primary',
                handler: async () => {},
                requiresConfirmation: false,
              },
            ],
            confidence: 78,
            timestamp: new Date().toISOString(),
            expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
            tags: ['prediction', 'cost', 'trend'],
          });
        }
      }
    }

    return insights;
  }

  /**
   * Find optimization opportunities
   */
  findOptimizations(agentData: any): Insight[] {
    const insights: Insight[] = [];

    // Model change suggestion
    if (agentData.model === 'gpt-4' && agentData.success_rate > 95) {
      insights.push({
        id: `opt-model-${Date.now()}`,
        type: 'optimization',
        severity: 'low',
        category: 'cost_optimization',
        title: 'Model Downgrade Opportunity',
        description: 'GPT-4 can be changed to GPT-3.5 while maintaining quality (95%+ success rate)',
        impact: {
          metric: 'cost',
          current: agentData.monthly_cost,
          predicted: agentData.monthly_cost * 0.1,
          change: -agentData.monthly_cost * 0.9,
          changePercent: -90,
        },
        actions: [
          {
            id: 'simulate-change',
            label: 'Run A/B Test',
            type: 'primary',
            handler: async () => {},
            requiresConfirmation: false,
            estimatedImpact: {
              metric: 'cost',
              value: -90,
              unit: '%',
            },
          },
        ],
        confidence: 82,
        timestamp: new Date().toISOString(),
        tags: ['optimization', 'cost', 'model'],
      });
    }

    return insights;
  }
}

export const insightEngine = new InsightEngine();