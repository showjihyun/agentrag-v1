'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/Card';

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

interface SystemMetrics {
  file_uploads: FileUploadStats;
  embeddings: EmbeddingStats;
  hybrid_search: HybridSearchStats;
  rag_processing: RAGProcessingStats;
  accuracy_trends: AccuracyTrend[];
}

export default function MonitoringPage() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [days, setDays] = useState(7);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [days]);

  const fetchMetrics = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/monitoring/stats/overview?days=${days}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch metrics');
      }

      const data = await response.json();
      setMetrics(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading metrics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold dark:text-white">System Monitoring</h1>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="px-4 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700 dark:text-white"
        >
          <option value={1}>Last 24 hours</option>
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* File Upload Stats */}
      {metrics?.file_uploads && (
        <Card title="File Uploads">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              label="Total Files"
              value={metrics.file_uploads.total_files}
            />
            <MetricCard
              label="Successful"
              value={metrics.file_uploads.successful_uploads}
            />
            <MetricCard
              label="Failed"
              value={metrics.file_uploads.failed_uploads}
              warning={metrics.file_uploads.failed_uploads > 0}
            />
            <MetricCard
              label="Total Size"
              value={`${metrics.file_uploads.total_size_mb.toFixed(1)} MB`}
            />
          </div>
        </Card>
      )}

      {/* Embedding Stats */}
      {metrics?.embeddings && (
        <Card title="Embeddings">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              label="Total Embeddings"
              value={metrics.embeddings.total_embeddings}
            />
            <MetricCard
              label="Total Chunks"
              value={metrics.embeddings.total_chunks}
            />
            <MetricCard
              label="Avg Chunks/Doc"
              value={metrics.embeddings.avg_chunks_per_document.toFixed(1)}
            />
            <MetricCard
              label="Avg Time"
              value={`${metrics.embeddings.avg_embedding_time_ms.toFixed(0)}ms`}
            />
          </div>
        </Card>
      )}

      {/* Workflow Execution Stats */}
      {metrics?.workflow_execution && (
        <Card title="Workflow Execution">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              label="Total Executions"
              value={metrics.workflow_execution.total_executions}
            />
            <MetricCard
              label="Success Rate"
              value={`${(metrics.workflow_execution.success_rate * 100).toFixed(1)}%`}
              warning={metrics.workflow_execution.success_rate < 0.8}
            />
            <MetricCard
              label="Avg Execution Time"
              value={`${metrics.workflow_execution.avg_execution_time_ms.toFixed(0)}ms`}
            />
            <MetricCard
              label="Active Workflows"
              value={metrics.workflow_execution.active_workflows}
            />
          </div>
        </Card>
      )}

      {/* RAG Processing Stats */}
      {metrics?.rag_processing && (
        <Card title="RAG Processing">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              label="Total Queries"
              value={metrics.rag_processing.total_queries}
            />
            <MetricCard
              label="Success Rate"
              value={`${(metrics.rag_processing.success_rate * 100).toFixed(1)}%`}
              warning={metrics.rag_processing.success_rate < 0.8}
            />
            <MetricCard
              label="Avg Confidence"
              value={metrics.rag_processing.avg_confidence_score.toFixed(2)}
            />
            <MetricCard
              label="Avg Response Time"
              value={`${metrics.rag_processing.avg_response_time_ms.toFixed(0)}ms`}
            />
          </div>
        </Card>
      )}

      <div className="text-sm text-gray-500 dark:text-gray-400 text-center">
        Last updated: {new Date().toLocaleString()}
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  warning = false,
}: {
  label: string;
  value: string | number;
  warning?: boolean;
}) {
  return (
    <div className={`p-4 rounded-lg ${warning ? 'bg-yellow-50 border-yellow-200' : 'bg-gray-50'} border`}>
      <div className="text-sm text-gray-600 mb-1">{label}</div>
      <div className={`text-2xl font-bold ${warning ? 'text-yellow-700' : 'text-gray-900'}`}>
        {value}
      </div>
    </div>
  );
}
