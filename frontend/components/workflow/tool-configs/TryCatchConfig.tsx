'use client';

/**
 * TryCatchConfig - Error Handling Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ShieldAlert, Plus, Trash } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ToolConfigProps } from './ToolConfigRegistry';
import {
  ToolConfigHeader,
  TextField,
  NumberField,
  TextareaField,
  SelectField,
  SwitchField,
  useToolConfig,
} from './common';

// ============================================
// Constants
// ============================================

const BACKOFF_STRATEGIES = [
  { value: 'fixed', label: 'Fixed Delay' },
  { value: 'linear', label: 'Linear (delay * attempt)' },
  { value: 'exponential', label: 'Exponential (delay * 2^attempt)' },
] as const;

const ERROR_TYPES = [
  { value: 'all', label: 'All Errors' },
  { value: 'timeout', label: 'Timeout Errors' },
  { value: 'network', label: 'Network Errors' },
  { value: 'validation', label: 'Validation Errors' },
  { value: 'auth', label: 'Authentication Errors' },
  { value: 'rate_limit', label: 'Rate Limit Errors' },
] as const;

const HANDLER_ACTIONS = [
  { value: 'continue', label: 'Continue' },
  { value: 'retry', label: 'Retry' },
  { value: 'skip', label: 'Skip' },
  { value: 'fail', label: 'Fail' },
  { value: 'goto', label: 'Go to Node' },
] as const;


const NOTIFICATION_CHANNELS = [
  { value: 'email', label: 'Email' },
  { value: 'slack', label: 'Slack' },
  { value: 'webhook', label: 'Webhook' },
] as const;

// ============================================
// Types
// ============================================

interface ErrorHandler {
  error_type: string;
  action: string;
  value: string;
}

interface TryCatchConfigData {
  retry_count: number;
  retry_delay: number;
  retry_backoff: string;
  catch_errors: string[];
  error_output: string;
  continue_on_error: boolean;
  fallback_value: string;
  log_errors: boolean;
  notify_on_error: boolean;
  notification_channel: string;
  custom_error_handlers: ErrorHandler[];
}

const DEFAULTS: TryCatchConfigData = {
  retry_count: 0,
  retry_delay: 1000,
  retry_backoff: 'fixed',
  catch_errors: ['all'],
  error_output: 'error',
  continue_on_error: false,
  fallback_value: '',
  log_errors: true,
  notify_on_error: false,
  notification_channel: '',
  custom_error_handlers: [],
};

// ============================================
// Component
// ============================================

export default function TryCatchConfig({ data, onChange }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<TryCatchConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });


  const addErrorHandler = useCallback(() => {
    updateField('custom_error_handlers', [
      ...config.custom_error_handlers,
      { error_type: '', action: 'continue', value: '' },
    ]);
  }, [config.custom_error_handlers, updateField]);

  const updateErrorHandler = useCallback((index: number, field: keyof ErrorHandler, value: string) => {
    const newHandlers = [...config.custom_error_handlers];
    newHandlers[index] = { ...newHandlers[index], [field]: value };
    updateField('custom_error_handlers', newHandlers);
  }, [config.custom_error_handlers, updateField]);

  const removeErrorHandler = useCallback((index: number) => {
    updateField('custom_error_handlers', config.custom_error_handlers.filter((_, i) => i !== index));
  }, [config.custom_error_handlers, updateField]);

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={ShieldAlert}
          iconBgColor="bg-red-100 dark:bg-red-950"
          iconColor="text-red-600 dark:text-red-400"
          title="Try/Catch"
          description="에러 처리 및 복구"
        />

        {/* Retry Settings */}
        <div className="space-y-4 p-4 border rounded-lg bg-muted/30">
          <h4 className="font-medium text-sm">재시도 설정</h4>
          <div className="grid grid-cols-2 gap-4">
            <NumberField
              label="재시도 횟수"
              value={config.retry_count}
              onChange={(v) => updateField('retry_count', v)}
              min={0}
              max={10}
            />
            <NumberField
              label="재시도 지연 (ms)"
              value={config.retry_delay}
              onChange={(v) => updateField('retry_delay', v)}
              min={0}
            />
          </div>
          <SelectField
            label="백오프 전략"
            value={config.retry_backoff}
            onChange={(v) => updateField('retry_backoff', v)}
            options={BACKOFF_STRATEGIES.map(b => ({ value: b.value, label: b.label }))}
          />
        </div>


        {/* Error Types to Catch */}
        <SelectField
          label="캐치할 에러 유형"
          value={config.catch_errors[0] || 'all'}
          onChange={(v) => updateField('catch_errors', [v])}
          options={ERROR_TYPES.map(e => ({ value: e.value, label: e.label }))}
        />

        {/* Error Output */}
        <TextField
          label="에러 출력 이름"
          value={config.error_output}
          onChange={(v) => updateField('error_output', v)}
          placeholder="error"
          hint="에러 상세 정보를 저장할 변수명 ({{error}}로 접근)"
        />

        {/* Fallback Value */}
        <TextareaField
          label="폴백 값 (에러 시)"
          value={config.fallback_value}
          onChange={(v) => updateField('fallback_value', v)}
          placeholder='{"status": "failed", "data": null}'
          rows={3}
          mono
        />

        {/* Custom Error Handlers */}
        <div className="space-y-3">
          <Label>커스텀 에러 핸들러</Label>
          {config.custom_error_handlers.map((handler, index) => (
            <div key={index} className="p-3 border rounded-lg bg-muted/30 space-y-2">
              <div className="flex gap-2">
                <Input
                  placeholder="에러 유형 또는 메시지 패턴"
                  value={handler.error_type}
                  onChange={(e) => updateErrorHandler(index, 'error_type', e.target.value)}
                  className="flex-1"
                />
                <Button variant="ghost" size="icon" onClick={() => removeErrorHandler(index)}>
                  <Trash className="h-4 w-4" />
                </Button>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <Select
                  value={handler.action}
                  onValueChange={(v) => updateErrorHandler(index, 'action', v)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {HANDLER_ACTIONS.map(a => (
                      <SelectItem key={a.value} value={a.value}>{a.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Input
                  placeholder="값 또는 노드 ID"
                  value={handler.value}
                  onChange={(e) => updateErrorHandler(index, 'value', e.target.value)}
                />
              </div>
            </div>
          ))}
          <Button variant="outline" size="sm" onClick={addErrorHandler} className="w-full">
            <Plus className="h-4 w-4 mr-2" />
            에러 핸들러 추가
          </Button>
        </div>


        {/* Options */}
        <SwitchField
          label="에러 시 계속"
          description="에러가 발생해도 워크플로우 계속 진행"
          checked={config.continue_on_error}
          onChange={(v) => updateField('continue_on_error', v)}
        />

        <SwitchField
          label="에러 로깅"
          description="디버깅을 위해 에러 상세 정보 기록"
          checked={config.log_errors}
          onChange={(v) => updateField('log_errors', v)}
        />

        <SwitchField
          label="에러 시 알림"
          description="에러 발생 시 알림 전송"
          checked={config.notify_on_error}
          onChange={(v) => updateField('notify_on_error', v)}
        />

        {config.notify_on_error && (
          <SelectField
            label="알림 채널"
            value={config.notification_channel}
            onChange={(v) => updateField('notification_channel', v)}
            options={NOTIFICATION_CHANNELS.map(n => ({ value: n.value, label: n.label }))}
            placeholder="채널 선택"
          />
        )}
      </div>
    </TooltipProvider>
  );
}
