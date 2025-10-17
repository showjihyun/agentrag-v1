/**
 * Rate Limit Warning Component
 * Displays warning when user is approaching or has hit rate limits
 */

'use client';

import { useEffect, useState } from 'react';

interface RateLimitWarningProps {
  action: 'login' | 'register' | 'query' | 'upload';
  attemptsRemaining?: number;
  resetTime?: number; // seconds until reset
  isBlocked?: boolean;
}

export default function RateLimitWarning({
  action,
  attemptsRemaining,
  resetTime,
  isBlocked = false,
}: RateLimitWarningProps) {
  const [timeLeft, setTimeLeft] = useState(resetTime || 0);

  useEffect(() => {
    if (!resetTime || resetTime <= 0) return;

    setTimeLeft(resetTime);
    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [resetTime]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (mins > 0) {
      return `${mins}m ${secs}s`;
    }
    return `${secs}s`;
  };

  const getActionLabel = (action: string): string => {
    const labels = {
      login: 'login attempts',
      register: 'registration attempts',
      query: 'queries',
      upload: 'file uploads',
    };
    return labels[action as keyof typeof labels] || action;
  };

  const getLimits = (action: string) => {
    const limits = {
      login: { max: 5, window: '15 minutes' },
      register: { max: 3, window: '1 hour' },
      query: { max: 100, window: '1 hour' },
      upload: { max: 20, window: '1 hour' },
    };
    return limits[action as keyof typeof limits] || { max: 0, window: 'unknown' };
  };

  if (isBlocked) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
        <div className="flex items-start space-x-3">
          <span className="text-red-600 text-xl">🚫</span>
          <div className="flex-1">
            <h4 className="text-red-800 font-semibold mb-1">
              Rate Limit Exceeded
            </h4>
            <p className="text-red-700 text-sm mb-2">
              You have exceeded the maximum number of {getActionLabel(action)}.
            </p>
            {timeLeft > 0 && (
              <div className="bg-red-100 rounded px-3 py-2 text-sm">
                <p className="text-red-800">
                  Please wait <span className="font-bold">{formatTime(timeLeft)}</span> before trying again.
                </p>
              </div>
            )}
            <p className="text-red-600 text-xs mt-2">
              Limit: {getLimits(action).max} {getActionLabel(action)} per {getLimits(action).window}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (attemptsRemaining !== undefined && attemptsRemaining <= 2) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
        <div className="flex items-start space-x-3">
          <span className="text-yellow-600 text-xl">⚠️</span>
          <div className="flex-1">
            <h4 className="text-yellow-800 font-semibold mb-1">
              Rate Limit Warning
            </h4>
            <p className="text-yellow-700 text-sm">
              You have <span className="font-bold">{attemptsRemaining}</span> {getActionLabel(action)} remaining.
            </p>
            <p className="text-yellow-600 text-xs mt-1">
              Limit: {getLimits(action).max} per {getLimits(action).window}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
