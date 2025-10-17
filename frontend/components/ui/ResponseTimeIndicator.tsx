/**
 * Response Time Indicator Component
 * Shows response time from X-Response-Time header
 */

'use client';

interface ResponseTimeIndicatorProps {
  responseTime?: number; // in milliseconds
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export default function ResponseTimeIndicator({
  responseTime,
  showLabel = true,
  size = 'md',
}: ResponseTimeIndicatorProps) {
  if (responseTime === undefined) return null;

  const getColor = (time: number) => {
    if (time < 100) return 'text-green-600 bg-green-50';
    if (time < 500) return 'text-blue-600 bg-blue-50';
    if (time < 1000) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getIcon = (time: number) => {
    if (time < 100) return '⚡';
    if (time < 500) return '✓';
    if (time < 1000) return '⏱️';
    return '🐌';
  };

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-2',
  };

  return (
    <div
      className={`inline-flex items-center space-x-1 rounded-full ${getColor(responseTime)} ${sizeClasses[size]}`}
      title={`Response time: ${responseTime.toFixed(2)}ms`}
    >
      <span>{getIcon(responseTime)}</span>
      {showLabel && (
        <span className="font-medium">
          {responseTime < 1000
            ? `${responseTime.toFixed(0)}ms`
            : `${(responseTime / 1000).toFixed(2)}s`}
        </span>
      )}
    </div>
  );
}
