'use client';

import { useState, useCallback, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle,
  Lightbulb,
  Wand2,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Copy,
  Loader2,
  XCircle,
} from 'lucide-react';
import { toast } from 'sonner';

interface CodeError {
  line: number;
  column?: number;
  severity: 'error' | 'warning' | 'info';
  message: string;
  code?: string;
  source?: string;
}

interface ErrorFix {
  description: string;
  code: string;
  confidence: number;
}

interface AnalyzedError extends CodeError {
  aiAnalysis?: string;
  suggestedFixes?: ErrorFix[];
  isExpanded?: boolean;
}

interface ErrorAnalyzerProps {
  code: string;
  language: string;
  onApplyFix: (fixedCode: string) => void;
  onGoToLine?: (line: number) => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ErrorAnalyzer({
  code,
  language,
  onApplyFix,
  onGoToLine,
}: ErrorAnalyzerProps) {
  const [errors, setErrors] = useState<AnalyzedError[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [lastAnalyzed, setLastAnalyzed] = useState<string>('');

  // 코드 분석 (린팅)
  const analyzeCode = useCallback(async () => {
    if (!code.trim() || code === lastAnalyzed) return;
    
    setIsAnalyzing(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/workflow/analyze-code`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({ code, language }),
      });

      const result = await response.json();
      if (result.errors) {
        setErrors(result.errors.map((e: CodeError) => ({ ...e, isExpanded: false })));
      } else {
        setErrors([]);
      }
      setLastAnalyzed(code);
    } catch (error) {
      console.error('Analysis error:', error);
    } finally {
      setIsAnalyzing(false);
    }
  }, [code, language, lastAnalyzed]);

  // AI 에러 분석
  const analyzeErrorWithAI = useCallback(async (errorIndex: number) => {
    const error = errors[errorIndex];
    if (!error) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/workflow/ai-copilot/analyze-error`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({
          code,
          language,
          error: {
            line: error.line,
            message: error.message,
          },
        }),
      });

      const result = await response.json();
      setErrors(prev => prev.map((e, i) => 
        i === errorIndex
          ? {
              ...e,
              aiAnalysis: result.analysis,
              suggestedFixes: result.fixes || [],
              isExpanded: true,
            }
          : e
      ));
    } catch (error) {
      toast.error('AI 분석 실패');
    }
  }, [code, language, errors]);

  // 수정 적용
  const applyFix = (fix: ErrorFix) => {
    onApplyFix(fix.code);
    toast.success('수정이 적용되었습니다.');
    // 에러 목록 새로고침
    setTimeout(() => analyzeCode(), 500);
  };

  // 에러 확장 토글
  const toggleExpand = (index: number) => {
    setErrors(prev => prev.map((e, i) => 
      i === index ? { ...e, isExpanded: !e.isExpanded } : e
    ));
  };

  // 코드 변경 시 자동 분석 (디바운스)
  useEffect(() => {
    const timer = setTimeout(() => {
      if (code.trim() && code !== lastAnalyzed) {
        analyzeCode();
      }
    }, 1000);
    return () => clearTimeout(timer);
  }, [code, analyzeCode, lastAnalyzed]);

