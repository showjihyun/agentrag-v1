# Agent Builder PWA Guide

## Overview

The Agent Builder is a Progressive Web App (PWA) that can be installed on devices and works offline.

## Features

### 🚀 Installable

Install the Agent Builder as a standalone app on:
- Desktop (Windows, Mac, Linux)
- Mobile (iOS, Android)
- Tablets

### 📴 Offline Support

- View cached agents and workflows
- Queue operations for when online
- Automatic sync when connection restored
- Offline indicator

### 🔔 Push Notifications

- Agent execution completed
- Workflow status updates
- Error notifications
- Custom alerts

### ⚡ Fast Loading

- Service worker caching
- Instant page loads
- Background updates
- Optimized assets

## Installation

### Desktop

#### Chrome/Edge
1. Open Agent Builder in browser
2. Click install icon in address bar
3. Click "Install" in popup
4. App opens in standalone window

#### Safari (Mac)
1. Open Agent Builder in Safari
2. Click Share button
3. Select "Add to Dock"
4. App appears in Dock

### Mobile

#### Android
1. Open Agent Builder in Chrome
2. Tap menu (⋮)
3. Select "Add to Home screen"
4. Tap "Add"
5. App appears on home screen

#### iOS
1. Open Agent Builder in Safari
2. Tap Share button
3. Select "Add to Home Screen"
4. Tap "Add"
5. App appears on home screen

## Offline Mode

### What Works Offline

✅ View cached agents
✅ View cached workflows
✅ View execution history
✅ Browse block library
✅ View knowledgebases
✅ Read documentation

### What Requires Connection

❌ Create new agents
❌ Execute agents
❌ Upload documents
❌ Real-time updates
❌ API calls

### Offline Indicator

The app shows an offline indicator when:
- Network connection is lost
- API is unreachable
- Service worker is active

### Background Sync

When offline, the app queues:
- Agent executions
- Workflow runs
- Document uploads
- Configuration changes

These sync automatically when connection is restored.

## Push Notifications

### Setup

1. Grant notification permission when prompted
2. Configure notification preferences in settings
3. Receive notifications for:
   - Agent execution completed
   - Workflow finished
   - Errors occurred
   - System alerts

### Managing Notifications

#### Desktop
- Click notification to open app
- Right-click for options
- Disable in browser settings

#### Mobile
- Tap notification to open app
- Swipe to dismiss
- Manage in system settings

### Notification Types

**Execution Complete**
```
Agent Execution Complete
Your agent "Data Analyzer" finished successfully
```

**Workflow Status**
```
Workflow Update
"Data Pipeline" completed in 3.5s
```

**Error Alert**
```
Execution Failed
Agent "Web Scraper" encountered an error
```

## App Shortcuts

Quick actions from app icon:

### Desktop
Right-click app icon:
- Create Agent
- Workflow Designer
- View Executions

### Mobile
Long-press app icon:
- New Agent
- Workflows
- Monitor

## Caching Strategy

### Network First
- HTML pages
- API responses
- Real-time data

### Cache First
- Static assets (JS, CSS)
- Images
- Fonts
- Icons

### Cache Then Network
- Agent configurations
- Workflow definitions
- Block library

## Updates

### Automatic Updates

The app checks for updates:
- On app launch
- Every 24 hours
- When connection restored

### Update Notification

When update available:
```
New Version Available
Reload to update?
[Reload] [Later]
```

### Manual Update

Force update check:
1. Open app settings
2. Click "Check for Updates"
3. Reload if available

## Storage

### What's Stored

- Agent configurations
- Workflow definitions
- Execution history (last 100)
- Block library
- User preferences
- Cached API responses

### Storage Limits

- Desktop: ~50MB
- Mobile: ~20MB
- Automatic cleanup of old data

### Clear Storage

To clear app data:
1. Open browser settings
2. Find Agent Builder
3. Clear site data
4. Reload app

## Troubleshooting

### App Won't Install

**Desktop**
- Update browser to latest version
- Check if already installed
- Try different browser
- Clear browser cache

**Mobile**
- Use Safari (iOS) or Chrome (Android)
- Check storage space
- Update OS if needed
- Restart device

### Offline Mode Not Working

1. Check service worker status:
   - Open DevTools
   - Go to Application > Service Workers
   - Verify "activated and running"

2. Clear cache and reinstall:
   - Unregister service worker
   - Clear site data
   - Reload app

3. Check browser support:
   - Service workers required
   - Update browser if needed

### Notifications Not Working

**Permission Denied**
1. Open browser settings
2. Find Agent Builder
3. Allow notifications
4. Reload app

**Not Receiving**
1. Check notification settings
2. Verify push subscription
3. Test with sample notification
4. Check browser console for errors

### Sync Issues

If offline changes not syncing:
1. Check network connection
2. Open app to trigger sync
3. Check browser console
4. Clear and re-sync

## Best Practices

### For Users

1. **Install the App**: Better experience than browser
2. **Enable Notifications**: Stay updated on executions
3. **Work Offline**: View and plan when offline
4. **Keep Updated**: Accept updates when prompted
5. **Manage Storage**: Clear old data periodically

### For Developers

1. **Test Offline**: Always test offline functionality
2. **Handle Errors**: Graceful degradation
3. **Cache Wisely**: Balance freshness and availability
4. **Update Strategy**: Clear old caches on update
5. **Monitor Usage**: Track PWA metrics

## Advanced Features

### Share Target

Share content to Agent Builder:
- Text → Create agent with prompt
- Files → Upload to knowledgebase
- URLs → Add to web search

### Shortcuts

Keyboard shortcuts work in installed app:
- `Ctrl/Cmd + N`: New agent
- `Ctrl/Cmd + W`: New workflow
- `Ctrl/Cmd + E`: View executions
- `Ctrl/Cmd + K`: Command palette

### Standalone Mode

When installed, app runs in standalone mode:
- No browser UI
- Full screen
- Native feel
- Better performance

## Browser Support

### Desktop
✅ Chrome 90+
✅ Edge 90+
✅ Firefox 90+
✅ Safari 15+

### Mobile
✅ Chrome Android 90+
✅ Safari iOS 15+
✅ Samsung Internet 15+

## Resources

- [PWA Documentation](https://web.dev/progressive-web-apps/)
- [Service Workers](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Web App Manifest](https://developer.mozilla.org/en-US/docs/Web/Manifest)
- [Push API](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)
