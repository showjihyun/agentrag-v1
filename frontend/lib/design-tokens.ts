/**
 * Design Tokens for Agentic RAG System
 * Centralized design system for consistent UI/UX
 */

// ============================================
// Colors
// ============================================
export const colors = {
  // Primary (Blue)
  primary: {
    50: 'bg-blue-50 dark:bg-blue-900/20',
    100: 'bg-blue-100 dark:bg-blue-900/30',
    500: 'bg-blue-500',
    600: 'bg-blue-600',
    700: 'bg-blue-700',
    800: 'bg-blue-800',
  },
  
  // Success (Green)
  success: {
    50: 'bg-green-50 dark:bg-green-900/20',
    100: 'bg-green-100 dark:bg-green-900/30',
    600: 'bg-green-600',
    700: 'bg-green-700',
  },
  
  // Error (Red)
  error: {
    50: 'bg-red-50 dark:bg-red-900/20',
    100: 'bg-red-100 dark:bg-red-900/30',
    600: 'bg-red-600',
    700: 'bg-red-700',
  },
  
  // Warning (Yellow/Orange)
  warning: {
    50: 'bg-yellow-50 dark:bg-yellow-900/20',
    100: 'bg-yellow-100 dark:bg-yellow-900/30',
    600: 'bg-yellow-600',
    700: 'bg-yellow-700',
  },
  
  // Neutral (Gray)
  neutral: {
    50: 'bg-gray-50 dark:bg-gray-900',
    100: 'bg-gray-100 dark:bg-gray-800',
    200: 'bg-gray-200 dark:bg-gray-700',
    300: 'bg-gray-300 dark:bg-gray-600',
    700: 'bg-gray-700 dark:bg-gray-300',
    800: 'bg-gray-800 dark:bg-gray-200',
    900: 'bg-gray-900 dark:bg-gray-100',
  },
};

// ============================================
// Spacing
// ============================================
export const spacing = {
  xs: '0.25rem',    // 4px
  sm: '0.5rem',     // 8px
  md: '1rem',       // 16px
  lg: '1.5rem',     // 24px
  xl: '2rem',       // 32px
  '2xl': '3rem',    // 48px
  '3xl': '4rem',    // 64px
};

// ============================================
// Border Radius
// ============================================
export const borderRadius = {
  none: 'rounded-none',
  sm: 'rounded',           // 4px
  md: 'rounded-lg',        // 8px
  lg: 'rounded-xl',        // 12px
  xl: 'rounded-2xl',       // 16px
  full: 'rounded-full',    // 9999px
};

// ============================================
// Typography
// ============================================
export const typography = {
  // Font Sizes
  fontSize: {
    xs: 'text-xs',      // 12px
    sm: 'text-sm',      // 14px
    base: 'text-base',  // 16px
    lg: 'text-lg',      // 18px
    xl: 'text-xl',      // 20px
    '2xl': 'text-2xl',  // 24px
    '3xl': 'text-3xl',  // 30px
  },
  
  // Font Weights
  fontWeight: {
    normal: 'font-normal',      // 400
    medium: 'font-medium',      // 500
    semibold: 'font-semibold',  // 600
    bold: 'font-bold',          // 700
  },
  
  // Line Heights
  lineHeight: {
    tight: 'leading-tight',
    normal: 'leading-normal',
    relaxed: 'leading-relaxed',
  },
};

// ============================================
// Shadows
// ============================================
export const shadows = {
  sm: 'shadow-sm',
  md: 'shadow-md',
  lg: 'shadow-lg',
  xl: 'shadow-xl',
  '2xl': 'shadow-2xl',
  none: 'shadow-none',
};

// ============================================
// Transitions
// ============================================
export const transitions = {
  fast: 'transition-all duration-150',
  normal: 'transition-all duration-200',
  slow: 'transition-all duration-300',
  colors: 'transition-colors duration-200',
};

// ============================================
// Z-Index
// ============================================
export const zIndex = {
  base: 'z-0',
  dropdown: 'z-10',
  sticky: 'z-20',
  fixed: 'z-30',
  modalBackdrop: 'z-40',
  modal: 'z-50',
  popover: 'z-60',
  tooltip: 'z-70',
};

// ============================================
// Component Variants
// ============================================
export const buttonVariants = {
  primary: 'bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white',
  secondary: 'bg-gray-200 hover:bg-gray-300 active:bg-gray-400 dark:bg-gray-700 dark:hover:bg-gray-600 dark:active:bg-gray-500 text-gray-900 dark:text-gray-100',
  danger: 'bg-red-600 hover:bg-red-700 active:bg-red-800 text-white',
  ghost: 'bg-transparent hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300',
  success: 'bg-green-600 hover:bg-green-700 active:bg-green-800 text-white',
};

export const badgeVariants = {
  primary: 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300',
  success: 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300',
  error: 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300',
  warning: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300',
  neutral: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300',
};

export const inputVariants = {
  default: 'border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500',
  error: 'border border-red-300 dark:border-red-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-red-500',
};

// ============================================
// Layout
// ============================================
export const layout = {
  container: 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8',
  card: 'bg-white dark:bg-gray-800 rounded-lg shadow-md p-6',
  section: 'py-8 space-y-6',
};

// ============================================
// Breakpoints (for reference)
// ============================================
export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
};

// ============================================
// Animation
// ============================================
export const animations = {
  spin: 'animate-spin',
  ping: 'animate-ping',
  pulse: 'animate-pulse',
  bounce: 'animate-bounce',
};

// ============================================
// Focus States
// ============================================
export const focusStates = {
  default: 'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
  error: 'focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2',
  success: 'focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2',
};
