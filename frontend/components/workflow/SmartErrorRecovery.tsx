'use client';

/**
 * Smart Error Recovery Component
 * 
 * AI-powered error analysis and recovery:
 * - Automatic error classification
 * - AI-generated fix suggestions
 * - One-click recovery options
 * - Error pattern learning
 */

import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  AlertTriangle,
  Sparkles,
  RefreshCw,
  ArrowRight,
  Clock,
  Zap,
  Database,
  Shield,
  CheckCircle2,
  XCircle,
  Loader2,
  ChevronDown,
  ChevronRight,
  Copy,
  ExternalLink,
  Lightbulb,
  History,
  TrendingUp,
} from 'lucide-react';

// Types
export interface WorkflowError {
  id: string;
  nodeId: string;
  nodeName: string;
  nodeType: string;
  errorType: ErrorType;
  errorCode?: string;
  message: string;
  stackTrace?: string;
  timestamp: number;
  context: Record<string, unknown>;
  retryCount: number;
  maxRetries: number;
}

export type ErrorType = 
  | 'rate_limit'
  | 'timeout'
  | 'connection'
  | 'authentication'
  | 'validation'
  | 'resource_not_found'
  | 'permission_denied'
  | 'internal_error'
  | 'unknown';

export interface RecoveryOption {
  id: string;
  type: RecoveryType;
  title: string;
  description: string;
  estimatedTime?: string;
  confidence: number;
  isRecommended?: boolean;
  requiresInput?: boolean;
  inputLabel?: string;
}

export type RecoveryType = 
  | 'retry_with_backoff'
  | 'use_fallback'
  | 'use_cache'
  | 'skip_node'
  | 'manual_input'
  | 'modify_config'
  | 'contact_support';

export interface AIAnalysis {
  summary: string;
  rootCause: string;
  impact: 'low' | 'medium' | 'high' | 'critical';
  similarErrors: number;
  suggestedFix?: string;
  codeSnippet?: string;
  documentation?: string;
}

interface SmartErrorRecoveryProps {
  error: WorkflowError;
  aiAnalysis?: AIAnalysis;
  recoveryOptions: RecoveryOption[];
  isAnalyzing?: boolean;
  onSelectRecovery: (optionId: string, input?: string) => void;
  onDismiss: () => void;
  onViewHistory: () => void;
  className?: string;
}

// Error Type Config
const errorTypeConfig: Record<ErrorType, { icon: React.ElementType; color: string; label: string }> = {
  rate_limit: { icon: Clock, color: 'text-yellow-500', label: 'Rate Limit' },
  timeout: { icon: Clock, color: 'text-orange-500', label: 'Timeout' },
  connection: { icon: Zap, color: 'text-red-500', label: 'Connection Error' },
  authentication: { icon: Shield, color: 'text-purple-500', label: 'Auth Error' },
  validation: { icon: AlertTriangle, color: 'text-amber-500', label: 'Validation Error' },
  resource_not_found: { icon: Database, color: 'text-gray-500', label: 'Not Found' },
  permission_denied: { icon: Shield, color: 'text-red-500', label: 'Permission Denied' },
  internal_error: { icon: XCircle, color: 'text-red-600', label: 'Internal Error' },
  unknown: { icon: AlertTriangle, color: 'text-gray-500', label: 'Unknown Error' },
};

// Impact Badge
const ImpactBadge: React.FC<{ impact: AIAnalysis['impact'] }> = ({ impact }) => {
  const config = {
    low: { color: 'bg-green-100 text-green-700', label: '낮음' },
    medium: { color: 'bg-yellow-100 text-yellow-700', label: '중간' },
    high: { color: 'bg-orange-100 text-orange-700', label: '높음' },
    critical: { color: 'bg-red-100 text-red-700', label: '심각' },
  };

  return (
    <Badge className={cn('text-xs', config[impact].color)}>
      영향도: {config[impact].label}
    </Badge>
  );
};

