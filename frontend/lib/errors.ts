/**
 * Unified error handling module
 * Combines error classes, handlers, and utilities
 */

// ============================================================================
// Error Classes
// ============================================================================

/**
 * Base API error class with status code and error code
 */
export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = 'APIError';
    Object.setPrototypeOf(this, APIError.prototype);
  }

  /**
   * Create APIError from fetch Response
   */
  static async fromResponse(response: Response): Promise<APIError> {
    let data: any = {};
    
    try {
      data = await response.json();
    } catch {
      data = { message: response.statusText };
    }

    return new APIError(
      data.message || data.detail || 'Request failed',
      response.status,
      data.error || data.error_code,
      data.details
    );
  }

  static isAPIError(error: unknown): error is APIError {
    return error instanceof APIError;
  }

  is(errorCode: string): boolean {
    return this.code === errorCode;
  }

  isAuthError(): boolean {
    return this.status === 401 || this.code === 'AuthenticationException';
  }

  isAuthorizationError(): boolean {
    return this.status === 403 || this.code === 'AuthorizationException';
  }

  isValidationError(): boolean {
    return this.status === 422 || this.code === 'ValidationException';
  }

  isRateLimitError(): boolean {
    return this.status === 429 || this.code === 'RateLimitException';
  }

  isNotFoundError(): boolean {
    return this.status === 404 || this.code === 'NOT_FOUND';
  }
}

/**
 * Validation error (400)
 */
export class ValidationError extends APIError {
  constructor(message: string, details?: any) {
    super(message, 400, 'VALIDATION_ERROR', details);
    this.name = 'ValidationError';
    Object.setPrototypeOf(this, ValidationError.prototype);
  }
}

/**
 * Authentication error (401)
 */
export class AuthenticationError extends APIError {
  constructor(message: string = 'Authentication required') {
    super(message, 401, 'AUTHENTICATION_ERROR');
    this.name = 'AuthenticationError';
    Object.setPrototypeOf(this, AuthenticationError.prototype);
  }
}

/**
 * Authorization error (403)
 */
export class AuthorizationError extends APIError {
  constructor(message: string = 'Permission denied') {
    super(message, 403, 'AUTHORIZATION_ERROR');
    this.name = 'AuthorizationError';
    Object.setPrototypeOf(this, AuthorizationError.prototype);
  }
}

/**
 * Not found error (404)
 */
export class NotFoundError extends APIError {
  constructor(resource: string) {
    super(`${resource} not found`, 404, 'NOT_FOUND');
    this.name = 'NotFoundError';
    Object.setPrototypeOf(this, NotFoundError.prototype);
  }
}

/**
 * Network error (connection issues)
 */
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

/**
 * Timeout error
 */
export class TimeoutError extends Error {
  constructor(message: string = 'Request timeout') {
    super(message);
    this.name = 'TimeoutError';
    Object.setPrototypeOf(this, TimeoutError.prototype);
  }
}

// ============================================================================
// Error Messages
// ============================================================================

const ERROR_MESSAGES: Record<string, string> = {
  // Authentication & Authorization
  'AuthenticationException': 'Please log in to continue.',
  'AUTHENTICATION_ERROR': 'Please log in to continue.',
  'AuthorizationException': 'You do not have permission to perform this action.',
  'AUTHORIZATION_ERROR': 'You do not have permission to perform this action.',
  
  // Validation
  'ValidationException': 'Please check your input and try again.',
  'VALIDATION_ERROR': 'Please check your input and try again.',
  
  // Resource
  'ResourceNotFoundException': 'The requested resource was not found.',
  'NOT_FOUND': 'The requested resource was not found.',
  
  // Quota & Limits
  'QuotaExceededException': 'You have reached your usage limit. Please upgrade your plan.',
  'RateLimitException': 'Too many requests. Please try again in a few moments.',
  
  // Processing
  'ProcessingException': 'Failed to process your request. Please try again.',
  
  // External Services
  'ExternalServiceException': 'An external service is temporarily unavailable. Please try again later.',
  
  // Network
  'NetworkError': 'Network connection failed. Please check your internet connection.',
  
  // Default
  'default': 'Something went wrong. Please try again.',
};

// ============================================================================
// Error Utilities
// ============================================================================

/**
 * Get user-friendly error message from error code
 */
export function getUserFriendlyMessage(errorCode?: string): string {
  if (!errorCode) return ERROR_MESSAGES.default;
  return ERROR_MESSAGES[errorCode as keyof typeof ERROR_MESSAGES] || ERROR_MESSAGES.default;
}

/**
 * Extract detailed error message from various error formats
 */
