/**
 * Real-time Validation Feedback Component
 * 실시간 검증 피드백 표시 컴포넌트
 */

import React from 'react';
import { AlertCircle, CheckCircle, AlertTriangle, Info, Loader2, Save } from 'lucide-react';
import { cn } from '@/lib/utils';
import { 
  ValidationResult, 
  getValidationSummary, 
  getSecurityRiskColor, 
  getValidationIcon 
} from '@/hooks/useRealTimeValidation';

interface RealTimeValidationFeedbackProps {
  validationResult: ValidationResult | null;
  isValidating: boolean;
  hasChanges: boolean;
  onSave?: () => void;
  className?: string;
  showDetails?: boolean;
  compact?: boolean;
}

export function RealTimeValidationFeedback({
  validationResult,
  isValidating,
  hasChanges,
  onSave,
  className,
  showDetails = true,
  compact = false
}: RealTimeValidationFeedbackProps) {
  const summary = getValidationSummary(validationResult);

  if (compact) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        {isValidating ? (
          <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
        ) : (
          <span className="text-sm">{getValidationIcon(summary.status)}</span>
        )}
        
        <span className={cn(
          "text-sm font-medium",
          summary.status === 'error' && "text-red-600",
          summary.status === 'warning' && "text-yellow-600",
          summary.status === 'valid' && "text-green-600",
          summary.status === 'unknown' && "text-gray-500"
        )}>
          {summary.message}
        </span>

        {hasChanges && onSave && (
          <button
            onClick={onSave}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
          >
            <Save className="h-3 w-3" />
            저장
          </button>
        )}
      </div>
    );
  }

  return (
    <div className={cn("space-y-3", className)}>
      {/* 상태 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isValidating ? (
            <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
          ) : (
            <ValidationStatusIcon status={summary.status} />
          )}
          
          <div>
            <h3 className={cn(
              "font-medium",
              summary.status === 'error' && "text-red-700",
              summary.status === 'warning' && "text-yellow-700",
              summary.status === 'valid' && "text-green-700",
              summary.status === 'unknown' && "text-gray-700"
            )}>
              {isValidating ? '검증 중...' : summary.message}
            </h3>
            
            {validationResult?.security && (
              <p className={cn(
                "text-sm",
                getSecurityRiskColor(validationResult.security.risk_level)
              )}>
                보안 위험도: {validationResult.security.risk_level?.toUpperCase()}
              </p>
            )}
          </div>
        </div>

        {hasChanges && onSave && (
          <button
            onClick={onSave}
            className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <Save className="h-4 w-4" />
            변경사항 저장
          </button>
        )}
      </div>

      {/* 상세 피드백 */}
      {showDetails && validationResult && (
        <div className="space-y-3">
          {/* 오류 */}
          {validationResult.errors.length > 0 && (
            <ValidationSection
              title="오류"
              items={validationResult.errors}
              icon={<AlertCircle className="h-4 w-4 text-red-500" />}
              className="border-red-200 bg-red-50"
              itemClassName="text-red-700"
            />
          )}

          {/* 경고 */}
          {validationResult.warnings.length > 0 && (
            <ValidationSection
              title="경고"
              items={validationResult.warnings}
              icon={<AlertTriangle className="h-4 w-4 text-yellow-500" />}
              className="border-yellow-200 bg-yellow-50"
              itemClassName="text-yellow-700"
            />
          )}

          {/* 제안사항 */}
          {validationResult.suggestions.length > 0 && (
            <ValidationSection
              title="제안사항"
              items={validationResult.suggestions}
              icon={<Info className="h-4 w-4 text-blue-500" />}
              className="border-blue-200 bg-blue-50"
              itemClassName="text-blue-700"
            />
          )}

          {/* 보안 경고 */}
          {validationResult.security?.warnings && validationResult.security.warnings.length > 0 && (
            <ValidationSection
              title="보안 경고"
              items={validationResult.security.warnings}
              icon={<AlertTriangle className="h-4 w-4 text-orange-500" />}
              className="border-orange-200 bg-orange-50"
              itemClassName="text-orange-700"
            />
          )}

          {/* 성공 메시지 */}
          {validationResult.valid && 
           validationResult.errors.length === 0 && 
           validationResult.warnings.length === 0 && (
            <div className="flex items-center gap-2 p-3 border border-green-200 bg-green-50 rounded-md">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <span className="text-green-700 font-medium">
                설정이 유효합니다. 실행할 준비가 되었습니다.
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface ValidationSectionProps {
  title: string;
  items: string[];
  icon: React.ReactNode;
  className?: string;
  itemClassName?: string;
}

function ValidationSection({
  title,
  items,
  icon,
  className,
  itemClassName
}: ValidationSectionProps) {
  return (
    <div className={cn("p-3 border rounded-md", className)}>
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <h4 className="font-medium">{title}</h4>
        <span className="text-sm text-gray-500">({items.length})</span>
      </div>
      
      <ul className="space-y-1">
        {items.map((item, index) => (
          <li key={index} className={cn("text-sm", itemClassName)}>
            • {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function ValidationStatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'valid':
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    case 'warning':
      return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
    case 'error':
      return <AlertCircle className="h-5 w-5 text-red-500" />;
    default:
      return <Info className="h-5 w-5 text-gray-500" />;
  }
}

/**
 * 간단한 검증 상태 표시기
 */
export function ValidationStatusBadge({ 
  validationResult, 
  isValidating 
}: { 
  validationResult: ValidationResult | null; 
  isValidating: boolean; 
}) {
  const summary = getValidationSummary(validationResult);

  if (isValidating) {
    return (
      <div className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
        <Loader2 className="h-3 w-3 animate-spin" />
        검증 중
      </div>
    );
  }

  return (
    <div className={cn(
      "flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium",
      summary.status === 'valid' && "bg-green-100 text-green-700",
      summary.status === 'warning' && "bg-yellow-100 text-yellow-700",
      summary.status === 'error' && "bg-red-100 text-red-700",
      summary.status === 'unknown' && "bg-gray-100 text-gray-700"
    )}>
      <span>{getValidationIcon(summary.status)}</span>
      {summary.message}
    </div>
  );
}

/**
 * 플로팅 검증 패널
 */
export function FloatingValidationPanel({
  validationResult,
  isValidating,
  hasChanges,
  onSave,
  onClose
}: RealTimeValidationFeedbackProps & { onClose?: () => void }) {
  if (!validationResult && !isValidating) return null;

  return (
    <div className="fixed bottom-4 right-4 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
      <div className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-medium text-gray-900">실시간 검증</h3>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          )}
        </div>
        
        <RealTimeValidationFeedback
          validationResult={validationResult}
          isValidating={isValidating}
          hasChanges={hasChanges}
          onSave={onSave}
          showDetails={true}
          compact={false}
        />
      </div>
    </div>
  );
}