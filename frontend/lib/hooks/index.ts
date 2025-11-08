/**
 * Advanced Hooks Index
 * 
 * Export all custom hooks from lib/hooks
 */

// Optimization Hooks
export { useOptimistic, useOptimisticList } from './useOptimistic';
export { useVirtualScroll, useAdvancedVirtualScroll } from './useVirtualScroll';
export { useWebWorker, useTextProcessingWorker, useSortingWorker } from './useWebWorker';
export { usePrefetch, usePrefetchOnHover, usePrefetchOnIntersection, useSmartPrefetch } from './usePrefetch';

// Chat Hooks
export { useSmartMode } from './useSmartMode';
export { useChatInput } from './useChatInput';
export { useChatSubmit } from './useChatSubmit';
export { useLoadingState } from './useLoadingState';
