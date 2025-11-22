"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { executeTool, getAvailableTools } from "@/lib/api/tools";
import { Loader2, Play, CheckCircle, XCircle } from "lucide-react";

export function ToolExecutionTester() {
  const [availableTools, setAvailableTools] = useState<Record<string, string[]>>({});
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [selectedTool, setSelectedTool] = useState<string>("");
  const [parameters, setParameters] = useState<string>("{}");
  const [config, setConfig] = useState<string>("{}");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load available tools on mount
  useState(() => {
    getAvailableTools().then(setAvailableTools).catch(console.error);
  });

  const handleExecute = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const parsedParams = JSON.parse(parameters);
      const parsedConfig = JSON.parse(config);

      const response = await executeTool({
        tool_name: selectedTool,
        parameters: parsedParams,
        config: parsedConfig,
      });

      setResult(response);
    } catch (err: any) {
      setError(err.message || "Execution failed");
    } finally {
      setLoading(false);
    }
  };

  const categories = Object.keys(availableTools);
  const tools = selectedCategory ? availableTools[selectedCategory] || [] : [];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Tool Execution Tester</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Category Selection */}
          <div className="space-y-2">
            <Label>Category</Label>
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger>
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                {categories.map((category) => (
                  <SelectItem key={category} value={category}>
                    {category}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Tool Selection */}
          {selectedCategory && (
            <div className="space-y-2">
              <Label>Tool</Label>
              <Select value={selectedTool} onValueChange={setSelectedTool}>
                <SelectTrigger>
                  <SelectValue placeholder="Select tool" />
                </SelectTrigger>
                <SelectContent>
                  {tools.map((tool) => (
                    <SelectItem key={tool} value={tool}>
                      {tool}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Parameters */}
          {selectedTool && (
            <>
              <div className="space-y-2">
                <Label>Parameters (JSON)</Label>
                <Textarea
                  value={parameters}
                  onChange={(e) => setParameters(e.target.value)}
                  placeholder='{"key": "value"}'
                  rows={6}
                  className="font-mono text-sm"
                />
              </div>

              {/* Configuration */}
              <div className="space-y-2">
                <Label>Configuration (JSON)</Label>
                <Textarea
                  value={config}
                  onChange={(e) => setConfig(e.target.value)}
                  placeholder='{"api_key": "..."}'
                  rows={4}
                  className="font-mono text-sm"
                />
              </div>

              {/* Execute Button */}
              <Button
                onClick={handleExecute}
                disabled={loading || !selectedTool}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Executing...
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Execute Tool
                  </>
                )}
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      {/* Result Display */}
      {(result || error) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {result?.success ? (
                <>
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  Execution Successful
                </>
              ) : (
                <>
                  <XCircle className="h-5 w-5 text-red-500" />
                  Execution Failed
                </>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {error && (
              <div className="text-red-500 mb-4">
                <strong>Error:</strong> {error}
              </div>
            )}

            {result && (
              <div className="space-y-4">
                {result.execution_time && (
                  <div className="text-sm text-muted-foreground">
                    Execution time: {result.execution_time.toFixed(3)}s
                  </div>
                )}

                <div className="space-y-2">
                  <Label>Result</Label>
                  <pre className="bg-muted p-4 rounded-lg overflow-auto max-h-96 text-sm">
                    {JSON.stringify(result.result || result.error, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
