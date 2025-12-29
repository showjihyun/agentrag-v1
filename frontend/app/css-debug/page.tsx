'use client';

import React, { useEffect, useState } from 'react';

export default function CSSDebugPage() {
  const [cssVariables, setCssVariables] = useState<Record<string, string>>({});

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const root = document.documentElement;
      const computedStyle = getComputedStyle(root);
      
      const variables: Record<string, string> = {};
      const cssVarNames = [
        '--background',
        '--foreground',
        '--card',
        '--card-foreground',
        '--primary',
        '--primary-foreground',
        '--secondary',
        '--secondary-foreground',
        '--muted',
        '--muted-foreground',
        '--border',
        '--input',
        '--ring',
        '--radius'
      ];
      
      cssVarNames.forEach(varName => {
        variables[varName] = computedStyle.getPropertyValue(varName).trim();
      });
      
      setCssVariables(variables);
    }
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">CSS Debug Information</h1>
        
        <div className="space-y-6">
          {/* CSS Variables */}
          <div className="bg-card border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">CSS Custom Properties</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(cssVariables).map(([varName, value]) => (
                <div key={varName} className="flex justify-between items-center p-2 bg-muted rounded">
                  <code className="text-sm font-mono">{varName}</code>
                  <span className="text-sm text-muted-foreground">{value || 'undefined'}</span>
                </div>
              ))}
            </div>
          </div>
          
          {/* Color Swatches */}
          <div className="bg-card border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Color Swatches</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-2">
                <div className="w-full h-12 bg-background border rounded"></div>
                <p className="text-sm">background</p>
              </div>
              <div className="space-y-2">
                <div className="w-full h-12 bg-card border rounded"></div>
                <p className="text-sm">card</p>
              </div>
              <div className="space-y-2">
                <div className="w-full h-12 bg-primary rounded"></div>
                <p className="text-sm">primary</p>
              </div>
              <div className="space-y-2">
                <div className="w-full h-12 bg-secondary rounded"></div>
                <p className="text-sm">secondary</p>
              </div>
              <div className="space-y-2">
                <div className="w-full h-12 bg-muted rounded"></div>
                <p className="text-sm">muted</p>
              </div>
              <div className="space-y-2">
                <div className="w-full h-12 bg-destructive rounded"></div>
                <p className="text-sm">destructive</p>
              </div>
              <div className="space-y-2">
                <div className="w-full h-12 bg-accent rounded"></div>
                <p className="text-sm">accent</p>
              </div>
              <div className="space-y-2">
                <div className="w-full h-12 bg-popover border rounded"></div>
                <p className="text-sm">popover</p>
              </div>
            </div>
          </div>
          
          {/* Typography Test */}
          <div className="bg-card border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Typography Test</h2>
            <div className="space-y-2">
              <p className="text-foreground">Default foreground text</p>
              <p className="text-muted-foreground">Muted foreground text</p>
              <p className="text-card-foreground">Card foreground text</p>
              <p className="text-primary">Primary text</p>
              <p className="text-secondary-foreground">Secondary foreground text</p>
            </div>
          </div>
          
          {/* Border Test */}
          <div className="bg-card border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Border Test</h2>
            <div className="space-y-4">
              <div className="p-4 border border-border rounded">Default border</div>
              <div className="p-4 border-2 border-primary rounded">Primary border</div>
              <div className="p-4 border-r-4 border-secondary bg-secondary/10">Right border (like sidebar)</div>
            </div>
          </div>
          
          {/* Sidebar Simulation */}
          <div className="bg-card border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Sidebar Simulation</h2>
            <div className="flex h-64 border rounded overflow-hidden">
              <div className="w-64 border-r bg-card">
                <div className="h-16 border-b px-4 flex items-center">
                  <h3 className="font-semibold">Agent Builder</h3>
                </div>
                <div className="p-4 space-y-1">
                  <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-2">
                    Flows
                  </div>
                  <button className="w-full text-left px-3 py-2 text-sm rounded hover:bg-secondary transition-colors">
                    Agentflows
                  </button>
                  <button className="w-full text-left px-3 py-2 text-sm rounded hover:bg-secondary transition-colors">
                    Chatflows
                  </button>
                </div>
              </div>
              <div className="flex-1 bg-background p-4">
                <p>Main content area</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}