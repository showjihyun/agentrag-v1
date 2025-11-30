'use client';

import { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  TestTube,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  Sparkles,
  RefreshCw,
  Plus,
  Trash2,
  Loader2,
  AlertTriangle,
  SkipForward,
} from 'lucide-react';
import { toast } from 'sonner';

interface TestCase {
  id: string;
  name: string;
  input: any;
  expectedOutput?: any;
  status: 'pending' | 'running' | 'passed' | 'failed' | 'skipped';
  actualOutput?: any;
  error?: string;
  duration?: number;
}

interface TestRunnerProps {
  code: string;
  language: string;
  onTestGenerated?: (tests: TestCase[]) => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function TestRunner({ code, language, onTestGenerated }: TestRunnerProps) {
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [coverage, setCoverage] = useState<number | null>(null);

  // AI로 테스트 케이스 생성
  const generateTests = useCallback(async () => {
    setIsGenerating(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/workflow/generate-tests`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({ code, language }),
      });

      const data = await response.json();
      if (data.tests) {
        const newTests: TestCase[] = data.tests.map((t: any, idx: number) => ({
          id: `test-${Date.now()}-${idx}`,
          name: t.name || `Test ${idx + 1}`,
          input: t.input,
          expectedOutput: t.expected_output,
          status: 'pending' as const,
        }));
        setTestCases(newTests);
        onTestGenerated?.(newTests);
        toast.success(`${newTests.length}개의 테스트 케이스가 생성되었습니다.`);
      }
    } catch (error) {
      toast.error('테스트 생성 실패');
    } finally {
      setIsGenerating(false);
    }
  }, [code, language, onTestGenerated]);

  // 모든 테스트 실행
  const runAllTests = useCallback(async () => {
    if (testCases.length === 0) {
      toast.error('실행할 테스트가 없습니다.');
      return;
    }

    setIsRunning(true);
    setCoverage(null);

    const updatedTests = [...testCases];
    let passed = 0;
    let failed = 0;

    for (let i = 0; i < updatedTests.length; i++) {
      updatedTests[i].status = 'running';
      setTestCases([...updatedTests]);

      try {
        const token = localStorage.getItem('token');
        const startTime = Date.now();
        
        const response = await fetch(`${API_BASE}/api/workflow/test-code`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { Authorization: `Bearer ${token}` }),
          },
          body: JSON.stringify({
            code,
            language,
            input: updatedTests[i].input,
            context: {},
          }),
        });

        const result = await response.json();
        const duration = Date.now() - startTime;

        updatedTests[i].duration = duration;
        updatedTests[i].actualOutput = result.output;

        // 결과 비교
        if (result.success) {
          if (updatedTests[i].expectedOutput !== undefined) {
            const matches = JSON.stringify(result.output) === JSON.stringify(updatedTests[i].expectedOutput);
            updatedTests[i].status = matches ? 'passed' : 'failed';
            if (!matches) {
              updatedTests[i].error = 'Output mismatch';
            }
          } else {
            updatedTests[i].status = 'passed';
          }
        } else {
          updatedTests[i].status = 'failed';
          updatedTests[i].error = result.error;
        }

        if (updatedTests[i].status === 'passed') passed++;
        else failed++;

      } catch (error: any) {
        updatedTests[i].status = 'failed';
        updatedTests[i].error = error.message;
        failed++;
      }

      setTestCases([...updatedTests]);
    }

    // 커버리지 계산 (간단한 시뮬레이션)
    const totalTests = testCases.length;
    const coveragePercent = totalTests > 0 ? Math.round((passed / totalTests) * 100) : 0;
    setCoverage(coveragePercent);

    setIsRunning(false);
    toast.success(`테스트 완료: ${passed} 통과, ${failed} 실패`);
  }, [code, language, testCases]);

  // 단일 테스트 실행
  const runSingleTest = useCallback(async (testId: string) => {
    const testIndex = testCases.findIndex(t => t.id === testId);
    if (testIndex === -1) return;

    const updatedTests = [...testCases];
    updatedTests[testIndex].status = 'running';
    setTestCases(updatedTests);

    try {
      const token = localStorage.getItem('token');
      const startTime = Date.now();

      const response = await fetch(`${API_BASE}/api/workflow/test-code`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({
          code,
          language,
          input: updatedTests[testIndex].input,
          context: {},
        }),
      });

      const result = await response.json();
      const duration = Date.now() - startTime;

      updatedTests[testIndex].duration = duration;
      updatedTests[testIndex].actualOutput = result.output;

      if (result.success) {
        updatedTests[testIndex].status = 'passed';
      } else {
        updatedTests[testIndex].status = 'failed';
        updatedTests[testIndex].error = result.error;
      }
    } catch (error: any) {
      updatedTests[testIndex].status = 'failed';
      updatedTests[testIndex].error = error.message;
    }

    setTestCases(updatedTests);
  }, [code, language, testCases]);

  // 테스트 삭제
  const removeTest = (testId: string) => {
    setTestCases(prev => prev.filter(t => t.id !== testId));
  };

  // 테스트 추가
  const addEmptyTest = () => {
    const newTest: TestCase = {
      id: `test-${Date.now()}`,
      name: `Test ${testCases.length + 1}`,
      input: {},
      status: 'pending',
    };
    setTestCases(prev => [...prev, newTest]);
  };

  const passedCount = testCases.filter(t => t.status === 'passed').length;
  const failedCount = testCases.filter(t => t.status === 'failed').length;
  const pendingCount = testCases.filter(t => t.status === 'pending').length;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'running': return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      case 'skipped': return <SkipForward className="h-4 w-4 text-gray-400" />;
      default: return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2 p-3 bg-gradient-to-r from-violet-50 to-purple-50 dark:from-violet-950/30 dark:to-purple-950/30 rounded-lg border border-violet-200 dark:border-violet-800">
        <TestTube className="h-5 w-5 text-violet-600" />
        <span className="font-medium flex-1">Test Runner</span>
        <Badge variant="secondary" className="text-xs">Phase 3</Badge>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <Button
          onClick={generateTests}
          disabled={isGenerating || !code.trim()}
          variant="outline"
          size="sm"
          className="gap-2"
        >
          {isGenerating ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Sparkles className="h-4 w-4" />
          )}
          AI 테스트 생성
        </Button>
        <Button
          onClick={runAllTests}
          disabled={isRunning || testCases.length === 0}
          size="sm"
          className="gap-2"
        >
          {isRunning ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          모두 실행
        </Button>
        <Button onClick={addEmptyTest} variant="ghost" size="sm">
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {/* Summary */}
      {testCases.length > 0 && (
        <div className="flex items-center gap-4 p-3 bg-muted rounded-lg">
          <div className="flex items-center gap-1">
            <CheckCircle className="h-4 w-4 text-green-500" />
            <span className="text-sm">{passedCount} 통과</span>
          </div>
          <div className="flex items-center gap-1">
            <XCircle className="h-4 w-4 text-red-500" />
            <span className="text-sm">{failedCount} 실패</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="h-4 w-4 text-gray-400" />
            <span className="text-sm">{pendingCount} 대기</span>
          </div>
          {coverage !== null && (
            <div className="ml-auto flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Coverage:</span>
              <Progress value={coverage} className="w-20 h-2" />
              <span className="text-sm font-medium">{coverage}%</span>
            </div>
          )}
        </div>
      )}

      {/* Test Cases */}
      <ScrollArea className="max-h-64">
        <div className="space-y-2">
          {testCases.map((test) => (
            <div
              key={test.id}
              className={`p-3 rounded-lg border ${
                test.status === 'passed'
                  ? 'bg-green-50 border-green-200 dark:bg-green-950/30 dark:border-green-800'
                  : test.status === 'failed'
                  ? 'bg-red-50 border-red-200 dark:bg-red-950/30 dark:border-red-800'
                  : 'bg-muted'
              }`}
            >
              <div className="flex items-center gap-2">
                {getStatusIcon(test.status)}
                <span className="text-sm font-medium flex-1">{test.name}</span>
                {test.duration && (
                  <span className="text-xs text-muted-foreground">{test.duration}ms</span>
                )}
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-6 w-6 p-0"
                  onClick={() => runSingleTest(test.id)}
                  disabled={isRunning}
                >
                  <Play className="h-3 w-3" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-6 w-6 p-0"
                  onClick={() => removeTest(test.id)}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>

              {/* Input/Output */}
              <div className="mt-2 text-xs space-y-1">
                <div>
                  <span className="text-muted-foreground">Input: </span>
                  <code className="bg-black/10 dark:bg-white/10 px-1 rounded">
                    {JSON.stringify(test.input).slice(0, 50)}
                  </code>
                </div>
                {test.actualOutput && (
                  <div>
                    <span className="text-muted-foreground">Output: </span>
                    <code className="bg-black/10 dark:bg-white/10 px-1 rounded">
                      {JSON.stringify(test.actualOutput).slice(0, 50)}
                    </code>
                  </div>
                )}
                {test.error && (
                  <div className="text-red-600 dark:text-red-400">
                    <AlertTriangle className="h-3 w-3 inline mr-1" />
                    {test.error}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* Empty State */}
      {testCases.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          <TestTube className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p className="text-sm">테스트 케이스가 없습니다.</p>
          <p className="text-xs mt-1">AI로 자동 생성하거나 직접 추가하세요.</p>
        </div>
      )}
    </div>
  );
}
