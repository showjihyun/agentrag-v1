'use client';

import { useState, useCallback, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import {
  Sparkles,
  Loader2,
  Wand2,
  MessageSquare,
  Lightbulb,
  RefreshCw,
  ThumbsUp,
  ThumbsDown,
  X,
  Zap,
} from 'lucide-react';
import { toast } from 'sonner';

interface AICopilotProps {
  code: string;
  language: string;
  onCodeUpdate: (code: string) => void;
  previousNodeOutput?: any;
  workflowContext?: any;
}

interface Suggestion {
  id: string;
  type: 'completion' | 'fix' | 'optimization' | 'explanation';
  content: string;
  code?: string;
  confidence: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function AICopilot({
  code,
  language,
  onCodeUpdate,
  previousNodeOutput,
  workflowContext,
}: AICopilotProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [prompt, setPrompt] = useState('');
  const [explanation, setExplanation] = useState<string | null>(null);
  const [showInlineAssist, setShowInlineAssist] = useState(false);

  // AI 코드 완성 요청
  const requestCompletion = useCallback(async (cursorPosition?: number) => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/workflow/ai-copilot/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({
          code,
          language,
          cursor_position: cursorPosition,
          previous_node_output: previousNodeOutput,
          workflow_context: workflowContext,
        }),
      });

      const result = await response.json();
      if (result.suggestions) {
        setSuggestions(result.suggestions);
      }
    } catch (error) {
      console.error('Completion error:', error);
    } finally {
      setIsLoading(false);
    }
  }, [code, language, previousNodeOutput, workflowContext]);

  // 코드 설명 요청
  const explainCode = useCallback(async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/workflow/ai-copilot/explain`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({ code, language }),
      });

      const result = await response.json();
      if (result.explanation) {
        setExplanation(result.explanation);
      }
    } catch (error) {
      toast.error('코드 설명 생성 실패');
    } finally {
      setIsLoading(false);
    }
  }, [code, language]);

  // 코드 최적화 제안
  const suggestOptimization = useCallback(async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/workflow/ai-copilot/optimize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({ code, language }),
      });

      const result = await response.json();
      if (result.optimized_code) {
        setSuggestions([{
          id: 'opt-1',
          type: 'optimization',
          content: result.explanation || '최적화된 코드',
          code: result.optimized_code,
          confidence: result.confidence || 0.8,
        }]);
      }
    } catch (error) {
      toast.error('최적화 제안 실패');
    } finally {
      setIsLoading(false);
    }
  }, [code, language]);

  // 에러 자동 수정
  const fixError = useCallback(async (errorMessage: string) => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/workflow/ai-copilot/fix`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({ code, language, error: errorMessage }),
      });

      const result = await response.json();
      if (result.fixed_code) {
        setSuggestions([{
          id: 'fix-1',
          type: 'fix',
          content: result.explanation || '에러 수정',
          code: result.fixed_code,
          confidence: result.confidence || 0.9,
        }]);
      }
    } catch (error) {
      toast.error('에러 수정 실패');
    } finally {
      setIsLoading(false);
    }
  }, [code, language]);

  // 자연어 → 코드 변환
  const generateFromPrompt = useCallback(async () => {
    if (!prompt.trim()) return;
    
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/workflow/ai-copilot/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({
          prompt,
          language,
          existing_code: code,
          previous_node_output: previousNodeOutput,
        }),
      });

      const result = await response.json();
      if (result.code) {
        onCodeUpdate(result.code);
        toast.success('코드가 생성되었습니다!');
        setPrompt('');
      }
    } catch (error) {
      toast.error('코드 생성 실패');
    } finally {
      setIsLoading(false);
    }
  }, [prompt, language, code, previousNodeOutput, onCodeUpdate]);

  // 제안 적용
  const applySuggestion = (suggestion: Suggestion) => {
    if (suggestion.code) {
      onCodeUpdate(suggestion.code);
      toast.success('제안이 적용되었습니다.');
      setSuggestions([]);
    }
  };

  return (
    <div className="space-y-4">
      {/* AI Assistant Header */}
      <div className="flex items-center gap-2 p-3 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-950/50 dark:to-blue-950/50 rounded-lg border">
        <Sparkles className="h-5 w-5 text-purple-600" />
        <span className="font-medium flex-1">AI Copilot</span>
        <Badge variant="secondary" className="text-xs">Beta</Badge>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={explainCode}
          disabled={isLoading || !code.trim()}
          className="gap-2"
        >
          <MessageSquare className="h-4 w-4" />
          코드 설명
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={suggestOptimization}
          disabled={isLoading || !code.trim()}
          className="gap-2"
        >
          <Zap className="h-4 w-4" />
          최적화 제안
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => requestCompletion()}
          disabled={isLoading || !code.trim()}
          className="gap-2"
        >
          <Lightbulb className="h-4 w-4" />
          자동 완성
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowInlineAssist(!showInlineAssist)}
          className="gap-2"
        >
          <Wand2 className="h-4 w-4" />
          인라인 어시스트
        </Button>
      </div>

      {/* Natural Language Input */}
      <div className="space-y-2">
        <Textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="원하는 기능을 자연어로 설명하세요... (예: 이전 노드의 items 배열을 필터링해서 active인 것만 추출)"
          rows={3}
          className="text-sm"
        />
        <Button
          onClick={generateFromPrompt}
          disabled={isLoading || !prompt.trim()}
          className="w-full gap-2 bg-gradient-to-r from-purple-600 to-blue-600"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Sparkles className="h-4 w-4" />
          )}
          코드 생성
        </Button>
      </div>

      {/* Code Explanation */}
      {explanation && (
        <div className="p-3 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-blue-700 dark:text-blue-300">코드 설명</span>
            <Button variant="ghost" size="sm" onClick={() => setExplanation(null)}>
              <X className="h-4 w-4" />
            </Button>
          </div>
          <p className="text-sm text-blue-600 dark:text-blue-400 whitespace-pre-wrap">{explanation}</p>
        </div>
      )}

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground">AI 제안</p>
          {suggestions.map((suggestion) => (
            <div
              key={suggestion.id}
              className="p-3 bg-muted rounded-lg border space-y-2"
            >
              <div className="flex items-center gap-2">
                <Badge variant={suggestion.type === 'fix' ? 'destructive' : 'secondary'} className="text-xs">
                  {suggestion.type === 'fix' ? '수정' : suggestion.type === 'optimization' ? '최적화' : '제안'}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  신뢰도: {Math.round(suggestion.confidence * 100)}%
                </span>
              </div>
              <p className="text-sm">{suggestion.content}</p>
              {suggestion.code && (
                <pre className="text-xs bg-black/10 dark:bg-white/10 p-2 rounded overflow-auto max-h-32">
                  {suggestion.code.slice(0, 500)}...
                </pre>
              )}
              <div className="flex gap-2">
                <Button size="sm" onClick={() => applySuggestion(suggestion)} className="gap-1">
                  <ThumbsUp className="h-3 w-3" />
                  적용
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setSuggestions(suggestions.filter(s => s.id !== suggestion.id))}
                >
                  <ThumbsDown className="h-3 w-3" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Previous Node Context */}
      {previousNodeOutput && (
        <div className="p-3 bg-muted rounded-lg">
          <p className="text-xs font-medium mb-2">이전 노드 출력 스키마:</p>
          <pre className="text-xs overflow-auto max-h-20">
            {JSON.stringify(previousNodeOutput, null, 2).slice(0, 200)}...
          </pre>
        </div>
      )}

      {/* Loading Indicator */}
      {isLoading && (
        <div className="flex items-center justify-center gap-2 p-4">
          <Loader2 className="h-5 w-5 animate-spin text-purple-600" />
          <span className="text-sm text-muted-foreground">AI가 분석 중...</span>
        </div>
      )}
    </div>
  );
}
