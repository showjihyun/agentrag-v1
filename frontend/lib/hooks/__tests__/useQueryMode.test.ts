import { renderHook, act } from '@testing-library/react';
import { useQueryMode } from '../useQueryMode';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('useQueryMode', () => {
  beforeEach(() => {
    localStorageMock.clear();
    jest.clearAllMocks();
  });

  describe('Initial State', () => {
    it('should initialize with BALANCED mode by default', () => {
      const { result } = renderHook(() => useQueryMode());

      expect(result.current.mode).toBe('BALANCED');
      expect(result.current.isLoaded).toBe(false);
    });

    it('should load saved mode from localStorage', () => {
      localStorageMock.setItem('query-mode-preference', 'FAST');

      const { result } = renderHook(() => useQueryMode());

      // Wait for effect to run
      act(() => {
        // Effect runs automatically
      });

      expect(result.current.mode).toBe('FAST');
      expect(result.current.isLoaded).toBe(true);
    });

    it('should use default mode if localStorage is empty', () => {
      const { result } = renderHook(() => useQueryMode());

      act(() => {
        // Effect runs automatically
      });

      expect(result.current.mode).toBe('BALANCED');
      expect(result.current.isLoaded).toBe(true);
    });

    it('should ignore invalid mode values from localStorage', () => {
      localStorageMock.setItem('query-mode-preference', 'INVALID');

      const { result } = renderHook(() => useQueryMode());

      act(() => {
        // Effect runs automatically
      });

      expect(result.current.mode).toBe('BALANCED');
    });
  });

  describe('Mode Updates', () => {
    it('should update mode when setMode is called', () => {
      const { result } = renderHook(() => useQueryMode());

      act(() => {
        result.current.setMode('DEEP');
      });

      expect(result.current.mode).toBe('DEEP');
    });

    it('should save mode to localStorage when updated', () => {
      const { result } = renderHook(() => useQueryMode());

      act(() => {
        result.current.setMode('FAST');
      });

      expect(localStorageMock.getItem('query-mode-preference')).toBe('FAST');
    });

    it('should persist mode across multiple updates', () => {
      const { result } = renderHook(() => useQueryMode());

      act(() => {
        result.current.setMode('FAST');
      });

      expect(result.current.mode).toBe('FAST');
      expect(localStorageMock.getItem('query-mode-preference')).toBe('FAST');

      act(() => {
        result.current.setMode('DEEP');
      });

      expect(result.current.mode).toBe('DEEP');
      expect(localStorageMock.getItem('query-mode-preference')).toBe('DEEP');
    });
  });

  describe('Persistence Across Sessions', () => {
    it('should load previously saved mode on new hook instance', () => {
      // First hook instance
      const { result: result1 } = renderHook(() => useQueryMode());

      act(() => {
        result1.current.setMode('DEEP');
      });

      // Unmount and create new hook instance
      const { result: result2 } = renderHook(() => useQueryMode());

      act(() => {
        // Wait for effect to load from localStorage
      });

      expect(result2.current.mode).toBe('DEEP');
    });

    it('should maintain mode after page reload simulation', () => {
      localStorageMock.setItem('query-mode-preference', 'FAST');

      const { result } = renderHook(() => useQueryMode());

      act(() => {
        // Effect runs automatically
      });

      expect(result.current.mode).toBe('FAST');
    });
  });

  describe('Error Handling', () => {
    it('should handle localStorage getItem errors gracefully', () => {
      const consoleErrorSpy = jest
        .spyOn(console, 'error')
        .mockImplementation(() => {});

      jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
        throw new Error('localStorage error');
      });

      const { result } = renderHook(() => useQueryMode());

      act(() => {
        // Effect runs automatically
      });

      expect(result.current.mode).toBe('BALANCED');
      expect(result.current.isLoaded).toBe(true);
      expect(consoleErrorSpy).toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });

    it('should handle localStorage setItem errors gracefully', () => {
      const consoleErrorSpy = jest
        .spyOn(console, 'error')
        .mockImplementation(() => {});

      jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
        throw new Error('localStorage error');
      });

      const { result } = renderHook(() => useQueryMode());

      act(() => {
        result.current.setMode('FAST');
      });

      // Mode should still update in state even if localStorage fails
      expect(result.current.mode).toBe('FAST');
      expect(consoleErrorSpy).toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });
  });

  describe('isLoaded Flag', () => {
    it('should set isLoaded to true after initial load', () => {
      const { result } = renderHook(() => useQueryMode());

      expect(result.current.isLoaded).toBe(false);

      act(() => {
        // Wait for effect to complete
      });

      expect(result.current.isLoaded).toBe(true);
    });

    it('should set isLoaded to true even on error', () => {
      jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
        throw new Error('localStorage error');
      });

      const consoleErrorSpy = jest
        .spyOn(console, 'error')
        .mockImplementation(() => {});

      const { result } = renderHook(() => useQueryMode());

      act(() => {
        // Wait for effect to complete
      });

      expect(result.current.isLoaded).toBe(true);

      consoleErrorSpy.mockRestore();
    });
  });
});