// Recovery Option Card
const RecoveryOptionCard: React.FC<{
  option: RecoveryOption;
  isSelected: boolean;
  onSelect: () => void;
}> = ({ option, isSelected, onSelect }) => {
  const getIcon = (type: RecoveryType) => {
    switch (type) {
      case 'retry_with_backoff': return RefreshCw;
      case 'use_fallback': return ArrowRight;
      case 'use_cache': return Database;
      case 'skip_node': return CheckCircle2;
      case 'manual_input': return Lightbulb;
      case 'modify_config': return Zap;
      case 'contact_support': return ExternalLink;
      default: return AlertTriangle;
    }
  };

  const Icon = getIcon(option.type);

  return (
    <div
      className={cn(
        'relative p-4 rounded-lg border-2 cursor-pointer transition-all',
        isSelected 
          ? 'border-primary bg-primary/5' 
          : 'border-muted hover:border-primary/50',
        option.isRecommended && 'ring-2 ring-green-500/20'
      )}
      onClick={onSelect}
    >
      {option.isRecommended && (
        <Badge className="absolute -top-2 -right-2 bg-green-500 text-white text-xs">
          추천
        </Badge>
      )}
      
      <div className="flex items-start gap-3">
        <div className={cn(
          'p-2 rounded-lg',
          isSelected ? 'bg-primary/10' : 'bg-muted'
        )}>
          <Icon className={cn('w-5 h-5', isSelected ? 'text-primary' : 'text-muted-foreground')} />
        </div>
        
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium">{option.title}</span>
            {option.estimatedTime && (
              <span className="text-xs text-muted-foreground">
                ~{option.estimatedTime}
              </span>
            )}
          </div>
          <p className="text-sm text-muted-foreground mt-1">{option.description}</p>
          
          {/* Confidence bar */}
          <div className="flex items-center gap-2 mt-2">
            <span className="text-xs text-muted-foreground">신뢰도</span>
            <Progress value={option.confidence} className="h-1.5 flex-1 max-w-24" />
            <span className="text-xs font-medium">{option.confidence}%</span>
          </div>
        </div>
        
        <div className={cn(
          'w-5 h-5 rounded-full border-2 flex items-center justify-center',
          isSelected ? 'border-primary bg-primary' : 'border-muted'
        )}>
          {isSelected && <CheckCircle2 className="w-3 h-3 text-white" />}
        </div>
      </div>
    </div>
  );
};

