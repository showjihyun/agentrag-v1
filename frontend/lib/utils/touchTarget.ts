/**
 * Touch Target Utilities
 * Ensures minimum touch target sizes for mobile accessibility
 */

export const TOUCH_TARGET_MIN_SIZE = 44; // 44x44px minimum (WCAG 2.1 AAA)

/**
 * Get touch-friendly button classes
 */
export function getTouchButtonClasses(size: 'sm' | 'md' | 'lg' = 'md') {
  const baseClasses = 'inline-flex items-center justify-center transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const sizeClasses = {
    sm: 'min-w-[44px] min-h-[44px] px-3 py-2 text-sm',
    md: 'min-w-[48px] min-h-[48px] px-4 py-3 text-base',
    lg: 'min-w-[52px] min-h-[52px] px-6 py-4 text-lg',
  };
  
  return `${baseClasses} ${sizeClasses[size]}`;
}

/**
 * Get touch-friendly icon button classes
 */
export function getTouchIconButtonClasses(size: 'sm' | 'md' | 'lg' = 'md') {
  const baseClasses = 'inline-flex items-center justify-center rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const sizeClasses = {
    sm: 'w-[44px] h-[44px] p-2',
    md: 'w-[48px] h-[48px] p-3',
    lg: 'w-[52px] h-[52px] p-4',
  };
  
  return `${baseClasses} ${sizeClasses[size]}`;
}

/**
 * Check if device is touch-enabled
 */
export function isTouchDevice(): boolean {
  if (typeof window === 'undefined') return false;
  
  return (
    'ontouchstart' in window ||
    navigator.maxTouchPoints > 0 ||
    // @ts-ignore
    navigator.msMaxTouchPoints > 0
  );
}

/**
 * Get spacing for touch-friendly layouts
 */
export function getTouchSpacing(density: 'compact' | 'comfortable' | 'spacious' = 'comfortable') {
  const spacingMap = {
    compact: 'gap-2',
    comfortable: 'gap-3',
    spacious: 'gap-4',
  };
  
  return spacingMap[density];
}
