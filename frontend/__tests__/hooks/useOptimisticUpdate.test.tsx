/**
 * Tests for useOptimisticUpdate hook
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useOptimisticUpdate } from '@/hooks/useOptimisticUpdate';

describe('useOptimisticUpdate', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('should apply optimistic update immediately', async () => {
    const { result } = renderHook(
      () =>
        useOptimisticUpdate({
          queryKey: ['test'],
          mutationFn: async (data: any) => data,
        }),
      { wrapper }
    );

    // Set initial data
    queryClient.setQueryData(['test'], { value: 1 });

    // Apply optimistic update
    act(() => {
      result.current.mutate({ value: 2 });
    });

    // Should immediately show optimistic value
    const data = queryClient.getQueryData(['test']);
    expect(data).toEqual({ value: 2 });
  });

  it('should rollback on error', async () => {
    const { result } = renderHook(
      () =>
        useOptimisticUpdate({
          queryKey: ['test'],
          mutationFn: async () => {
            throw new Error('Failed');
          },
        }),
      { wrapper }
    );

    // Set initial data
    queryClient.setQueryData(['test'], { value: 1 });

    // Apply optimistic update that will fail
    act(() => {
      result.current.mutate({ value: 2 });
    });

    // Wait for error
    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    // Should rollback to original value
    const data = queryClient.getQueryData(['test']);
    expect(data).toEqual({ value: 1 });
  });

  it('should keep optimistic value on success', async () => {
    const { result } = renderHook(
      () =>
        useOptimisticUpdate({
          queryKey: ['test'],
          mutationFn: async (data: any) => data,
        }),
      { wrapper }
    );

    // Set initial data
    queryClient.setQueryData(['test'], { value: 1 });

    // Apply optimistic update
    act(() => {
      result.current.mutate({ value: 2 });
    });

    // Wait for success
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Should keep optimistic value
    const data = queryClient.getQueryData(['test']);
    expect(data).toEqual({ value: 2 });
  });
});
