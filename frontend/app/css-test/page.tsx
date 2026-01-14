'use client';

import React from 'react';
import { Button } from '@/components/ui/button';

export default function CSSTestPage() {
  return (
    <div className="min-h-screen bg-background text-foreground p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <h1 className="text-3xl font-bold text-center mb-8">CSS Recovery Test</h1>
        
        {/* Basic Colors Test */}
        <div className="bg-card border rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Basic Color Test</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-primary text-primary-foreground rounded text-center">Primary</div>
            <div className="p-4 bg-secondary text-secondary-foreground rounded text-center">Secondary</div>
            <div className="p-4 bg-muted text-muted-foreground rounded text-center">Muted</div>
            <div className="p-4 bg-destructive text-destructive-foreground rounded text-center">Destructive</div>
          </div>
        </div>

        {/* Button Test */}
        <div className="bg-card border rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Button Test</h2>
          <div className="flex flex-wrap gap-4">
            <Button variant="default">Default</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="destructive">Destructive</Button>
          </div>
        </div>

        {/* Layout Test */}
        <div className="bg-card border rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Layout Test</h2>
          <div className="flex gap-4">
            <div className="flex-1 p-4 bg-muted rounded">
              <h3 className="font-medium mb-2">Flex Item 1</h3>
              <p className="text-muted-foreground text-sm">This area uses the flex-1 class.</p>
            </div>
            <div className="w-64 p-4 bg-secondary rounded">
              <h3 className="font-medium mb-2">Fixed Width</h3>
              <p className="text-secondary-foreground text-sm">This area uses the w-64 class.</p>
            </div>
          </div>
        </div>

        {/* Sidebar Simulation */}
        <div className="bg-card border rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Sidebar Simulation</h2>
          <div className="flex h-64 border rounded overflow-hidden">
            {/* Sidebar */}
            <div className="w-64 border-r bg-card">
              <div className="h-16 border-b px-4 flex items-center bg-card">
                <h3 className="font-semibold text-card-foreground">Agent Builder</h3>
              </div>
              <div className="p-4 space-y-1">
                <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-2">
                  Flows
                </div>
                <button className="w-full text-left px-3 py-2 text-sm rounded hover:bg-secondary transition-colors text-foreground">
                  Agentflows
                </button>
                <button className="w-full text-left px-3 py-2 text-sm rounded hover:bg-secondary transition-colors text-foreground">
                  Chatflows
                </button>
                <button className="w-full text-left px-3 py-2 text-sm rounded hover:bg-secondary transition-colors text-foreground">
                  Workflows
                </button>
              </div>
            </div>
            {/* Main Content */}
            <div className="flex-1 bg-background p-4">
              <h3 className="font-semibold mb-2 text-foreground">Main Content Area</h3>
              <p className="text-muted-foreground text-sm">
                If the sidebar is properly styled, the Left Menu CSS has been recovered.
              </p>
            </div>
          </div>
        </div>

        {/* Status */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="font-medium text-green-800">CSS Recovery Complete</span>
          </div>
          <p className="text-green-700 text-sm mt-2">
            Downgraded to Tailwind CSS v3 and modified the configuration. 
            If the elements above are properly styled, the Left Menu should display correctly.
          </p>
        </div>
      </div>
    </div>
  );
}