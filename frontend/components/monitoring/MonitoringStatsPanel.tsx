'use client';

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/Card';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

interface FileUploadStats {
  total_files: number;
  successful_uploads: number;
  failed_uploads: number;
  total_size_mb: number;
  avg_processing_time_ms: number;
  by_file_type: Record<string, number>;
  recent_uploads: Array<{
    id: string;
    filename: string;
    file_type: string;
    status: string;
    created_at: string;
    file_size_mb: number;
  }>;
}

interface EmbeddingStats {
  total_embeddings: number;
  total_chunks: number;
  avg_chunks_per_document: number;
  embedding_model: string;
  avg_embedding_time_ms: number;
  by_chunking_strategy: Record<string, number>;
}

interface HybridSearchStats {
  total_searches: number;
  vector_only: number;
  keyword_only: number;
  hybrid: number;
  avg_search_time_ms: number;
  avg_results_count: number;
  cache_hit_rate: number;
}

interface RAGProcessingStats {
  total_queries: number;
  by_mode: Record<string, number>;
  by_complexity: Record<string, number>;
  avg_response_time_ms: number;
  avg_confidence_score: number;
  success_rate: number;
}

interface AccuracyTrend {
  date: string;
  total_queries: number;
  avg_confidence: number;
  high_confidence_rate: number;
  success_rate: number;
  avg_response_time_ms: number;
}

interface MonitoringStats {
  file_uploads: FileUploadStats;
  embeddings: EmbeddingStats;
  hybrid_search: HybridSearchStats;
  rag_processing: RAGProcessingStats;
  accuracy_trends: AccuracyTrend[];
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export default function MonitoringStatsPanel() {
  const [stats, setStats] = useState<MonitoringStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(7);

  useEffect(() => {
    fetchStats();
  }, [days]);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/monitoring/stats/overview?days=${days}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch monitoring stats');
      }

      const data = await response.json();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-lg text-gray-600">Loading statistics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  // Prepare chart data
  const fileTypeData = Object.entries(stats.file_uploads.by_file_type).map(([type, count]) => ({
    name: type.toUpperCase(),
    value: count
  }));

  const searchTypeData = [
    { name: 'Vector Only', value: stats.hybrid_search.vector_only },
    { name: 'Keyword Only', value: stats.hybrid_search.keyword_only },
    { name: 'Hybrid', value: stats.hybrid_search.hybrid }
  ].filter(item => item.value > 0);

  const modeData = Object.entries(stats.rag_processing.by_mode).map(([mode, count]) => ({
    name: mode.toUpperCase(),
    value: count
  }));

