/**
 * Custom error classes for better error handling
 */

export class APIError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
    Object.setPrototypeOf(this, APIError.prototype);
  }

  static isAPIError(error: unknown): error is APIError {
    return error instanceof APIError;
  }
}

export class ValidationError extends APIError {
  constructor(message: string, details?: any) {
    super(400, 'VALIDATION_ERROR', message, details);
    this.name = 'ValidationError';
    Object.setPrototypeOf(this, ValidationError.prototype);
  }
}

export class AuthenticationError extends APIError {
  constructor(message: string = 'Authentication required') {
    super(401, 'AUTHENTICATION_ERROR', message);
    this.name = 'AuthenticationError';
    Object.setPrototypeOf(this, AuthenticationError.prototype);
  }
}

export class AuthorizationError extends APIError {
  constructor(message: string = 'Permission denied') {
    super(403, 'AUTHORIZATION_ERROR', message);
    this.name = 'AuthorizationError';
    Object.setPrototypeOf(this, AuthorizationError.prototype);
  }
}

export class NotFoundError extends APIError {
  constructor(resource: string) {
    super(404, 'NOT_FOUND', `${resource} not found`);
    this.name = 'NotFoundError';
    Object.setPrototypeOf(this, NotFoundError.prototype);
  }
}

export class NetworkError extends Error {
  constructor(message: string = 'Network request failed') {
    super(message);
    this.name = 'NetworkError';
    Object.setPrototypeOf(this, NetworkError.prototype);
  }

  static isNetworkError(error: unknown): error is NetworkError {
    return error instanceof NetworkError;
  }
}

export class TimeoutError extends Error {
  constructor(message: string = 'Request timeout') {
    super(message);
    this.name = 'TimeoutError';
    Object.setPrototypeOf(this, TimeoutError.prototype);
  }
}

/**
 * Error handler utility
 */
export class ErrorHandler {
  static handle(error: unknown): {
    title: string;
    description: string;
    variant: 'default' | 'destructive';
  } {
    // API Errors
    if (APIError.isAPIError(error)) {
      if (error instanceof ValidationError) {
        return {
          title: 'Validation Error',
          description: error.message,
          variant: 'destructive',
        };
      }
      
      if (error instanceof AuthenticationError) {
        return {
          title: 'Authentication Required',
          description: 'Please log in to continue',
          variant: 'destructive',
        };
      }
      
      if (error instanceof AuthorizationError) {
        return {
          title: 'Permission Denied',
          description: error.message,
          variant: 'destructive',
        };
      }
      
      if (error instanceof NotFoundError) {
        return {
          title: 'Not Found',
          description: error.message,
          variant: 'destructive',
        };
      }
      
      // Generic API error
      return {
        title: 'Error',
        description: error.message || 'An error occurred',
        variant: 'destructive',
      };
    }
    
    // Network Errors
    if (NetworkError.isNetworkError(error)) {
      return {
        title: 'Network Error',
        description: 'Please check your connection and try again',
        variant: 'destructive',
      };
    }
    
    // Timeout Errors
    if (error instanceof TimeoutError) {
      return {
        title: 'Request Timeout',
        description: 'The request took too long. Please try again',
        variant: 'destructive',
      };
    }
    
    // Generic Error
    if (error instanceof Error) {
      return {
        title: 'Error',
        description: error.message || 'An unexpected error occurred',
        variant: 'destructive',
      };
    }
    
    // Unknown error
    return {
      title: 'Error',
      description: 'An unexpected error occurred',
      variant: 'destructive',
    };
  }

  static log(error: unknown, context?: string) {
    const timestamp = new Date().toISOString();
    const contextStr = context ? `[${context}]` : '';
    
    console.error(`${timestamp} ${contextStr}`, error);
    
    // In production, send to error tracking service
    if (process.env.NODE_ENV === 'production') {
      // TODO: Send to Sentry, LogRocket, etc.
      // Sentry.captureException(error, { tags: { context } });
    }
  }
}

/**
 * Retry utility for failed requests
 */
export async function fetchWithRetry<T>(
  fn: () => Promise<T>,
  options: {
    maxRetries?: number;
    delay?: number;
    backoff?: number;
    shouldRetry?: (error: unknown) => boolean;
  } = {}
): Promise<T> {
  const {
    maxRetries = 3,
    delay = 1000,
    backoff = 2,
    shouldRetry = (error) => {
      // Don't retry client errors (4xx)
      if (APIError.isAPIError(error) && error.status >= 400 && error.status < 500) {
        return false;
      }
      return true;
    },
  } = options;

  let lastError: unknown;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Don't retry if we shouldn't
      if (!shouldRetry(error)) {
        throw error;
      }

      // Don't wait after last attempt
      if (attempt < maxRetries - 1) {
        const waitTime = delay * Math.pow(backoff, attempt);
        await new Promise((resolve) => setTimeout(resolve, waitTime));
      }
    }
  }

  throw lastError;
}
