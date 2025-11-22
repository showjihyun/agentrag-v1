"use client";

/**
 * Smart Parameter Input - 타입별 최적화된 입력 컴포넌트
 * 
 * Features:
 * - 자동완성
 * - 실시간 검증
 * - 타입별 최적화된 UI
 * - 도움말 툴팁
 * - 변수 참조 지원
 */

import React, { useState, useEffect } from "react";
import {
  Info, Eye, EyeOff, Calendar, Clock, Link as LinkIcon,
  Mail, Lock, FileText, Code, Palette, Check, X, Sparkles
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import type { ParameterInputProps } from "./types";

export function SmartParameterInput({
  name,
  config,
  value,
  onChange,
  error,
  disabled = false,
  compact = false,
}: ParameterInputProps) {
  const [showPassword, setShowPassword] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [localValue, setLocalValue] = useState(value);

  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  // Load suggestions
  useEffect(() => {
    if (config.suggestions) {
      if (Array.isArray(config.suggestions)) {
        setSuggestions(config.suggestions);
      } else if (typeof config.suggestions === 'function' && localValue) {
        config.suggestions(localValue).then(setSuggestions);
      }
    }
  }, [config.suggestions, localValue]);

  const handleChange = (newValue: any) => {
    setLocalValue(newValue);
    onChange(newValue);
  };

  const renderIcon = () => {
    switch (config.type) {
      case 'email':
        return <Mail className="h-4 w-4 text-muted-foreground" />;
      case 'password':
        return <Lock className="h-4 w-4 text-muted-foreground" />;
      case 'url':
        return <LinkIcon className="h-4 w-4 text-muted-foreground" />;
      case 'date':
        return <Calendar className="h-4 w-4 text-muted-foreground" />;
      case 'time':
      case 'datetime':
        return <Clock className="h-4 w-4 text-muted-foreground" />;
      case 'color':
        return <Palette className="h-4 w-4 text-muted-foreground" />;
      case 'code':
      case 'json':
        return <Code className="h-4 w-4 text-muted-foreground" />;
      case 'textarea':
        return <FileText className="h-4 w-4 text-muted-foreground" />;
      default:
        return null;
    }
  };

  const renderInput = () => {
    switch (config.type) {
      case 'string':
      case 'email':
      case 'url':
        return (
          <div className="relative">
            {renderIcon() && (
              <div className="absolute left-3 top-1/2 -translate-y-1/2">
                {renderIcon()}
              </div>
            )}
            <Input
              type={config.type === 'email' ? 'email' : config.type === 'url' ? 'url' : 'text'}
              value={localValue || ""}
              onChange={(e) => handleChange(e.target.value)}
              placeholder={config.placeholder || config.default || ""}
              disabled={disabled}
              className={renderIcon() ? 'pl-10' : ''}
            />
            {suggestions.length > 0 && (
              <Popover open={showSuggestions} onOpenChange={setShowSuggestions}>
                <PopoverTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7"
                    onClick={() => setShowSuggestions(true)}
                  >
                    <Sparkles className="h-3 w-3" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="p-0" align="end">
                  <Command>
                    <CommandInput placeholder="Search suggestions..." />
                    <CommandList>
                      <CommandEmpty>No suggestions found.</CommandEmpty>
                      <CommandGroup>
                        {suggestions.map((suggestion, i) => (
                          <CommandItem
                            key={i}
                            onSelect={() => {
                              handleChange(suggestion);
                              setShowSuggestions(false);
                            }}
                          >
                            {suggestion}
                          </CommandItem>
                        ))}
                      </CommandGroup>
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
            )}
          </div>
        );

      case 'password':
        return (
          <div className="relative">
            <div className="absolute left-3 top-1/2 -translate-y-1/2">
              <Lock className="h-4 w-4 text-muted-foreground" />
            </div>
            <Input
              type={showPassword ? 'text' : 'password'}
              value={localValue || ""}
              onChange={(e) => handleChange(e.target.value)}
              placeholder={config.placeholder || "••••••••"}
              disabled={disabled}
              className="pl-10 pr-10"
            />
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? (
                <EyeOff className="h-3 w-3" />
              ) : (
                <Eye className="h-3 w-3" />
              )}
            </Button>
          </div>
        );

      case 'number':
        return (
          <Input
            type="number"
            value={localValue ?? ""}
            onChange={(e) => handleChange(e.target.value ? Number(e.target.value) : undefined)}
            min={config.min}
            max={config.max}
            step="any"
            placeholder={config.placeholder || config.default?.toString() || ""}
            disabled={disabled}
          />
        );

      case 'boolean':
        return (
          <div className="flex items-center justify-between p-3 border rounded-lg bg-card">
            <div className="flex items-center gap-2">
              <Switch
                checked={localValue ?? false}
                onCheckedChange={handleChange}
                disabled={disabled}
              />
              <span className="text-sm font-medium">
                {localValue ? "Enabled" : "Disabled"}
              </span>
            </div>
            {localValue ? (
              <Check className="h-4 w-4 text-green-500" />
            ) : (
              <X className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
        );

      case 'select':
        return (
          <Select
            value={localValue || ""}
            onValueChange={handleChange}
            disabled={disabled}
          >
            <SelectTrigger>
              <SelectValue placeholder={config.placeholder || "Select an option"} />
            </SelectTrigger>
            <SelectContent>
              {config.enum?.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      case 'multiselect':
        const selectedValues = Array.isArray(localValue) ? localValue : [];
        return (
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-start font-normal"
                disabled={disabled}
              >
                {selectedValues.length > 0 ? (
                  <div className="flex flex-wrap gap-1">
                    {selectedValues.map((val) => (
                      <Badge key={val} variant="secondary" className="text-xs">
                        {val}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <span className="text-muted-foreground">
                    {config.placeholder || "Select options"}
                  </span>
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="p-0" align="start">
              <Command>
                <CommandInput placeholder="Search options..." />
                <CommandList>
                  <CommandEmpty>No options found.</CommandEmpty>
                  <CommandGroup>
                    {config.enum?.map((option) => {
                      const isSelected = selectedValues.includes(option);
                      return (
                        <CommandItem
                          key={option}
                          onSelect={() => {
                            const newValues = isSelected
                              ? selectedValues.filter((v) => v !== option)
                              : [...selectedValues, option];
                            handleChange(newValues);
                          }}
                        >
                          <div className="flex items-center gap-2">
                            <div className={`w-4 h-4 border rounded flex items-center justify-center ${
                              isSelected ? 'bg-primary border-primary' : 'border-muted-foreground'
                            }`}>
                              {isSelected && <Check className="h-3 w-3 text-primary-foreground" />}
                            </div>
                            {option}
                          </div>
                        </CommandItem>
                      );
                    })}
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>
        );

      case 'textarea':
        return (
          <Textarea
            value={localValue || ""}
            onChange={(e) => handleChange(e.target.value)}
            placeholder={config.placeholder || config.default || ""}
            disabled={disabled}
            rows={compact ? 3 : 5}
            className="resize-y"
          />
        );

      case 'code':
      case 'json':
        return (
          <div className="relative">
            <Textarea
              value={typeof localValue === 'object' ? JSON.stringify(localValue, null, 2) : localValue || ""}
              onChange={(e) => {
                if (config.type === 'json') {
                  try {
                    const parsed = JSON.parse(e.target.value);
                    handleChange(parsed);
                  } catch {
                    // Invalid JSON, keep as string
                    handleChange(e.target.value);
                  }
                } else {
                  handleChange(e.target.value);
                }
              }}
              placeholder={config.placeholder || (config.type === 'json' ? '{}' : '')}
              disabled={disabled}
              rows={compact ? 4 : 8}
              className="font-mono text-sm resize-y"
            />
            <div className="absolute top-2 right-2">
              <Badge variant="secondary" className="text-xs">
                {config.type === 'json' ? 'JSON' : 'Code'}
              </Badge>
            </div>
          </div>
        );

      case 'color':
        return (
          <div className="flex gap-2">
            <Input
              type="color"
              value={localValue || "#000000"}
              onChange={(e) => handleChange(e.target.value)}
              disabled={disabled}
              className="w-20 h-10 p-1 cursor-pointer"
            />
            <Input
              type="text"
              value={localValue || ""}
              onChange={(e) => handleChange(e.target.value)}
              placeholder="#000000"
              disabled={disabled}
              className="flex-1 font-mono"
            />
          </div>
        );

      case 'date':
        return (
          <Input
            type="date"
            value={localValue || ""}
            onChange={(e) => handleChange(e.target.value)}
            disabled={disabled}
          />
        );

      case 'time':
        return (
          <Input
            type="time"
            value={localValue || ""}
            onChange={(e) => handleChange(e.target.value)}
            disabled={disabled}
          />
        );

      case 'datetime':
        return (
          <Input
            type="datetime-local"
            value={localValue || ""}
            onChange={(e) => handleChange(e.target.value)}
            disabled={disabled}
          />
        );

      case 'array':
        return (
          <Textarea
            value={Array.isArray(localValue) ? JSON.stringify(localValue, null, 2) : ""}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                if (Array.isArray(parsed)) {
                  handleChange(parsed);
                }
              } catch {
                // Invalid JSON
              }
            }}
            placeholder={config.placeholder || '["item1", "item2"]'}
            disabled={disabled}
            rows={compact ? 3 : 5}
            className="font-mono text-sm resize-y"
          />
        );

      case 'object':
        return (
          <Textarea
            value={typeof localValue === 'object' ? JSON.stringify(localValue, null, 2) : ""}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                handleChange(parsed);
              } catch {
                // Invalid JSON
              }
            }}
            placeholder={config.placeholder || '{"key": "value"}'}
            disabled={disabled}
            rows={compact ? 4 : 6}
            className="font-mono text-sm resize-y"
          />
        );

      default:
        return (
          <Input
            type="text"
            value={localValue || ""}
            onChange={(e) => handleChange(e.target.value)}
            placeholder={config.placeholder || config.default || ""}
            disabled={disabled}
          />
        );
    }
  };

  return (
    <div className={`space-y-2 ${compact ? 'space-y-1' : ''}`}>
      {/* Label */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 flex-1">
          <Label htmlFor={name} className="text-sm font-medium">
            {name}
          </Label>
          
          {config.required && (
            <Badge variant="destructive" className="text-xs px-1.5 py-0">
              Required
            </Badge>
          )}
          
          {config.helpText && (
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="ghost" size="icon" className="h-5 w-5">
                  <Info className="h-3 w-3 text-muted-foreground" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="text-sm" side="top">
                {config.helpText}
              </PopoverContent>
            </Popover>
          )}
        </div>
        
        {config.default !== undefined && (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 text-xs"
            onClick={() => handleChange(config.default)}
          >
            Reset
          </Button>
        )}
      </div>

      {/* Description */}
      {config.description && !compact && (
        <p className="text-xs text-muted-foreground">{config.description}</p>
      )}

      {/* Input */}
      <div className="space-y-1">
        {renderInput()}
        
        {/* Error */}
        {error && (
          <p className="text-xs text-destructive flex items-center gap-1">
            <X className="h-3 w-3" />
            {error}
          </p>
        )}
        
        {/* Validation hints */}
        {!error && !compact && (config.min !== undefined || config.max !== undefined || config.pattern) && (
          <p className="text-xs text-muted-foreground">
            {config.min !== undefined && `Min: ${config.min}`}
            {config.min !== undefined && config.max !== undefined && ' • '}
            {config.max !== undefined && `Max: ${config.max}`}
            {config.pattern && ` • Pattern: ${config.pattern}`}
          </p>
        )}
      </div>
    </div>
  );
}
