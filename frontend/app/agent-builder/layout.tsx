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
} from 'lucide-react';

const navigation = [
  { name: 'Agents', href: '/agent-builder/agents', icon: Layers },
  { name: 'Blocks', href: '/agent-builder/blocks', icon: Box },
  { name: 'Triggers', href: '/agent-builder/triggers', icon: Zap },
  { name: 'Workflows', href: '/agent-builder/workflows', icon: GitBranch },
  { name: 'Knowledgebases', href: '/agent-builder/knowledgebases', icon: Database },
  { name: 'Variables', href: '/agent-builder/variables', icon: Variable },
  { name: 'Executions', href: '/agent-builder/executions', icon: Activity },
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
          <nav className="space-y-2 p-4">
            {navigation.map((item) => {
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
