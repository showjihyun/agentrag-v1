'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { WifiOff, RefreshCw } from 'lucide-react';

export default function OfflinePage() {
  const [isOnline, setIsOnline] = React.useState(true);

  React.useEffect(() => {
    setIsOnline(navigator.onLine);

    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const handleRetry = () => {
    if (navigator.onLine) {
      window.location.href = '/agent-builder';
    } else {
      alert('Still offline. Please check your connection.');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen p-4 bg-background">
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-full bg-muted">
              <WifiOff className="h-6 w-6 text-muted-foreground" />
            </div>
            <div>
              <CardTitle>You're Offline</CardTitle>
              <CardDescription>
                {isOnline
                  ? 'Connection restored! You can go back now.'
                  : 'Please check your internet connection'}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Some features of Agent Builder require an internet connection. You can still:
          </p>
          
          <ul className="list-disc list-inside space-y-2 text-sm text-muted-foreground">
            <li>View cached agents and workflows</li>
            <li>Edit agent configurations (will sync when online)</li>
            <li>Review execution history</li>
          </ul>

          <div className="flex gap-3 pt-4">
            <Button onClick={handleRetry} className="flex-1">
              <RefreshCw className="mr-2 h-4 w-4" />
              {isOnline ? 'Go Back' : 'Retry'}
            </Button>
          </div>

          {isOnline && (
            <div className="p-3 rounded-lg bg-green-50 dark:bg-green-950/50 border border-green-200 dark:border-green-800">
              <p className="text-sm text-green-800 dark:text-green-200">
                ✓ Connection restored
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
