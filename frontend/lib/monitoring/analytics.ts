/**
 * Analytics tracking integration
 */

interface AnalyticsEvent {
  name: string;
  properties?: Record<string, any>;
  timestamp?: number;
}

interface UserProperties {
  userId?: string;
  email?: string;
  name?: string;
  [key: string]: any;
}

class Analytics {
  private initialized = false;
  private queue: AnalyticsEvent[] = [];

  /**
   * Initialize analytics
   */
  init() {
    if (this.initialized) return;
    
    if (process.env.NODE_ENV !== 'production') {
      console.log('[Analytics] Running in development mode');
      this.initialized = true;
      return;
    }

    // Initialize your analytics provider (e.g., Google Analytics, Mixpanel, Amplitude)
    // Example for Google Analytics 4:
    if (typeof window !== 'undefined' && process.env.NEXT_PUBLIC_GA_ID) {
      const script = document.createElement('script');
      script.src = `https://www.googletagmanager.com/gtag/js?id=${process.env.NEXT_PUBLIC_GA_ID}`;
      script.async = true;
      document.head.appendChild(script);

      (window as any).dataLayer = (window as any).dataLayer || [];
      function gtag(...args: any[]) {
        (window as any).dataLayer.push(args);
      }
      gtag('js', new Date());
      gtag('config', process.env.NEXT_PUBLIC_GA_ID);
      
      (window as any).gtag = gtag;
    }

    this.initialized = true;
    this.flushQueue();
    
    console.log('[Analytics] Initialized');
  }

  /**
   * Track event
   */
  track(name: string, properties?: Record<string, any>) {
    const event: AnalyticsEvent = {
      name,
      properties: properties || {},
      timestamp: Date.now(),
    };

    if (!this.initialized) {
      this.queue.push(event);
      return;
    }

    if (process.env.NODE_ENV !== 'production') {
      console.log('[Analytics] Track:', name, properties);
      return;
    }

    // Send to analytics provider
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', name, properties);
    }
  }

  /**
   * Track page view
   */
  page(path: string, properties?: Record<string, any>) {
    this.track('page_view', {
      page_path: path,
      ...properties,
    });
  }

  /**
   * Identify user
   */
  identify(userId: string, properties?: UserProperties) {
    if (process.env.NODE_ENV !== 'production') {
      console.log('[Analytics] Identify:', userId, properties);
      return;
    }

    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('set', 'user_properties', {
        user_id: userId,
        ...properties,
      });
    }
  }

  /**
   * Flush queued events
   */
  private flushQueue() {
    while (this.queue.length > 0) {
      const event = this.queue.shift();
      if (event) {
        this.track(event.name, event.properties);
      }
    }
  }
}

// Singleton instance
export const analytics = new Analytics();

/**
 * Agent Builder specific analytics
 */
export const AgentBuilderAnalytics = {
  // Agent events
  agentCreated: (agentType: string, llmProvider: string) => {
    analytics.track('agent_created', {
      agent_type: agentType,
      llm_provider: llmProvider,
    });
  },

  agentUpdated: (agentId: string) => {
    analytics.track('agent_updated', { agent_id: agentId });
  },

  agentDeleted: (agentId: string) => {
    analytics.track('agent_deleted', { agent_id: agentId });
  },

  agentExecuted: (agentId: string, duration: number, status: string) => {
    analytics.track('agent_executed', {
      agent_id: agentId,
      duration_ms: duration,
      status,
    });
  },

  // Block events
  blockCreated: (blockType: string) => {
    analytics.track('block_created', { block_type: blockType });
  },

  blockTested: (blockId: string, success: boolean, duration: number) => {
    analytics.track('block_tested', {
      block_id: blockId,
      success,
      duration_ms: duration,
    });
  },

  // Workflow events
  workflowCreated: (nodeCount: number, edgeCount: number) => {
    analytics.track('workflow_created', {
      node_count: nodeCount,
      edge_count: edgeCount,
    });
  },

  workflowExecuted: (workflowId: string, duration: number, status: string) => {
    analytics.track('workflow_executed', {
      workflow_id: workflowId,
      duration_ms: duration,
      status,
    });
  },

  // Knowledgebase events
  knowledgebaseCreated: (documentCount: number) => {
    analytics.track('knowledgebase_created', {
      document_count: documentCount,
    });
  },

  documentUploaded: (fileType: string, fileSize: number) => {
    analytics.track('document_uploaded', {
      file_type: fileType,
      file_size_bytes: fileSize,
    });
  },

  // Search events
  knowledgebaseSearched: (resultCount: number, duration: number) => {
    analytics.track('knowledgebase_searched', {
      result_count: resultCount,
      duration_ms: duration,
    });
  },

  // User engagement
  dashboardViewed: () => {
    analytics.track('dashboard_viewed');
  },

  featureUsed: (feature: string) => {
    analytics.track('feature_used', { feature });
  },

  errorEncountered: (errorType: string, component: string) => {
    analytics.track('error_encountered', {
      error_type: errorType,
      component,
    });
  },
};

/**
 * Hook for tracking page views
 */
export function usePageTracking() {
  if (typeof window !== 'undefined') {
    const path = window.location.pathname;
    analytics.page(path);
  }
}
