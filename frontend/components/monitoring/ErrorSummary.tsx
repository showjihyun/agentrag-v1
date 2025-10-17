/**
 * Error Summary Component
 * Displays error summary from /health/errors endpoint
 */

'use client';

import { useState, useEffect } from 'react';

interface ErrorEntry {
  error: string;
  count: number;
}

interface ErrorSummary {
  errors: ErrorEntry[];
  total_unique_errors: number;
}

export default function ErrorSummary() {
  const [summary, setSummary] = useState<ErrorSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [limit, setLimit] = useState(10);

  useEffect(() => {
    fetchErrors();
  }, [limit]);

  const fetchErrors = async () => {
    try {
      const response = await fetch(`/api/health/errors?limit=${limit}`);
      if (!response.ok) throw new Error('Failed to fetch errors');
      const data = await response.json();
      setSummary(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="animate-pulse bg-gray-100 rounded-lg p-4 h-64"></div>
    );
  }

  if (error || !summary) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800 text-sm">⚠️ Unable to fetch error summary</p>
        {error && <p className="text-red-600 text-xs mt-1">{error}</p>}
      </div>
    );
  }

  const parseError = (errorStr: string) => {
    const parts = errorStr.split(':');
    return {
      statusCode: parts[0] || 'Unknown',
      endpoint: parts[1] || errorStr,
    };
  };

  return (
    <div className="bg-white border rounded-lg p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold flex items-center">
          <span className="mr-2">🚨</span>
          Error Summary
        </h3>
        <div className="flex items-center space-x-2">
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="text-sm border rounded px-2 py-1"
          >
            <option value={5}>Top 5</option>
            <option value={10}>Top 10</option>
            <option value={20}>Top 20</option>
          </select>
          <button
            onClick={fetchErrors}
            className="text-sm px-3 py-1 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
            title="Refresh"
          >
            🔄
          </button>
        </div>
      </div>

      {summary.errors.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-green-600 text-lg mb-2">✓</p>
          <p className="text-gray-600 text-sm">No errors recorded</p>
          <p className="text-gray-500 text-xs mt-1">System is running smoothly!</p>
        </div>
      ) : (
        <>
          <div className="mb-4 p-3 bg-gray-50 rounded">
            <p className="text-sm text-gray-700">
              <span className="font-semibold">{summary.total_unique_errors}</span> unique error types detected
            </p>
          </div>

          <div className="space-y-2 max-h-96 overflow-y-auto">
            {summary.errors.map((entry, idx) => {
              const { statusCode, endpoint } = parseError(entry.error);
              const severity = 
                statusCode.startsWith('5') ? 'high' :
                statusCode.startsWith('4') ? 'medium' :
                'low';

              return (
                <div
                  key={idx}
                  className={`border-l-4 p-3 rounded ${
                    severity === 'high'
                      ? 'border-red-500 bg-red-50'
                      : severity === 'medium'
                      ? 'border-yellow-500 bg-yellow-50'
                      : 'border-blue-500 bg-blue-50'
                  }`}
                >
                  <div className="flex justify-between items-start mb-1">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className={`text-xs font-bold px-2 py-1 rounded ${
                          severity === 'high'
                            ? 'bg-red-200 text-red-800'
                            : severity === 'medium'
                            ? 'bg-yellow-200 text-yellow-800'
                            : 'bg-blue-200 text-blue-800'
                        }`}>
                          {statusCode}
                        </span>
                        <span className="text-sm font-medium text-gray-700 truncate">
                          {endpoint}
                        </span>
                      </div>
                    </div>
                    <div className="ml-4 text-right">
                      <p className="text-lg font-bold text-gray-800">
                        {entry.count}
                      </p>
                      <p className="text-xs text-gray-500">occurrences</p>
                    </div>
                  </div>
                  
                  {/* Error Bar */}
                  <div className="mt-2">
                    <div className="w-full bg-gray-200 rounded-full h-1.5">
                      <div
                        className={`h-1.5 rounded-full ${
                          severity === 'high'
                            ? 'bg-red-500'
                            : severity === 'medium'
                            ? 'bg-yellow-500'
                            : 'bg-blue-500'
                        }`}
                        style={{
                          width: `${Math.min((entry.count / summary.errors[0].count) * 100, 100)}%`,
                        }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Legend */}
          <div className="mt-4 pt-4 border-t">
            <p className="text-xs text-gray-600 mb-2">Severity Levels:</p>
            <div className="flex space-x-4 text-xs">
              <div className="flex items-center space-x-1">
                <div className="w-3 h-3 bg-red-500 rounded"></div>
                <span className="text-gray-600">5xx (Server Error)</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="w-3 h-3 bg-yellow-500 rounded"></div>
                <span className="text-gray-600">4xx (Client Error)</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="w-3 h-3 bg-blue-500 rounded"></div>
                <span className="text-gray-600">Other</span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
