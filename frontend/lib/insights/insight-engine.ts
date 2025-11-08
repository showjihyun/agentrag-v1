/**
 * AI Insights Engine
 * 실시간 데이터 분석 및 인사이트 생성
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
   * 실시간 데이터 분석
   */
  analyzeRealtime(executions: ExecutionData[]): Insight[] {
    const insights: Insight[] = [];

    // 성능 분석
    insights.push(...this.analyzePerformance(executions));

    // 비용 분석
    insights.push(...this.analyzeCost(executions));

    // 에러 분석
    insights.push(...this.analyzeErrors(executions));

    // 이상 탐지
    insights.push(...this.detectAnomalies(executions));

    return insights.sort((a, b) => {
      const severityOrder = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
      return severityOrder[a.severity] - severityOrder[b.severity];
    });
  }

  /**
   * 성능 분석
   */
  private analyzePerformance(executions: ExecutionData[]): Insight[] {
    const insights: Insight[] = [];

    if (executions.length < 10) return insights;

    const recentExecutions = executions.slice(-20);
    const avgDuration = recentExecutions.reduce((sum, e) => sum + e.duration, 0) / recentExecutions.length;

    // 느린 실행 감지
    const slowExecutions = recentExecutions.filter(e => e.duration > avgDuration * 2);
    if (slowExecutions.length > 5) {
      insights.push({
        id: `perf-slow-${Date.now()}`,
        type: 'performance',
        severity: 'high',
        category: 'agent_performance',
        title: '응답 시간 저하 감지',
        description: `최근 ${slowExecutions.length}개의 실행이 평균보다 2배 이상 느립니다. 평균: ${avgDuration.toFixed(2)}s`,
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
            label: '프롬프트 최적화',
            type: 'primary',
            handler: async () => {
              // 프롬프트 최적화 로직
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
            label: '상세 분석',
            type: 'secondary',
            handler: async () => {
              // 상세 분석 모달 열기
            },
            requiresConfirmation: false,
          },
        ],
        confidence: 92,
        timestamp: new Date().toISOString(),
        tags: ['performance', 'response-time', 'degradation'],
      });
    }

    // P95 분석
    const sortedDurations = [...recentExecutions.map(e => e.duration)].sort((a, b) => a - b);
    const p95Index = Math.floor(sortedDurations.length * 0.95);
    const p95 = sortedDurations[p95Index];

    if (p95 > avgDuration * 3) {
      insights.push({
        id: `perf-p95-${Date.now()}`,
        type: 'performance',
        severity: 'medium',
        category: 'agent_performance',
        title: 'P95 응답 시간 높음',
        description: `상위 5%의 실행이 평균보다 3배 이상 느립니다. P95: ${p95.toFixed(2)}s`,
        confidence: 88,
        timestamp: new Date().toISOString(),
        actions: [
          {
            id: 'investigate',
            label: '원인 조사',
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
   * 비용 분석
   */
  private analyzeCost(executions: ExecutionData[]): Insight[] {
    const insights: Insight[] = [];

    if (executions.length < 10) return insights;

    const recentExecutions = executions.slice(-50);
    const totalCost = recentExecutions.reduce((sum, e) => sum + e.cost, 0);
    const avgCost = totalCost / recentExecutions.length;

    // 비용 급증 감지
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
        title: '비용 급증 감지',
        description: `최근 실행 비용이 ${increase.toFixed(1)}% 증가했습니다. 현재 평균: $${recentAvg.toFixed(4)}`,
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
            label: '모델 최적화',
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
            label: '캐싱 활성화',
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
   * 에러 분석
   */
  private analyzeErrors(executions: ExecutionData[]): Insight[] {
    const insights: Insight[] = [];

    const recentExecutions = executions.slice(-50);
    const errors = recentExecutions.filter(e => e.status === 'failed');
    const errorRate = (errors.length / recentExecutions.length) * 100;

    if (errorRate > 10) {
      // 에러 패턴 분석
      const errorTypes = new Map<string, number>();
      errors.forEach(e => {
        if (e.error) {
          const errorType = e.error.split(':')[0];
          errorTypes.set(errorType, (errorTypes.get(errorType) || 0) + 1);
        }
      });

      const mostCommonError = Array.from(errorTypes.entries())
        .sort((a, b) => b[1] - a[1])[0];

      insights.push({
        id: `error-rate-${Date.now()}`,
        type: 'alert',
        severity: errorRate > 20 ? 'critical' : 'high',
        category: 'system_health',
        title: '높은 에러율 감지',
        description: `에러율이 ${errorRate.toFixed(1)}%입니다. 가장 흔한 에러: ${mostCommonError?.[0] || 'Unknown'}`,
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
            label: '자동 수정 시도',
            type: 'primary',
            handler: async () => {},
            requiresConfirmation: true,
          },
          {
            id: 'view-logs',
            label: '로그 확인',
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
   * 이상 탐지 (Statistical Anomaly Detection)
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
        title: '이상 실행 패턴 감지',
        description: `${anomalies.length}개의 실행이 정상 범위를 벗어났습니다 (3σ 기준)`,
        actions: [
          {
            id: 'investigate-anomalies',
            label: '이상 실행 조사',
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
   * 트렌드 예측
   */
  predictTrends(historicalData: MetricsData): Insight[] {
    const insights: Insight[] = [];

    // 선형 회귀로 간단한 트렌드 예측
    const costs = historicalData.costs;
    if (costs.length < 7) return insights;

    const n = costs.length;
    const sumX = costs.reduce((sum, _, i) => sum + i, 0);
    const sumY = costs.reduce((sum, y) => sum + y, 0);
    const sumXY = costs.reduce((sum, y, i) => sum + i * y, 0);
    const sumX2 = costs.reduce((sum, _, i) => sum + i * i, 0);

    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);

    if (slope > 0) {
      const predicted7Days = costs[costs.length - 1] + slope * 7;
      const increase = ((predicted7Days - costs[costs.length - 1]) / costs[costs.length - 1]) * 100;

      if (increase > 20) {
        insights.push({
          id: `trend-cost-${Date.now()}`,
          type: 'prediction',
          severity: 'medium',
          category: 'cost_optimization',
          title: '비용 증가 추세 예측',
          description: `현재 추세로 7일 후 비용이 ${increase.toFixed(1)}% 증가할 것으로 예상됩니다`,
          impact: {
            metric: 'cost',
            current: costs[costs.length - 1],
            predicted: predicted7Days,
            change: predicted7Days - costs[costs.length - 1],
            changePercent: increase,
          },
          actions: [
            {
              id: 'set-budget-alert',
              label: '예산 알림 설정',
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

    return insights;
  }

  /**
   * 최적화 기회 발견
   */
  findOptimizations(agentData: any): Insight[] {
    const insights: Insight[] = [];

    // 모델 변경 제안
    if (agentData.model === 'gpt-4' && agentData.success_rate > 95) {
      insights.push({
        id: `opt-model-${Date.now()}`,
        type: 'optimization',
        severity: 'low',
        category: 'cost_optimization',
        title: '모델 다운그레이드 기회',
        description: 'GPT-4를 GPT-3.5로 변경해도 품질 유지 가능 (95% 이상 성공률)',
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
            label: 'A/B 테스트 실행',
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
