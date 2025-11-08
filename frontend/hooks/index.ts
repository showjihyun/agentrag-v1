/**
 * Custom Hooks Library
 * 
 * Centralized export for all custom hooks
 */

// State Management
export { useToggle } from './useToggle';
export { useAsync } from './useAsync';
export { useLocalStorage } from './useLocalStorage';
export { usePrevious } from './usePrevious';

// Performance
export { useDebounce } from './useDebounce';

// UI & Interaction
export { useMediaQuery, useIsMobile, useIsTablet, useIsDesktop } from './useMediaQuery';
export { useOnClickOutside } from './useOnClickOutside';
export { useKeyPress } from './useKeyPress';
export { useWindowSize } from './useWindowSize';
export { useIntersectionObserver } from './useIntersectionObserver';

// Notifications
export { useToast } from './use-toast';
