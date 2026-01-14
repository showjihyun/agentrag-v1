'use client';

import React, { useState, useEffect } from 'react';
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Zap,
  BarChart3,
  PieChart,
  RefreshCw,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
  Cpu,
  Clock,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface UsageSummary {
  total_input_tokens: number;
  total_output_tokens: number;
  total_tokens: number;
  total_cost_usd: number;
  request_count: number;
  avg_tokens_per_request: number;
  avg_cost_per_request: number;
}

interface ModelUsage {
  model: string;
  provider: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_usd: number;
  request_count: number;
  percentage: number;
}

interface DailyUsage {
  date: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_usd: number;
  request_count: number;
}

interface TokenUsageRecord {
  id: string;
  workflow_id?: string;
  execution_id?: string;
  model: string;
  provider: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_usd: number;
  timestamp: string;
  node_id?: string;
  node_type?: string;
}

interface DashboardData {
  summary: UsageSummary;
  by_model: ModelUsage[];
  daily_usage: DailyUsage[];
  recent_records: TokenUsageRecord[];
}

interface CostTrackingDashboardProps {
  workflowId?: string;
}

const PROVIDER_COLORS: Record<string, string> = {
  openai: 'bg-green-500',
  anthropic: 'bg-orange-500',
  google: 'bg-blue-500',
  mistral: 'bg-purple-500',
  ollama: 'bg-gray-500',
};

const formatNumber = (num: number): string => {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
};

const formatCost = (cost: number): string => {
  if (cost < 0.01) return `$${cost.toFixed(4)}`;
  if (cost < 1) return `$${cost.toFixed(3)}`;
  return `$${cost.toFixed(2)}`;
};

