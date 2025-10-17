/**
 * Tests for authentication utilities.
 * 
 * Note: To run these tests, install @types/jest:
 * npm install --save-dev @types/jest
 * 
 * Then run: npm test -- auth.test.ts
 */

/// <reference types="jest" />

import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { it } from 'node:test';
import { describe } from 'node:test';
import { beforeEach } from 'node:test';
import { describe } from 'node:test';
import {
  setTokens,
  getAccessToken,
  getRefreshToken,
  clearTokens,
  isTokenExpired,
} from '../auth';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
});

describe('Auth Utilities', () => {
  beforeEach(() => {
    localStorageMock.clear();
  });

  describe('setTokens', () => {
    it('should store access and refresh tokens', () => {
      setTokens('access123', 'refresh456');
      expect(localStorageMock.getItem('access_token')).toBe('access123');
      expect(localStorageMock.getItem('refresh_token')).toBe('refresh456');
    });
  });

  describe('getAccessToken', () => {
    it('should retrieve access token', () => {
      localStorageMock.setItem('access_token', 'access123');
      expect(getAccessToken()).toBe('access123');
    });

    it('should return null if no token exists', () => {
      expect(getAccessToken()).toBeNull();
    });
  });

  describe('getRefreshToken', () => {
    it('should retrieve refresh token', () => {
      localStorageMock.setItem('refresh_token', 'refresh456');
      expect(getRefreshToken()).toBe('refresh456');
    });

    it('should return null if no token exists', () => {
      expect(getRefreshToken()).toBeNull();
    });
  });

  describe('clearTokens', () => {
    it('should remove all tokens', () => {
      localStorageMock.setItem('access_token', 'access123');
      localStorageMock.setItem('refresh_token', 'refresh456');
      
      clearTokens();
      
      expect(getAccessToken()).toBeNull();
      expect(getRefreshToken()).toBeNull();
    });
  });

  describe('isTokenExpired', () => {
    it('should return false for valid non-expired token', () => {
      // Create a token that expires in 1 hour
      const futureExp = Math.floor(Date.now() / 1000) + 3600;
      const token = createMockJWT({ exp: futureExp });
      
      expect(isTokenExpired(token)).toBe(false);
    });

    it('should return true for expired token', () => {
      // Create a token that expired 1 hour ago
      const pastExp = Math.floor(Date.now() / 1000) - 3600;
      const token = createMockJWT({ exp: pastExp });
      
      expect(isTokenExpired(token)).toBe(true);
    });

    it('should return true for token without exp claim', () => {
      const token = createMockJWT({ sub: 'user123' });
      expect(isTokenExpired(token)).toBe(true);
    });

    it('should return true for invalid token', () => {
      expect(isTokenExpired('invalid.token')).toBe(true);
      expect(isTokenExpired('not-a-jwt')).toBe(true);
    });
  });
});

/**
 * Helper function to create a mock JWT token for testing.
 */
function createMockJWT(payload: Record<string, any>): string {
  const header = { alg: 'HS256', typ: 'JWT' };
  
  const base64UrlEncode = (obj: any) => {
    const json = JSON.stringify(obj);
    return btoa(json)
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  };
  
  const encodedHeader = base64UrlEncode(header);
  const encodedPayload = base64UrlEncode(payload);
  const signature = 'mock-signature';
  
  return `${encodedHeader}.${encodedPayload}.${signature}`;
}
