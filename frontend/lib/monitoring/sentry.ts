/**
 * Sentry error tracking integration
 */

import * as Sentry from '@sentry/nextjs';

export function initSentry() {
  if (process.env.NODE_ENV !== 'production') {
    console.log('[Sentry] Skipping initialization in development');
    return;
  }

  const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
  if (!dsn) {
    console.warn('[Sentry] DSN not configured');
    return;
  }

  Sentry.init({
    dsn,
    environment: process.env.NEXT_PUBLIC_ENV || 'production',
    
    // Performance Monitoring
    tracesSampleRate: 0.1, // 10% of transactions
    
    // Session Replay
    replaysSessionSampleRate: 0.1, // 10% of sessions
    replaysOnErrorSampleRate: 1.0, // 100% of sessions with errors
    
    // Error filtering
    beforeSend(event, hint) {
      // Filter out certain errors
      const error = hint.originalException;
      
      if (error instanceof Error) {
        // Ignore network errors in development
        if (error.message.includes('NetworkError') && process.env.NODE_ENV === 'development') {
          return null;
        }
        
        // Ignore cancelled requests
        if (error.message.includes('AbortError') || error.message.includes('cancelled')) {
          return null;
        }
      }
      
      return event;
    },
    
    // Integrations - Sentry v8 uses different API
    integrations: [
      Sentry.browserTracingIntegration({
        tracePropagationTargets: [
          'localhost',
          /^https:\/\/[^/]*\.yourdomain\.com/,
        ],
      }),
      Sentry.replayIntegration({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],
  });

  console.log('[Sentry] Initialized successfully');
}

/**
 * Capture exception with context
 */
export function captureException(
  error: Error,
  context?: {
    tags?: Record<string, string>;
    extra?: Record<string, any>;
    level?: Sentry.SeverityLevel;
  }
) {
  if (process.env.NODE_ENV !== 'production') {
    console.error('[Sentry] Would capture:', error, context);
    return;
  }

  Sentry.withScope((scope) => {
    if (context?.tags) {
      Object.entries(context.tags).forEach(([key, value]) => {
        scope.setTag(key, value);
      });
    }
    
    if (context?.extra) {
      Object.entries(context.extra).forEach(([key, value]) => {
        scope.setExtra(key, value);
      });
    }
    
    if (context?.level) {
      scope.setLevel(context.level);
    }
    
    Sentry.captureException(error);
  });
}

/**
 * Capture message
 */
export function captureMessage(
  message: string,
  level: Sentry.SeverityLevel = 'info'
) {
  if (process.env.NODE_ENV !== 'production') {
    console.log('[Sentry] Would capture message:', message, level);
    return;
  }

  Sentry.captureMessage(message, level);
}

/**
 * Set user context
 */
export function setUser(user: {
  id: string;
  email?: string;
  username?: string;
}) {
  Sentry.setUser(user);
}

/**
 * Clear user context
 */
export function clearUser() {
  Sentry.setUser(null);
}

/**
 * Add breadcrumb
 */
export function addBreadcrumb(
  message: string,
  data?: Record<string, any>,
  category?: string
) {
  Sentry.addBreadcrumb({
    message,
    data,
    category: category || 'custom',
    level: 'info',
  });
}

/**
 * Start transaction for performance monitoring
 * Note: Using startSpan for Sentry v8 compatibility
 */
export function startTransaction(
  name: string,
  op: string
): any {
  if (process.env.NODE_ENV !== 'production') {
    return undefined;
  }

  // Use startSpan for Sentry v8+
  if (typeof Sentry.startSpan === 'function') {
    return Sentry.startSpan({ name, op }, (span) => span);
  }
  
  // Fallback for older versions
  return undefined;
}

/**
 * Agent Builder specific error tracking
 */
export const AgentBuilderMonitoring = {
  // Agent operations
  agentCreated: (agentId: string, agentType: string) => {
    addBreadcrumb('Agent created', { agentId, agentType }, 'agent');
  },
  
  agentExecutionStarted: (agentId: string, executionId: string) => {
    addBreadcrumb('Agent execution started', { agentId, executionId }, 'execution');
  },
  
  agentExecutionCompleted: (executionId: string, duration: number) => {
    addBreadcrumb('Agent execution completed', { executionId, duration }, 'execution');
  },
  
  agentExecutionFailed: (executionId: string, error: Error) => {
    captureException(error, {
      tags: { component: 'agent-execution', executionId },
      level: 'error',
    });
  },
  
  // Block operations
  blockCreated: (blockId: string, blockType: string) => {
    addBreadcrumb('Block created', { blockId, blockType }, 'block');
  },
  
  blockTestFailed: (blockId: string, error: Error) => {
    captureException(error, {
      tags: { component: 'block-test', blockId },
      level: 'warning',
    });
  },
  
  // Workflow operations
  workflowExecutionStarted: (workflowId: string) => {
    addBreadcrumb('Workflow execution started', { workflowId }, 'workflow');
  },
  
  workflowExecutionFailed: (workflowId: string, error: Error) => {
    captureException(error, {
      tags: { component: 'workflow-execution', workflowId },
      level: 'error',
    });
  },
  
  // API errors
  apiError: (endpoint: string, status: number, error: Error) => {
    captureException(error, {
      tags: { 
        component: 'api',
        endpoint,
        status: status.toString(),
      },
      level: status >= 500 ? 'error' : 'warning',
    });
  },
};
