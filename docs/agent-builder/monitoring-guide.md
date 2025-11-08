# Agent Builder Monitoring Guide

## Overview

The Agent Builder includes comprehensive monitoring capabilities for error tracking, analytics, and performance monitoring.

## Error Tracking (Sentry)

### Setup

1. Create a Sentry project at https://sentry.io
2. Get your DSN from project settings
3. Add to environment variables:

```env
NEXT_PUBLIC_SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
NEXT_PUBLIC_ENV=production
```

### Features

- **Automatic Error Capture**: All unhandled errors are captured
- **Performance Monitoring**: 10% of transactions tracked
- **Session Replay**: 10% of sessions, 100% of error sessions
- **Source Maps**: Automatic upload for debugging
- **User Context**: Track which users encounter errors
- **Breadcrumbs**: See user actions leading to errors

### Usage

```typescript
import { captureException, addBreadcrumb } from '@/lib/monitoring/sentry';

// Capture error with context
try {
  await executeAgent(agentId);
} catch (error) {
  captureException(error, {
    tags: { component: 'agent-execution', agentId },
    extra: { input: userInput },
    level: 'error',
  });
}

// Add breadcrumb
addBreadcrumb('Agent execution started', { agentId }, 'execution');
```

### Agent Builder Specific Tracking

```typescript
import { AgentBuilderMonitoring } from '@/lib/monitoring/sentry';

// Track agent operations
AgentBuilderMonitoring.agentCreated(agentId, agentType);
AgentBuilderMonitoring.agentExecutionStarted(agentId, executionId);
AgentBuilderMonitoring.agentExecutionFailed(executionId, error);

// Track workflow operations
AgentBuilderMonitoring.workflowExecutionFailed(workflowId, error);

// Track API errors
AgentBuilderMonitoring.apiError('/api/agents', 500, error);
```

## Analytics (Google Analytics)

### Setup

1. Create a GA4 property at https://analytics.google.com
2. Get your Measurement ID
3. Add to environment variables:

```env
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
```

### Features

- **Page View Tracking**: Automatic page view tracking
- **Custom Events**: Track user actions
- **User Identification**: Associate events with users
- **Conversion Tracking**: Track important actions
- **Feature Usage**: Monitor which features are used

### Usage

```typescript
import { analytics, AgentBuilderAnalytics } from '@/lib/monitoring/analytics';

// Track custom event
analytics.track('button_clicked', {
  button_name: 'create_agent',
  location: 'dashboard',
});

// Identify user
analytics.identify(userId, {
  email: user.email,
  name: user.name,
});

// Track page view
analytics.page('/agent-builder/workflows');
```

### Agent Builder Specific Events

```typescript
// Agent events
AgentBuilderAnalytics.agentCreated('custom', 'openai');
AgentBuilderAnalytics.agentExecuted(agentId, 1500, 'success');

// Block events
AgentBuilderAnalytics.blockCreated('tool');
AgentBuilderAnalytics.blockTested(blockId, true, 500);

// Workflow events
AgentBuilderAnalytics.workflowCreated(5, 4);
AgentBuilderAnalytics.workflowExecuted(workflowId, 3000, 'success');

// Knowledgebase events
AgentBuilderAnalytics.documentUploaded('pdf', 1024000);
AgentBuilderAnalytics.knowledgebaseSearched(10, 200);

// User engagement
AgentBuilderAnalytics.dashboardViewed();
AgentBuilderAnalytics.featureUsed('workflow-designer');
AgentBuilderAnalytics.errorEncountered('validation', 'agent-form');
```

## Performance Monitoring

### Setup

Performance monitoring is automatically initialized. No configuration required.

### Features

- **Core Web Vitals**: LCP, FCP, TTFB, FID, CLS
- **Long Task Detection**: Tasks >50ms
- **Layout Shift Monitoring**: Visual stability
- **Custom Metrics**: Component render times
- **Function Timing**: Measure execution time

### Usage

