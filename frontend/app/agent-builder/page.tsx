'use client';

import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Users,
  MessageSquare,
  GitBranch,
  Layers,
  Box,
  Database,
  Activity,
  BarChart3,
  Key,
  Store,
  Plus,
  ArrowRight,
  Sparkles,
  Zap,
  Brain,
  Workflow,
  TrendingUp,
} from 'lucide-react';

const quickActions = [
  {
    title: 'Create Agentflow',
    description: 'Build multi-agent workflows',
    icon: Users,
    href: '/agent-builder/agentflows/new',
    color: 'from-blue-500 to-purple-500',
    badge: 'Popular',
  },
  {
    title: 'Create Chatflow',
    description: 'Design conversational AI',
    icon: MessageSquare,
    href: '/agent-builder/chatflows/new',
    color: 'from-green-500 to-emerald-500',
    badge: 'Easy',
  },
  {
    title: 'Create Workflow',
    description: 'General automation',
    icon: GitBranch,
    href: '/agent-builder/workflows/new',
    color: 'from-orange-500 to-amber-500',
  },
  {
    title: 'Browse Templates',
    description: 'Start from marketplace',
    icon: Store,
    href: '/agent-builder/marketplace',
    color: 'from-purple-500 to-pink-500',
    badge: 'New',
  },
];

const recentStats = [
  { label: 'Active Workflows', value: '12', change: '+3', icon: Workflow },
  { label: 'Total Executions', value: '1,247', change: '+156', icon: Activity },
  { label: 'Success Rate', value: '98.2%', change: '+2.1%', icon: TrendingUp },
  { label: 'Avg Response', value: '1.2s', change: '-0.3s', icon: Zap },
];

const featuredSections = [
  {
    title: 'Building Blocks',
    description: 'Manage your reusable components',
    items: [
      { name: 'Agents', count: 8, icon: Layers },
      { name: 'Blocks', count: 24, icon: Box },
      { name: 'Variables', count: 12, icon: Database },
    ],
    href: '/agent-builder/agents',
  },
  {
    title: 'Monitoring',
    description: 'Track performance and usage',
    items: [
      { name: 'Executions', count: 156, icon: Activity },
      { name: 'Observability', count: 5, icon: BarChart3 },
      { name: 'API Keys', count: 3, icon: Key },
    ],
    href: '/agent-builder/executions',
  },
];

export default function AgentBuilderPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/30 dark:from-slate-900 dark:via-blue-950/30 dark:to-purple-950/30">
      <div className="container mx-auto p-6 space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-purple-500 shadow-lg">
              <Sparkles className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Agent Builder
              </h1>
              <p className="text-slate-600 dark:text-slate-400">
                Visual AI Workflow Platform
              </p>
            </div>
          </div>
          <p className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
            Create sophisticated AI workflows with drag-and-drop simplicity. 
            Build everything from simple automations to complex multi-agent systems.
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {recentStats.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <Card key={index} className="relative overflow-hidden border-0 shadow-md bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-600 dark:text-slate-400">{stat.label}</p>
                      <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{stat.value}</p>
                      <p className="text-xs text-green-600 dark:text-green-400 font-medium">{stat.change}</p>
                    </div>
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500/10 to-purple-500/10">
                      <Icon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Quick Actions */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Quick Start</h2>
            <Badge variant="secondary" className="text-xs">
              Get Started
            </Badge>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {quickActions.map((action, index) => {
              const Icon = action.icon;
              return (
                <Link key={index} href={action.href}>
                  <Card className="group relative overflow-hidden border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 bg-white dark:bg-slate-800">
                    <div className={`absolute inset-0 bg-gradient-to-br ${action.color} opacity-5 group-hover:opacity-10 transition-opacity`} />
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className={`flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${action.color} shadow-lg`}>
                          <Icon className="h-6 w-6 text-white" />
                        </div>
                        {action.badge && (
                          <Badge variant="outline" className="text-xs">
                            {action.badge}
                          </Badge>
                        )}
                      </div>
                      <CardTitle className="text-lg group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                        {action.title}
                      </CardTitle>
                      <CardDescription className="text-sm">
                        {action.description}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="flex items-center text-sm text-blue-600 dark:text-blue-400 font-medium group-hover:gap-2 transition-all">
                        <span>Get Started</span>
                        <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Featured Sections */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {featuredSections.map((section, index) => (
            <Card key={index} className="border-0 shadow-lg bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-xl">{section.title}</CardTitle>
                    <CardDescription>{section.description}</CardDescription>
                  </div>
                  <Link href={section.href}>
                    <Button variant="outline" size="sm" className="gap-2">
                      View All
                      <ArrowRight className="h-4 w-4" />
                    </Button>
                  </Link>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {section.items.map((item, itemIndex) => {
                    const Icon = item.icon;
                    return (
                      <div key={itemIndex} className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
                        <div className="flex items-center gap-3">
                          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-slate-500 to-slate-600">
                            <Icon className="h-4 w-4 text-white" />
                          </div>
                          <span className="font-medium text-slate-900 dark:text-slate-100">{item.name}</span>
                        </div>
                        <Badge variant="secondary" className="text-xs">
                          {item.count}
                        </Badge>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Getting Started */}
        <Card className="border-0 shadow-lg bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/50 dark:to-purple-950/50">
          <CardContent className="p-8">
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-purple-500 shadow-lg">
                <Brain className="h-8 w-8 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
                  Ready to build your first AI workflow?
                </h3>
                <p className="text-slate-600 dark:text-slate-400 mb-4">
                  Start with our guided tutorial or explore pre-built templates in the marketplace.
                </p>
                <div className="flex gap-3">
                  <Button className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600">
                    <Plus className="mr-2 h-4 w-4" />
                    Create Workflow
                  </Button>
                  <Button variant="outline">
                    View Tutorial
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}