  const errorCount = errors.filter(e => e.severity === 'error').length;
  const warningCount = errors.filter(e => e.severity === 'warning').length;
  const infoCount = errors.filter(e => e.severity === 'info').length;

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'warning': return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'info': return <Info className="h-4 w-4 text-blue-500" />;
      default: return <AlertCircle className="h-4 w-4" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error': return 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950/30';
      case 'warning': return 'border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-950/30';
      case 'info': return 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950/30';
      default: return 'border-gray-200 bg-gray-50';
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2 p-3 bg-muted rounded-lg">
        <AlertCircle className="h-5 w-5" />
        <span className="font-medium flex-1">코드 분석</span>
        <div className="flex gap-2">
          {errorCount > 0 && (
            <Badge variant="destructive" className="text-xs">{errorCount} 에러</Badge>
          )}
          {warningCount > 0 && (
            <Badge variant="secondary" className="text-xs bg-yellow-100 text-yellow-800">{warningCount} 경고</Badge>
          )}
          {infoCount > 0 && (
            <Badge variant="secondary" className="text-xs">{infoCount} 정보</Badge>
          )}
          {errors.length === 0 && !isAnalyzing && (
            <Badge variant="secondary" className="text-xs bg-green-100 text-green-800">
              <CheckCircle className="h-3 w-3 mr-1" />
              문제 없음
            </Badge>
          )}
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={analyzeCode}
          disabled={isAnalyzing}
        >
          {isAnalyzing ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Error List */}
      {errors.length > 0 && (
        <ScrollArea className="max-h-80">
          <div className="space-y-2">
            {errors.map((error, index) => (
              <div
                key={`${error.line}-${index}`}
                className={`rounded-lg border p-3 ${getSeverityColor(error.severity)}`}
              >
                {/* Error Header */}
                <div
                  className="flex items-start gap-2 cursor-pointer"
                  onClick={() => toggleExpand(index)}
                >
                  {error.isExpanded ? (
                    <ChevronDown className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  ) : (
                    <ChevronRight className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  )}
                  {getSeverityIcon(error.severity)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span
                        className="text-xs font-mono text-muted-foreground cursor-pointer hover:underline"
                        onClick={(e) => {
                          e.stopPropagation();
                          onGoToLine?.(error.line);
                        }}
                      >
                        Line {error.line}{error.column ? `:${error.column}` : ''}
                      </span>
                      {error.code && (
                        <Badge variant="outline" className="text-xs">{error.code}</Badge>
                      )}
                    </div>
                    <p className="text-sm mt-1">{error.message}</p>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="flex-shrink-0"
                    onClick={(e) => {
                      e.stopPropagation();
                      analyzeErrorWithAI(index);
                    }}
                  >
                    <Lightbulb className="h-4 w-4" />
                  </Button>
                </div>

                {/* Expanded Content */}
                {error.isExpanded && (
                  <div className="mt-3 pt-3 border-t space-y-3">
                    {/* AI Analysis */}
                    {error.aiAnalysis && (
                      <div className="p-2 bg-purple-50 dark:bg-purple-950/30 rounded border border-purple-200 dark:border-purple-800">
                        <div className="flex items-center gap-2 mb-2">
                          <Lightbulb className="h-4 w-4 text-purple-600" />
                          <span className="text-xs font-medium text-purple-700 dark:text-purple-300">AI 분석</span>
                        </div>
                        <p className="text-sm text-purple-600 dark:text-purple-400">{error.aiAnalysis}</p>
                      </div>
                    )}

                    {/* Suggested Fixes */}
                    {error.suggestedFixes && error.suggestedFixes.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs font-medium">수정 제안:</p>
                        {error.suggestedFixes.map((fix, fixIndex) => (
                          <div
                            key={fixIndex}
                            className="p-2 bg-green-50 dark:bg-green-950/30 rounded border border-green-200 dark:border-green-800"
                          >
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs">{fix.description}</span>
                              <Badge variant="outline" className="text-xs">
                                {Math.round(fix.confidence * 100)}% 신뢰도
                              </Badge>
                            </div>
                            <pre className="text-xs bg-black/10 dark:bg-white/10 p-2 rounded overflow-auto max-h-24 font-mono">
                              {fix.code.slice(0, 300)}...
                            </pre>
                            <div className="flex gap-2 mt-2">
                              <Button
                                size="sm"
                                onClick={() => applyFix(fix)}
                                className="gap-1"
                              >
                                <Wand2 className="h-3 w-3" />
                                적용
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  navigator.clipboard.writeText(fix.code);
                                  toast.success('코드가 복사되었습니다.');
                                }}
                              >
                                <Copy className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Request AI Analysis Button */}
                    {!error.aiAnalysis && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => analyzeErrorWithAI(index)}
                        className="w-full gap-2"
                      >
                        <Lightbulb className="h-4 w-4" />
                        AI로 분석하기
                      </Button>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
      )}

      {/* Empty State */}
      {errors.length === 0 && !isAnalyzing && (
        <div className="text-center py-8 text-muted-foreground">
          <CheckCircle className="h-12 w-12 mx-auto mb-3 text-green-500" />
          <p className="text-sm">코드에 문제가 없습니다!</p>
          <p className="text-xs mt-1">코드를 수정하면 자동으로 분석됩니다.</p>
        </div>
      )}

      {/* Loading State */}
      {isAnalyzing && (
        <div className="flex items-center justify-center gap-2 py-8">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span className="text-sm text-muted-foreground">코드 분석 중...</span>
        </div>
      )}
    </div>
  );
}
