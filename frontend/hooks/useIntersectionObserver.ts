/**
 * Custom hook for Intersection Observer API
 * 
 * @param ref - Element ref to observe
 * @param options - IntersectionObserver options
 * @returns Boolean indicating if element is intersecting
 * 
 * @example
 * const ref = useRef(null);
 * const isVisible = useIntersectionObserver(ref, { threshold: 0.5 });
 */

import { RefObject, useEffect, useState } from 'react';

interface UseIntersectionObserverOptions extends IntersectionObserverInit {
  freezeOnceVisible?: boolean;
}

export function useIntersectionObserver(
  ref: RefObject<Element>,
  options: UseIntersectionObserverOptions = {}
): boolean {
  const { threshold = 0, root = null, rootMargin = '0px', freezeOnceVisible = false } = options;

  const [isIntersecting, setIsIntersecting] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    // If already visible and freeze is enabled, don't observe
    if (freezeOnceVisible && isIntersecting) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsIntersecting(entry.isIntersecting);
      },
      { threshold, root, rootMargin }
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [ref, threshold, root, rootMargin, freezeOnceVisible, isIntersecting]);

  return isIntersecting;
}
