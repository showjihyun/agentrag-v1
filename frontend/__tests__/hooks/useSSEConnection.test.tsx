import { renderHook, act } from '@testing-library/react';
import { useSSEConnection } from '@/hooks/useSSEConnection';

// Mock EventSource
class MockEventSource {
  public onopen: ((event: Event) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;
  public readyState: number = EventSource.CONNECTING;
  
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSED = 2;

  constructor(public url: string) {
    // Simulate async connection
    setTimeout(() => {
      this.readyState = EventSource.OPEN;
      this.onopen?.(new Event('open'));
    }, 0);
  }

  close() {
    this.readyState = EventSource.CLOSED;
  }

  dispatchMessage(data: string) {
    const event = new MessageEvent('message', { data });
    this.onmessage?.(event);
  }

  dispatchError() {
    this.readyState = EventSource.CLOSED;
    this.onerror?.(new Event('error'));
  }
}

// Mock global EventSource
Object.defineProperty(global, 'EventSource', {
  writable: true,
  value: MockEventSource,
});

describe('useSSEConnection', () => {
  let mockOnMessage: jest.Mock;
  let mockOnError: jest.Mock;

  beforeEach(() => {
    mockOnMessage = jest.fn();
    mockOnError = jest.fn();
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.clearAllTimers();
  });

  it('should establish connection when enabled', async () => {
    const { result } = renderHook(() =>
      useSSEConnection({
        url: 'http://test.com/stream',
        enabled: true,
        onMessage: mockOnMessage,
        onError: mockOnError,
      })
    );

    expect(result.current.isConnected).toBe(false);
    expect(result.current.connectionAttempts).toBe(0);

    // Wait for connection to establish
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 10));
    });

    expect(result.current.isConnected).toBe(true);
  });

  it('should not connect when disabled', () => {
    const { result } = renderHook(() =>
      useSSEConnection({
        url: 'http://test.com/stream',
        enabled: false,
        onMessage: mockOnMessage,
        onError: mockOnError,
      })
    );

    expect(result.current.isConnected).toBe(false);
  });

  it('should handle messages correctly', async () => {
    const { result } = renderHook(() =>
      useSSEConnection({
        url: 'http://test.com/stream',
        enabled: true,
        onMessage: mockOnMessage,
        onError: mockOnError,
      })
    );

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 10));
    });

    // Simulate message
    const mockEventSource = (global.EventSource as any).mock.instances[0];
    act(() => {
      mockEventSource.dispatchMessage('{"type": "test", "payload": {"data": "value"}}');
    });

    expect(mockOnMessage).toHaveBeenCalledWith({
      type: 'test',
      payload: { data: 'value' }
    });
  });

  it('should handle connection errors and attempt reconnection', async () => {
    jest.useFakeTimers();
    
    const { result } = renderHook(() =>
      useSSEConnection({
        url: 'http://test.com/stream',
        enabled: true,
        onMessage: mockOnMessage,
        onError: mockOnError,
        reconnectInterval: 1000,
      })
    );

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 10));
    });

    // Simulate error
    const mockEventSource = (global.EventSource as any).mock.instances[0];
    act(() => {
      mockEventSource.dispatchError();
    });

    expect(result.current.isConnected).toBe(false);
    expect(result.current.connectionAttempts).toBe(1);
    expect(mockOnError).toHaveBeenCalled();

    // Fast-forward time to trigger reconnection
    act(() => {
      jest.advanceTimersByTime(1000);
    });

    jest.useRealTimers();
  });

  it('should cleanup connection on unmount', async () => {
    const { result, unmount } = renderHook(() =>
      useSSEConnection({
        url: 'http://test.com/stream',
        enabled: true,
        onMessage: mockOnMessage,
        onError: mockOnError,
      })
    );

    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 10));
    });

    expect(result.current.isConnected).toBe(true);

    unmount();

    expect(result.current.isConnected).toBe(false);
  });

  it('should provide reconnect and disconnect methods', async () => {
    const { result } = renderHook(() =>
      useSSEConnection({
        url: 'http://test.com/stream',
        enabled: true,
        onMessage: mockOnMessage,
        onError: mockOnError,
      })
    );

    expect(typeof result.current.reconnect).toBe('function');
    expect(typeof result.current.disconnect).toBe('function');

    // Test disconnect
    act(() => {
      result.current.disconnect();
    });

    expect(result.current.isConnected).toBe(false);
  });
});