/**
 * System Health Monitoring Page
 * Displays comprehensive system health and performance metrics
 */

'use client';

import { useState } from 'react';
import SystemHealth from '@/components/monitoring/SystemHealth';
import PerformanceMetrics from '@/components/monitoring/PerformanceMetrics';
import ErrorSummary from '@/components/monitoring/ErrorSummary';

export default function HealthMonitoringPage() {
  const [activeTab, setActiveTab] = useState<'health' | 'performance' | 'errors'>('health');

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          System Monitoring
        </h1>
        <p className="text-gray-600">
          Real-time system health, performance metrics, and error tracking
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b mb-6">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('health')}
            className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'health'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <span className="mr-2">💚</span>
            System Health
          </button>
          <button
            onClick={() => setActiveTab('performance')}
            className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'performance'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <span className="mr-2">⚡</span>
            Performance
          </button>
          <button
            onClick={() => setActiveTab('errors')}
            className={`pb-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'errors'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <span className="mr-2">🚨</span>
            Errors
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeTab === 'health' && <SystemHealth />}
        {activeTab === 'performance' && <PerformanceMetrics />}
        {activeTab === 'errors' && <ErrorSummary />}
      </div>

      {/* Info Footer */}
      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="font-semibold text-blue-900 mb-2">
          📊 About System Monitoring
        </h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• <strong>System Health:</strong> Real-time status of database, system resources, and components</li>
          <li>• <strong>Performance:</strong> Request metrics, response times, and throughput statistics</li>
          <li>• <strong>Errors:</strong> Error tracking and analysis for troubleshooting</li>
        </ul>
        <p className="text-xs text-blue-600 mt-3">
          Data refreshes automatically. Click refresh buttons for immediate updates.
        </p>
      </div>
    </div>
  );
}
