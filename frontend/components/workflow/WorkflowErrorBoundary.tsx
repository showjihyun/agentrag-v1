'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

interface Props {
  children: ReactNode;
  workflowId?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class WorkflowErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Workflow Error:', error, errorInfo);
    // TODO: Send to error tracking service
  }

  reset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-full min-h-[400px] p-8 text-center bg-background">
          <AlertTriangle className="h-16 w-16 text-destructive mb-6" />
          <h2 className="text-xl font-semibold mb-2">Workflow Error</h2>
          <p className="text-muted-foreground mb-6 max-w-md">
            An error occurred while loading the workflow.
          </p>
          <div className="flex gap-3">
            <Button onClick={this.reset} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
            <Link href="/agent-builder/workflows">
              <Button variant="default">
                <Home className="h-4 w-4 mr-2" />
                Workflow List
              </Button>
            </Link>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
