'use client';

import { Suspense } from 'react';
import MonitoringStatsPanel from '@/components/monitoring/MonitoringStatsPanel';

export default function MonitoringStatsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Monitoring Dashboard</h1>
              <p className="text-sm text-gray-600 mt-1">
                Comprehensive statistics for file uploads, embeddings, search, and RAG processing
              </p>
            </div>
            <a
              href="/"
              className="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-1"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Chat
            </a>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        <Suspense fallback={
          <div className="flex items-center justify-center p-12">
            <div className="text-lg text-gray-600">Loading statistics...</div>
          </div>
        }>
          <MonitoringStatsPanel />
        </Suspense>
      </div>
    </div>
  );
}
