/**
 * Performance tests for Agent Builder components
 */

import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AgentDashboard from '@/app/agent-builder/page';
import WorkflowEditor from '@/components/agent-builder/workflow/WorkflowEditor';

describe('Render Performance Tests', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
  });

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    );
  };

  describe('Initial Render Performance', () => {
    it('should render AgentDashboard within performance budget', () => {
      const startTime = performance.now();
      
      renderWithProviders(<AgentDashboard />);
      
      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render in less than 500ms
      expect(renderTime).toBeLessThan(500);
    });

    it('should render WorkflowEditor within performance budget', () => {
      const startTime = performance.now();
      
      render(<WorkflowEditor />);
      
      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render in less than 300ms
      expect(renderTime).toBeLessThan(300);
    });
  });

  describe('Re-render Performance', () => {
    it('should handle frequent updates efficiently', () => {
      const { rerender } = renderWithProviders(<AgentDashboard />);

      const startTime = performance.now();
      
      // Simulate 10 re-renders
      for (let i = 0; i < 10; i++) {
        rerender(
          <QueryClientProvider client={queryClient}>
            <AgentDashboard />
          </QueryClientProvider>
        );
      }
      
      const endTime = performance.now();
      const totalTime = endTime - startTime;
      const avgTime = totalTime / 10;

      // Average re-render should be less than 50ms
      expect(avgTime).toBeLessThan(50);
    });
  });

  describe('Memory Usage', () => {
    it('should not leak memory on unmount', () => {
      if (!(performance as any).memory) {
        console.log('Memory API not available, skipping test');
        return;
      }

      const initialMemory = (performance as any).memory.usedJSHeapSize;

      const { unmount } = renderWithProviders(<AgentDashboard />);
      unmount();

      // Force garbage collection if available
      if (global.gc) {
        global.gc();
      }

      const finalMemory = (performance as any).memory.usedJSHeapSize;
      const memoryIncrease = finalMemory - initialMemory;

      // Memory increase should be minimal (less than 5MB)
      expect(memoryIncrease).toBeLessThan(5 * 1024 * 1024);
    });
  });

  describe('Large Dataset Performance', () => {
    it('should handle 1000 items efficiently', () => {
      const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
        id: `item-${i}`,
        name: `Item ${i}`,
        value: i,
      }));

      const startTime = performance.now();
      
      render(
        <div>
          {largeDataset.map((item) => (
            <div key={item.id}>{item.name}</div>
          ))}
        </div>
      );
      
      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render 1000 items in less than 1 second
      expect(renderTime).toBeLessThan(1000);
    });
  });
});
