/**
 * Accessibility hooks for better a11y support
 */

import { useEffect, useRef, useCallback, useState } from 'react';

/**
 * Focus trap for modals and dialogs
 */
export function useFocusTrap(isActive: boolean) {
  const containerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!isActive || !containerRef.current) return;

    const container = containerRef.current;
    const focusableElements = container.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    // Focus first element
    firstElement?.focus();

    const handleTab = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement?.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement?.focus();
          e.preventDefault();
        }
      }
    };

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        // Trigger close event
        const closeButton = container.querySelector<HTMLElement>('[data-close]');
        closeButton?.click();
      }
    };

    container.addEventListener('keydown', handleTab);
    container.addEventListener('keydown', handleEscape);

    return () => {
      container.removeEventListener('keydown', handleTab);
      container.removeEventListener('keydown', handleEscape);
    };
  }, [isActive]);

  return containerRef;
}

/**
 * Announce to screen readers
 */
export function useScreenReaderAnnouncement() {
  const announce = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', priority);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;

    document.body.appendChild(announcement);

    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  }, []);

  return announce;
}

/**
 * Keyboard navigation for lists
 */
export function useKeyboardNavigation<T extends HTMLElement = HTMLElement>(
  items: T[],
  options: {
    loop?: boolean;
    onSelect?: (index: number) => void;
  } = {}
) {
  const { loop = true, onSelect } = options;
  const [activeIndex, setActiveIndex] = useState(-1);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      const { key } = e;

      if (!['ArrowUp', 'ArrowDown', 'Home', 'End', 'Enter', ' '].includes(key)) {
        return;
      }

      e.preventDefault();

      switch (key) {
        case 'ArrowDown':
          setActiveIndex((prev) => {
            const next = prev + 1;
            if (next >= items.length) {
              return loop ? 0 : prev;
            }
            return next;
          });
          break;

        case 'ArrowUp':
          setActiveIndex((prev) => {
            const next = prev - 1;
            if (next < 0) {
              return loop ? items.length - 1 : 0;
            }
            return next;
          });
          break;

        case 'Home':
          setActiveIndex(0);
          break;

        case 'End':
          setActiveIndex(items.length - 1);
          break;

        case 'Enter':
        case ' ':
          if (activeIndex >= 0) {
            onSelect?.(activeIndex);
          }
          break;
      }
    },
    [items.length, loop, activeIndex, onSelect]
  );

  useEffect(() => {
    if (activeIndex >= 0 && activeIndex < items.length) {
      items[activeIndex]?.focus();
    }
  }, [activeIndex, items]);

  return {
    activeIndex,
    setActiveIndex,
    handleKeyDown,
  };
}

/**
 * Skip to content link
 */
export function useSkipToContent() {
  const skipToMain = useCallback(() => {
    const main = document.getElementById('main-content');
    if (main) {
      main.focus();
      main.scrollIntoView({ behavior: 'smooth' });
    }
  }, []);

  return skipToMain;
}

/**
 * Reduced motion preference
 */
export function useReducedMotion() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return prefersReducedMotion;
}

/**
 * ARIA live region for dynamic content
 */
export function useAriaLiveRegion() {
  const regionRef = useRef<HTMLDivElement>(null);

  const announce = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    if (regionRef.current) {
      regionRef.current.setAttribute('aria-live', priority);
      regionRef.current.textContent = message;

      // Clear after announcement
      setTimeout(() => {
        if (regionRef.current) {
          regionRef.current.textContent = '';
        }
      }, 1000);
    }
  }, []);

  return { regionRef, announce };
}

/**
 * Focus management for route changes
 */
export function useRouteFocus() {
  useEffect(() => {
    // Focus main content on route change
    const main = document.getElementById('main-content');
    if (main) {
      main.focus();
    }
  }, []);
}

/**
 * Keyboard shortcuts
 */
export function useKeyboardShortcuts(
  shortcuts: Record<string, (e: KeyboardEvent) => void>
) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const key = [
        e.ctrlKey && 'ctrl',
        e.shiftKey && 'shift',
        e.altKey && 'alt',
        e.metaKey && 'meta',
        e.key.toLowerCase(),
      ]
        .filter(Boolean)
        .join('+');

      const handler = shortcuts[key];
      if (handler) {
        e.preventDefault();
        handler(e);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);
}

/**
 * Form field error announcement
 */
export function useFormErrorAnnouncement() {
  const announce = useScreenReaderAnnouncement();

  const announceError = useCallback(
    (fieldName: string, errorMessage: string) => {
      announce(`${fieldName}: ${errorMessage}`, 'assertive');
    },
    [announce]
  );

  const announceSuccess = useCallback(
    (message: string) => {
      announce(message, 'polite');
    },
    [announce]
  );

  return { announceError, announceSuccess };
}
