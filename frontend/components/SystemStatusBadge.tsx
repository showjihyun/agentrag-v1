'use client';

/**
 * Enhanced System Status Badge Component
 * Displays real-time system health status in header
 * Shows PostgreSQL pool utilization, Milvus status, and response times
 */

import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { cn } from '@/lib/utils';

interface SystemHealth {
  status: string;
  latency?: number;
  postgresql?: {
    status: string;
    message: string;
    utilization: number;
  };
  milvus?: {
    status: string;
    message: string;
  };
}

export default function SystemStatusBadge() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [loading, setLoading] = useState(true);
  const [responseTime, setResponseTime] = useState<number | null>(null);
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, right: 0 });
  const buttonRef = useRef<HTMLButtonElement>(null);

  const fetchHealth = async () => {
    try {
      const startTime = Date.now();
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/metrics/database/summary`);
      const endTime = Date.now();
      
      if (response.ok) {
        const data = await response.json();
        setHealth({
          status: data.overall_status,
          postgresql: data.postgresql,
          milvus: data.milvus,
        });
        setResponseTime(endTime - startTime);
      }
    } catch (error) {
      console.error('Failed to fetch system health:', error);
      setHealth({ status: 'critical' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // 30 seconds
    return () => clearInterval(interval);
  }, []);

  const updateDropdownPosition = () => {
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      setDropdownPosition({
        top: rect.bottom + window.scrollY + 8,
        right: window.innerWidth - rect.right - window.scrollX,
      });
    }
  };

  useEffect(() => {
    if (showDetails) {
      updateDropdownPosition();
      window.addEventListener('resize', updateDropdownPosition);
      window.addEventListener('scroll', updateDropdownPosition, true);
      return () => {
        window.removeEventListener('resize', updateDropdownPosition);
        window.removeEventListener('scroll', updateDropdownPosition, true);
      };
    }
  }, [showDetails]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-100 dark:bg-gray-800">
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" />
        <span className="text-xs text-gray-600 dark:text-gray-400">Checking...</span>
      </div>
    );
  }

  if (!health) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-100 dark:bg-gray-800">
        <div className="w-2 h-2 bg-gray-400 rounded-full" />
        <span className="text-xs text-gray-600 dark:text-gray-400">Unknown</span>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return {
          bg: 'bg-green-100 dark:bg-green-900/30',
          text: 'text-green-800 dark:text-green-300',
          dot: 'bg-green-500',
        };
      case 'degraded':
      case 'warning':
        return {
          bg: 'bg-yellow-100 dark:bg-yellow-900/30',
          text: 'text-yellow-800 dark:text-yellow-300',
          dot: 'bg-yellow-500',
        };
      case 'critical':
        return {
          bg: 'bg-red-100 dark:bg-red-900/30',
          text: 'text-red-800 dark:text-red-300',
          dot: 'bg-red-500',
        };
      default:
        return {
          bg: 'bg-gray-100 dark:bg-gray-800',
          text: 'text-gray-800 dark:text-gray-300',
          dot: 'bg-gray-500',
        };
    }
  };

  const colors = getStatusColor(health.status);

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        onClick={() => {
          setShowDetails(!showDetails);
          if (!showDetails) {
            updateDropdownPosition();
          }
        }}
        className={cn(
          'flex items-center gap-2 px-3 py-1.5 rounded-full transition-all duration-200',
          colors.bg,
          'hover:shadow-md'
        )}
        aria-label="System status"
      >
        <div className={cn(
          'w-2 h-2 rounded-full',
          colors.dot,
          health.status === 'healthy' && 'animate-pulse'
        )} />
        <span className={cn('text-xs font-medium', colors.text)}>
          {health.status === 'healthy' ? 'All Systems Operational' : 
           health.status === 'degraded' ? 'Degraded Performance' :
           health.status === 'critical' ? 'System Issues' : 'Unknown'}
        </span>
        {responseTime && (
          <span className={cn(
            'text-xs opacity-70',
            colors.text
          )}>
            {responseTime}ms
          </span>
        )}
        <svg 
          className={cn(
            'w-3 h-3 transition-transform',
            colors.text,
            showDetails && 'rotate-180'
          )} 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Details Dropdown with Portal */}
      {showDetails && typeof window !== 'undefined' && createPortal(
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-black/10 dark:bg-black/30 z-[9998]" 
            onClick={() => setShowDetails(false)}
          />
          
          {/* Dropdown */}
          <div 
            className="fixed w-80 bg-white dark:bg-gray-800 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 z-[9999]"
            style={{
              top: `${dropdownPosition.top}px`,
              right: `${dropdownPosition.right}px`,
            }}
          >
            <div className="p-4 space-y-3">
              <div className="flex items-center justify-between pb-3 border-b border-gray-200 dark:border-gray-700">
                <h3 className="font-semibold text-gray-900 dark:text-gray-100">System Status</h3>
                <button
                  onClick={() => setShowDetails(false)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Response Time */}
              {responseTime && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">Response Time</span>
                  <span className={cn(
                    'font-medium',
                    responseTime < 100 ? 'text-green-600 dark:text-green-400' :
                    responseTime < 500 ? 'text-yellow-600 dark:text-yellow-400' :
                    'text-red-600 dark:text-red-400'
                  )}>
                    {responseTime}ms
                  </span>
                </div>
              )}

              {/* PostgreSQL Status */}
              {health.postgresql && (
                <div className="space-y-2 p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <svg className="w-4 h-4 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                      </svg>
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">PostgreSQL</span>
                    </div>
                    <span className={cn(
                      'text-xs font-medium px-2 py-0.5 rounded-full',
                      getStatusColor(health.postgresql.status).bg,
                      getStatusColor(health.postgresql.status).text
                    )}>
                      {health.postgresql.status}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {health.postgresql.message}
                  </p>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-600 dark:text-gray-400">Pool Utilization</span>
                      <span className={cn(
                        'font-medium',
                        health.postgresql.utilization > 90 ? 'text-red-600 dark:text-red-400' :
                        health.postgresql.utilization > 75 ? 'text-yellow-600 dark:text-yellow-400' :
                        'text-green-600 dark:text-green-400'
                      )}>
                        {health.postgresql.utilization.toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className={cn(
                          'h-2 rounded-full transition-all duration-300',
                          health.postgresql.utilization > 90 ? 'bg-red-500' :
                          health.postgresql.utilization > 75 ? 'bg-yellow-500' :
                          'bg-green-500'
                        )}
                        style={{ width: `${Math.min(health.postgresql.utilization, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Milvus Status */}
              {health.milvus && (
                <div className="space-y-2 p-3 bg-gray-50 dark:bg-gray-900/50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <svg className="w-4 h-4 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                      </svg>
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Milvus</span>
                    </div>
                    <span className={cn(
                      'text-xs font-medium px-2 py-0.5 rounded-full',
                      getStatusColor(health.milvus.status).bg,
                      getStatusColor(health.milvus.status).text
                    )}>
                      {health.milvus.status}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {health.milvus.message}
                  </p>
                </div>
              )}

              {/* Actions */}
              <div className="pt-2 border-t border-gray-200 dark:border-gray-700 space-y-2">
                <a
                  href="/monitoring"
                  className="flex items-center justify-between text-sm text-blue-600 dark:text-blue-400 hover:underline"
                  onClick={() => setShowDetails(false)}
                >
                  <span>View Detailed Metrics</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </a>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Auto-refreshes every 30 seconds
                </p>
              </div>
            </div>
          </div>
        </>,
        document.body
      )}
    </div>
  );
}
