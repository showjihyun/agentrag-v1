'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Eye, EyeOff, RefreshCw } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';

interface PromptPreviewProps {
  template: string;
  variables?: Record<string, string>;
  onVariableChange?: (name: string, value: string) => void;
}

export function PromptPreview({ template, variables = {}, onVariableChange }: PromptPreviewProps) {
  const [isVisible, setIsVisible] = React.useState(true);
  const [sampleValues, setSampleValues] = React.useState<Record<string, string>>(variables);

  // Extract variables from template
  const extractedVars = React.useMemo(() => {
    const varRegex = /\$\{([^}]+)\}/g;
    const matches = template.matchAll(varRegex);
    const vars = new Set<string>();
    
    for (const match of matches) {
      vars.add(match[1].trim());
    }
    
    return Array.from(vars);
  }, [template]);

  // Render template with sample values
  const renderedTemplate = React.useMemo(() => {
    let result = template;
    
    extractedVars.forEach((varName) => {
      const value = sampleValues[varName] || `[${varName}]`;
      result = result.replace(new RegExp(`\\$\\{${varName}\\}`, 'g'), value);
    });
    
    return result;
  }, [template, extractedVars, sampleValues]);

  const handleVariableChange = (name: string, value: string) => {
    setSampleValues((prev) => ({ ...prev, [name]: value }));
    onVariableChange?.(name, value);
  };

  const handleReset = () => {
    setSampleValues({});
  };

  if (!isVisible) {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsVisible(true)}
        className="w-full"
      >
        <Eye className="h-4 w-4 mr-2" />
        Show Preview
      </Button>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">Prompt Preview</CardTitle>
            <CardDescription>
              See how your prompt will look with sample values
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={handleReset}
              title="Reset values"
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsVisible(false)}
              title="Hide preview"
            >
              <EyeOff className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Variable inputs */}
        {extractedVars.length > 0 && (
          <div className="space-y-3">
            <Label className="text-sm font-semibold">Sample Values</Label>
            <div className="grid gap-3">
              {extractedVars.map((varName) => (
                <div key={varName} className="space-y-1">
                  <Label htmlFor={`var-${varName}`} className="text-xs">
                    {varName}
                  </Label>
                  <Input
                    id={`var-${varName}`}
                    placeholder={`Enter ${varName}...`}
                    value={sampleValues[varName] || ''}
                    onChange={(e) => handleVariableChange(varName, e.target.value)}
                    className="text-sm"
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Rendered preview */}
        <div className="space-y-2">
          <Label className="text-sm font-semibold">Rendered Prompt</Label>
          <ScrollArea className="h-[200px] w-full rounded-md border">
            <div className="p-4">
              <pre className="text-sm whitespace-pre-wrap font-mono">
                {renderedTemplate || 'Enter a template to see preview...'}
              </pre>
            </div>
          </ScrollArea>
        </div>

        {/* Character count */}
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>{extractedVars.length} variable(s)</span>
          <span>{renderedTemplate.length} characters</span>
        </div>
      </CardContent>
    </Card>
  );
}
