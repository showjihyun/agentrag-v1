'use client';

/**
 * Database Monitoring Page
 * Displays PostgreSQL and Milvus metrics
 */

import React from 'react';
import DatabaseMonitoring from '@/components/monitoring/DatabaseMonitoring';

export default function DatabaseMonitoringPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <DatabaseMonitoring autoRefresh={true} refreshInterval={30} />
      </div>
    </div>
  );
}
