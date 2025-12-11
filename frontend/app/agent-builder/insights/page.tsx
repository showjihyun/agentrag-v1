'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import {
  BarChart3,
  TrendingUp,
  Clock,
  CheckCircle,
  XCircle,
  Lightbulb,
  Download,
  Calendar,
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

interface UserInsights {
  user_id: number;
  time_range_days: number;
  generated_at: string;
  workflows: {
    total_workflows: number;
    total_chatflows: number;
    total_agentflows: number;
    most_used: Array<{
      flow_id: number;
      flow_type: string;
      execution_count: number;
    }>;
  };
  executions: {
    total_executions: number;
    successful: number;
    failed: number;
    success_rate: number;
    daily_executions: Array<{
      date: string;
      count: number;
    }>;
  };
  performance: {
    avg_duration_ms: number;
    min_duration_ms: number;
    max_duration_ms: number;
    by_type: Record<string, any>;
  };
  patterns: {
    peak_hours: Array<{ hour: number; count: number }>;
    peak_days: Array<{ day: string; count: number }>;
    most_active_day: string | null;
  };
  recommendations: Array<{
    type: string;
    priority: string;
    message: string;
    action: string;
  }>;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export default function InsightsPage() {
  const [insights, setInsights] = useState<UserInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(30);

  useEffect(() => {
    loadInsights();
  }, [timeRange]);

  const loadInsights = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/agent-builder/insights/user?time_range=${timeRange}`
      );
      if (!response.ok) throw new Error('Failed to load insights');
      const data = await response.json();
      setInsights(data);
    } catch (error) {
      console.error('Failed to load insights:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportInsights = async (format: 'json' | 'csv') => {
    try {
      const response = await fetch(
        `/api/agent-builder/insights/export?format=${format}&time_range=${timeRange}`
      );
      if (!response.ok) throw new Error('Export failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `insights_${timeRange}days.${format}`;
      a.click();
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
        </div>
      </div>
    );
  }

  if (!insights) {
    return (
      <div className="container mx-auto p-6">
        <Card className="p-6 text-center">
          <p className="text-gray-500">No insights available</p>
        </Card>
      </div>
    );
  }

  const workflowTypeData = [
    { name: 'Chatflows', value: insights.workflows.total_chatflows },
    { name: 'Agentflows', value: insights.workflows.total_agentflows },
  ];

  const executionStatusData = [
    { name: 'Successful', value: insights.executions.successful },
    { name: 'Failed', value: insights.executions.failed },
  ];

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
            <BarChart3 className="w-8 h-8 text-blue-500" />
            Insights & Analytics
          </h1>
          <p className="text-gray-600">
            Analyze your workflow performance and usage patterns
          </p>
        </div>

        <div className="flex gap-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="px-4 py-2 border rounded-lg"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>

          <Button onClick={() => exportInsights('json')} variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export JSON
          </Button>

          <Button onClick={() => exportInsights('csv')} variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Workflows</p>
              <p className="text-3xl font-bold mt-1">
                {insights.workflows.total_workflows}
              </p>
            </div>
            <BarChart3 className="w-10 h-10 text-blue-500 opacity-20" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Executions</p>
              <p className="text-3xl font-bold mt-1">
                {insights.executions.total_executions}
              </p>
            </div>
            <TrendingUp className="w-10 h-10 text-green-500 opacity-20" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Success Rate</p>
              <p className="text-3xl font-bold mt-1">
                {insights.executions.success_rate.toFixed(1)}%
              </p>
            </div>
            <CheckCircle className="w-10 h-10 text-green-500 opacity-20" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Duration</p>
              <p className="text-3xl font-bold mt-1">
                {(insights.performance.avg_duration_ms / 1000).toFixed(1)}s
              </p>
            </div>
            <Clock className="w-10 h-10 text-purple-500 opacity-20" />
          </div>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Daily Executions */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Daily Executions</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={insights.executions.daily_executions}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(date) => new Date(date).toLocaleDateString()}
              />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#3b82f6"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        {/* Workflow Types */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Workflow Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={workflowTypeData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {workflowTypeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        {/* Peak Hours */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Peak Usage Hours</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={insights.patterns.peak_hours}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Execution Status */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Execution Status</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={executionStatusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {executionStatusData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={index === 0 ? '#10b981' : '#ef4444'}
                  />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Recommendations */}
      {insights.recommendations.length > 0 && (
        <Card className="p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-yellow-500" />
            Recommendations
          </h3>
          <div className="space-y-3">
            {insights.recommendations.map((rec, idx) => (
              <div
                key={idx}
                className="p-4 border rounded-lg hover:bg-gray-50 transition"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge
                        variant={
                          rec.priority === 'high'
                            ? 'destructive'
                            : rec.priority === 'medium'
                            ? 'default'
                            : 'secondary'
                        }
                      >
                        {rec.priority}
                      </Badge>
                      <span className="text-xs text-gray-500">{rec.type}</span>
                    </div>
                    <p className="font-medium">{rec.message}</p>
                    <p className="text-sm text-gray-600 mt-1">{rec.action}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Most Used Workflows */}
      {insights.workflows.most_used.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Most Used Workflows</h3>
          <div className="space-y-2">
            {insights.workflows.most_used.map((workflow, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 border rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <div className="text-2xl font-bold text-gray-400">
                    #{idx + 1}
                  </div>
                  <div>
                    <p className="font-medium">
                      {workflow.flow_type} #{workflow.flow_id}
                    </p>
                    <Badge variant="secondary">{workflow.flow_type}</Badge>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-blue-600">
                    {workflow.execution_count}
                  </p>
                  <p className="text-xs text-gray-500">executions</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