// Main Component
export function SmartErrorRecovery({
  error,
  aiAnalysis,
  recoveryOptions,
  isAnalyzing = false,
  onSelectRecovery,
  onDismiss,
  onViewHistory,
  className,
}: SmartErrorRecoveryProps) {
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [manualInput, setManualInput] = useState('');
  const [showStackTrace, setShowStackTrace] = useState(false);
  const [isApplying, setIsApplying] = useState(false);

  const errorConfig = errorTypeConfig[error.errorType];
  const ErrorIcon = errorConfig.icon;

  // Auto-select recommended option
  useEffect(() => {
    const recommended = recoveryOptions.find(o => o.isRecommended);
    if (recommended) {
      setSelectedOption(recommended.id);
    }
  }, [recoveryOptions]);

  const handleApplyRecovery = async () => {
    if (!selectedOption) return;
    
    setIsApplying(true);
    const option = recoveryOptions.find(o => o.id === selectedOption);
    
    try {
      await onSelectRecovery(selectedOption, option?.requiresInput ? manualInput : undefined);
    } finally {
      setIsApplying(false);
    }
  };

  const selectedRecoveryOption = recoveryOptions.find(o => o.id === selectedOption);

  return (
    <div className={cn('bg-background border rounded-lg shadow-lg overflow-hidden', className)}>
      {/* Header */}
      <div className="bg-gradient-to-r from-red-500 to-orange-500 p-4 text-white">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-white/20 rounded-lg">
            <ErrorIcon className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-lg">워크플로우 오류 발생</h3>
              <Badge variant="secondary" className="bg-white/20 text-white">
                {errorConfig.label}
              </Badge>
            </div>
            <p className="text-white/80 text-sm mt-1">
              {error.nodeName} ({error.nodeType})
            </p>
          </div>
          <Button 
            variant="ghost" 
            size="sm" 
            className="text-white hover:bg-white/20"
            onClick={onViewHistory}
          >
            <History className="w-4 h-4 mr-1" />
            이력
          </Button>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Error Message */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-500" />
              오류 메시지
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm font-mono bg-muted p-2 rounded">{error.message}</p>
            
            {error.stackTrace && (
              <div className="mt-2">
                <button
                  className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
                  onClick={() => setShowStackTrace(!showStackTrace)}
                >
                  {showStackTrace ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                  Stack Trace
                </button>
                {showStackTrace && (
                  <pre className="mt-2 text-xs bg-muted p-2 rounded overflow-x-auto">
                    {error.stackTrace}
                  </pre>
                )}
              </div>
            )}
            
            <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
              <span>재시도: {error.retryCount}/{error.maxRetries}</span>
              <span>발생 시간: {new Date(error.timestamp).toLocaleString()}</span>
            </div>
          </CardContent>
        </Card>

        {/* AI Analysis */}
        <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-blue-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-500" />
              AI 분석
              {isAnalyzing && <Loader2 className="w-3 h-3 animate-spin" />}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isAnalyzing ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="w-4 h-4 animate-spin" />
                오류를 분석하고 있습니다...
              </div>
            ) : aiAnalysis ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <ImpactBadge impact={aiAnalysis.impact} />
                  {aiAnalysis.similarErrors > 0 && (
                    <Badge variant="outline" className="text-xs">
                      <TrendingUp className="w-3 h-3 mr-1" />
                      유사 오류 {aiAnalysis.similarErrors}건
                    </Badge>
                  )}
                </div>
                
                <div>
                  <p className="text-sm font-medium">요약</p>
                  <p className="text-sm text-muted-foreground">{aiAnalysis.summary}</p>
                </div>
                
                <div>
                  <p className="text-sm font-medium">근본 원인</p>
                  <p className="text-sm text-muted-foreground">{aiAnalysis.rootCause}</p>
                </div>
                
                {aiAnalysis.suggestedFix && (
                  <div>
                    <p className="text-sm font-medium">제안된 수정</p>
                    <p className="text-sm text-muted-foreground">{aiAnalysis.suggestedFix}</p>
                  </div>
                )}
                
                {aiAnalysis.codeSnippet && (
                  <div>
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium">코드 수정</p>
                      <Button variant="ghost" size="sm" className="h-6">
                        <Copy className="w-3 h-3 mr-1" />
                        복사
                      </Button>
                    </div>
                    <pre className="text-xs bg-gray-900 text-gray-100 p-3 rounded-md mt-1 overflow-x-auto">
                      {aiAnalysis.codeSnippet}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">분석 결과가 없습니다</p>
            )}
          </CardContent>
        </Card>

        {/* Recovery Options */}
        <div>
          <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
            <Lightbulb className="w-4 h-4 text-yellow-500" />
            복구 옵션 선택
          </h4>
          
          <div className="space-y-2">
            {recoveryOptions.map((option) => (
              <RecoveryOptionCard
                key={option.id}
                option={option}
                isSelected={selectedOption === option.id}
                onSelect={() => setSelectedOption(option.id)}
              />
            ))}
          </div>

          {/* Manual Input */}
          {selectedRecoveryOption?.requiresInput && (
            <div className="mt-4">
              <Label className="text-sm">{selectedRecoveryOption.inputLabel || '입력값'}</Label>
              <textarea
                value={manualInput}
                onChange={(e) => setManualInput(e.target.value)}
                className="w-full mt-1 p-2 border rounded-md text-sm"
                rows={3}
                placeholder="값을 입력하세요..."
              />
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between p-4 border-t bg-muted/30">
        <Button variant="ghost" onClick={onDismiss}>
          나중에 처리
        </Button>
        <div className="flex gap-2">
          <Button variant="outline" onClick={onDismiss}>
            워크플로우 중단
          </Button>
          <Button 
            onClick={handleApplyRecovery}
            disabled={!selectedOption || isApplying}
          >
            {isApplying ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                적용 중...
              </>
            ) : (
              <>
                <CheckCircle2 className="w-4 h-4 mr-2" />
                복구 적용
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

export default SmartErrorRecovery;