export function getErrorMessage(error: unknown): string {
  if (!error) return 'An unknown error occurred';
  
  if (error instanceof APIError) {
    if (error.details?.detail) {
      if (typeof error.details.detail === 'string') {
        return error.details.detail;
      }
      if (Array.isArray(error.details.detail)) {
        return error.details.detail
          .map((e: any) => `${e.loc?.join('.')}: ${e.msg}`)
          .join('; ');
      }
      return JSON.stringify(error.details.detail);
    }
    return error.message;
  }
  
  if (typeof error === 'object' && error !== null) {
    const err = error as any;
    if (err.details?.detail) {
      return typeof err.details.detail === 'string' 
        ? err.details.detail 
        : JSON.stringify(err.details.detail);
    }
    if (err.detail) {
      return typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail);
    }
    if (err.message) return err.message;
  }
  
  if (error instanceof Error) return error.message;
  if (typeof error === 'string') return error;
  
  return 'An unexpected error occurred';
}

/**
 * Check if error is retryable
 */
export function isRetryableError(error: unknown): boolean {
  if (APIError.isAPIError(error)) {
    return error.status >= 500 || error.isRateLimitError();
  }
  if (NetworkError.isNetworkError(error)) {
    return true;
  }
  return false;
}

/**
 * Get retry delay based on error type and attempt
 */
export function getRetryDelay(error: unknown, attempt: number): number {
  const baseDelay = 1000;
  const maxDelay = 30000;
  
  if (APIError.isAPIError(error) && error.isRateLimitError()) {
    return Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
  }
  
  return Math.min(baseDelay * attempt, maxDelay);
}

// ============================================================================
// Error Handler
// ============================================================================

export interface ErrorInfo {
  title: string;
  description: string;
  variant: 'default' | 'destructive';
  canRetry?: boolean;
}

/**
 * Error handler utility class
 */
export class ErrorHandler {
  static handle(error: unknown): ErrorInfo {
    if (APIError.isAPIError(error)) {
      if (error instanceof ValidationError) {
        return {
          title: 'Validation Error',
          description: getErrorMessage(error),
          variant: 'destructive',
          canRetry: false,
        };
      }
      
      if (error instanceof AuthenticationError || error.isAuthError()) {
        return {
          title: 'Authentication Required',
          description: 'Please log in to continue',
          variant: 'destructive',
          canRetry: false,
        };
      }
      
      if (error instanceof AuthorizationError || error.isAuthorizationError()) {
        return {
          title: 'Permission Denied',
          description: error.message,
          variant: 'destructive',
          canRetry: false,
        };
      }
      
      if (error instanceof NotFoundError || error.isNotFoundError()) {
        return {
          title: 'Not Found',
          description: error.message,
          variant: 'destructive',
          canRetry: false,
        };
      }
      
      return {
        title: `Error${error.status ? ` (${error.status})` : ''}`,
        description: getErrorMessage(error),
        variant: 'destructive',
        canRetry: isRetryableError(error),
      };
    }
    
    if (NetworkError.isNetworkError(error)) {
      return {
        title: 'Network Error',
        description: 'Please check your connection and try again',
        variant: 'destructive',
        canRetry: true,
      };
    }
    
    if (error instanceof TimeoutError) {
      return {
        title: 'Request Timeout',
        description: 'The request took too long. Please try again',
        variant: 'destructive',
        canRetry: true,
      };
    }
    
    return {
      title: 'Error',
      description: getErrorMessage(error),
      variant: 'destructive',
      canRetry: false,
    };
  }

  static log(error: unknown, context?: string) {
    const timestamp = new Date().toISOString();
    const contextStr = context ? `[${context}]` : '';
    
    console.error(`${timestamp} ${contextStr}`, error);
    
    if (process.env.NODE_ENV === 'production') {
      // TODO: Send to Sentry, LogRocket, etc.
    }
  }
}

// ============================================================================
// Retry Utility
// ============================================================================

/**
 * Retry utility for failed requests with exponential backoff
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
    shouldRetry = isRetryableError,
  } = options;

  let lastError: unknown;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      if (!shouldRetry(error)) {
        throw error;
      }

      if (attempt < maxRetries - 1) {
        const waitTime = delay * Math.pow(backoff, attempt);
        await new Promise((resolve) => setTimeout(resolve, waitTime));
      }
    }
  }

  throw lastError;
}

/**
 * Log error for debugging
 */
export function logError(error: unknown, context?: Record<string, any>): void {
  if (process.env.NODE_ENV === 'development') {
    console.error('Error occurred:', error);
    if (context) {
      console.error('Context:', context);
    }
  }
}
