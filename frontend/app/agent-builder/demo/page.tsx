'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
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
  Sparkles,
  CheckCircle2,
  ArrowRight,
  Play,
  Pause,
  Settings,
  Eye,
} from 'lucide-react';

export default function AgentBuilderDemoPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/30 dark:from-slate-900 dark:via-blue-950/30 dark:to-purple-950/30">
      <div className="container mx-auto p-6 space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-green-500 to-emerald-500 shadow-lg">
              <Play className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                Agent Builder Demo
              </h1>
              <p className="text-slate-600 dark:text-slate-400">
                Interactive UI/UX Showcase
              </p>
            </div>
          </div>
          <p className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
            Experience the enhanced Agent Builder interface with modern design, 
            improved navigation, and intuitive user experience.
          </p>
        </div>

        {/* UI Improvements Showcase */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Menu Improvements */}
          <Card className="border-0 shadow-lg bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-500">
                  <Sparkles className="h-4 w-4 text-white" />
                </div>
                Enhanced Left Menu
              </CardTitle>
              <CardDescription>
                Redesigned navigation with improved visual hierarchy and user experience
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="text-sm">Color-coded sections with visual indicators</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="text-sm">Gradient backgrounds for active states</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="text-sm">Enhanced badges and descriptions</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="text-sm">Improved spacing and typography</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="text-sm">Backdrop blur and transparency effects</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Design System */}
          <Card className="border-0 shadow-lg bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-purple-500 to-pink-500">
                  <Eye className="h-4 w-4 text-white" />
                </div>
                Modern Design System
              </CardTitle>
              <CardDescription>
                Consistent visual language with shadcn/ui and Tailwind CSS
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="text-sm">Gradient backgrounds and glass morphism</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="text-sm">Consistent color palette and spacing</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="text-sm">Smooth animations and transitions</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="text-sm">Responsive design for all devices</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="text-sm">Dark mode support</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Navigation Sections Demo */}
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Navigation Sections</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Flows Section */}
            <Card className="group border-0 shadow-lg hover:shadow-xl transition-all duration-300 bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-950/50 dark:to-purple-950/50">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-500 shadow-lg">
                    <Users className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">Flows</CardTitle>
                    <Badge variant="secondary" className="text-xs mt-1">3 items</Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <MessageSquare className="h-4 w-4 text-blue-600" />
                    <span>Agentflows</span>
                    <Badge variant="outline" className="text-xs ml-auto">Multi-Agent</Badge>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <MessageSquare className="h-4 w-4 text-green-600" />
                    <span>Chatflows</span>
                    <Badge variant="outline" className="text-xs ml-auto">Chatbot</Badge>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <GitBranch className="h-4 w-4 text-orange-600" />
                    <span>Workflows</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Building Blocks Section */}
            <Card className="group border-0 shadow-lg hover:shadow-xl transition-all duration-300 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/50 dark:to-emerald-950/50">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-green-500 to-emerald-500 shadow-lg">
                    <Box className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">Building Blocks</CardTitle>
                    <Badge variant="secondary" className="text-xs mt-1">4 items</Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <Layers className="h-4 w-4 text-green-600" />
                    <span>Agents</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <Box className="h-4 w-4 text-blue-600" />
                    <span>Blocks</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <Users className="h-4 w-4 text-purple-600" />
                    <span>Team Templates</span>
                    <Badge variant="outline" className="text-xs ml-auto">New</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Developer Tools Section */}
            <Card className="group border-0 shadow-lg hover:shadow-xl transition-all duration-300 bg-gradient-to-br from-indigo-50 to-blue-50 dark:from-indigo-950/50 dark:to-blue-950/50">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-blue-500 shadow-lg">
                    <Key className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">Developer</CardTitle>
                    <Badge variant="secondary" className="text-xs mt-1">3 items</Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <Key className="h-4 w-4 text-indigo-600" />
                    <span>API Keys</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <Store className="h-4 w-4 text-purple-600" />
                    <span>Marketplace</span>
                    <Badge variant="outline" className="text-xs ml-auto">Enhanced</Badge>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <Settings className="h-4 w-4 text-slate-600" />
                    <span>Settings</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Interactive Demo */}
        <Card className="border-0 shadow-lg bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/50 dark:to-purple-950/50">
          <CardContent className="p-8">
            <div className="text-center space-y-6">
              <div className="flex items-center justify-center gap-3">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-purple-500 shadow-lg">
                  <Sparkles className="h-8 w-8 text-white" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                    Enhanced UI/UX Complete!
                  </h3>
                  <p className="text-slate-600 dark:text-slate-400">
                    Modern, intuitive, and visually appealing interface
                  </p>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-2xl mx-auto">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">100%</div>
                  <div className="text-sm text-slate-600 dark:text-slate-400">TailwindCSS Applied</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600 dark:text-green-400">✓</div>
                  <div className="text-sm text-slate-600 dark:text-slate-400">shadcn/ui Integrated</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">🎨</div>
                  <div className="text-sm text-slate-600 dark:text-slate-400">Modern Design</div>
                </div>
              </div>

              <div className="flex justify-center gap-4">
                <Button className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600">
                  <Play className="mr-2 h-4 w-4" />
                  Explore Features
                </Button>
                <Button variant="outline">
                  <ArrowRight className="mr-2 h-4 w-4" />
                  View Documentation
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}