  return (
    <div className="space-y-6">
      {/* Time Range Selector */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Monitoring Statistics</h2>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value={1}>Last 24 hours</option>
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* File Upload Stats */}
      <Card title="📤 File Upload Statistics">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <StatCard label="Total Files" value={stats.file_uploads.total_files} />
            <StatCard 
              label="Successful" 
              value={stats.file_uploads.successful_uploads} 
              color="text-green-600"
            />
            <StatCard 
              label="Failed" 
              value={stats.file_uploads.failed_uploads} 
              color="text-red-600"
            />
            <StatCard 
              label="Total Size" 
              value={`${stats.file_uploads.total_size_mb.toFixed(2)} MB`} 
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* File Type Distribution */}
            <div>
              <h4 className="text-sm font-semibold mb-3">File Type Distribution</h4>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={fileTypeData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }: any) => `${name} ${((percent as number) * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {fileTypeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Recent Uploads */}
            <div>
              <h4 className="text-sm font-semibold mb-3">Recent Uploads</h4>
              <div className="space-y-2 max-h-[250px] overflow-y-auto">
                {stats.file_uploads.recent_uploads.map((upload) => (
                  <div key={upload.id} className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
                    <div className="flex-1 truncate">
                      <div className="font-medium truncate">{upload.filename}</div>
                      <div className="text-xs text-gray-500">
                        {upload.file_type} • {upload.file_size_mb.toFixed(2)} MB
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs ${
                      upload.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {upload.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
      </Card>

      {/* Embedding Stats */}
      <Card title="🔢 Embedding Statistics">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <StatCard label="Total Embeddings" value={stats.embeddings.total_embeddings} />
            <StatCard label="Total Chunks" value={stats.embeddings.total_chunks} />
            <StatCard 
              label="Avg Chunks/Doc" 
              value={stats.embeddings.avg_chunks_per_document.toFixed(1)} 
            />
            <StatCard 
              label="Avg Time" 
              value={`${stats.embeddings.avg_embedding_time_ms.toFixed(0)}ms`} 
            />
          </div>
          <div className="text-sm text-gray-600">
            <strong>Model:</strong> {stats.embeddings.embedding_model}
          </div>
      </Card>

      {/* Hybrid Search Stats */}
      <Card title="🔍 Hybrid Search Statistics">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <StatCard label="Total Searches" value={stats.hybrid_search.total_searches} />
            <StatCard 
              label="Avg Time" 
              value={`${stats.hybrid_search.avg_search_time_ms.toFixed(0)}ms`} 
            />
            <StatCard 
              label="Avg Results" 
              value={stats.hybrid_search.avg_results_count.toFixed(1)} 
            />
            <StatCard 
              label="Cache Hit Rate" 
              value={`${(stats.hybrid_search.cache_hit_rate * 100).toFixed(1)}%`}
              color="text-blue-600"
            />
          </div>

          {/* Search Type Distribution */}
          <div>
            <h4 className="text-sm font-semibold mb-3">Search Type Distribution</h4>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={searchTypeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
      </Card>

      {/* RAG Processing Stats */}
      <Card title="💡 RAG Processing Statistics">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <StatCard label="Total Queries" value={stats.rag_processing.total_queries} />
            <StatCard 
              label="Avg Response Time" 
              value={`${stats.rag_processing.avg_response_time_ms.toFixed(0)}ms`} 
            />
            <StatCard 
              label="Avg Confidence" 
              value={stats.rag_processing.avg_confidence_score.toFixed(3)}
              color="text-purple-600"
            />
            <StatCard 
              label="Success Rate" 
              value={`${(stats.rag_processing.success_rate * 100).toFixed(1)}%`}
              color="text-green-600"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Mode Distribution */}
            <div>
              <h4 className="text-sm font-semibold mb-3">Query Mode Distribution</h4>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={modeData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }: any) => `${name} ${((percent as number) * 100).toFixed(0)}%`}
                    outerRadius={70}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {modeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Complexity Distribution */}
            <div>
              <h4 className="text-sm font-semibold mb-3">Complexity Distribution</h4>
              <div className="space-y-2">
                {Object.entries(stats.rag_processing.by_complexity).map(([level, count]) => (
                  <div key={level} className="flex items-center justify-between">
                    <span className="text-sm capitalize">{level}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ 
                            width: `${(count / stats.rag_processing.total_queries) * 100}%` 
                          }}
                        />
                      </div>
                      <span className="text-sm font-medium w-12 text-right">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
      </Card>

      {/* Accuracy Trends */}
      <Card title="📊 Daily Accuracy Trends">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={stats.accuracy_trends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tickFormatter={(value) => new Date(value).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })}
              />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip 
                labelFormatter={(value) => new Date(value).toLocaleDateString('ko-KR')}
                formatter={(value: any) => typeof value === 'number' ? value.toFixed(3) : value}
              />
              <Legend />
              <Line 
                yAxisId="left"
                type="monotone" 
                dataKey="avg_confidence" 
                stroke="#8b5cf6" 
                name="Avg Confidence"
                strokeWidth={2}
              />
              <Line 
                yAxisId="left"
                type="monotone" 
                dataKey="success_rate" 
                stroke="#10b981" 
                name="Success Rate"
                strokeWidth={2}
              />
              <Line 
                yAxisId="right"
                type="monotone" 
                dataKey="avg_response_time_ms" 
                stroke="#f59e0b" 
                name="Avg Response Time (ms)"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
      </Card>
    </div>
  );
}

function StatCard({ 
  label, 
  value, 
  color = "text-gray-900" 
}: { 
  label: string; 
  value: string | number; 
  color?: string;
}) {
  return (
    <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
      <div className="text-sm text-gray-600 mb-1">{label}</div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
    </div>
  );
}
