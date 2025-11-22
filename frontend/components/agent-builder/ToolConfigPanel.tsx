"use client";

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { X, Info, ChevronDown, ChevronRight } from "lucide-react";
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
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

interface ParamConfig {
  type: string;
  description: string;
  required?: boolean;
  default?: any;
  enum?: string[];
  min?: number;
  max?: number;
  pattern?: string;
  items?: ParamConfig;
  properties?: Record<string, ParamConfig>;
}

interface ToolConfig {
  id: string;
  name: string;
  description: string;
  category: string;
  params: Record<string, ParamConfig>;
  outputs: Record<string, any>;
  icon?: string;
  bg_color?: string;
  docs_link?: string;
}

interface ToolConfigPanelProps {
  tool: ToolConfig;
  initialConfig?: Record<string, any>;
  onSave: (config: Record<string, any>) => void;
  onClose: () => void;
}

export function ToolConfigPanel({
  tool,
  initialConfig = {},
  onSave,
  onClose,
}: ToolConfigPanelProps) {
  const [config, setConfig] = useState<Record<string, any>>(initialConfig);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(["required"])
  );
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    console.log('ToolConfigPanel mounted for tool:', tool.name);
    setMounted(true);
    return () => {
      console.log('ToolConfigPanel unmounted');
      setMounted(false);
    };
  }, []);

  useEffect(() => {
    // Initialize with default values
    const defaults: Record<string, any> = {};
    if (tool.params) {
      Object.entries(tool.params).forEach(([key, param]) => {
        if (param.default !== undefined && !(key in initialConfig)) {
          defaults[key] = param.default;
        }
      });
    }
    setConfig({ ...defaults, ...initialConfig });
  }, [tool, initialConfig]);

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const validateField = (key: string, value: any, param: ParamConfig): string | null => {
    if (param.required && (value === undefined || value === null || value === "")) {
      return "This field is required";
    }

    if (value !== undefined && value !== null && value !== "") {
      if (param.type === "number") {
        const num = Number(value);
        if (isNaN(num)) return "Must be a valid number";
        if (param.min !== undefined && num < param.min) {
          return `Must be at least ${param.min}`;
        }
        if (param.max !== undefined && num > param.max) {
          return `Must be at most ${param.max}`;
        }
      }

      if (param.type === "string" && param.pattern) {
        const regex = new RegExp(param.pattern);
        if (!regex.test(value)) {
          return "Invalid format";
        }
      }
    }

    return null;
  };

  const handleChange = (key: string, value: any, param: ParamConfig) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
    
    // Validate
    const error = validateField(key, value, param);
    setErrors((prev) => {
      const newErrors = { ...prev };
      if (error) {
        newErrors[key] = error;
      } else {
        delete newErrors[key];
      }
      return newErrors;
    });
  };

  const handleSave = () => {
    // Validate all required fields
    const newErrors: Record<string, string> = {};
    if (tool.params) {
      Object.entries(tool.params).forEach(([key, param]) => {
        const error = validateField(key, config[key], param);
        if (error) {
          newErrors[key] = error;
        }
      });
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    onSave(config);
  };

  const renderField = (key: string, param: ParamConfig) => {
    const value = config[key];
    const error = errors[key];

    return (
      <div key={key} className="space-y-2">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <Label htmlFor={key} className="flex items-center gap-2">
              {key}
              {param.required && <Badge variant="destructive" className="text-xs">Required</Badge>}
            </Label>
            {param.description && (
              <p className="text-xs text-muted-foreground mt-1">{param.description}</p>
            )}
          </div>
        </div>

        <div className="space-y-1">
          {renderInput(key, param, value)}
          {error && <p className="text-xs text-destructive">{error}</p>}
        </div>
      </div>
    );
  };

  const renderInput = (key: string, param: ParamConfig, value: any) => {
    switch (param.type) {
      case "string":
        if (param.enum) {
          return (
            <Select
              value={value || ""}
              onValueChange={(val) => handleChange(key, val, param)}
            >
              <SelectTrigger id={key}>
                <SelectValue placeholder="Select an option" />
              </SelectTrigger>
              <SelectContent>
                {param.enum.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          );
        }
        return (
          <Input
            id={key}
            type="text"
            value={value || ""}
            onChange={(e) => handleChange(key, e.target.value, param)}
            placeholder={param.default || ""}
          />
        );

      case "number":
        return (
          <Input
            id={key}
            type="number"
            value={value ?? ""}
            onChange={(e) => handleChange(key, e.target.value ? Number(e.target.value) : undefined, param)}
            min={param.min}
            max={param.max}
            step="any"
            placeholder={param.default?.toString() || ""}
          />
        );

      case "boolean":
        return (
          <div className="flex items-center space-x-2">
            <Switch
              id={key}
              checked={value ?? false}
              onCheckedChange={(checked) => handleChange(key, checked, param)}
            />
            <Label htmlFor={key} className="text-sm font-normal">
              {value ? "Enabled" : "Disabled"}
            </Label>
          </div>
        );

      case "array":
        return (
          <Textarea
            id={key}
            value={Array.isArray(value) ? JSON.stringify(value, null, 2) : ""}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                handleChange(key, parsed, param);
              } catch {
                // Invalid JSON, keep as string for now
              }
            }}
            placeholder='["item1", "item2"]'
            rows={4}
            className="font-mono text-sm"
          />
        );

      case "object":
        return (
          <Textarea
            id={key}
            value={typeof value === "object" ? JSON.stringify(value, null, 2) : ""}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                handleChange(key, parsed, param);
              } catch {
                // Invalid JSON
              }
            }}
            placeholder='{"key": "value"}'
            rows={6}
            className="font-mono text-sm"
          />
        );

      default:
        return (
          <Input
            id={key}
            type="text"
            value={value || ""}
            onChange={(e) => handleChange(key, e.target.value, param)}
          />
        );
    }
  };

  // Group parameters by required/optional
  const requiredParams = tool.params ? Object.entries(tool.params).filter(([_, param]) => param.required) : [];
  const optionalParams = tool.params ? Object.entries(tool.params).filter(([_, param]) => !param.required) : [];

  if (!mounted) {
    console.log('ToolConfigPanel not mounted yet');
    return null;
  }

  console.log('ToolConfigPanel rendering modal for:', tool.name);

  const modalContent = (
    <div 
      className="fixed inset-0 bg-background/80 backdrop-blur-sm z-[9999] flex items-center justify-center p-4"
      onClick={(e) => {
        // Close modal when clicking backdrop
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
      style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0 }}
    >
      <div 
        className="bg-background border rounded-lg shadow-lg w-full max-w-2xl max-h-[90vh] flex flex-col"
        onClick={(e) => {
          // Prevent clicks inside modal from propagating
          e.stopPropagation();
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold">{tool.name} Configuration</h2>
            <p className="text-sm text-muted-foreground mt-1">{tool.description}</p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Required Parameters */}
          {requiredParams.length > 0 && (
            <div className="space-y-4">
              <button
                onClick={() => toggleSection("required")}
                className="flex items-center gap-2 text-sm font-medium w-full text-left"
              >
                {expandedSections.has("required") ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
                Required Parameters
                <Badge variant="secondary" className="ml-auto">
                  {requiredParams.length}
                </Badge>
              </button>
              {expandedSections.has("required") && (
                <div className="space-y-4 pl-6">
                  {requiredParams.map(([key, param]) => renderField(key, param))}
                </div>
              )}
            </div>
          )}

          {/* Optional Parameters */}
          {optionalParams.length > 0 && (
            <div className="space-y-4">
              <button
                onClick={() => toggleSection("optional")}
                className="flex items-center gap-2 text-sm font-medium w-full text-left"
              >
                {expandedSections.has("optional") ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
                Optional Parameters
                <Badge variant="outline" className="ml-auto">
                  {optionalParams.length}
                </Badge>
              </button>
              {expandedSections.has("optional") && (
                <div className="space-y-4 pl-6">
                  {optionalParams.map(([key, param]) => renderField(key, param))}
                </div>
              )}
            </div>
          )}

          {/* Documentation Link */}
          {tool.docs_link && (
            <div className="flex items-center gap-2 p-4 bg-muted rounded-lg">
              <Info className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                Need help?{" "}
                <a
                  href={tool.docs_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  View documentation
                </a>
              </span>
            </div>
          )}
        </div>

        {/* Footer */}
        <Separator />
        <div className="flex items-center justify-end gap-3 p-6">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            Save Configuration
          </Button>
        </div>
      </div>
    </div>
  );

  return typeof document !== 'undefined' 
    ? createPortal(modalContent, document.body)
    : null;
}
