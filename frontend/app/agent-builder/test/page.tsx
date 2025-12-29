'use client';

import React from 'react';

export default function AgentBuilderTestPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Agent Builder Test Page</h1>
      <p className="text-muted-foreground mb-4">
        This page should show the Left Menu from the agent-builder layout.
      </p>
      
      <div className="space-y-4">
        <div className="p-4 bg-card border rounded-lg">
          <h2 className="font-semibold mb-2">Layout Test</h2>
          <p>If you can see the Left Menu sidebar, the CSS is working correctly.</p>
          <p>If the sidebar is missing or unstyled, there's a CSS loading issue.</p>
        </div>
        
        <div className="p-4 bg-secondary rounded-lg">
          <h2 className="font-semibold mb-2">Expected Behavior</h2>
          <ul className="list-disc list-inside space-y-1 text-sm">
            <li>Left sidebar should be visible on desktop</li>
            <li>Sidebar should have "Agent Builder" title at the top</li>
            <li>Navigation sections: Flows, Building Blocks, Data & Knowledge, etc.</li>
            <li>Menu items should have icons and proper styling</li>
            <li>Hover effects should work on menu items</li>
          </ul>
        </div>
        
        <div className="p-4 bg-muted rounded-lg">
          <h2 className="font-semibold mb-2">Troubleshooting</h2>
          <p className="text-sm">
            If the sidebar is not visible, check the browser developer tools for:
          </p>
          <ul className="list-disc list-inside space-y-1 text-sm mt-2">
            <li>CSS loading errors in the Network tab</li>
            <li>JavaScript errors in the Console tab</li>
            <li>Missing CSS variables in the Elements tab</li>
            <li>Tailwind CSS classes not being applied</li>
          </ul>
        </div>
      </div>
    </div>
  );
}