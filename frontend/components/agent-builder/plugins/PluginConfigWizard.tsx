/**
 * Plugin Configuration Wizard
 * 스키마 기반 동적 설정 UI 컴포넌트
 */

'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Settings,
  Save,
  RotateCcw,
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle,
  Info,
  History,
  Download,
  Upload,
  Copy,
  FileText,
  Zap,
  Loader2,
} from 'lucide-react';
import { toast } from 'sonner';

export interface PluginConfigField {
  name: string;
  type: 'text' | 'number' | 'boolean' | 'select' | 'multiselect' | 'textarea' | 'password' | 'url' | 'email';
  label: string;
  description?: string;
  required?: boolean;
  defaultValue?: any;
  placeholder?: string;
  validation?: {
    pattern?: string;
    min?: number;
    max?: number;
    minLength?: number;
    maxLength?: number;
    custom?: (value: any) => boolean | string;
  };
  options?: Array<{ label: string; value: any; description?: string }>;
  group?: string;
  dependsOn?: {
    field: string;
    value: any;
  };
  sensitive?: boolean;
}

export interface PluginConfigSchema {
  title: string;
  description?: string;
  version: string;
  fields: PluginConfigField[];
  presets?: Array<{
    name: string;
    description: string;
    values: Record<string, any>;
  }>;
}

export interface PluginConfigHistory {
  id: string;
  timestamp: string;
  values: Record<string, any>;
  description?: string;
}

interface PluginConfigWizardProps {
  pluginId: string;
  schema: PluginConfigSchema;
  initialValues?: Record<string, any>;
  history?: PluginConfigHistory[];
  onSave: (values: Record<string, any>) => Promise<void>;
  onValidate?: (values: Record<string, any>) => Promise<Record<string, string>>;
  onCancel?: () => void;
  showPreview?: boolean;
  showHistory?: boolean;
  className?: string;
}

interface ValidationErrors {
  [fieldName: string]: string;
}

