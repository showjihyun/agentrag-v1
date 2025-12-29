'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Menu, X, Users, MessageSquare, GitBranch } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function TestSidebarPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
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
          <h2 className="text-lg font-semibold">Test Sidebar</h2>
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>
        
        <div className="h-[calc(100vh-4rem)] overflow-auto">
          <nav className="space-y-1 p-4">
            {/* Test Section */}
            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-2">
              Test Menu Items
            </div>
            
            <Button variant="ghost" className="w-full justify-start">
              <Users className="mr-2 h-4 w-4" />
              Agentflows
              <span className="ml-auto text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded">
                Multi-Agent
              </span>
            </Button>
            
            <Button variant="ghost" className="w-full justify-start">
              <MessageSquare className="mr-2 h-4 w-4" />
              Chatflows
              <span className="ml-auto text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded">
                Chatbot
              </span>
            </Button>
            
            <Button variant="ghost" className="w-full justify-start">
              <GitBranch className="mr-2 h-4 w-4" />
              Workflows
            </Button>
            
            {/* Test different background colors */}
            <div className="mt-4 space-y-2">
              <div className="p-2 bg-red-100 text-red-800 rounded">Red Test</div>
              <div className="p-2 bg-blue-100 text-blue-800 rounded">Blue Test</div>
              <div className="p-2 bg-green-100 text-green-800 rounded">Green Test</div>
              <div className="p-2 bg-card border rounded">Card Background</div>
              <div className="p-2 bg-secondary text-secondary-foreground rounded">Secondary Background</div>
              <div className="p-2 bg-muted text-muted-foreground rounded">Muted Background</div>
            </div>
          </nav>
        </div>
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
          <h1 className="ml-4 text-lg font-semibold">Test Sidebar</h1>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-6">
          <div className="max-w-4xl mx-auto">
            <h1 className="text-3xl font-bold mb-6">Sidebar CSS Test</h1>
            
            <div className="space-y-4">
              <div className="p-4 bg-card border rounded-lg">
                <h2 className="text-xl font-semibold mb-2">Test Results</h2>
                <p>This page tests the Left Menu styling to identify any CSS issues.</p>
              </div>
              
              <div className="p-4 bg-secondary rounded-lg">
                <h3 className="font-semibold mb-2">What to check:</h3>
                <ul className="list-disc list-inside space-y-1">
                  <li>Sidebar should be visible on desktop (lg screens and up)</li>
                  <li>Sidebar should be hidden on mobile by default</li>
                  <li>Mobile menu button should toggle sidebar</li>
                  <li>Colors should match the design system</li>
                  <li>Hover effects should work on buttons</li>
                  <li>Icons should be properly aligned</li>
                </ul>
              </div>
              
              <div className="p-4 bg-muted rounded-lg">
                <h3 className="font-semibold mb-2">CSS Variables Test:</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>Background: <span className="bg-background p-1 border">background</span></div>
                  <div>Foreground: <span className="text-foreground">foreground</span></div>
                  <div>Card: <span className="bg-card p-1 border">card</span></div>
                  <div>Card Foreground: <span className="text-card-foreground">card-foreground</span></div>
                  <div>Primary: <span className="bg-primary text-primary-foreground p-1 rounded">primary</span></div>
                  <div>Secondary: <span className="bg-secondary text-secondary-foreground p-1 rounded">secondary</span></div>
                  <div>Muted: <span className="bg-muted text-muted-foreground p-1 rounded">muted</span></div>
                  <div>Border: <span className="border-2 border-border p-1">border</span></div>
                </div>
              </div>
              
              <Button 
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden"
              >
                Toggle Sidebar (Mobile)
              </Button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}