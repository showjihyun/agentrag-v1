'use client';

import React, { Component, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home, Bug, ChevronDown, ChevronUp, Copy, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  showDetails: boolean;
  copied: boolean;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  resetKeys?: any[];
  level?: 'page' | 'section' | 'component';
}

// Base Error Boundary Class
class BaseErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false,
      copied: false,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ errorInfo });
    this.props.onError?.(error, errorInfo);
    
    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('Error caught by boundary:', error);
      console.error('Component stack:', errorInfo.componentStack);
    }
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps) {
    // Reset error state if resetKeys change
    if (this.state.hasError && this.props.resetKeys) {
      const hasChanged = this.props.resetKeys.some(
        (key, index) => key !== prevProps.resetKeys?.[index]
      );
      if (hasChanged) {
        this.resetError();
      }
    }
  }

  resetError = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false,
    });
  };

  toggleDetails = () => {
    this.setState((prev) => ({ showDetails: !prev.showDetails }));
  };

  copyErrorDetails = () => {
    const { error, errorInfo } = this.state;
    const details = `Error: ${error?.message}\n\nStack: ${error?.stack}\n\nComponent Stack: ${errorInfo?.componentStack}`;
    navigator.clipboard.writeText(details);
    this.setState({ copied: true });
    setTimeout(() => this.setState({ copied: false }), 2000);
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return this.renderErrorUI();
    }
    return this.props.children;
  }

  renderErrorUI(): ReactNode {
    return null; // Override in subclasses
  }
}