```typescript
import { performanceMonitor, measureRender } from '@/lib/monitoring/performance';

// Measure function execution
const result = performanceMonitor.measure('processData', () => {
  return processData(data);
});

// Measure async function
const result = await performanceMonitor.measureAsync('fetchData', async () => {
  return await fetchData();
});

// Measure component render
const { onRenderStart, onRenderEnd } = measureRender('AgentDashboard');

function AgentDashboard() {
  onRenderStart();
  
  // Component logic
  
  useEffect(() => {
    onRenderEnd();
  });
  
  return <div>...</div>;
}

// Use performance marks
performanceMonitor.mark('operation-start');
// ... do work ...
performanceMonitor.mark('operation-end');
performanceMonitor.measureBetween('operation', 'operation-start', 'operation-end');
```

### React Hook

```typescript
import { usePerformanceMonitoring } from '@/lib/monitoring/performance';

function MyComponent() {
  usePerformanceMonitoring('MyComponent');
  
  return <div>...</div>;
}
```

### Viewing Metrics

```typescript
// Get all metrics
const metrics = performanceMonitor.getMetrics();

// Get specific metric
const lcpMetrics = performanceMonitor.getMetricsByName('lcp');

// Get average
const avgLCP = performanceMonitor.getAverageMetric('lcp');
```

## Performance Budgets

### Target Metrics

- **LCP**: <2.5s (Largest Contentful Paint)
- **FID**: <100ms (First Input Delay)
- **CLS**: <0.1 (Cumulative Layout Shift)
- **FCP**: <1.8s (First Contentful Paint)
- **TTFB**: <600ms (Time to First Byte)

### Component Budgets

- **Initial Render**: <500ms (Dashboard)
- **Component Render**: <300ms (Workflow Editor)
- **Re-render**: <50ms average
- **Large List**: <1s (1000 items)

## Monitoring Dashboard

### Sentry Dashboard

1. Go to https://sentry.io
2. Select your project
3. View:
   - Error trends
   - Performance issues
   - Session replays
   - User feedback

### Google Analytics Dashboard

1. Go to https://analytics.google.com
2. Select your property
3. View:
   - Real-time users
   - User engagement
   - Event tracking
   - Conversion funnels

### Custom Dashboard

Create a custom dashboard combining:
- Sentry error rates
- GA user metrics
- Performance metrics
- Business KPIs

## Alerts

### Sentry Alerts

Configure alerts for:
- Error rate spikes
- New error types
- Performance degradation
- User impact

### GA Alerts

Configure alerts for:
- Traffic drops
- Conversion rate changes
- Feature usage changes

## Best Practices

### Error Tracking

1. **Add Context**: Always include relevant context with errors
2. **Use Breadcrumbs**: Track user actions leading to errors
3. **Filter Noise**: Ignore expected errors (network, cancelled requests)
4. **Set User Context**: Identify users for better debugging
5. **Monitor Trends**: Watch for error rate increases

### Analytics

1. **Track Key Actions**: Focus on important user actions
2. **Use Consistent Naming**: Follow naming conventions
3. **Add Metadata**: Include relevant properties
4. **Respect Privacy**: Don't track PII
5. **Monitor Funnels**: Track user journeys

### Performance

1. **Set Budgets**: Define acceptable performance thresholds
2. **Monitor Trends**: Watch for performance degradation
3. **Optimize Hot Paths**: Focus on frequently used features
4. **Test on Real Devices**: Don't rely only on dev machines
5. **Use Profiling**: Identify bottlenecks

## Troubleshooting

### Sentry Not Working

- Check DSN is correct
- Verify environment is production
- Check network requests in DevTools
- Review Sentry project settings

### Analytics Not Tracking

- Check GA ID is correct
- Verify script is loaded
- Check browser console for errors
- Test in incognito mode (ad blockers)

### Performance Metrics Missing

- Check browser support (PerformanceObserver)
- Verify monitoring is initialized
- Check console for errors
- Test in different browsers

## Resources

- [Sentry Documentation](https://docs.sentry.io)
- [Google Analytics Documentation](https://developers.google.com/analytics)
- [Web Vitals](https://web.dev/vitals/)
- [Performance API](https://developer.mozilla.org/en-US/docs/Web/API/Performance)
