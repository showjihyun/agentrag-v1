/**
 * Code splitting and lazy loading utilities
 */

import dynamic from 'next/dynamic';
import { ComponentType } from 'react';

/**
 * Lazy load component with loading fallback
 */
export function lazyLoad<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  options?: {
    loading?: ComponentType;
    ssr?: boolean;
  }
) {
  return dynamic(importFn, {
    loading: options?.loading || (() => <div>Loading...</div>),
    ssr: options?.ssr ?? true,
  });
}

/**
 * Preload component
 */
export function preloadComponent(importFn: () => Promise<any>) {
  importFn();
}

/**
 * Lazy load with retry logic
 */
export function lazyLoadWithRetry<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  retries = 3
) {
  return dynamic(
    () =>
      new Promise<{ default: T }>((resolve, reject) => {
        const attemptLoad = (attemptsLeft: number) => {
          importFn()
            .then(resolve)
            .catch((error) => {
              if (attemptsLeft === 0) {
                reject(error);
              } else {
                setTimeout(() => attemptLoad(attemptsLeft - 1), 1000);
              }
            });
        };
        attemptLoad(retries);
      }),
    { ssr: false }
  );
}
