"use client";

/**
 * Tool Preview - 실시간 미리보기 컴포넌트
 */

import React from "react";
import { Play, CheckCircle2, AlertCircle, Code2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import type { ToolPreviewProps } from "./types";

export function ToolPreview({ tool, config, showOutput = false }: ToolPreviewProps) {
  const [testResult, setTestResult] = React.useState<any>(null);
  const [testing, setTesting] = React.useState(false);

  const handleTest = async () => {
    setTesting(true);
    try {
      // Simulate tool execution
      await new Promise(resolve => setTimeout(resolve, 1000));
      setTestResult({
        success: true,
        output: { message: "Test execution successful", data: config },
        duration: 1.2,
      });
    } catch (error) {
      setTestResult({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Tool Info */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-semibold"
            style={{ backgroundColor: tool.bg_color || "#6B7280" }}
          >
            {tool.icon || tool.name.charAt(0)}
          </div>
          <div className="flex-1">
            <h4 className="text-sm font-semibold">{tool.name}</h4>
            <p className="text-xs text-muted-foreground">{tool.category}</p>
          </div>
        </div>

        {tool.tags && tool.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {tool.tags.map((tag) => (
              <Badge key={tag} variant="outline" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </div>

      <Separator />

      {/* Configuration Summary */}
      <div className="space-y-2">
        <h4 className="text-sm font-semibold">Configuration</h4>
        <div className="space-y-1">
          {Object.entries(config).filter(([key]) => !key.startsWith('_')).map(([key, value]) => (
            <div key={key} className="flex items-start justify-between gap-2 text-xs">
              <span className="text-muted-foreground font-medium">{key}:</span>
              <span className="text-right font-mono truncate max-w-[60%]">
                {typeof value === 'object' ? JSON.stringify(value) : String(value)}
              </span>
            </div>
          ))}
          
          {Object.keys(config).filter(k => !k.startsWith('_')).length === 0 && (
            <p className="text-xs text-muted-foreground italic">No parameters configured</p>
          )}
        </div>
      </div>

      {showOutput && (
        <>
          <Separator />

          {/* Test Execution */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold">Test Execution</h4>
              <Button
                size="sm"
                onClick={handleTest}
                disabled={testing}
                className="gap-2"
              >
                <Play className="h-3 w-3" />
                {testing ? 'Testing...' : 'Test'}
              </Button>
            </div>

            {testResult && (
              <div className={`p-3 rounded-lg border ${
                testResult.success
                  ? 'bg-green-50 border-green-200 dark:bg-green-950 dark:border-green-800'
                  : 'bg-red-50 border-red-200 dark:bg-red-950 dark:border-red-800'
              }`}>
                <div className="flex items-start gap-2">
                  {testResult.success ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400 mt-0.5" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400 mt-0.5" />
                  )}
                  <div className="flex-1 space-y-2">
                    <p className="text-sm font-medium">
                      {testResult.success ? 'Success' : 'Failed'}
                    </p>
                    
                    {testResult.success && (
                      <>
                        <p className="text-xs text-muted-foreground">
                          Completed in {testResult.duration}s
                        </p>
                        <div className="mt-2">
                          <details className="text-xs">
                            <summary className="cursor-pointer font-medium mb-1">
                              View Output
                            </summary>
                            <pre className="bg-background p-2 rounded border overflow-x-auto">
                              {JSON.stringify(testResult.output, null, 2)}
                            </pre>
                          </details>
                        </div>
                      </>
                    )}
                    
                    {!testResult.success && (
                      <p className="text-xs text-red-600 dark:text-red-400">
                        {testResult.error}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </>
      )}

      {/* Expected Output Schema */}
      {tool.outputs && Object.keys(tool.outputs).length > 0 && (
        <>
          <Separator />
          <div className="space-y-2">
            <h4 className="text-sm font-semibold flex items-center gap-2">
              <Code2 className="h-4 w-4" />
              Output Schema
            </h4>
            <ScrollArea className="h-32">
              <pre className="text-xs font-mono bg-muted p-3 rounded-lg overflow-x-auto">
                {JSON.stringify(tool.outputs, null, 2)}
              </pre>
            </ScrollArea>
          </div>
        </>
      )}
    </div>
  );
}
