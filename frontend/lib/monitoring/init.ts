/**
 * Initialize all monitoring and analytics
 */

import { initSentry } from './sentry';
import { analytics } from './analytics';
import { registerServiceWorker } from '../pwa/register-sw';

export function initMonitoring() {
  // Initialize Sentry for error tracking
  initSentry();

  // Initialize Analytics
  analytics.init();

  // Register Service Worker for PWA
  registerServiceWorker();

  console.log('[Monitoring] All services initialized');
}

/**
 * Track application lifecycle
 */
export function trackAppLifecycle() {
  if (typeof window === 'undefined') return;

  // Track app load
  window.addEventListener('load', () => {
    analytics.track('app_loaded', {
      load_time: performance.now(),
    });
  });

  // Track visibility changes
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      analytics.track('app_hidden');
    } else {
      analytics.track('app_visible');
    }
  });

  // Track before unload
  window.addEventListener('beforeunload', () => {
    analytics.track('app_unload');
  });

  // Track errors
  window.addEventListener('error', (event) => {
    console.error('[Global Error]', event.error);
  });

  window.addEventListener('unhandledrejection', (event) => {
    console.error('[Unhandled Rejection]', event.reason);
  });
}
