'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { insightEngine, Insight, InsightSeverity } from '@/lib/insights/insight-engine';
import { InsightCard } from './InsightCard';
import { InsightDetailModal } from './InsightDetailModal';
import {
  Brain,
  TrendingUp,
  AlertTriangle,
  Sparkles,
  Filter,
  RefreshCw,
} from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface EnhancedInsightsPanelProps {
  agentId?: string;
  executionData?: any[];
  metricsData?: any;
  autoRefresh?: boolean;
  refreshInterval?: number; // seconds
}

export function EnhancedInsightsPanel({
  agentId,
  executionData = [],
  metricsData,
  autoRefresh = true,
  refreshInterval = 30,
}: EnhancedInsightsPanelProps) {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedInsight, setSelectedInsight] = useState<Insight | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<InsightSeverity | 'all'>('all');
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    analyzeData();

    if (autoRefresh) {
      const interval = setInterval(analyzeData, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [executionData, metricsData, autoRefresh, refreshInterval]);

  const analyzeData = () => {
    setLoading(true);
    try {
      const newInsights: Insight[] = [];

      // 실시간 분석
      if (executionData.length > 0) {
        newInsights.push(...insightEngine.analyzeRealtime(executionData));
      }

      // 트렌드 예측
      if (metricsData) {
        newInsights.push(...insightEngine.predictTrends(metricsData));
      }

      // 최적화 기회
      if (agentId) {
        // agentData를 가져와서 분석
        // newInsights.push(...insightEngine.findOptimizations(agentData));
      }

      setInsights(newInsights);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to analyze data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityCount = (severity: InsightSeverity) => {
    return insights.filter((i) => i.severity === severity).length;
  };

  const filteredInsights = insights.filter((insight) => {
    if (filterSeverity !== 'all' && insight.severity !== filterSeverity) {
      return false;
    }
    if (filterCategory !== 'all' && insight.category !== filterCategory) {
      return false;
    }
    return true;
  });

  const criticalCount = getSeverityCount('critical');
  const highCount = getSeverityCount('high');
  const mediumCount = getSeverityCount('medium');

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Brain className="h-6 w-6 text-primary" />
              <div>
                <CardTitle className="flex items-center gap-2">
                  AI Insights
                  <Badge variant="secondary" className="text-xs">
                    실시간
                  </Badge>
                </CardTitle>
                <p className="text-xs text-muted-foreground mt-1">
                  마지막 업데이트: {lastUpdate.toLocaleTimeString()}
                </p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={analyzeData}
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              새로고침
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            {criticalCount > 0 && (
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500 animate-pulse" />
                <span className="text-sm font-medium">
                  Critical ({criticalCount})
                </span>
              </div>
            )}
            {highCount > 0 && (
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <span className="text-sm font-medium">High ({highCount})</span>
              </div>
            )}
            {mediumCount > 0 && (
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-blue-500" />
                <span className="text-sm font-medium">Medium ({mediumCount})</span>
              </div>
            )}
            <div className="flex items-center gap-2 ml-auto">
              <Sparkles className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                {insights.length} insights
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">필터:</span>
        </div>
        <Select value={filterSeverity} onValueChange={(v: any) => setFilterSeverity(v)}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="심각도" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">모든 심각도</SelectItem>
            <SelectItem value="critical">Critical</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="low">Low</SelectItem>
            <SelectItem value="info">Info</SelectItem>
          </SelectContent>
        </Select>

        <Select value={filterCategory} onValueChange={setFilterCategory}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="카테고리" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">모든 카테고리</SelectItem>
            <SelectItem value="agent_performance">Agent 성능</SelectItem>
            <SelectItem value="workflow_efficiency">Workflow 효율성</SelectItem>
            <SelectItem value="cost_optimization">비용 최적화</SelectItem>
            <SelectItem value="quality_improvement">품질 개선</SelectItem>
            <SelectItem value="security_risk">보안 위험</SelectItem>
            <SelectItem value="system_health">시스템 상태</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Insights Tabs */}
      <Tabs defaultValue="all" className="w-full">
        <TabsList>
          <TabsTrigger value="all">
            전체 ({filteredInsights.length})
          </TabsTrigger>
          <TabsTrigger value="critical">
            Critical ({getSeverityCount('critical')})
          </TabsTrigger>
          <TabsTrigger value="actionable">
            실행 가능 ({filteredInsights.filter(i => i.actions.length > 0).length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="mt-4">
          <ScrollArea className="h-[600px]">
            <div className="space-y-3">
              {filteredInsights.length === 0 ? (
                <Card>
                  <CardContent className="p-12 text-center text-muted-foreground">
                    <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>현재 인사이트가 없습니다</p>
                    <p className="text-sm mt-2">
                      데이터가 수집되면 AI가 자동으로 분석합니다
                    </p>
                  </CardContent>
                </Card>
              ) : (
                filteredInsights.map((insight) => (
                  <InsightCard
                    key={insight.id}
                    insight={insight}
                    onViewDetails={() => setSelectedInsight(insight)}
                  />
                ))
              )}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="critical" className="mt-4">
          <ScrollArea className="h-[600px]">
            <div className="space-y-3">
              {filteredInsights
                .filter((i) => i.severity === 'critical')
                .map((insight) => (
                  <InsightCard
                    key={insight.id}
                    insight={insight}
                    onViewDetails={() => setSelectedInsight(insight)}
                  />
                ))}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="actionable" className="mt-4">
          <ScrollArea className="h-[600px]">
            <div className="space-y-3">
              {filteredInsights
                .filter((i) => i.actions.length > 0)
                .map((insight) => (
                  <InsightCard
                    key={insight.id}
                    insight={insight}
                    onViewDetails={() => setSelectedInsight(insight)}
                  />
                ))}
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>

      {/* Detail Modal */}
      {selectedInsight && (
        <InsightDetailModal
          insight={selectedInsight}
          open={!!selectedInsight}
          onClose={() => setSelectedInsight(null)}
        />
      )}
    </div>
  );
}
