'use client';

import { useEffect, useCallback } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import DocumentUpload from '@/components/DocumentUpload';
import ChatInterface from '@/components/ChatInterface';
import ConversationHistory from '@/components/ConversationHistory';
import UserMenu from '@/components/UserMenu';
import { ChatErrorBoundary, DocumentErrorBoundary } from '@/components/ErrorBoundary';
import { useAuth } from '@/contexts/AuthContext';
import ThemeToggle from '@/components/ThemeToggle';
import Breadcrumb from '@/components/Breadcrumb';
import SystemStatusBadge from '@/components/SystemStatusBadge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
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
  
  // Use Zustand store instead of local state
  const activeSessionId = useActiveSessionId();
  const showSidebar = useShowSidebar();
  const setActiveSessionId = useSetActiveSessionId();
  const setSidebarOpen = useSetSidebarOpen();
  
  // Use React Query for data fetching
  const { data: sessionData, isLoading: isLoadingMessages } = useSessionMessages(activeSessionId || null);
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
            activeSessionId={activeSessionId}
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
            activeSessionId={activeSessionId}
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
              <div className="flex items-center gap-4">
                <SystemStatusBadge />
                <ThemeToggle />
                {isAuthenticated && <UserMenu />}
              </div>
            </div>
          </div>
        </header>

        <main 
          id="main-content" 
          className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full overflow-y-auto"
          tabIndex={-1}
        >
          {/* Desktop: Side-by-side layout */}
          <div className="hidden lg:grid lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1">
              <DocumentErrorBoundary>
                <DocumentUpload />
              </DocumentErrorBoundary>
            </div>
            <div className="lg:col-span-2">
              <ChatErrorBoundary>
                <ChatInterface
                  sessionId={activeSessionId}
                  initialMessages={sessionMessages}
                  isLoadingMessages={isLoadingMessages}
                  onNewMessage={(message) => {
                    console.log('New message sent:', message);
                  }}
                />
              </ChatErrorBoundary>
            </div>
          </div>

          {/* Mobile/Tablet: Tab-based layout */}
          <div className="lg:hidden">
            <Tabs defaultValue="chat" className="w-full">
              <TabsList className="w-full grid grid-cols-2 mb-6">
                <TabsTrigger value="chat" className="flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                  Chat
                </TabsTrigger>
                <TabsTrigger value="documents" className="flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  Documents
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="chat">
                <ChatErrorBoundary>
                  <ChatInterface
                    sessionId={activeSessionId}
                    initialMessages={sessionMessages}
                    isLoadingMessages={isLoadingMessages}
                    onNewMessage={(message) => {
                      console.log('New message sent:', message);
                    }}
                  />
                </ChatErrorBoundary>
              </TabsContent>
              
              <TabsContent value="documents">
                <DocumentErrorBoundary>
                  <DocumentUpload />
                </DocumentErrorBoundary>
              </TabsContent>
            </Tabs>
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
