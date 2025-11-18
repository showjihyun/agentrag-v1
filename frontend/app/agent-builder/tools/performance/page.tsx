'use client';

import { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { ToolPerformanceMonitor } from '@/components/agent-builder/ToolPerformanceMonitor';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function ToolPerformancePage() {
  const searchParams = useSearchParams();
  const initialToolId = searchParams.get('tool_id') || 'http_request';
  
  const [toolId, setToolId] = useState(initialToolId);
  const [selectedTool, setSelectedTool] = useState(initialToolId);

  const handleToolChange = () => {
    setSelectedTool(toolId);
  };

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Tool Selector */}
      <Card>
        <CardHeader>
          <CardTitle>Select Tool to Monitor</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <div className="flex-1">
              <Label htmlFor="tool-id">Tool ID</Label>
              <Input
                id="tool-id"
                value={toolId}
                onChange={(e) => setToolId(e.target.value)}
                placeholder="Enter tool ID (e.g., http_request)"
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={handleToolChange}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
              >
                Load Metrics
              </button>
            </div>
          </div>
          
          {/* Quick Select */}
          <div className="mt-4">
            <p className="text-sm text-muted-foreground mb-2">Quick select:</p>
            <div className="flex flex-wrap gap-2">
              {[
                'http_request',
                'llm_call',
                'calculator',
                'vector_search',
                'python_executor',
                'web_search'
              ].map((id) => (
                <button
                  key={id}
                  onClick={() => {
                    setToolId(id);
                    setSelectedTool(id);
                  }}
                  className="px-3 py-1 text-sm border rounded-md hover:bg-accent"
                >
                  {id}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Monitor */}
      <ToolPerformanceMonitor 
        toolId={selectedTool}
        timeRange="24h"
        showAlerts={true}
      />
    </div>
  );
}