export function PluginConfigWizard({
  pluginId,
  schema,
  initialValues = {},
  history = [],
  onSave,
  onValidate,
  onCancel,
  showPreview = true,
  showHistory = true,
  className,
}: PluginConfigWizardProps) {
  const [values, setValues] = useState<Record<string, any>>(initialValues);
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [isValidating, setIsValidating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [showSensitive, setShowSensitive] = useState<Record<string, boolean>>({});
  const [selectedPreset, setSelectedPreset] = useState<string>('');
  const [activeTab, setActiveTab] = useState('config');
  const [isDirty, setIsDirty] = useState(false);

  // 필드를 그룹별로 정리
  const fieldGroups = useMemo(() => {
    const groups: Record<string, PluginConfigField[]> = {};
    
    schema.fields.forEach(field => {
      const groupName = field.group || 'General';
      if (!groups[groupName]) {
        groups[groupName] = [];
      }
      groups[groupName].push(field);
    });
    
    return groups;
  }, [schema.fields]);

  // 의존성 체크
  const isFieldVisible = (field: PluginConfigField): boolean => {
    if (!field.dependsOn) return true;
    
    const dependentValue = values[field.dependsOn.field];
    return dependentValue === field.dependsOn.value;
  };

  // 실시간 검증
  useEffect(() => {
    if (!onValidate || !isDirty) return;

    const validateDebounced = setTimeout(async () => {
      setIsValidating(true);
      try {
        const validationErrors = await onValidate(values);
        setErrors(validationErrors);
      } catch (error) {
        console.error('Validation error:', error);
      } finally {
        setIsValidating(false);
      }
    }, 500);

    return () => clearTimeout(validateDebounced);
  }, [values, onValidate, isDirty]);

  // 값 변경 핸들러
  const handleValueChange = (fieldName: string, value: any) => {
    setValues(prev => ({
      ...prev,
      [fieldName]: value,
    }));
    setIsDirty(true);
    
    // 해당 필드의 에러 제거
    if (errors[fieldName]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[fieldName];
        return newErrors;
      });
    }
  };

  // 프리셋 적용
  const applyPreset = (presetName: string) => {
    const preset = schema.presets?.find(p => p.name === presetName);
    if (preset) {
      setValues(prev => ({
        ...prev,
        ...preset.values,
      }));
      setSelectedPreset(presetName);
      setIsDirty(true);
      toast.success(`Preset "${preset.name}" applied`);
    }
  };

  // 히스토리에서 복원
  const restoreFromHistory = (historyItem: PluginConfigHistory) => {
    setValues(historyItem.values);
    setIsDirty(true);
    toast.success('Configuration restored from history');
  };

  // 저장
  const handleSave = async () => {
    setIsSaving(true);
    try {
      // 최종 검증
      if (onValidate) {
        const validationErrors = await onValidate(values);
        if (Object.keys(validationErrors).length > 0) {
          setErrors(validationErrors);
          toast.error('Please fix validation errors before saving');
          return;
        }
      }

      await onSave(values);
      setIsDirty(false);
      toast.success('Configuration saved successfully');
    } catch (error) {
      toast.error('Failed to save configuration');
      console.error('Save error:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // 리셋
  const handleReset = () => {
    setValues(initialValues);
    setErrors({});
    setIsDirty(false);
    setSelectedPreset('');
    toast.info('Configuration reset to initial values');
  };

  // 필드 렌더링
  const renderField = (field: PluginConfigField) => {
    if (!isFieldVisible(field)) return null;

    const value = values[field.name] ?? field.defaultValue;
    const error = errors[field.name];
    const isRequired = field.required;
    const isSensitive = field.sensitive;

    return (
      <div key={field.name} className="space-y-2">
        <div className="flex items-center gap-2">
          <Label htmlFor={field.name} className="text-sm font-medium">
            {field.label}
            {isRequired && <span className="text-red-500">*</span>}
          </Label>
          {field.description && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Info className="h-4 w-4 text-muted-foreground" />
                </TooltipTrigger>
                <TooltipContent>
                  <p className="max-w-xs">{field.description}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>

        {field.type === 'text' || field.type === 'url' || field.type === 'email' ? (
          <div className="relative">
            <Input
              id={field.name}
              type={isSensitive && !showSensitive[field.name] ? 'password' : field.type}
              value={value || ''}
              onChange={(e) => handleValueChange(field.name, e.target.value)}
              placeholder={field.placeholder}
              className={error ? 'border-red-500' : ''}
            />
            {isSensitive && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-2 top-1/2 -translate-y-1/2 h-6 w-6 p-0"
                onClick={() => setShowSensitive(prev => ({
                  ...prev,
                  [field.name]: !prev[field.name]
                }))}
              >
                {showSensitive[field.name] ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
            )}
          </div>
        ) : field.type === 'number' ? (
          <Input
            id={field.name}
            type="number"
            value={value || ''}
            onChange={(e) => handleValueChange(field.name, parseFloat(e.target.value) || 0)}
            placeholder={field.placeholder}
            min={field.validation?.min}
            max={field.validation?.max}
            className={error ? 'border-red-500' : ''}
          />
        ) : field.type === 'textarea' ? (
          <Textarea
            id={field.name}
            value={value || ''}
            onChange={(e) => handleValueChange(field.name, e.target.value)}
            placeholder={field.placeholder}
            className={error ? 'border-red-500' : ''}
            rows={4}
          />
        ) : field.type === 'boolean' ? (
          <div className="flex items-center space-x-2">
            <Switch
              id={field.name}
              checked={value || false}
              onCheckedChange={(checked) => handleValueChange(field.name, checked)}
            />
            <Label htmlFor={field.name} className="text-sm text-muted-foreground">
              {value ? 'Enabled' : 'Disabled'}
            </Label>
          </div>
        ) : field.type === 'select' ? (
          <Select
            value={value || ''}
            onValueChange={(newValue) => handleValueChange(field.name, newValue)}
          >
            <SelectTrigger className={error ? 'border-red-500' : ''}>
              <SelectValue placeholder={field.placeholder || 'Select an option'} />
            </SelectTrigger>
            <SelectContent>
              {field.options?.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  <div>
                    <div>{option.label}</div>
                    {option.description && (
                      <div className="text-xs text-muted-foreground">
                        {option.description}
                      </div>
                    )}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : field.type === 'multiselect' ? (
          <div className="space-y-2">
            {field.options?.map((option) => (
              <div key={option.value} className="flex items-center space-x-2">
                <Checkbox
                  id={`${field.name}-${option.value}`}
                  checked={(value || []).includes(option.value)}
                  onCheckedChange={(checked) => {
                    const currentValues = value || [];
                    const newValues = checked
                      ? [...currentValues, option.value]
                      : currentValues.filter((v: any) => v !== option.value);
                    handleValueChange(field.name, newValues);
                  }}
                />
                <Label htmlFor={`${field.name}-${option.value}`} className="text-sm">
                  {option.label}
                </Label>
              </div>
            ))}
          </div>
        ) : null}

        {error && (
          <Alert variant="destructive" className="py-2">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-sm">{error}</AlertDescription>
          </Alert>
        )}
      </div>
    );
  };

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">{schema.title} Configuration</h2>
          {schema.description && (
            <p className="text-muted-foreground mt-1">{schema.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {isValidating && <Loader2 className="h-4 w-4 animate-spin" />}
          <Badge variant={Object.keys(errors).length > 0 ? 'destructive' : 'default'}>
            v{schema.version}
          </Badge>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="config">Configuration</TabsTrigger>
          {schema.presets && schema.presets.length > 0 && (
            <TabsTrigger value="presets">Presets</TabsTrigger>
          )}
          {showPreview && <TabsTrigger value="preview">Preview</TabsTrigger>}
          {showHistory && history.length > 0 && (
            <TabsTrigger value="history">History</TabsTrigger>
          )}
        </TabsList>

        <TabsContent value="config" className="space-y-6">
          <ScrollArea className="h-[600px] pr-4">
            {Object.entries(fieldGroups).map(([groupName, fields]) => (
              <Card key={groupName} className="mb-4">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">{groupName}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {fields.map(renderField)}
                </CardContent>
              </Card>
            ))}
          </ScrollArea>
        </TabsContent>

        {schema.presets && schema.presets.length > 0 && (
          <TabsContent value="presets" className="space-y-4">
            <div className="grid gap-4">
              {schema.presets.map((preset) => (
                <Card
                  key={preset.name}
                  className={`cursor-pointer transition-colors ${
                    selectedPreset === preset.name ? 'ring-2 ring-primary' : ''
                  }`}
                  onClick={() => applyPreset(preset.name)}
                >
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base">{preset.name}</CardTitle>
                    <CardDescription>{preset.description}</CardDescription>
                  </CardHeader>
                </Card>
              ))}
            </div>
          </TabsContent>
        )}

        {showPreview && (
          <TabsContent value="preview">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Configuration Preview
                </CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="bg-muted p-4 rounded-lg overflow-auto text-sm">
                  {JSON.stringify(values, null, 2)}
                </pre>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {showHistory && history.length > 0 && (
          <TabsContent value="history" className="space-y-4">
            {history.map((item) => (
              <Card key={item.id} className="cursor-pointer hover:bg-muted/50">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">
                      {new Date(item.timestamp).toLocaleString()}
                    </CardTitle>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => restoreFromHistory(item)}
                    >
                      <History className="h-4 w-4 mr-1" />
                      Restore
                    </Button>
                  </div>
                  {item.description && (
                    <CardDescription>{item.description}</CardDescription>
                  )}
                </CardHeader>
              </Card>
            ))}
          </TabsContent>
        )}
      </Tabs>

      <Separator />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleReset} disabled={!isDirty}>
            <RotateCcw className="h-4 w-4 mr-1" />
            Reset
          </Button>
          {onCancel && (
            <Button variant="outline" onClick={onCancel}>
              Cancel
            </Button>
          )}
        </div>

        <div className="flex items-center gap-2">
          {Object.keys(errors).length > 0 && (
            <Alert variant="destructive" className="py-2 px-3">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="text-sm">
                {Object.keys(errors).length} validation error(s)
              </AlertDescription>
            </Alert>
          )}
          
          <Button
            onClick={handleSave}
            disabled={isSaving || Object.keys(errors).length > 0}
            className="min-w-[120px]"
          >
            {isSaving ? (
              <>
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-1" />
                Save Config
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}