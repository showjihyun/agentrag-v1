'use client';

import { useEffect, useCallback } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import ChatInterface from '@/components/ChatInterface';
import ConversationHistory from '@/components/ConversationHistory';
import UserMenu from '@/components/UserMenu';
import { ChatErrorBoundary } from '@/components/ErrorBoundary';
import { useAuth } from '@/contexts/AuthContext';
import ThemeToggle from '@/components/ThemeToggle';
import Breadcrumb from '@/components/Breadcrumb';
import SystemStatusBadge from '@/components/SystemStatusBadge';
import AdminActions from '@/components/AdminActions';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Drawer } from '@/components/ui/Drawer';
import WelcomeModal from '@/components/WelcomeModal';
import OnboardingTour from '@/components/OnboardingTour';
import { useOnboarding } from '@/lib/hooks/useOnboarding';
import { useSessionMessages } from '@/lib/hooks/useSession';
import { useActiveSessionId, useShowSidebar, useSetActiveSessionId, useSetSidebarOpen } from '@/lib/stores/app-store';

export default function Home() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated } = useAuth();
  
  // Redirect to Agent Builder Dashboard
  useEffect(() => {
    router.push('/agent-builder');
  }, [router]);
  
  // Use Zustand store instead of local state
  const activeSessionId = useActiveSessionId();
  const showSidebar = useShowSidebar();
  const setActiveSessionId = useSetActiveSessionId();
  const setSidebarOpen = useSetSidebarOpen();
  
  // Use React Query for data fetching
  const { data: sessionData } = useSessionMessages(activeSessionId || null);
  const sessionMessages = sessionData?.messages || [];
  
  // Onboarding
  const { showWelcome, showTour, startTour, skipWelcome, completeTour, skipTour } = useOnboarding();
  
  const tourSteps = [
    {
      target: '#document-upload-area',
      title: 'Step 1: Upload Documents',
      content: 'Start by uploading your documents here. We support PDF, TXT, DOCX, and HWP files. You can drag and drop or click to browse.',
      placement: 'bottom' as const,
    },
    {
      target: '#chat-input-area',
      title: 'Step 2: Ask Questions',
      content: 'Once your documents are uploaded, type your questions here. Our AI will search through your documents and provide intelligent answers.',
      placement: 'top' as const,
    },
    {
      target: '#mode-selector-area',
      title: 'Step 3: Choose Response Mode',
      content: 'Select Fast mode for quick answers (~2s), Balanced for refined responses (~5s), or Deep for comprehensive analysis (~10s+).',
      placement: 'top' as const,
    },
    {
      target: '#conversation-history-button',
      title: 'Step 4: Access Your History',
      content: 'All your conversations are automatically saved. Click here to view and continue previous conversations.',
      placement: 'right' as const,
    },
  ];

  // Get session ID from URL on mount
  useEffect(() => {
    const sessionId = searchParams.get('session');
    if (sessionId) {
      setActiveSessionId(sessionId);
    }
  }, [searchParams, setActiveSessionId]);

  /**
   * Handle session selection from sidebar.
   * Memoized to prevent unnecessary re-renders
   */
  const handleSessionSelect = useCallback((sessionId: string) => {
    setActiveSessionId(sessionId);
    router.push(`/?session=${sessionId}`);
  }, [setActiveSessionId, router]);

  return (
    <>
      {/* Onboarding */}
      {showWelcome && <WelcomeModal onStartTour={startTour} onClose={skipWelcome} />}
      {showTour && <OnboardingTour steps={tourSteps} onComplete={completeTour} onSkip={skipTour} />}
      
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
      {/* Desktop Sidebar */}
      {isAuthenticated && (
        <div className="hidden lg:block">
          <ConversationHistory
            activeSessionId={activeSessionId || undefined}
            onSessionSelect={handleSessionSelect}
          />
        </div>
      )}

      {/* Mobile Drawer */}
      {isAuthenticated && (
        <Drawer
          open={showSidebar}
          onClose={() => setSidebarOpen(false)}
          side="left"
        >
          <ConversationHistory
            activeSessionId={activeSessionId || undefined}
            onSessionSelect={(sessionId) => {
              handleSessionSelect(sessionId);
              setSidebarOpen(false);
            }}
          />
        </Drawer>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <Breadcrumb className="mb-3" />
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {/* Mobile Menu Button */}
                {isAuthenticated && (
                  <button
                    id="conversation-history-button"
                    onClick={() => setSidebarOpen(true)}
                    className="lg:hidden p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                    aria-label="Open conversation history"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                  </button>
                )}
                <div>
                  <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    Agentic RAG System
                  </h1>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    Intelligent document retrieval with multi-agent reasoning
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <SystemStatusBadge />
                <AdminActions />
                <ThemeToggle />
                {isAuthenticated && <UserMenu />}
              </div>
            </div>
          </div>
        </header>

        <main 
          id="main-content" 
          className="flex-1 w-full px-4 sm:px-6 lg:px-8 py-8 overflow-y-auto"
          tabIndex={-1}
        >
          {/* Quick Access Cards - Compact Design */}
          <div className="mb-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <button
                onClick={() => router.push('/dashboard')}
                className="group bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3 hover:border-blue-400 dark:hover:border-blue-600 hover:shadow-md transition-all duration-200 hover:scale-[1.02] text-left w-full cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-500 rounded-lg text-white group-hover:scale-110 transition-transform flex-shrink-0">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1H5a1 1 0 01-1-1v-3zM14 13a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1h-4a1 1 0 01-1-1v-7z" />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-base font-bold text-gray-900 dark:text-white mb-0.5">
                      Dashboard
                    </h3>
                    <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                      문서 관리 및 사용 통계
                    </p>
                  </div>
                  <svg className="w-4 h-4 text-blue-400 group-hover:translate-x-1 transition-transform flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </button>

              <button
                onClick={() => router.push('/monitoring')}
                className="group bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border border-green-200 dark:border-green-800 rounded-lg p-3 hover:border-green-400 dark:hover:border-green-600 hover:shadow-md transition-all duration-200 hover:scale-[1.02] text-left w-full cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-500 rounded-lg text-white group-hover:scale-110 transition-transform flex-shrink-0">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-base font-bold text-gray-900 dark:text-white mb-0.5">
                      System Metrics
                    </h3>
                    <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                      실시간 시스템 모니터링
                    </p>
                  </div>
                  <svg className="w-4 h-4 text-green-400 group-hover:translate-x-1 transition-transform flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </button>

              <button
                onClick={() => router.push('/monitoring/stats')}
                className="group bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 border border-purple-200 dark:border-purple-800 rounded-lg p-3 hover:border-purple-400 dark:hover:border-purple-600 hover:shadow-md transition-all duration-200 hover:scale-[1.02] text-left w-full cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-500 rounded-lg text-white group-hover:scale-110 transition-transform flex-shrink-0">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-base font-bold text-gray-900 dark:text-white mb-0.5">
                      Statistics Dashboard
                    </h3>
                    <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                      상세 통계 및 정확도 분석
                    </p>
                  </div>
                  <svg className="w-4 h-4 text-purple-400 group-hover:translate-x-1 transition-transform flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </button>
            </div>

            {/* Agent Builder Section */}
            <div className="mt-6 p-4 bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 border-2 border-orange-300 dark:border-orange-700 rounded-xl">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-orange-500 rounded-xl text-white flex-shrink-0">
                  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                    🤖 Agent Builder
                  </h3>
                  <p className="text-sm text-gray-700 dark:text-gray-300 mb-4">
                    커스텀 AI 에이전트를 생성하고 관리하세요. 워크플로우, 지식베이스, 블록을 조합하여 강력한 자동화를 구축할 수 있습니다.
                  </p>
                  <button
                    onClick={() => router.push('/agent-builder')}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white font-medium rounded-lg transition-colors shadow-md hover:shadow-lg"
                  >
                    <span>Agent Builder 열기</span>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Desktop: Side-by-side layout with resizable panels */}
          <div className="hidden lg:block w-full">
            <ChatErrorBoundary>
              <ChatInterface
                sessionId={activeSessionId || undefined}
                initialMessages={sessionMessages}
                onNewMessage={(message) => {
                  console.log('New message sent:', message);
                }}
              />
            </ChatErrorBoundary>
          </div>

          {/* Mobile/Tablet: Integrated layout */}
          <div className="lg:hidden">
            <ChatErrorBoundary>
              <ChatInterface
                sessionId={activeSessionId || undefined}
                initialMessages={sessionMessages}
                onNewMessage={(message) => {
                  console.log('New message sent:', message);
                }}
              />
            </ChatErrorBoundary>
          </div>
        </main>

        <footer className="mt-auto py-6 border-t border-gray-200 dark:border-gray-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <p className="text-center text-sm text-gray-500 dark:text-gray-400">
              Powered by Next.js, FastAPI, and Multi-Agent AI
            </p>
          </div>
        </footer>
      </div>
    </div>
    </>
  );
}
