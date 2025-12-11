/**
 * Main components barrel file
 * Provides organized exports by domain for cleaner imports
 * 
 * Usage:
 *   import { ChatInterface, MessageList } from '@/components/chat';
 *   import { DocumentUpload, DocumentViewer } from '@/components/documents';
 *   import { Button, Card, Input } from '@/components/ui';
 * 
 * Or import from specific domain:
 *   import { Header, UserMenu } from '@/components/layout';
 */

// Re-export domain modules
export * from './chat';
export * from './documents';
export * from './search';
export * from './feedback';
export * from './layout';
export * from './onboarding';
export * from './forms';
export * from './stats';
export * from './loading';

// Re-export UI primitives
export * from './ui';

// Re-export common components
export * from './common';

// Re-export error handling
export * from './error-boundary';

// Direct exports for backward compatibility with root-level imports
// These can be gradually migrated to domain-specific imports

// Core UI
export { default as Button } from './Button';
export { default as Card } from './Card';
export { default as Input } from './Input';
export { Toast, ToastProvider, useToast } from './Toast';

// Error handling
export { default as ErrorBoundary } from './ErrorBoundary';
export { default as FriendlyError } from './FriendlyError';

// PWA and monitoring
export { default as PWAInit } from './PWAInit';
export { default as MonitoringInit } from './MonitoringInit';
