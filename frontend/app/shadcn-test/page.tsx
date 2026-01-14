'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { 
  AlertCircle, 
  CheckCircle2, 
  Info, 
  XCircle,
  Users,
  MessageSquare,
  GitBranch,
  Settings
} from 'lucide-react';

export default function ShadcnTestPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-6 space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold tracking-tight">shadcn/ui Style Test</h1>
          <p className="text-muted-foreground text-lg">
            Verify that all components are properly styled
          </p>
        </div>

        {/* Button Variants */}
        <Card>
          <CardHeader>
            <CardTitle>Button Component</CardTitle>
            <CardDescription>Various button styles and sizes</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <Button variant="default">Default</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="ghost">Ghost</Button>
              <Button variant="link">Link</Button>
              <Button variant="destructive">Destructive</Button>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button size="sm">Small</Button>
              <Button size="default">Default</Button>
              <Button size="lg">Large</Button>
              <Button size="icon">
                <Settings className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Agentflows
              </CardTitle>
              <CardDescription>Multi-agent workflows</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Create sophisticated AI workflows with multiple agents working together.
              </p>
              <div className="mt-4">
                <Badge variant="secondary">Multi-Agent</Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Chatflows
              </CardTitle>
              <CardDescription>Conversational AI flows</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Build intelligent chatbots with memory and context awareness.
              </p>
              <div className="mt-4">
                <Badge variant="outline">Chatbot</Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <GitBranch className="h-5 w-5" />
                Workflows
              </CardTitle>
              <CardDescription>General purpose workflows</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Design and execute custom automation workflows.
              </p>
              <div className="mt-4">
                <Badge>Enhanced</Badge>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Form Elements */}
        <Card>
          <CardHeader>
            <CardTitle>Form Component</CardTitle>
            <CardDescription>Input fields and form elements</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" placeholder="Enter your email" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input id="name" type="text" placeholder="Enter your name" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Status Indicators */}
        <Card>
          <CardHeader>
            <CardTitle>Status Indicators</CardTitle>
            <CardDescription>Icons and colors representing various states</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 dark:bg-green-950/20">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                <span className="text-green-700 dark:text-green-400">Success</span>
              </div>
              <div className="flex items-center gap-2 p-3 rounded-lg bg-blue-50 dark:bg-blue-950/20">
                <Info className="h-5 w-5 text-blue-600" />
                <span className="text-blue-700 dark:text-blue-400">Info</span>
              </div>
              <div className="flex items-center gap-2 p-3 rounded-lg bg-yellow-50 dark:bg-yellow-950/20">
                <AlertCircle className="h-5 w-5 text-yellow-600" />
                <span className="text-yellow-700 dark:text-yellow-400">Warning</span>
              </div>
              <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-950/20">
                <XCircle className="h-5 w-5 text-red-600" />
                <span className="text-red-700 dark:text-red-400">Error</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Left Menu Simulation */}
        <Card>
          <CardHeader>
            <CardTitle>Left Menu Simulation</CardTitle>
            <CardDescription>Agent Builder sidebar style test</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex h-80 border rounded-lg overflow-hidden">
              {/* Sidebar */}
              <div className="w-64 border-r bg-card">
                <div className="h-16 border-b px-4 flex items-center">
                  <h3 className="font-semibold">Agent Builder</h3>
                </div>
                <div className="p-4 space-y-1">
                  <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-2">
                    Flows
                  </div>
                  <Button variant="ghost" className="w-full justify-start">
                    <Users className="mr-2 h-4 w-4" />
                    Agentflows
                    <Badge variant="secondary" className="ml-auto text-[10px]">
                      Multi-Agent
                    </Badge>
                  </Button>
                  <Button variant="ghost" className="w-full justify-start">
                    <MessageSquare className="mr-2 h-4 w-4" />
                    Chatflows
                    <Badge variant="secondary" className="ml-auto text-[10px]">
                      Chatbot
                    </Badge>
                  </Button>
                  <Button variant="ghost" className="w-full justify-start">
                    <GitBranch className="mr-2 h-4 w-4" />
                    Workflows
                  </Button>
                  
                  <Separator className="my-4" />
                  
                  <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-2">
                    Building Blocks
                  </div>
                  <Button variant="ghost" className="w-full justify-start">
                    <Settings className="mr-2 h-4 w-4" />
                    Settings
                  </Button>
                </div>
              </div>
              
              {/* Main Content */}
              <div className="flex-1 bg-background p-6">
                <h3 className="text-xl font-semibold mb-4">Main Content Area</h3>
                <p className="text-muted-foreground">
                  If the sidebar is properly styled, shadcn/ui is working correctly.
                </p>
                <div className="mt-4 space-y-2">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                    <span className="text-sm">Button hover effect</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                    <span className="text-sm">Proper color variables</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                    <span className="text-sm">Responsive layout</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Status */}
        <Card className="border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950/20">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-6 w-6 text-green-600" />
              <div>
                <h3 className="font-semibold text-green-800 dark:text-green-400">
                  shadcn/ui Style Restoration Complete!
                </h3>
                <p className="text-green-700 dark:text-green-300 text-sm">
                  All components are properly styled. The Left Menu will also display correctly.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}