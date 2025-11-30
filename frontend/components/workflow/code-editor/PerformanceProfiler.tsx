'use client';

import { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Activity,
  Clock,
  Cpu,
  HardDrive,
  Zap,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Loader2,
  BarChart3,
  Flame,
} from 'lucide-react';
import { toast } from 'sonner';

interface ProfileResult {
  totalTime: number;
  memoryUsage: number;
  functions: FunctionProfile[];
  hotspots: Hotspot[];
  suggestions: string[];
}

interface FunctionProfile {
  name: string;
  calls: number;
  totalTime: number;
  avgTime: number;
  percentage: number;
  memoryUsage: number;
}

interface Hotspot {
  line: number;
  description: string;
  impact: 'high' | 'medium' | 'low';
  suggestion: string;
}

interface PerformanceProfilerProps {
  code: string;
  language: string;
  input: any;
  onOptimize?: (optimizedCode: string) => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function PerformanceProfiler({
  code,
  language,
  input,
  onOptimize,
}: PerformanceProfilerProps) {
  const [isProfileing, setIsProfiling] = useState(false);
  const [result, setResult] = useState<ProfileResult | null>(null);

  // 프로파일링 실행
  const runProfile = useCallback(async () => {
    setIsProfiling(true);
    setResult(null);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/workflow/profile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({ code, language, input }),
      });

      const data = await response.json();
      if (data.error) {
        toast.error(data.error);
      } else {
        setResult(data);
      }
    } catch (error) {
      toast.error('프로파일링 실패');
    } finally {
      setIsProfiling(false);
    }
  }, [code, language, input]);

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'text-red-500 bg-red-50 dark:bg-red-950/30';
      case 'medium': return 'text-yellow-500 bg-yellow-50 dark:bg-yellow-950/30';
      case 'low': return 'text-blue-500 bg-blue-50 dark:bg-blue-950/30';
      default: return 'text-gray-500';
    }
  };

  const formatTime = (ms: number) => {
    if (ms < 1) return `${(ms * 1000).toFixed(2)}μs`;
    if (ms < 1000) return `${ms.toFixed(2)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatMemory = (bytes: number) => {
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)}MB`;
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2 p-3 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950/30 dark:to-emerald-950/30 rounded-lg border border-green-200 dark:border-green-800">
        <Activity className="h-5 w-5 text-green-600" />
        <span className="font-medium flex-1">Performance Profiler</span>
        <Badge variant="secondary" className="text-xs">Phase 3</Badge>
      </div>

      {/* Run Button */}
      <Button
        onClick={runProfile}
        disabled={isProfileing || !code.trim()}
        className="w-full gap-2"
      >
        {isProfileing ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            프로파일링 중...
          </>
        ) : (
          <>
            <Flame className="h-4 w-4" />
            성능 분석 실행
          </>
        )}
      </Button>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-muted rounded-lg">
              <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                <Clock className="h-4 w-4" />
                총 실행 시간
              </div>
              <p className="text-lg font-semibold">{formatTime(result.totalTime)}</p>
            </div>
            <div className="p-3 bg-muted rounded-lg">
              <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                <HardDrive className="h-4 w-4" />
                메모리 사용량
              </div>
              <p className="text-lg font-semibold">{formatMemory(result.memoryUsage)}</p>
            </div>
          </div>

          {/* Function Profiles */}
          {result.functions.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                함수별 성능
              </p>
              <div className="space-y-2">
                {result.functions.slice(0, 5).map((fn, idx) => (
                  <div key={idx} className="p-2 bg-muted rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-mono">{fn.name}()</span>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">{fn.calls} calls</Badge>
                        <span className="text-xs text-muted-foreground">{formatTime(fn.totalTime)}</span>
                      </div>
                    </div>
                    <Progress value={fn.percentage} className="h-1.5" />
                    <p className="text-xs text-muted-foreground mt-1">
                      {fn.percentage.toFixed(1)}% of total time
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Hotspots */}
          {result.hotspots.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium flex items-center gap-2">
                <Flame className="h-4 w-4 text-orange-500" />
                성능 핫스팟
              </p>
              <div className="space-y-2">
                {result.hotspots.map((hotspot, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-lg border ${getImpactColor(hotspot.impact)}`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Badge
                        variant={hotspot.impact === 'high' ? 'destructive' : 'secondary'}
                        className="text-xs"
                      >
                        {hotspot.impact === 'high' ? '높음' : hotspot.impact === 'medium' ? '중간' : '낮음'}
                      </Badge>
                      <span className="text-xs">Line {hotspot.line}</span>
                    </div>
                    <p className="text-sm">{hotspot.description}</p>
                    <p className="text-xs mt-1 opacity-80">💡 {hotspot.suggestion}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Suggestions */}
          {result.suggestions.length > 0 && (
            <div className="p-3 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-800">
              <p className="text-sm font-medium mb-2 flex items-center gap-2">
                <Zap className="h-4 w-4 text-blue-600" />
                최적화 제안
              </p>
              <ul className="space-y-1">
                {result.suggestions.map((suggestion, idx) => (
                  <li key={idx} className="text-sm text-blue-700 dark:text-blue-300 flex items-start gap-2">
                    <TrendingUp className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    {suggestion}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!result && !isProfileing && (
        <div className="text-center py-8 text-muted-foreground">
          <Activity className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p className="text-sm">코드 성능을 분석하려면 위 버튼을 클릭하세요.</p>
          <p className="text-xs mt-1">실행 시간, 메모리 사용량, 병목 지점을 분석합니다.</p>
        </div>
      )}
    </div>
  );
}
