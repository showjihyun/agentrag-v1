/**
 * Type Guards for Runtime Type Checking
 * 
 * Provides type-safe runtime validation for API responses and data structures
 */

import { MessageResponse, SearchResult, UserResponse, SessionResponse } from './types';

/**
 * Check if value is a valid MessageResponse
 */
export function isMessageResponse(value: unknown): value is MessageResponse {
  if (typeof value !== 'object' || value === null) {
    return false;
  }

  const msg = value as Record<string, unknown>;

  return (
    typeof msg.role === 'string' &&
    typeof msg.content === 'string' &&
    (msg.sources === undefined || Array.isArray(msg.sources))
  );
}

/**
 * Check if value is a valid SearchResult
 */
export function isSearchResult(value: unknown): value is SearchResult {
  if (typeof value !== 'object' || value === null) {
    return false;
  }

  const result = value as Record<string, unknown>;

  return (
    typeof result.document_id === 'string' &&
    typeof result.document_name === 'string' &&
    typeof result.score === 'number'
  );
}

/**
 * Check if value is a valid UserResponse
 */
export function isUserResponse(value: unknown): value is UserResponse {
  if (typeof value !== 'object' || value === null) {
    return false;
  }

  const user = value as Record<string, unknown>;

  return (
    typeof user.id === 'string' &&
    typeof user.username === 'string' &&
    typeof user.email === 'string'
  );
}

/**
 * Check if value is a valid SessionResponse
 */
export function isSessionResponse(value: unknown): value is SessionResponse {
  if (typeof value !== 'object' || value === null) {
    return false;
  }

  const session = value as Record<string, unknown>;

  return (
    typeof session.id === 'string' &&
    typeof session.user_id === 'string' &&
    typeof session.created_at === 'string'
  );
}

/**
 * Check if error is an API error with message
 */
export function isAPIError(error: unknown): error is { message: string; status?: number } {
  if (typeof error !== 'object' || error === null) {
    return false;
  }

  const err = error as Record<string, unknown>;

  return typeof err.message === 'string';
}

/**
 * Check if value is a non-null object
 */
export function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/**
 * Check if value is a non-empty string
 */
export function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

/**
 * Check if value is a valid array of specific type
 */
export function isArrayOf<T>(
  value: unknown,
  guard: (item: unknown) => item is T
): value is T[] {
  return Array.isArray(value) && value.every(guard);
}
