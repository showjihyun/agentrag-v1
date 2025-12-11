'use client';

/**
 * HumanApprovalConfig - Human Approval Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { UserCheck, Plus, Trash } from 'lucide-react';
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

const APPROVAL_TYPES = [
  { value: 'single', label: 'Single Approver (any one)' },
  { value: 'all', label: 'All Approvers Required' },
  { value: 'majority', label: 'Majority Vote' },
  { value: 'sequential', label: 'Sequential (in order)' },
] as const;

const TIMEOUT_ACTIONS = [
  { value: 'reject', label: 'Auto Reject' },
  { value: 'approve', label: 'Auto Approve' },
  { value: 'escalate', label: 'Escalate' },
  { value: 'fail', label: 'Fail Workflow' },
] as const;

const NOTIFICATION_METHODS = [
  { value: 'email', label: 'Email' },
  { value: 'slack', label: 'Slack' },
  { value: 'both', label: 'Email + Slack' },
  { value: 'none', label: 'None (UI only)' },
] as const;

const OPTION_COLORS = [
  { value: 'green', label: 'Green' },
  { value: 'red', label: 'Red' },
  { value: 'yellow', label: 'Yellow' },
  { value: 'blue', label: 'Blue' },
  { value: 'gray', label: 'Gray' },
] as const;


// ============================================
// Types
// ============================================

interface Approver {
  email: string;
  name: string;
}

interface ApprovalOption {
  value: string;
  label: string;
  color: string;
}

interface HumanApprovalConfigData {
  title: string;
  description: string;
  approval_type: string;
  approvers: Approver[];
  timeout: number;
  timeout_action: string;
  require_comment: boolean;
  show_data: boolean;
  data_fields: string;
  approval_options: ApprovalOption[];
  notification_method: string;
  reminder_interval: number;
  escalation_after: number;
  escalation_to: string;
}

const DEFAULTS: HumanApprovalConfigData = {
  title: 'Approval Required',
  description: '',
  approval_type: 'single',
  approvers: [],
  timeout: 0,
  timeout_action: 'reject',
  require_comment: false,
  show_data: true,
  data_fields: '',
  approval_options: [
    { value: 'approve', label: 'Approve', color: 'green' },
    { value: 'reject', label: 'Reject', color: 'red' },
  ],
  notification_method: 'email',
  reminder_interval: 0,
  escalation_after: 0,
  escalation_to: '',
};

// ============================================
// Component
// ============================================

export default function HumanApprovalConfig({ data, onChange }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<HumanApprovalConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });


  const addApprover = useCallback(() => {
    updateField('approvers', [...config.approvers, { email: '', name: '' }]);
  }, [config.approvers, updateField]);

  const updateApprover = useCallback((index: number, field: keyof Approver, value: string) => {
    const newApprovers = [...config.approvers];
    newApprovers[index] = { ...newApprovers[index], [field]: value };
    updateField('approvers', newApprovers);
  }, [config.approvers, updateField]);

  const removeApprover = useCallback((index: number) => {
    updateField('approvers', config.approvers.filter((_, i) => i !== index));
  }, [config.approvers, updateField]);

  const addOption = useCallback(() => {
    updateField('approval_options', [
      ...config.approval_options,
      { value: '', label: '', color: 'gray' },
    ]);
  }, [config.approval_options, updateField]);

  const updateOption = useCallback((index: number, field: keyof ApprovalOption, value: string) => {
    const newOptions = [...config.approval_options];
    newOptions[index] = { ...newOptions[index], [field]: value };
    updateField('approval_options', newOptions);
  }, [config.approval_options, updateField]);

  const removeOption = useCallback((index: number) => {
    updateField('approval_options', config.approval_options.filter((_, i) => i !== index));
  }, [config.approval_options, updateField]);

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={UserCheck}
          iconBgColor="bg-emerald-100 dark:bg-emerald-950"
          iconColor="text-emerald-600 dark:text-emerald-400"
          title="Human Approval"
          description="사람의 결정을 기다림"
        />

        {/* Title & Description */}
        <TextField
          label="승인 제목"
          value={config.title}
          onChange={(v) => updateField('title', v)}
          placeholder="Review and approve this request"
        />

        <TextareaField
          label="설명"
          value={config.description}
          onChange={(v) => updateField('description', v)}
          placeholder="Please review the following data and make a decision..."
          rows={3}
          hint="{{variables}}를 사용하여 동적 콘텐츠 포함 가능"
        />


        {/* Approval Type */}
        <SelectField
          label="승인 유형"
          value={config.approval_type}
          onChange={(v) => updateField('approval_type', v)}
          options={APPROVAL_TYPES.map(a => ({ value: a.value, label: a.label }))}
        />

        {/* Approvers */}
        <div className="space-y-3">
          <Label>승인자</Label>
          {config.approvers.map((approver, index) => (
            <div key={index} className="flex gap-2">
              <Input
                placeholder="Email"
                value={approver.email}
                onChange={(e) => updateApprover(index, 'email', e.target.value)}
                className="flex-1"
              />
              <Input
                placeholder="이름 (선택)"
                value={approver.name}
                onChange={(e) => updateApprover(index, 'name', e.target.value)}
                className="flex-1"
              />
              <Button variant="ghost" size="icon" onClick={() => removeApprover(index)}>
                <Trash className="h-4 w-4" />
              </Button>
            </div>
          ))}
          <Button variant="outline" size="sm" onClick={addApprover} className="w-full">
            <Plus className="h-4 w-4 mr-2" />
            승인자 추가
          </Button>
          <p className="text-xs text-muted-foreground">
            비워두면 워크플로우 소유자가 승인자가 됩니다
          </p>
        </div>

        {/* Approval Options */}
        <div className="space-y-3">
          <Label>승인 옵션</Label>
          {config.approval_options.map((option, index) => (
            <div key={index} className="flex gap-2">
              <Input
                placeholder="Value"
                value={option.value}
                onChange={(e) => updateOption(index, 'value', e.target.value)}
                className="w-24"
              />
              <Input
                placeholder="Label"
                value={option.label}
                onChange={(e) => updateOption(index, 'label', e.target.value)}
                className="flex-1"
              />
              <Select value={option.color} onValueChange={(v) => updateOption(index, 'color', v)}>
                <SelectTrigger className="w-24">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {OPTION_COLORS.map(c => (
                    <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => removeOption(index)}
                disabled={config.approval_options.length <= 2}
              >
                <Trash className="h-4 w-4" />
              </Button>
            </div>
          ))}
          <Button variant="outline" size="sm" onClick={addOption} className="w-full">
            <Plus className="h-4 w-4 mr-2" />
            옵션 추가
          </Button>
        </div>


        {/* Timeout */}
        <div className="grid grid-cols-2 gap-4">
          <NumberField
            label="타임아웃 (시간, 0 = 무제한)"
            value={config.timeout}
            onChange={(v) => updateField('timeout', v)}
            min={0}
          />
          <SelectField
            label="타임아웃 시"
            value={config.timeout_action}
            onChange={(v) => updateField('timeout_action', v)}
            options={TIMEOUT_ACTIONS.map(t => ({ value: t.value, label: t.label }))}
          />
        </div>

        {/* Notification */}
        <SelectField
          label="알림 방법"
          value={config.notification_method}
          onChange={(v) => updateField('notification_method', v)}
          options={NOTIFICATION_METHODS.map(n => ({ value: n.value, label: n.label }))}
        />

        {/* Reminder & Escalation */}
        <div className="grid grid-cols-2 gap-4">
          <NumberField
            label="리마인더 간격 (시간)"
            value={config.reminder_interval}
            onChange={(v) => updateField('reminder_interval', v)}
            min={0}
          />
          <NumberField
            label="에스컬레이션 (시간 후)"
            value={config.escalation_after}
            onChange={(v) => updateField('escalation_after', v)}
            min={0}
          />
        </div>

        {config.escalation_after > 0 && (
          <TextField
            label="에스컬레이션 대상 (email)"
            value={config.escalation_to}
            onChange={(v) => updateField('escalation_to', v)}
            placeholder="manager@example.com"
          />
        )}

        {/* Options */}
        <SwitchField
          label="코멘트 필수"
          description="승인자가 코멘트를 반드시 작성해야 함"
          checked={config.require_comment}
          onChange={(v) => updateField('require_comment', v)}
        />

        <SwitchField
          label="승인자에게 데이터 표시"
          description="승인 요청에 워크플로우 데이터 표시"
          checked={config.show_data}
          onChange={(v) => updateField('show_data', v)}
        />

        {config.show_data && (
          <TextField
            label="표시할 데이터 필드"
            value={config.data_fields}
            onChange={(v) => updateField('data_fields', v)}
            placeholder="field1, field2, nested.field (비워두면 전체)"
          />
        )}
      </div>
    </TooltipProvider>
  );
}
