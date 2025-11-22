"use client";

import React, { useState } from "react";
import { Code, Zap, Variable, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface AdvancedToolConfigProps {
  toolId: string;
  config: Record<string, any>;
  onChange: (config: Record<string, any>) => void;
}

export function AdvancedToolConfig({
  toolId,
  config,
  onChange,
}: AdvancedToolConfigProps) {
  const [activeTab, setActiveTab] = useState("expressions");
  const [showSecrets, setShowSecrets] = useState(false);

  // Expression builder for dynamic values
  const [expressions, setExpressions] = useState<Record<string, string>>(
    config._expressions || {}
  );

  // Conditional execution
  const [conditions, setConditions] = useState<string>(
    config._conditions || ""
  );

  // Error handling
  const [errorHandling, setErrorHandling] = useState({
    retry: config._retry || false,
    retryCount: config._retryCount || 3,
    retryDelay: config._retryDelay || 1000,
    fallback: config._fallback || "",
    continueOnError: config._continueOnError || false,
  });

  const handleExpressionChange = (field: string, expression: string) => {
    const updated = { ...expressions, [field]: expression };
    setExpressions(updated);
    onChange({ ...config, _expressions: updated });
  };

  const handleConditionChange = (condition: string) => {
    setConditions(condition);
    onChange({ ...config, _conditions: condition });
  };

  const handleErrorHandlingChange = (key: string, value: any) => {
    const updated = { ...errorHandling, [key]: value };
    setErrorHandling(updated);
    onChange({
      ...config,
      _retry: updated.retry,
      _retryCount: updated.retryCount,
      _retryDelay: updated.retryDelay,
      _fallback: updated.fallback,
      _continueOnError: updated.continueOnError,
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Zap className="h-4 w-4 text-primary" />
        <h3 className="text-sm font-medium">Advanced Configuration</h3>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="expressions">
            <Variable className="h-4 w-4 mr-2" />
            Expressions
          </TabsTrigger>
          <TabsTrigger value="conditions">
            <Code className="h-4 w-4 mr-2" />
            Conditions
          </TabsTrigger>
          <TabsTrigger value="errors">
            Error Handling
          </TabsTrigger>
        </TabsList>

        {/* Expressions Tab */}
        <TabsContent value="expressions" className="space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-sm">Dynamic Values</Label>
              <Badge variant="outline" className="text-xs">
                Use {`{{ }}`} for variables
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              Reference previous block outputs, workflow variables, or use JavaScript expressions.
            </p>

            <div className="space-y-3">
              {Object.keys(config).filter(k => !k.startsWith('_')).map((field) => (
                <div key={field} className="space-y-2">
                  <Label className="text-xs font-medium">{field}</Label>
                  <Textarea
                    value={expressions[field] || ""}
                    onChange={(e) => handleExpressionChange(field, e.target.value)}
                    placeholder={`{{ previousBlock.output }} or {{ workflow.variable }}`}
                    rows={2}
                    className="font-mono text-xs"
                  />
                </div>
              ))}
            </div>

            <div className="p-3 bg-muted rounded-lg space-y-2">
              <p className="text-xs font-medium">Available Variables:</p>
              <ul className="text-xs text-muted-foreground space-y-1">
                <li>• <code className="bg-background px-1 rounded">{`{{ workflow.input }}`}</code> - Workflow input data</li>
                <li>• <code className="bg-background px-1 rounded">{`{{ previousBlock.output }}`}</code> - Previous block output</li>
                <li>• <code className="bg-background px-1 rounded">{`{{ env.API_KEY }}`}</code> - Environment variables</li>
                <li>• <code className="bg-background px-1 rounded">{`{{ Math.random() }}`}</code> - JavaScript expressions</li>
              </ul>
            </div>
          </div>
        </TabsContent>

        {/* Conditions Tab */}
        <TabsContent value="conditions" className="space-y-4">
          <div className="space-y-3">
            <Label className="text-sm">Execution Condition</Label>
            <p className="text-xs text-muted-foreground">
              Define when this tool should execute. Leave empty to always execute.
            </p>

            <Textarea
              value={conditions}
              onChange={(e) => handleConditionChange(e.target.value)}
              placeholder={`{{ previousBlock.status === "success" && workflow.input.type === "urgent" }}`}
              rows={4}
              className="font-mono text-sm"
            />

            <div className="p-3 bg-muted rounded-lg space-y-2">
              <p className="text-xs font-medium">Example Conditions:</p>
              <ul className="text-xs text-muted-foreground space-y-1">
                <li>• <code className="bg-background px-1 rounded">{`{{ input.priority === "high" }}`}</code></li>
                <li>• <code className="bg-background px-1 rounded">{`{{ previousBlock.confidence > 0.8 }}`}</code></li>
                <li>• <code className="bg-background px-1 rounded">{`{{ workflow.retryCount < 3 }}`}</code></li>
              </ul>
            </div>
          </div>
        </TabsContent>

        {/* Error Handling Tab */}
        <TabsContent value="errors" className="space-y-4">
          <div className="space-y-4">
            {/* Retry Configuration */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label className="text-sm">Automatic Retry</Label>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleErrorHandlingChange("retry", !errorHandling.retry)}
                >
                  {errorHandling.retry ? "Enabled" : "Disabled"}
                </Button>
              </div>

              {errorHandling.retry && (
                <div className="grid grid-cols-2 gap-3 pl-4">
                  <div className="space-y-2">
                    <Label className="text-xs">Retry Count</Label>
                    <Select
                      value={errorHandling.retryCount.toString()}
                      onValueChange={(val) =>
                        handleErrorHandlingChange("retryCount", parseInt(val))
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {[1, 2, 3, 5, 10].map((count) => (
                          <SelectItem key={count} value={count.toString()}>
                            {count} {count === 1 ? "time" : "times"}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-xs">Retry Delay (ms)</Label>
                    <Select
                      value={errorHandling.retryDelay.toString()}
                      onValueChange={(val) =>
                        handleErrorHandlingChange("retryDelay", parseInt(val))
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {[500, 1000, 2000, 5000, 10000].map((delay) => (
                          <SelectItem key={delay} value={delay.toString()}>
                            {delay}ms
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}
            </div>

            {/* Fallback Value */}
            <div className="space-y-2">
              <Label className="text-sm">Fallback Value</Label>
              <p className="text-xs text-muted-foreground">
                Value to use if the tool fails after all retries
              </p>
              <Textarea
                value={errorHandling.fallback}
                onChange={(e) => handleErrorHandlingChange("fallback", e.target.value)}
                placeholder='{"status": "fallback", "message": "Tool execution failed"}'
                rows={3}
                className="font-mono text-xs"
              />
            </div>

            {/* Continue on Error */}
            <div className="flex items-center justify-between p-3 border rounded-lg">
              <div className="space-y-1">
                <Label className="text-sm">Continue on Error</Label>
                <p className="text-xs text-muted-foreground">
                  Continue workflow execution even if this tool fails
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  handleErrorHandlingChange("continueOnError", !errorHandling.continueOnError)
                }
              >
                {errorHandling.continueOnError ? "Yes" : "No"}
              </Button>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
