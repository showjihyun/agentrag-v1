"use client";

/**
 * Premium Tool Editor - Advanced Tool editing component
 * 
 * Features:
 * - Drag and drop support
 * - Real-time preview
 * - Auto save
 * - Template gallery
 * - Smart validation
 * - Responsive layout
 */

import React, { useState, useEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import { 
  X, Save, Eye, Code, Sparkles, Copy, Download, Upload,
  ChevronLeft, ChevronRight, Maximize2, Minimize2, Settings2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useDebounce } from "@/hooks/useDebounce";
import { SmartParameterInput } from "./SmartParameterInput";
import { EnhancedParameterInput } from "./EnhancedParameterInput";
import { ToolPreview } from "./ToolPreview";
import { ToolTemplateGallery } from "./ToolTemplateGallery";
import type { ToolEditorProps, ValidationResult } from "./types";

export function PremiumToolEditor({
  tool,
  initialConfig = {},
  onSave,
  onClose,
  mode = 'modal',
  showPreview = true,
  showTemplates = true,
  showAdvanced = true,
  autoSave = false,
  autoSaveDelay = 2000,
}: ToolEditorProps) {
  const [config, setConfig] = useState<Record<string, any>>(initialConfig);
  const [validation, setValidation] = useState<ValidationResult>({
    valid: true,
    errors: {},
    warnings: {},
  });
  const [activeTab, setActiveTab] = useState<string>("basic");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [mounted, setMounted] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    setMounted(true);
    // Initialize with defaults
    const defaults: Record<string, any> = {};
    Object.entries(tool.params || {}).forEach(([key, param]) => {
      if (param.default !== undefined && !(key in initialConfig)) {
        defaults[key] = param.default;
      }
    });
    setConfig({ ...defaults, ...initialConfig });
  }, [tool, initialConfig]);

  // Auto-save with debounce
  const debouncedConfig = useDebounce(config, autoSaveDelay);
  
  useEffect(() => {
    if (autoSave && hasChanges && validation.valid) {
      onSave(debouncedConfig);
      setHasChanges(false);
    }
  }, [debouncedConfig, autoSave, hasChanges, validation.valid, onSave]);

  // Validate configuration
  const validateConfig = useCallback(() => {
    const errors: Record<string, string> = {};
    const warnings: Record<string, string> = {};

    Object.entries(tool.params || {}).forEach(([key, param]) => {
      const value = config[key];

      // Required validation
      if (param.required && (value === undefined || value === null || value === "")) {
        errors[key] = "This field is required";
        return;
      }

      // Skip validation for empty optional fields
      if (!param.required && (value === undefined || value === null || value === "")) {
        return;
      }

      // Type validation
      if (param.type === "number") {
        const num = Number(value);
        if (isNaN(num)) {
          errors[key] = "Must be a valid number";
        } else {
          if (param.min !== undefined && num < param.min) {
            errors[key] = `Must be at least ${param.min}`;
          }
          if (param.max !== undefined && num > param.max) {
            errors[key] = `Must be at most ${param.max}`;
          }
        }
      }

      // Pattern validation
      if (param.type === "string" && param.pattern && value) {
        const regex = new RegExp(param.pattern);
        if (!regex.test(value)) {
          errors[key] = "Invalid format";
        }
      }

      // Custom validation
      if (param.validation && value !== undefined) {
        const error = param.validation(value);
        if (error) {
          errors[key] = error;
        }
      }

      // Warnings for best practices
      if (param.type === "password" && value && value.length < 8) {
        warnings[key] = "Password should be at least 8 characters";
      }
    });

    setValidation({
      valid: Object.keys(errors).length === 0,
      errors,
      warnings,
    });
  }, [config, tool.params]);

  useEffect(() => {
    validateConfig();
  }, [validateConfig]);

  const handleChange = (key: string, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const handleSave = () => {
    if (!validation.valid) {
      return;
    }
    onSave(config);
    setHasChanges(false);
  };

  const handleTemplateSelect = (templateConfig: Record<string, any>) => {
    setConfig(templateConfig);
    setHasChanges(true);
  };

  const handleExport = () => {
    const dataStr = JSON.stringify(config, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${tool.id}-config.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'application/json';
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          try {
            const imported = JSON.parse(e.target?.result as string);
            setConfig(imported);
            setHasChanges(true);
          } catch (error) {
            console.error('Failed to import config:', error);
          }
        };
        reader.readAsText(file);
      }
    };
    input.click();
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(config, null, 2));
  };

  // Group parameters
  const groupedParams = Object.entries(tool.params || {}).reduce((acc, [key, param]) => {
    const group = param.group || 'basic';
    if (!acc[group]) acc[group] = [];
    acc[group].push([key, param]);
    return acc;
  }, {} as Record<string, Array<[string, any]>>);

  // Sort by order
  Object.values(groupedParams).forEach(params => {
    params.sort((a, b) => (a[1].order || 0) - (b[1].order || 0));
  });

  const renderContent = () => (
    <div className={`flex ${isFullscreen ? 'h-screen' : 'h-[85vh]'} bg-background`}>
      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b bg-card/50 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-semibold shadow-lg"
              style={{ backgroundColor: tool.bg_color || "#6B7280" }}
            >
              {tool.icon || tool.name.charAt(0)}
            </div>
            <div>
              <h2 className="text-lg font-semibold flex items-center gap-2">
                {tool.name}
                {tool.version && (
                  <Badge variant="outline" className="text-xs">
                    v{tool.version}
                  </Badge>
                )}
              </h2>
              <p className="text-sm text-muted-foreground">{tool.description}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {hasChanges && !autoSave && (
              <Badge variant="secondary" className="animate-pulse">
                Unsaved changes
              </Badge>
            )}
            
            {/* Action Buttons */}
            <Button
              variant="ghost"
              size="icon"
              onClick={handleCopy}
              title="Copy config"
            >
              <Copy className="h-4 w-4" />
            </Button>
            
            <Button
              variant="ghost"
              size="icon"
              onClick={handleExport}
              title="Export config"
            >
              <Download className="h-4 w-4" />
            </Button>
            
            <Button
              variant="ghost"
              size="icon"
              onClick={handleImport}
              title="Import config"
            >
              <Upload className="h-4 w-4" />
            </Button>
            
            <Separator orientation="vertical" className="h-6" />
            
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsFullscreen(!isFullscreen)}
              title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
            >
              {isFullscreen ? (
                <Minimize2 className="h-4 w-4" />
              ) : (
                <Maximize2 className="h-4 w-4" />
              )}
            </Button>
            
            {mode === 'modal' && (
              <Button variant="ghost" size="icon" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
          <div className="border-b px-4 bg-card/30">
            <TabsList className="h-12">
              <TabsTrigger value="basic" className="gap-2">
                <Settings2 className="h-4 w-4" />
                Configuration
              </TabsTrigger>
              
              {showTemplates && tool.examples && tool.examples.length > 0 && (
                <TabsTrigger value="templates" className="gap-2">
                  <Sparkles className="h-4 w-4" />
                  Templates
                </TabsTrigger>
              )}
              
              {showAdvanced && (
                <TabsTrigger value="advanced" className="gap-2">
                  <Code className="h-4 w-4" />
                  Advanced
                </TabsTrigger>
              )}
              
              {showPreview && (
                <TabsTrigger value="preview" className="gap-2">
                  <Eye className="h-4 w-4" />
                  Preview
                </TabsTrigger>
              )}
            </TabsList>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-hidden">
            <TabsContent value="basic" className="h-full m-0 p-0">
              <ScrollArea className="h-full">
                <div className="p-6 space-y-6">
                  {Object.entries(groupedParams).map(([group, params]) => (
                    <div key={group} className="space-y-4">
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-semibold capitalize">{group} Parameters</h3>
                        <Badge variant="outline" className="text-xs">
                          {params.length}
                        </Badge>
                      </div>
                      
                      <div className="grid gap-4">
                        {params.map(([key, param]) => {
                          // Check if should show based on dependencies
                          if (param.showIf && !param.showIf(config)) {
                            return null;
                          }
                          
                          return (
                            <EnhancedParameterInput
                              key={key}
                              name={key}
                              config={param}
                              value={config[key]}
                              onChange={(value) => handleChange(key, value)}
                              error={validation.errors[key]}
                              disabled={param.disabled}
                            />
                          );
                        })}
                      </div>
                    </div>
                  ))}
                  
                  {/* Validation Summary */}
                  {(Object.keys(validation.errors).length > 0 || Object.keys(validation.warnings).length > 0) && (
                    <div className="space-y-2 p-4 border rounded-lg bg-muted/50">
                      {Object.keys(validation.errors).length > 0 && (
                        <div className="space-y-1">
                          <p className="text-sm font-medium text-destructive">
                            {Object.keys(validation.errors).length} error(s) found
                          </p>
                        </div>
                      )}
                      
                      {Object.keys(validation.warnings).length > 0 && (
                        <div className="space-y-1">
                          <p className="text-sm font-medium text-yellow-600">
                            {Object.keys(validation.warnings).length} warning(s)
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </ScrollArea>
            </TabsContent>

            {showTemplates && tool.examples && (
              <TabsContent value="templates" className="h-full m-0 p-0">
                <ScrollArea className="h-full">
                  <div className="p-6">
                    <ToolTemplateGallery
                      tool={tool}
                      onSelectTemplate={handleTemplateSelect}
                    />
                  </div>
                </ScrollArea>
              </TabsContent>
            )}

            {showAdvanced && (
              <TabsContent value="advanced" className="h-full m-0 p-0">
                <ScrollArea className="h-full">
                  <div className="p-6 space-y-4">
                    <div className="space-y-2">
                      <Label className="text-sm font-medium">JSON Configuration</Label>
                      <p className="text-xs text-muted-foreground">
                        Edit the raw JSON configuration. Changes will be validated automatically.
                      </p>
                    </div>
                    
                    <Textarea
                      value={JSON.stringify(config, null, 2)}
                      onChange={(e) => {
                        try {
                          const parsed = JSON.parse(e.target.value);
                          setConfig(parsed);
                          setHasChanges(true);
                        } catch {
                          // Invalid JSON, ignore
                        }
                      }}
                      className="font-mono text-sm min-h-[400px]"
                    />
                  </div>
                </ScrollArea>
              </TabsContent>
            )}

            {showPreview && (
              <TabsContent value="preview" className="h-full m-0 p-0">
                <ScrollArea className="h-full">
                  <div className="p-6">
                    <ToolPreview tool={tool} config={config} showOutput />
                  </div>
                </ScrollArea>
              </TabsContent>
            )}
          </div>
        </Tabs>

        {/* Footer */}
        <Separator />
        <div className="flex items-center justify-between p-4 bg-card/50 backdrop-blur-sm">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            {tool.docs_link && (
              <a
                href={tool.docs_link}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                View Documentation
              </a>
            )}
          </div>
          
          <div className="flex items-center gap-3">
            {mode === 'modal' && (
              <Button variant="outline" onClick={onClose}>
                Cancel
              </Button>
            )}
            
            <Button
              onClick={handleSave}
              disabled={!validation.valid || (!hasChanges && !autoSave)}
              className="gap-2"
            >
              <Save className="h-4 w-4" />
              {autoSave ? 'Apply Changes' : 'Save Configuration'}
            </Button>
          </div>
        </div>
      </div>

      {/* Sidebar - Preview/Info */}
      {showSidebar && showPreview && (
        <>
          <Separator orientation="vertical" />
          <div className="w-80 flex flex-col border-l bg-card/30">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-sm font-semibold">Live Preview</h3>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowSidebar(false)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
            
            <ScrollArea className="flex-1">
              <div className="p-4">
                <ToolPreview tool={tool} config={config} />
              </div>
            </ScrollArea>
          </div>
        </>
      )}
      
      {/* Sidebar Toggle */}
      {!showSidebar && showPreview && (
        <Button
          variant="ghost"
          size="icon"
          className="absolute right-4 top-20"
          onClick={() => setShowSidebar(true)}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
      )}
    </div>
  );

  if (!mounted) return null;

  if (mode === 'modal') {
    return createPortal(
      <div
        className="fixed inset-0 bg-background/80 backdrop-blur-sm z-[9999] flex items-center justify-center p-4"
        onClick={(e) => {
          if (e.target === e.currentTarget) onClose();
        }}
      >
        <div
          className={`bg-background border rounded-lg shadow-2xl ${
            isFullscreen ? 'w-full h-full' : 'w-full max-w-6xl'
          }`}
          onClick={(e) => e.stopPropagation()}
        >
          {renderContent()}
        </div>
      </div>,
      document.body
    );
  }

  return (
    <div className={mode === 'sidebar' ? 'h-full' : ''}>
      {renderContent()}
    </div>
  );
}

// Missing imports
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
