/**
 * @deprecated Use '@/lib/errors' instead
 * This file is kept for backward compatibility
 */

export {
  APIError,
  NetworkError,
  getUserFriendlyMessage,
  isRetryableError,
  getRetryDelay,
  logError,
  type ErrorInfo,
} from './errors';

// Re-export handleAPIError as a function that returns ErrorInfo
import { ErrorHandler, type ErrorInfo } from './errors';

export function handleAPIError(error: unknown): ErrorInfo & { message: string; userMessage: string } {
  const info = ErrorHandler.handle(error);
  return {
    ...info,
    message: info.description,
    userMessage: info.description,
    canRetry: info.canRetry ?? false,
  };
}
