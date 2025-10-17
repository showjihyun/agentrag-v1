/**
 * Authentication utilities for token management and JWT handling.
 * Provides functions for storing, retrieving, and validating JWT tokens.
 */

const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

/**
 * Store authentication tokens in localStorage.
 * @param accessToken - JWT access token
 * @param refreshToken - JWT refresh token
 */
export function setTokens(accessToken: string, refreshToken: string): void {
  if (typeof window === 'undefined') {
    return; // Skip on server-side rendering
  }
  
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

/**
 * Retrieve the access token from localStorage.
 * @returns The access token or null if not found
 */
export function getAccessToken(): string | null {
  if (typeof window === 'undefined') {
    return null; // Skip on server-side rendering
  }
  
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

/**
 * Retrieve the refresh token from localStorage.
 * @returns The refresh token or null if not found
 */
export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') {
    return null; // Skip on server-side rendering
  }
  
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Remove all authentication tokens from localStorage.
 */
export function clearTokens(): void {
  if (typeof window === 'undefined') {
    return; // Skip on server-side rendering
  }
  
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/**
 * Decode a JWT token payload without verification.
 * @param token - JWT token string
 * @returns Decoded payload or null if invalid
 */
function decodeJWT(token: string): Record<string, any> | null {
  try {
    // JWT format: header.payload.signature
    const parts = token.split('.');
    if (parts.length !== 3) {
      return null;
    }
    
    // Decode the payload (second part)
    const payload = parts[1];
    
    // Base64 URL decode
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Failed to decode JWT:', error);
    return null;
  }
}

/**
 * Check if a JWT token is expired.
 * @param token - JWT token string
 * @returns true if token is expired or invalid, false otherwise
 */
export function isTokenExpired(token: string): boolean {
  const payload = decodeJWT(token);
  
  if (!payload || !payload.exp) {
    return true; // Invalid token or no expiration
  }
  
  // JWT exp is in seconds, Date.now() is in milliseconds
  const expirationTime = payload.exp * 1000;
  const currentTime = Date.now();
  
  return currentTime >= expirationTime;
}
