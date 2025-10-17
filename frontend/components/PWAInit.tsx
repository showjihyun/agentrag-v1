'use client';

/**
 * PWA Initialization Component
 * 
 * Registers service worker and handles PWA features
 */

import { useEffect } from 'react';
import { registerServiceWorker } from '@/lib/pwa/register-sw';

export default function PWAInit() {
  useEffect(() => {
    // Register service worker
    if (process.env.NODE_ENV === 'production') {
      registerServiceWorker();
    }

    // Handle install prompt
    let deferredPrompt: any;

    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      deferredPrompt = e;
      
      // Show install button or banner
      console.log('[PWA] Install prompt available');
    };

    const handleAppInstalled = () => {
      console.log('[PWA] App installed');
      deferredPrompt = null;
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  return null; // This component doesn't render anything
}
