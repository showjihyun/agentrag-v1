'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
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
  UserCheck,
  Sparkles,
  ChevronRight,
} from 'lucide-react';

const navigation = [
  // Flow Types (Primary)
  { 
    name: 'Agentflows', 
    href: '/agent-builder/agentflows', 
    icon: Users, 
    badge: 'Multi-Agent',
    badgeVariant: 'default' as const,
    description: 'Multi-agent workflows'
  },
  { 
    name: 'Chatflows', 
    href: '/agent-builder/chatflows', 
    icon: MessageSquare, 
    badge: 'Chatbot',
    badgeVariant: 'secondary' as const,
    description: 'Conversational AI flows'
  },
  { 
    name: 'Workflows', 
    href: '/agent-builder/workflows', 
    icon: GitBranch,
    description: 'General purpose workflows'
  },
  // Building Blocks
  { 
    name: 'Agents', 
    href: '/agent-builder/agents', 
    icon: Layers,
    description: 'AI agent configurations'
  },
  { 
    name: 'Team Templates', 
    href: '/agent-builder/team-templates', 
    icon: UserCheck, 
    badge: 'New',
    badgeVariant: 'outline' as const,
    description: 'Collaborative templates'
  },
  { 
    name: 'Blocks', 
    href: '/agent-builder/blocks', 
    icon: Box,
    description: 'Reusable workflow blocks'
  },
  { 
    name: 'Triggers', 
    href: '/agent-builder/triggers', 
    icon: Zap,
    description: 'Event-driven automation'
  },
  // Data & Knowledge
  { 
    name: 'Knowledgebases', 
    href: '/agent-builder/knowledgebases', 
    icon: Database,
    description: 'Document and data storage'
  },
  { 
    name: 'Variables', 
    href: '/agent-builder/variables', 
    icon: Variable,
    description: 'Global configuration'
  },
  // Monitoring & Observability
  { 
    name: 'Executions', 
    href: '/agent-builder/executions', 
    icon: Activity,
    description: 'Workflow execution history'
  },
  { 
    name: 'Observability', 
    href: '/agent-builder/observability', 
    icon: BarChart3, 
    badge: 'New',
    badgeVariant: 'outline' as const,
    description: 'Performance monitoring'
  },
  // Developer Tools
  { 
    name: 'API Keys', 
    href: '/agent-builder/api-keys', 
    icon: Key,
    description: 'External integrations'
  },
  { 
    name: 'Embed', 
    href: '/agent-builder/embed', 
    icon: Code,
    description: 'Integration code'
  },
  { 
    name: 'Marketplace', 
    href: '/agent-builder/marketplace', 
    icon: Store, 
    badge: 'Enhanced',
    badgeVariant: 'secondary' as const,
    description: 'Template marketplace'
  },
];

