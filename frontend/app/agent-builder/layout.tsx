'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import { ToastProvider } from '@/components/Toast';
import {
  Layers,
  Box,
  GitBranch,
  Database,
  Variable,
  Activity,
  Zap,
  Menu,
  X,
  Settings,
  Users,
  MessageSquare,
  BarChart3,
  Key,
  Code,
  Store,
} from 'lucide-react';

const navigation = [
  // Flow Types (Primary)
  { name: 'Agentflows', href: '/agent-builder/agentflows', icon: Users, badge: 'Multi-Agent' },
  { name: 'Chatflows', href: '/agent-builder/chatflows', icon: MessageSquare, badge: 'Chatbot' },
  { name: 'Workflows', href: '/agent-builder/workflows', icon: GitBranch },
  // Building Blocks
  { name: 'Agents', href: '/agent-builder/agents', icon: Layers },
  { name: 'Blocks', href: '/agent-builder/blocks', icon: Box },
  { name: 'Triggers', href: '/agent-builder/triggers', icon: Zap },
  // Data & Knowledge
  { name: 'Knowledgebases', href: '/agent-builder/knowledgebases', icon: Database },
  { name: 'Variables', href: '/agent-builder/variables', icon: Variable },
  // Monitoring & Observability
  { name: 'Executions', href: '/agent-builder/executions', icon: Activity },
  { name: 'Observability', href: '/agent-builder/observability', icon: BarChart3, badge: 'New' },
  // Developer Tools
  { name: 'API Keys', href: '/agent-builder/api-keys', icon: Key },
  { name: 'Embed', href: '/agent-builder/embed', icon: Code },
  { name: 'Marketplace', href: '/agent-builder/marketplace', icon: Store },
];

const settingsNavigation = [
  { name: 'Settings', href: '/agent-builder/settings', icon: Settings },
];

import { AgentBuilderErrorBoundary } from '@/components/agent-builder/AgentBuilderErrorBoundary';

import { useAgentBuilderStore } from '@/lib/stores/agent-builder-store';

export default function AgentBuilderLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { sidebarOpen, setSidebarOpen } = useAgentBuilderStore();

  return (
    <AgentBuilderErrorBoundary>
      <ToastProvider>
        <div className="flex h-screen bg-background">
        {/* Mobile sidebar backdrop */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-40 bg-black/50 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 border-r bg-card transition-transform duration-300 lg:static lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-16 items-center justify-between border-b px-4 lg:justify-center">
          <h2 className="text-lg font-semibold">Agent Builder</h2>
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>
        <ScrollArea className="h-[calc(100vh-4rem)]">
          <nav className="space-y-1 p-4">
            {/* Flow Types Section */}
            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-2">
              Flows
            </div>
            {navigation.slice(0, 3).map((item) => {
              const Icon = item.icon;
              const isActive = pathname?.startsWith(item.href);
              return (
                <Link key={item.name} href={item.href}>
                  <Button
                    variant={isActive ? "secondary" : "ghost"}
                    className="w-full justify-start"
                    onClick={() => setSidebarOpen(false)}
                  >
                    <Icon className="mr-2 h-4 w-4" />
                    {item.name}
                    {item.badge && (
                      <span className="ml-auto text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded">
                        {item.badge}
                      </span>
                    )}
                  </Button>
                </Link>
              );
            })}
            
            {/* Building Blocks Section */}
            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mt-4 mb-2 px-2">
              Building Blocks
            </div>
            {navigation.slice(3, 6).map((item) => {
              const Icon = item.icon;
              const isActive = pathname?.startsWith(item.href);
              return (
                <Link key={item.name} href={item.href}>
                  <Button
                    variant={isActive ? "secondary" : "ghost"}
                    className="w-full justify-start"
                    onClick={() => setSidebarOpen(false)}
                  >
                    <Icon className="mr-2 h-4 w-4" />
                    {item.name}
                  </Button>
                </Link>
              );
            })}
            
            {/* Data & Knowledge Section */}
            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mt-4 mb-2 px-2">
              Data & Knowledge
            </div>
            {navigation.slice(6, 8).map((item) => {
              const Icon = item.icon;
              const isActive = pathname?.startsWith(item.href);
              return (
                <Link key={item.name} href={item.href}>
                  <Button
                    variant={isActive ? "secondary" : "ghost"}
                    className="w-full justify-start"
                    onClick={() => setSidebarOpen(false)}
                  >
                    <Icon className="mr-2 h-4 w-4" />
                    {item.name}
                  </Button>
                </Link>
              );
            })}
            
            {/* Observability Section */}
            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mt-4 mb-2 px-2">
              Observability
            </div>
            {navigation.slice(8, 10).map((item) => {
              const Icon = item.icon;
              const isActive = pathname?.startsWith(item.href);
              return (
                <Link key={item.name} href={item.href}>
                  <Button
                    variant={isActive ? "secondary" : "ghost"}
                    className="w-full justify-start"
                    onClick={() => setSidebarOpen(false)}
                  >
                    <Icon className="mr-2 h-4 w-4" />
                    {item.name}
                    {item.badge && (
                      <span className="ml-auto text-[10px] bg-green-500/10 text-green-600 px-1.5 py-0.5 rounded">
                        {item.badge}
                      </span>
                    )}
                  </Button>
                </Link>
              );
            })}
            
            {/* Developer Section */}
            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mt-4 mb-2 px-2">
              Developer
            </div>
            {navigation.slice(10).map((item) => {
              const Icon = item.icon;
              const isActive = pathname?.startsWith(item.href);
              return (
                <Link key={item.name} href={item.href}>
                  <Button
                    variant={isActive ? "secondary" : "ghost"}
                    className="w-full justify-start"
                    onClick={() => setSidebarOpen(false)}
                  >
                    <Icon className="mr-2 h-4 w-4" />
                    {item.name}
                  </Button>
                </Link>
              );
            })}
            
            {/* Divider */}
            <div className="my-4 border-t border-gray-200 dark:border-gray-700" />
            
            {/* Settings Section */}
            {settingsNavigation.map((item) => {
              const Icon = item.icon;
              const isActive = pathname?.startsWith(item.href);
              return (
                <Link key={item.name} href={item.href}>
                  <Button
                    variant={isActive ? "secondary" : "ghost"}
                    className="w-full justify-start"
                    onClick={() => setSidebarOpen(false)}
                  >
                    <Icon className="mr-2 h-4 w-4" />
                    {item.name}
                  </Button>
                </Link>
              );
            })}
          </nav>
        </ScrollArea>
      </aside>

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Mobile header */}
        <header className="flex h-16 items-center border-b bg-card px-4 lg:hidden">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </Button>
          <h1 className="ml-4 text-lg font-semibold">Agent Builder</h1>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
      </ToastProvider>
    </AgentBuilderErrorBoundary>
  );
}
