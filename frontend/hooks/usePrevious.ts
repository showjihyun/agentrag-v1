/**
 * Custom hook to get previous value
 * 
 * @param value - Current value
 * @returns Previous value
 * 
 * @example
 * const prevCount = usePrevious(count);
 */

import { useEffect, useRef } from 'react';

export function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T>();

  useEffect(() => {
    ref.current = value;
  }, [value]);

  return ref.current;
}