// Page-level Error Boundary (full page error)
export class PageErrorBoundary extends BaseErrorBoundary {
  renderErrorUI() {
    const { error, errorInfo, showDetails, copied } = this.state;

    return (
      <div className="min-h-screen flex items-center justify-center p-6 bg-background">
        <Card className="max-w-lg w-full">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 h-16 w-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
              <AlertTriangle className="h-8 w-8 text-red-600 dark:text-red-400" />
            </div>
            <CardTitle className="text-xl">문제가 발생했습니다</CardTitle>
            <CardDescription>
              페이지를 로드하는 중 오류가 발생했습니다. 다시 시도하거나 홈으로 돌아가세요.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>오류</AlertTitle>
              <AlertDescription className="font-mono text-sm">
                {error?.message || '알 수 없는 오류'}
              </AlertDescription>
            </Alert>

            <div className="flex gap-2">
              <Button onClick={this.resetError} className="flex-1">
                <RefreshCw className="h-4 w-4 mr-2" />
                다시 시도
              </Button>
              <Button variant="outline" onClick={() => window.location.href = '/agent-builder'}>
                <Home className="h-4 w-4 mr-2" />
                홈으로
              </Button>
            </div>

            {process.env.NODE_ENV === 'development' && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full"
                  onClick={this.toggleDetails}
                >
                  {showDetails ? (
                    <ChevronUp className="h-4 w-4 mr-2" />
                  ) : (
                    <ChevronDown className="h-4 w-4 mr-2" />
                  )}
                  개발자 정보 {showDetails ? '숨기기' : '보기'}
                </Button>

                {showDetails && (
                  <div className="relative">
                    <pre className="p-4 bg-muted rounded-lg text-xs overflow-auto max-h-64">
                      <code>
                        {error?.stack}
                        {'\n\n--- Component Stack ---\n'}
                        {errorInfo?.componentStack}
                      </code>
                    </pre>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute top-2 right-2 h-8 w-8"
                      onClick={this.copyErrorDetails}
                    >
                      {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </Button>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }
}

// Section-level Error Boundary (card-style error)
export class SectionErrorBoundary extends BaseErrorBoundary {
  renderErrorUI() {
    const { error } = this.state;

    return (
      <Card className="border-red-200 dark:border-red-800 bg-red-50/50 dark:bg-red-950/20">
        <CardContent className="py-8">
          <div className="flex flex-col items-center text-center gap-4">
            <div className="h-12 w-12 rounded-full bg-red-100 dark:bg-red-900/50 flex items-center justify-center">
              <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <h3 className="font-semibold text-red-900 dark:text-red-100">
                이 섹션을 로드할 수 없습니다
              </h3>
              <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                {error?.message || '알 수 없는 오류가 발생했습니다'}
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={this.resetError}>
              <RefreshCw className="h-4 w-4 mr-2" />
              다시 시도
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }
}

// Component-level Error Boundary (inline error)
export class ComponentErrorBoundary extends BaseErrorBoundary {
  renderErrorUI() {
    return (
      <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800">
        <AlertTriangle className="h-4 w-4 text-red-500 flex-shrink-0" />
        <span className="text-sm text-red-700 dark:text-red-300">
          컴포넌트 로드 실패
        </span>
        <Button
          variant="ghost"
          size="sm"
          className="ml-auto h-7 px-2"
          onClick={this.resetError}
        >
          <RefreshCw className="h-3 w-3" />
        </Button>
      </div>
    );
  }
}

// Async Error Fallback (for Suspense boundaries)
export function AsyncErrorFallback({
  error,
  resetErrorBoundary,
}: {
  error: Error;
  resetErrorBoundary: () => void;
}) {
  return (
    <Alert variant="destructive" className="my-4">
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle>데이터 로드 실패</AlertTitle>
      <AlertDescription className="flex items-center justify-between">
        <span>{error.message}</span>
        <Button variant="outline" size="sm" onClick={resetErrorBoundary}>
          <RefreshCw className="h-4 w-4 mr-2" />
          재시도
        </Button>
      </AlertDescription>
    </Alert>
  );
}

// Network Error Component
export function NetworkError({ onRetry }: { onRetry?: () => void }) {
  return (
    <Card className="max-w-md mx-auto my-8">
      <CardContent className="py-8 text-center">
        <div className="mx-auto mb-4 h-12 w-12 rounded-full bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center">
          <AlertTriangle className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
        </div>
        <h3 className="font-semibold mb-2">네트워크 연결 오류</h3>
        <p className="text-sm text-muted-foreground mb-4">
          서버에 연결할 수 없습니다. 인터넷 연결을 확인하고 다시 시도해주세요.
        </p>
        {onRetry && (
          <Button onClick={onRetry}>
            <RefreshCw className="h-4 w-4 mr-2" />
            다시 시도
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

// Not Found Component
export function NotFoundError({ 
  title = '찾을 수 없습니다',
  description = '요청하신 리소스를 찾을 수 없습니다.',
  backUrl = '/agent-builder',
}: { 
  title?: string;
  description?: string;
  backUrl?: string;
}) {
  return (
    <Card className="max-w-md mx-auto my-8">
      <CardContent className="py-8 text-center">
        <div className="mx-auto mb-4 text-6xl font-bold text-muted-foreground/30">
          404
        </div>
        <h3 className="font-semibold mb-2">{title}</h3>
        <p className="text-sm text-muted-foreground mb-4">{description}</p>
        <Button variant="outline" onClick={() => window.location.href = backUrl}>
          <Home className="h-4 w-4 mr-2" />
          돌아가기
        </Button>
      </CardContent>
    </Card>
  );
}

// Permission Denied Component
export function PermissionDenied({ onBack }: { onBack?: () => void }) {
  return (
    <Card className="max-w-md mx-auto my-8">
      <CardContent className="py-8 text-center">
        <div className="mx-auto mb-4 h-12 w-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
          <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-400" />
        </div>
        <h3 className="font-semibold mb-2">접근 권한이 없습니다</h3>
        <p className="text-sm text-muted-foreground mb-4">
          이 리소스에 접근할 권한이 없습니다. 관리자에게 문의하세요.
        </p>
        <Button variant="outline" onClick={onBack || (() => window.history.back())}>
          돌아가기
        </Button>
      </CardContent>
    </Card>
  );
}
