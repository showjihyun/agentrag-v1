'use client';

import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingUp,
  Clock,
  AlertCircle,
  CheckCircle,
  Activity,
  DollarSign,
  Zap,
} from 'lucide-react';

interface WorkflowStats {
  totalExecutions: number;
  successRate: number;
  avgExecutionTime: number;
  totalErrors: number;
  executionsToday: number;
  executionsThisWeek: number;
  totalCost: number;
  mostUsedWorkflow: string;
}

interface NodeStats {
  nodeType: string;
  count: number;
  avgTime: number;
  errorRate: number;
}

export default function AnalyticsPage() {
  const [stats, setStats] = useState<WorkflowStats>({
    totalExecutions: 1247,
    successRate: 94.2,
    avgExecutionTime: 2.3,
    totalErrors: 72,
    executionsToday: 45,
    executionsThisWeek: 312,
    totalCost: 12.45,
    mostUsedWorkflow: 'Customer Support Bot',
  });

  const [nodeStats, setNodeStats] = useState<NodeStats[]>([
    { nodeType: 'Agent', count: 523, avgTime: 1.8, errorRate: 3.2 },
    { nodeType: 'HTTP Request', count: 412, avgTime: 0.5, errorRate: 5.1 },
    { nodeType: 'Code', count: 289, avgTime: 0.3, errorRate: 2.8 },
    { nodeType: 'Condition', count: 234, avgTime: 0.1, errorRate: 0.5 },
    { nodeType: 'Loop', count: 156, avgTime: 3.2, errorRate: 4.2 },
  ]);

  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('7d');

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Workflow Analytics
          </h1>
          <p className="text-gray-600">
            Monitor performance, costs, and execution statistics
          </p>
        </div>

        {/* Time Range Selector */}
        <div className="flex gap-2 mb-6">
          {(['24h', '7d', '30d'] as const).map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                timeRange === range
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              {range === '24h' ? 'Last 24 Hours' : range === '7d' ? 'Last 7 Days' : 'Last 30 Days'}
            </button>
          ))}
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <MetricCard
            icon={<Activity className="w-6 h-6 text-blue-600" />}
            title="Total Executions"
            value={stats.totalExecutions.toLocaleString()}
            change="+12.5%"
            positive
          />
          <MetricCard
            icon={<CheckCircle className="w-6 h-6 text-green-600" />}
            title="Success Rate"
            value={`${stats.successRate}%`}
            change="+2.1%"
            positive
          />
          <MetricCard
            icon={<Clock className="w-6 h-6 text-purple-600" />}
            title="Avg Execution Time"
            value={`${stats.avgExecutionTime}s`}
            change="-0.3s"
            positive
          />
          <MetricCard
            icon={<DollarSign className="w-6 h-6 text-yellow-600" />}
            title="Total Cost"
            value={`$${stats.totalCost.toFixed(2)}`}
            change="+$1.20"
            positive={false}
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Execution Trend */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-600" />
              Execution Trend
            </h3>
            <div className="h-64 flex items-end justify-between gap-2">
              {[45, 62, 38, 71, 55, 68, 82].map((value, idx) => (
                <div key={idx} className="flex-1 flex flex-col items-center">
                  <div
                    className="w-full bg-blue-500 rounded-t hover:bg-blue-600 transition-colors cursor-pointer"
                    style={{ height: `${(value / 100) * 100}%` }}
                    title={`${value} executions`}
                  />
                  <span className="text-xs text-gray-500 mt-2">
                    {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][idx]}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Error Distribution */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-red-600" />
              Error Distribution
            </h3>
            <div className="space-y-3">
              {[
                { type: 'Timeout', count: 28, color: 'bg-red-500' },
                { type: 'API Error', count: 19, color: 'bg-orange-500' },
                { type: 'Validation', count: 15, color: 'bg-yellow-500' },
                { type: 'Network', count: 10, color: 'bg-purple-500' },
              ].map((error) => (
                <div key={error.type}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-gray-700">{error.type}</span>
                    <span className="text-sm font-medium text-gray-900">
                      {error.count}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`${error.color} h-2 rounded-full`}
                      style={{ width: `${(error.count / 72) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Node Performance Table */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-green-600" />
            Node Performance
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">
                    Node Type
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-gray-700">
                    Executions
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-gray-700">
                    Avg Time
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-gray-700">
                    Error Rate
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-gray-700">
                    Performance
                  </th>
                </tr>
              </thead>
              <tbody>
                {nodeStats.map((node) => (
                  <tr key={node.nodeType} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm text-gray-900">
                      {node.nodeType}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-900 text-right">
                      {node.count.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-900 text-right">
                      {node.avgTime}s
                    </td>
                    <td className="py-3 px-4 text-sm text-right">
                      <span
                        className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                          node.errorRate < 3
                            ? 'bg-green-100 text-green-700'
                            : node.errorRate < 5
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {node.errorRate}%
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1">
                        {Array.from({ length: 5 }).map((_, idx) => (
                          <div
                            key={idx}
                            className={`w-2 h-4 rounded ${
                              idx < Math.floor((100 - node.errorRate) / 20)
                                ? 'bg-green-500'
                                : 'bg-gray-200'
                            }`}
                          />
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Cost Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-yellow-600" />
              Cost by Provider
            </h3>
            <div className="space-y-3">
              {[
                { provider: 'OpenAI GPT-4', cost: 8.32, percentage: 67 },
                { provider: 'Anthropic Claude', cost: 2.89, percentage: 23 },
                { provider: 'Ollama (Local)', cost: 0.0, percentage: 10 },
              ].map((item) => (
                <div key={item.provider}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-gray-700">{item.provider}</span>
                    <span className="text-sm font-medium text-gray-900">
                      ${item.cost.toFixed(2)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-yellow-500 h-2 rounded-full"
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Zap className="w-5 h-5 text-orange-600" />
              Top Workflows
            </h3>
            <div className="space-y-3">
              {[
                { name: 'Customer Support Bot', executions: 342, time: '2.1s' },
                { name: 'Document Processor', executions: 289, time: '4.5s' },
                { name: 'Data Enrichment', executions: 234, time: '1.8s' },
                { name: 'Email Automation', executions: 187, time: '0.9s' },
              ].map((workflow) => (
                <div
                  key={workflow.name}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {workflow.name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {workflow.executions} executions
                    </div>
                  </div>
                  <div className="text-sm text-gray-600">{workflow.time}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface MetricCardProps {
  icon: React.ReactNode;
  title: string;
  value: string;
  change: string;
  positive: boolean;
}

function MetricCard({ icon, title, value, change, positive }: MetricCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-2">
        <div className="p-2 bg-gray-100 rounded-lg">{icon}</div>
        <span
          className={`text-sm font-medium ${
            positive ? 'text-green-600' : 'text-red-600'
          }`}
        >
          {change}
        </span>
      </div>
      <h3 className="text-sm text-gray-600 mb-1">{title}</h3>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}