export const CostTrackingDashboard: React.FC<CostTrackingDashboardProps> = ({
  workflowId,
}) => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState('30');
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams({ days });
      if (workflowId) params.append('workflow_id', workflowId);
      
      const response = await fetch(`/api/agent-builder/cost-tracking/dashboard?${params}`, {
        credentials: 'include',
      });
      
      if (!response.ok) throw new Error('Failed to fetch data');
      
      const result = await response.json();
      setData(result);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [days, workflowId]);

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-destructive">
        <p>{error}</p>
        <Button onClick={fetchData} variant="outline" className="mt-4">
          Retry
        </Button>
      </div>
    );
  }

  const summary = data?.summary || {
    total_input_tokens: 0,
    total_output_tokens: 0,
    total_tokens: 0,
    total_cost_usd: 0,
    request_count: 0,
    avg_tokens_per_request: 0,
    avg_cost_per_request: 0,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">Cost & Token Tracking</h2>
          <p className="text-sm text-muted-foreground">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={days} onValueChange={setDays}>
            <SelectTrigger className="w-32">
              <Calendar className="h-4 w-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">7 days</SelectItem>
              <SelectItem value="30">30 days</SelectItem>
              <SelectItem value="90">90 days</SelectItem>
              <SelectItem value="365">1 year</SelectItem>
            </SelectContent>
          </Select>
          <Button size="sm" variant="outline" onClick={fetchData} disabled={loading}>
            <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-4 hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Cost</p>
              <p className="text-2xl font-bold mt-1">{formatCost(summary.total_cost_usd)}</p>
              <p className="text-xs text-muted-foreground mt-1">
                {summary.request_count} requests
              </p>
            </div>
            <div className="p-2 rounded-lg bg-green-100">
              <DollarSign className="h-5 w-5 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4 hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Tokens</p>
              <p className="text-2xl font-bold mt-1">{formatNumber(summary.total_tokens)}</p>
              <div className="flex gap-2 mt-1">
                <span className="text-xs text-blue-600">Input: {formatNumber(summary.total_input_tokens)}</span>
                <span className="text-xs text-purple-600">Output: {formatNumber(summary.total_output_tokens)}</span>
              </div>
            </div>
            <div className="p-2 rounded-lg bg-blue-100">
              <Zap className="h-5 w-5 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4 hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-500">Avg Tokens/Request</p>
              <p className="text-2xl font-bold mt-1">{formatNumber(summary.avg_tokens_per_request)}</p>
            </div>
            <div className="p-2 rounded-lg bg-purple-100">
              <BarChart3 className="h-5 w-5 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4 hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-500">Avg Cost/Request</p>
              <p className="text-2xl font-bold mt-1">{formatCost(summary.avg_cost_per_request)}</p>
            </div>
            <div className="p-2 rounded-lg bg-orange-100">
              <TrendingUp className="h-5 w-5 text-orange-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Model Usage */}
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Cpu className="h-5 w-5 text-blue-500" />
              <h3 className="font-semibold">Usage by Model</h3>
            </div>
          </div>
          
          {data?.by_model && data.by_model.length > 0 ? (
            <div className="space-y-3">
              {data.by_model.map((model, index) => (
                <div key={model.model} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div className={cn("w-3 h-3 rounded-full", PROVIDER_COLORS[model.provider] || 'bg-gray-400')} />
                      <span className="font-medium">{model.model}</span>
                      <Badge variant="outline" className="text-xs">{model.provider}</Badge>
                    </div>
                    <span className="font-medium">{formatCost(model.cost_usd)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-100 rounded-full h-2">
                      <div 
                        className={cn("h-2 rounded-full transition-all", PROVIDER_COLORS[model.provider] || 'bg-gray-400')}
                        style={{ width: `${model.percentage}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground w-12 text-right">
                      {model.percentage.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex gap-4 text-xs text-muted-foreground">
                    <span>{formatNumber(model.total_tokens)} tokens</span>
                    <span>{model.request_count} requests</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-8">
              No usage data available
            </p>
          )}
        </div>

        {/* Daily Trend */}
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-500" />
              <h3 className="font-semibold">Daily Trend</h3>
            </div>
          </div>
          
          {data?.daily_usage && data.daily_usage.length > 0 ? (
            <div className="space-y-2">
              {/* Simple bar chart */}
              <div className="flex items-end gap-1 h-32">
                {data.daily_usage.slice(-14).map((day, index) => {
                  const maxCost = Math.max(...data.daily_usage.map(d => d.cost_usd));
                  const height = maxCost > 0 ? (day.cost_usd / maxCost) * 100 : 0;
                  
                  return (
                    <div 
                      key={day.date}
                      className="flex-1 flex flex-col items-center gap-1"
                    >
                      <div 
                        className="w-full bg-blue-500 rounded-t transition-all hover:bg-blue-600"
                        style={{ height: `${Math.max(height, 2)}%` }}
                        title={`${day.date}: ${formatCost(day.cost_usd)}`}
                      />
                    </div>
                  );
                })}
              </div>
              
              {/* X-axis labels */}
              <div className="flex gap-1 text-xs text-muted-foreground">
                {data.daily_usage.slice(-14).map((day, index) => (
                  <div key={day.date} className="flex-1 text-center truncate">
                    {index % 2 === 0 ? day.date.slice(5) : ''}
                  </div>
                ))}
              </div>
              
              {/* Summary */}
              <div className="flex justify-between text-sm pt-2 border-t">
                <span className="text-muted-foreground">Last {data.daily_usage.length} days</span>
                <span className="font-medium">
                  Total {formatCost(data.daily_usage.reduce((sum, d) => sum + d.cost_usd, 0))}
                </span>
              </div>
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-8">
              No daily data available
            </p>
          )}
        </div>
      </div>

      {/* Recent Records */}
      <div className="bg-white rounded-lg border p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-gray-500" />
            <h3 className="font-semibold">Recent Usage Records</h3>
          </div>
        </div>
        
        {data?.recent_records && data.recent_records.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 font-medium">Time</th>
                  <th className="text-left py-2 font-medium">Model</th>
                  <th className="text-right py-2 font-medium">Input</th>
                  <th className="text-right py-2 font-medium">Output</th>
                  <th className="text-right py-2 font-medium">Cost</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_records.slice(0, 10).map((record) => (
                  <tr key={record.id} className="border-b last:border-0 hover:bg-muted/50">
                    <td className="py-2 text-muted-foreground">
                      {new Date(record.timestamp).toLocaleString()}
                    </td>
                    <td className="py-2">
                      <div className="flex items-center gap-2">
                        <div className={cn("w-2 h-2 rounded-full", PROVIDER_COLORS[record.provider] || 'bg-gray-400')} />
                        <span>{record.model}</span>
                      </div>
                    </td>
                    <td className="py-2 text-right font-mono">
                      {formatNumber(record.input_tokens)}
                    </td>
                    <td className="py-2 text-right font-mono">
                      {formatNumber(record.output_tokens)}
                    </td>
                    <td className="py-2 text-right font-mono font-medium">
                      {formatCost(record.cost_usd)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-center text-muted-foreground py-8">
            No usage records available
          </p>
        )}
      </div>
    </div>
  );
};

export default CostTrackingDashboard;
