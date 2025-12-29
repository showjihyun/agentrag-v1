// Enhanced error handling utilities

export class MonitoringError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly context?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'MonitoringError';
  }
}

export class SSEConnectionError extends MonitoringError {
  constructor(message: string, context?: Record<string, unknown>) {
    super(message, 'SSE_CONNECTION_ERROR', context);
    this.name = 'SSEConnectionError';
  }
}

export function handleSSEError(error: Event): void {
  console.error('SSE connection error:', error);
  // Add telemetry or error reporting here
}

export function parseSSEData<T>(data: string): T {
  try {
    return JSON.parse(data) as T;
  } catch (error) {
    throw new MonitoringError(
      'Failed to parse SSE data',
      'SSE_PARSE_ERROR',
      { originalData: data, error }
    );
  }
}

export function validateSSEEventType(type: string): boolean {
  const validTypes = [
    'log',
    'agent_status',
    'metrics',
    'system_metrics',
    'prediction',
    'optimization_insights',
    'execution_complete',
    'execution_failed'
  ];
  
  return validTypes.includes(type);
}