const settingsNavigation = [
  { 
    name: 'Settings', 
    href: '/agent-builder/settings', 
    icon: Settings,
    description: 'Application preferences'
  },
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
        <div className="flex h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
          {/* Mobile sidebar backdrop */}
          {sidebarOpen && (
            <div
              className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
              onClick={() => setSidebarOpen(false)}
            />
          )}

          {/* Sidebar */}
          <aside
            className={cn(
              "fixed inset-y-0 left-0 z-50 w-72 bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border-r border-slate-200/60 dark:border-slate-700/60 shadow-xl transition-all duration-300 lg:static lg:translate-x-0",
              sidebarOpen ? "translate-x-0" : "-translate-x-full"
            )}
          >
            {/* Header */}
            <div className="flex h-16 items-center justify-between border-b border-slate-200/60 dark:border-slate-700/60 px-6 lg:justify-center bg-gradient-to-r from-blue-600 to-purple-600">
              <Link href="/agent-builder" className="group flex items-center gap-2 hover:opacity-90 transition-opacity">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/20 backdrop-blur-sm">
                  <Sparkles className="h-4 w-4 text-white" />
                </div>
                <h2 className="text-lg font-bold text-white cursor-pointer">Agent Builder</h2>
              </Link>
              <Button
                variant="ghost"
                size="icon"
                className="lg:hidden text-white hover:bg-white/20"
                onClick={() => setSidebarOpen(false)}
              >
                <X className="h-5 w-5" />
              </Button>
            </div>

            <ScrollArea className="h-[calc(100vh-4rem)]">
              <nav className="space-y-2 p-4">
                {/* Flow Types Section */}
                <div className="mb-4">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3 px-3">
                    <div className="h-1 w-1 rounded-full bg-blue-500"></div>
                    Flows
                  </div>
                  <div className="space-y-1">
                    {navigation.slice(0, 3).map((item) => {
                      const Icon = item.icon;
                      const isActive = pathname?.startsWith(item.href);
                      return (
                        <Link key={item.name} href={item.href}>
                          <div
                            className={cn(
                              "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 hover:bg-slate-100 dark:hover:bg-slate-800/60",
                              isActive 
                                ? "bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/50 dark:to-purple-950/50 text-blue-700 dark:text-blue-300 shadow-sm border border-blue-200/50 dark:border-blue-800/50" 
                                : "text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100"
                            )}
                            onClick={() => setSidebarOpen(false)}
                          >
                            <div className={cn(
                              "flex h-8 w-8 items-center justify-center rounded-lg transition-colors",
                              isActive 
                                ? "bg-gradient-to-br from-blue-500 to-purple-500 text-white shadow-sm" 
                                : "bg-slate-100 dark:bg-slate-800 group-hover:bg-slate-200 dark:group-hover:bg-slate-700"
                            )}>
                              <Icon className="h-4 w-4" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="truncate">{item.name}</span>
                                {item.badge && (
                                  <Badge 
                                    variant={item.badgeVariant || 'default'} 
                                    className="text-[10px] px-1.5 py-0.5 h-5"
                                  >
                                    {item.badge}
                                  </Badge>
                                )}
                              </div>
                              <p className="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5">
                                {item.description}
                              </p>
                            </div>
                            {isActive && (
                              <ChevronRight className="h-4 w-4 text-blue-500" />
                            )}
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                </div>

                <Separator className="my-4" />

                {/* Building Blocks Section */}
                <div className="mb-4">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3 px-3">
                    <div className="h-1 w-1 rounded-full bg-green-500"></div>
                    Building Blocks
                  </div>
                  <div className="space-y-1">
                    {navigation.slice(3, 7).map((item) => {
                      const Icon = item.icon;
                      const isActive = pathname?.startsWith(item.href);
                      return (
                        <Link key={item.name} href={item.href}>
                          <div
                            className={cn(
                              "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 hover:bg-slate-100 dark:hover:bg-slate-800/60",
                              isActive 
                                ? "bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950/50 dark:to-emerald-950/50 text-green-700 dark:text-green-300 shadow-sm border border-green-200/50 dark:border-green-800/50" 
                                : "text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100"
                            )}
                            onClick={() => setSidebarOpen(false)}
                          >
                            <div className={cn(
                              "flex h-8 w-8 items-center justify-center rounded-lg transition-colors",
                              isActive 
                                ? "bg-gradient-to-br from-green-500 to-emerald-500 text-white shadow-sm" 
                                : "bg-slate-100 dark:bg-slate-800 group-hover:bg-slate-200 dark:group-hover:bg-slate-700"
                            )}>
                              <Icon className="h-4 w-4" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="truncate">{item.name}</span>
                                {item.badge && (
                                  <Badge 
                                    variant={item.badgeVariant || 'default'} 
                                    className="text-[10px] px-1.5 py-0.5 h-5"
                                  >
                                    {item.badge}
                                  </Badge>
                                )}
                              </div>
                              <p className="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5">
                                {item.description}
                              </p>
                            </div>
                            {isActive && (
                              <ChevronRight className="h-4 w-4 text-green-500" />
                            )}
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                </div>

                <Separator className="my-4" />

                {/* Data & Knowledge Section */}
                <div className="mb-4">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3 px-3">
                    <div className="h-1 w-1 rounded-full bg-orange-500"></div>
                    Data & Knowledge
                  </div>
                  <div className="space-y-1">
                    {navigation.slice(7, 9).map((item) => {
                      const Icon = item.icon;
                      const isActive = pathname?.startsWith(item.href);
                      return (
                        <Link key={item.name} href={item.href}>
                          <div
                            className={cn(
                              "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 hover:bg-slate-100 dark:hover:bg-slate-800/60",
                              isActive 
                                ? "bg-gradient-to-r from-orange-50 to-amber-50 dark:from-orange-950/50 dark:to-amber-950/50 text-orange-700 dark:text-orange-300 shadow-sm border border-orange-200/50 dark:border-orange-800/50" 
                                : "text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100"
                            )}
                            onClick={() => setSidebarOpen(false)}
                          >
                            <div className={cn(
                              "flex h-8 w-8 items-center justify-center rounded-lg transition-colors",
                              isActive 
                                ? "bg-gradient-to-br from-orange-500 to-amber-500 text-white shadow-sm" 
                                : "bg-slate-100 dark:bg-slate-800 group-hover:bg-slate-200 dark:group-hover:bg-slate-700"
                            )}>
                              <Icon className="h-4 w-4" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="truncate">{item.name}</span>
                                {item.badge && (
                                  <Badge 
                                    variant={item.badgeVariant || 'default'} 
                                    className="text-[10px] px-1.5 py-0.5 h-5"
                                  >
                                    {item.badge}
                                  </Badge>
                                )}
                              </div>
                              <p className="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5">
                                {item.description}
                              </p>
                            </div>
                            {isActive && (
                              <ChevronRight className="h-4 w-4 text-orange-500" />
                            )}
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                </div>

                <Separator className="my-4" />

                {/* Observability Section */}
                <div className="mb-4">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3 px-3">
                    <div className="h-1 w-1 rounded-full bg-purple-500"></div>
                    Observability
                  </div>
                  <div className="space-y-1">
                    {navigation.slice(9, 11).map((item) => {
                      const Icon = item.icon;
                      const isActive = pathname?.startsWith(item.href);
                      return (
                        <Link key={item.name} href={item.href}>
                          <div
                            className={cn(
                              "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 hover:bg-slate-100 dark:hover:bg-slate-800/60",
                              isActive 
                                ? "bg-gradient-to-r from-purple-50 to-violet-50 dark:from-purple-950/50 dark:to-violet-950/50 text-purple-700 dark:text-purple-300 shadow-sm border border-purple-200/50 dark:border-purple-800/50" 
                                : "text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100"
                            )}
                            onClick={() => setSidebarOpen(false)}
                          >
                            <div className={cn(
                              "flex h-8 w-8 items-center justify-center rounded-lg transition-colors",
                              isActive 
                                ? "bg-gradient-to-br from-purple-500 to-violet-500 text-white shadow-sm" 
                                : "bg-slate-100 dark:bg-slate-800 group-hover:bg-slate-200 dark:group-hover:bg-slate-700"
                            )}>
                              <Icon className="h-4 w-4" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="truncate">{item.name}</span>
                                {item.badge && (
                                  <Badge 
                                    variant={item.badgeVariant || 'default'} 
                                    className="text-[10px] px-1.5 py-0.5 h-5"
                                  >
                                    {item.badge}
                                  </Badge>
                                )}
                              </div>
                              <p className="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5">
                                {item.description}
                              </p>
                            </div>
                            {isActive && (
                              <ChevronRight className="h-4 w-4 text-purple-500" />
                            )}
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                </div>

                <Separator className="my-4" />

                {/* Developer Section */}
                <div className="mb-4">
                  <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3 px-3">
                    <div className="h-1 w-1 rounded-full bg-indigo-500"></div>
                    Developer
                  </div>
                  <div className="space-y-1">
                    {navigation.slice(11).map((item) => {
                      const Icon = item.icon;
                      const isActive = pathname?.startsWith(item.href);
                      return (
                        <Link key={item.name} href={item.href}>
                          <div
                            className={cn(
                              "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 hover:bg-slate-100 dark:hover:bg-slate-800/60",
                              isActive 
                                ? "bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-950/50 dark:to-blue-950/50 text-indigo-700 dark:text-indigo-300 shadow-sm border border-indigo-200/50 dark:border-indigo-800/50" 
                                : "text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100"
                            )}
                            onClick={() => setSidebarOpen(false)}
                          >
                            <div className={cn(
                              "flex h-8 w-8 items-center justify-center rounded-lg transition-colors",
                              isActive 
                                ? "bg-gradient-to-br from-indigo-500 to-blue-500 text-white shadow-sm" 
                                : "bg-slate-100 dark:bg-slate-800 group-hover:bg-slate-200 dark:group-hover:bg-slate-700"
                            )}>
                              <Icon className="h-4 w-4" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="truncate">{item.name}</span>
                                {item.badge && (
                                  <Badge 
                                    variant={item.badgeVariant || 'default'} 
                                    className="text-[10px] px-1.5 py-0.5 h-5"
                                  >
                                    {item.badge}
                                  </Badge>
                                )}
                              </div>
                              <p className="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5">
                                {item.description}
                              </p>
                            </div>
                            {isActive && (
                              <ChevronRight className="h-4 w-4 text-indigo-500" />
                            )}
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                </div>

                <Separator className="my-4" />

                {/* Settings Section */}
                <div className="mb-4">
                  {settingsNavigation.map((item) => {
                    const Icon = item.icon;
                    const isActive = pathname?.startsWith(item.href);
                    return (
                      <Link key={item.name} href={item.href}>
                        <div
                          className={cn(
                            "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 hover:bg-slate-100 dark:hover:bg-slate-800/60",
                            isActive 
                              ? "bg-gradient-to-r from-slate-50 to-gray-50 dark:from-slate-800/50 dark:to-gray-800/50 text-slate-700 dark:text-slate-300 shadow-sm border border-slate-200/50 dark:border-slate-700/50" 
                              : "text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100"
                          )}
                          onClick={() => setSidebarOpen(false)}
                        >
                          <div className={cn(
                            "flex h-8 w-8 items-center justify-center rounded-lg transition-colors",
                            isActive 
                              ? "bg-gradient-to-br from-slate-500 to-gray-500 text-white shadow-sm" 
                              : "bg-slate-100 dark:bg-slate-800 group-hover:bg-slate-200 dark:group-hover:bg-slate-700"
                          )}>
                            <Icon className="h-4 w-4" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <span className="truncate">{item.name}</span>
                            <p className="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5">
                              {item.description}
                            </p>
                          </div>
                          {isActive && (
                            <ChevronRight className="h-4 w-4 text-slate-500" />
                          )}
                        </div>
                      </Link>
                    );
                  })}
                </div>
              </nav>
            </ScrollArea>
          </aside>

          {/* Main content */}
          <div className="flex flex-1 flex-col overflow-hidden">
            {/* Mobile header */}
            <header className="flex h-16 items-center border-b border-slate-200/60 dark:border-slate-700/60 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl px-4 lg:hidden shadow-sm">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarOpen(true)}
                className="hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <Menu className="h-5 w-5" />
              </Button>
              <Link href="/agent-builder" className="ml-4 flex items-center gap-2 hover:opacity-80 transition-opacity">
                <div className="flex h-6 w-6 items-center justify-center rounded bg-gradient-to-br from-blue-500 to-purple-500">
                  <Sparkles className="h-3 w-3 text-white" />
                </div>
                <h1 className="text-lg font-semibold cursor-pointer">Agent Builder</h1>
              </Link>
            </header>

            {/* Page content */}
            <main className="flex-1 overflow-auto bg-slate-50/50 dark:bg-slate-900/50">
              {children}
            </main>
          </div>
        </div>
      </ToastProvider>
    </AgentBuilderErrorBoundary>
  );
}
