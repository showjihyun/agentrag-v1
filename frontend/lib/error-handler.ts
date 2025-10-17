/**
 * Error handling utilities for the frontend.
 * 
 * Provides standardized error handling with user-friendly messages
 * and proper error classification.
 */

/**
 * Custom API error class with status code and error code.
 */
export class APIError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public errorCode?: string,
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = 'APIError';
    
    // Maintains proper stack trace for where our error was thrown (only available on V8)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, APIError);
    }
  }

  /**
   * Create APIError from fetch Response.
   */
  static async fromResponse(response: Response): Promise<APIError> {
    let data: any = {};
    
    try {
      data = await response.json();
    } catch {
      // If response is not JSON, use status text
      data = { message: response.statusText };
    }

    return new APIError(
      data.message || data.detail || 'Request failed',
      response.status,
      data.error || data.error_code,
      data.details
    );
  }

  /**
   * Check if error is a specific type.
   */
  is(errorCode: string): boolean {
    return this.errorCode === errorCode;
  }

  /**
   * Check if error is authentication related.
   */
  isAuthError(): boolean {
    return this.statusCode === 401 || this.errorCode === 'AuthenticationException';
  }

  /**
   * Check if error is authorization related.
   */
  isAuthorizationError(): boolean {
    return this.statusCode === 403 || this.errorCode === 'AuthorizationException';
  }

  /**
   * Check if error is validation related.
   */
  isValidationError(): boolean {
    return this.statusCode === 422 || this.errorCode === 'ValidationException';
  }

  /**
   * Check if error is rate limit related.
   */
  isRateLimitError(): boolean {
    return this.statusCode === 429 || this.errorCode === 'RateLimitException';
  }
}

/**
 * Network error class.
 */
export class NetworkError extends Error {
  constructor(message: string = 'Network error occurred') {
    super(message);
    this.name = 'NetworkError';
  }
}

/**
 * Error information for display.
 */
export interface ErrorInfo {
  message: string;
  statusCode?: number;
  errorCode?: string;
  userMessage: string;
  canRetry: boolean;
}

/**
 * User-friendly error messages mapping.
 */
const ERROR_MESSAGES: Record<string, string> = {
  // Authentication & Authorization
  'AuthenticationException': 'Please log in to continue.',
  'AuthorizationException': 'You do not have permission to perform this action.',
  
  // Validation
  'ValidationException': 'Please check your input and try again.',
  
  // Resource
  'ResourceNotFoundException': 'The requested resource was not found.',
  
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

/**
 * Get user-friendly error message.
 */
export function getUserFriendlyMessage(errorCode?: string): string {
  if (!errorCode) {
    return ERROR_MESSAGES.default;
  }
  
  return ERROR_MESSAGES[errorCode] || ERROR_MESSAGES.default;
}

/**
 * Handle API error and return error information.
 */
export function handleAPIError(error: unknown): ErrorInfo {
  // APIError
  if (error instanceof APIError) {
    return {
      message: error.message,
      statusCode: error.statusCode,
      errorCode: error.errorCode,
      userMessage: getUserFriendlyMessage(error.errorCode),
      canRetry: error.statusCode >= 500 || error.isRateLimitError(),
    };
  }
  
  // NetworkError
  if (error instanceof NetworkError) {
    return {
      message: error.message,
      userMessage: ERROR_MESSAGES.NetworkError,
      canRetry: true,
    };
  }
  
  // Standard Error
  if (error instanceof Error) {
    return {
      message: error.message,
      userMessage: ERROR_MESSAGES.default,
      canRetry: false,
    };
  }
  
  // Unknown error
  return {
    message: 'Unknown error',
    userMessage: ERROR_MESSAGES.default,
    canRetry: false,
  };
}

/**
 * Check if error is retryable.
 */
export function isRetryableError(error: unknown): boolean {
  if (error instanceof APIError) {
    // Retry on server errors (5xx) or rate limit
    return error.statusCode >= 500 || error.isRateLimitError();
  }
  
  if (error instanceof NetworkError) {
    return true;
  }
  
  return false;
}

/**
 * Get retry delay based on error type.
 */
export function getRetryDelay(error: unknown, attempt: number): number {
  const baseDelay = 1000; // 1 second
  const maxDelay = 30000; // 30 seconds
  
  if (error instanceof APIError && error.isRateLimitError()) {
    // Exponential backoff for rate limit errors
    return Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
  }
  
  // Linear backoff for other errors
  return Math.min(baseDelay * attempt, maxDelay);
}

/**
 * Log error for debugging (can be extended to send to error tracking service).
 */
export function logError(error: unknown, context?: Record<string, any>): void {
  if (process.env.NODE_ENV === 'development') {
    console.error('Error occurred:', error);
    if (context) {
      console.error('Context:', context);
    }
  }
  
  // TODO: Send to error tracking service (e.g., Sentry)
  // if (process.env.NODE_ENV === 'production') {
  //   Sentry.captureException(error, { extra: context });
  // }
}
