/**
 * Tests for Performance Hooks
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import {
  useDebounce,
  useThrottle,
  usePrevious,
  useIsMounted,
} from '../usePerformance';

describe('useDebounce', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('should debounce function calls', () => {
    const callback = jest.fn();
    const { result } = renderHook(() => useDebounce(callback, 300));

    // Call multiple times
    act(() => {
      result.current('test1');
      result.current('test2');
      result.current('test3');
    });

    // Should not be called yet
    expect(callback).not.toHaveBeenCalled();

    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(300);
    });

    // Should be called once with last value
    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith('test3');
  });

  it('should cancel previous timeout', () => {
    const callback = jest.fn();
    const { result } = renderHook(() => useDebounce(callback, 300));

    act(() => {
      result.current('test1');
    });

    act(() => {
      jest.advanceTimersByTime(200);
    });

    act(() => {
      result.current('test2');
    });

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith('test2');
  });
});

describe('useThrottle', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('should throttle function calls', () => {
    const callback = jest.fn();
    const { result } = renderHook(() => useThrottle(callback, 100));

    // First call should execute immediately
    act(() => {
      result.current('test1');
    });
    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith('test1');

    // Subsequent calls within limit should be ignored
    act(() => {
      result.current('test2');
      result.current('test3');
    });
    expect(callback).toHaveBeenCalledTimes(1);

    // After limit, next call should execute
    act(() => {
      jest.advanceTimersByTime(100);
      result.current('test4');
    });
    expect(callback).toHaveBeenCalledTimes(2);
    expect(callback).toHaveBeenCalledWith('test4');
  });
});

describe('usePrevious', () => {
  it('should return undefined on first render', () => {
    const { result } = renderHook(() => usePrevious('initial'));
    expect(result.current).toBeUndefined();
  });

  it('should return previous value after update', () => {
    const { result, rerender } = renderHook(
      ({ value }) => usePrevious(value),
      { initialProps: { value: 'first' } }
    );

    expect(result.current).toBeUndefined();

    rerender({ value: 'second' });
    expect(result.current).toBe('first');

    rerender({ value: 'third' });
    expect(result.current).toBe('second');
  });
});

describe('useIsMounted', () => {
  it('should return false before mount', () => {
    const { result } = renderHook(() => useIsMounted());
    // Initially false, becomes true after effect
    expect(result.current()).toBe(false);
  });

  it('should return true when mounted', async () => {
    const { result } = renderHook(() => useIsMounted());
    
    await waitFor(() => {
      expect(result.current()).toBe(true);
    });
  });

  it('should return false after unmount', async () => {
    const { result, unmount } = renderHook(() => useIsMounted());
    
    await waitFor(() => {
      expect(result.current()).toBe(true);
    });

    unmount();
    expect(result.current()).toBe(false);
  });
});
