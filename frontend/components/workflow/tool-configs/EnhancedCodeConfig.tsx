'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Code,
  Play,
  Sparkles,
  Bug,
  FileCode,
  Copy,
  Check,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  Wand2,
  BookOpen,
  Terminal,
  Settings,
  Zap,
} from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';
import Editor, { OnMount } from '@monaco-editor/react';
import { toast } from 'sonner';
import { testCode, generateCode } from '@/lib/api/code-execution';
import dynamic from 'next/dynamic';

// Lazy load Phase 2 components
const AICopilot = dynamic(() => import('../code-editor/AICopilot'), { ssr: false });
const CodeDebugger = dynamic(() => import('../code-editor/CodeDebugger'), { ssr: false });
const ErrorAnalyzer = dynamic(() => import('../code-editor/ErrorAnalyzer'), { ssr: false });

// Lazy load Phase 3 components
const PerformanceProfiler = dynamic(() => import('../code-editor/PerformanceProfiler'), { ssr: false });
const TestRunner = dynamic(() => import('../code-editor/TestRunner'), { ssr: false });
const PackageManager = dynamic(() => import('../code-editor/PackageManager'), { ssr: false });

// Lazy load Phase 4 components
const SecretManager = dynamic(() => import('../code-editor/SecretManager'), { ssr: false });
const CodeLibrary = dynamic(() => import('../code-editor/CodeLibrary'), { ssr: false });

// 언어별 기본 템플릿
const CODE_TEMPLATES: Record<string, Record<string, string>> = {
  python: {
    basic: `# Available variables:
# - input: Input from previous node
# - context: Workflow context

def main(input_data, context):
    result = input_data
    return {"output": result, "status": "success"}

return main(input, context)`,
    dataTransform: `import json

def transform_data(input_data, context):
    """데이터 변환 템플릿"""
    # 입력 데이터 파싱
    data = input_data if isinstance(input_data, dict) else json.loads(input_data)
    
    # 변환 로직
    transformed = {
        "items": [item.upper() if isinstance(item, str) else item for item in data.get("items", [])],
        "count": len(data.get("items", [])),
        "processed_at": context.get("timestamp", "")
    }
    
    return {"output": transformed, "status": "success"}

return transform_data(input, context)`,
    apiCall: `import requests
import json

def call_api(input_data, context):
    """API 호출 템플릿"""
    url = input_data.get("url", "https://api.example.com/data")
    method = input_data.get("method", "GET")
    headers = input_data.get("headers", {"Content-Type": "application/json"})
    body = input_data.get("body", {})
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        else:
            response = requests.post(url, headers=headers, json=body, timeout=30)
        
        return {
            "output": response.json(),
            "status_code": response.status_code,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}

return call_api(input, context)`,
    fileProcess: `import json
import csv
from io import StringIO

def process_file(input_data, context):
    """파일 처리 템플릿"""
    file_content = input_data.get("content", "")
    file_type = input_data.get("type", "json")
    
    if file_type == "json":
        data = json.loads(file_content)
    elif file_type == "csv":
        reader = csv.DictReader(StringIO(file_content))
        data = list(reader)
    else:
        data = file_content
    
    return {"output": data, "row_count": len(data) if isinstance(data, list) else 1, "status": "success"}

return process_file(input, context)`,
    dataValidation: `def validate_data(input_data, context):
    """데이터 검증 템플릿"""
    errors = []
    warnings = []
    
    # 필수 필드 검증
    required_fields = ["name", "email"]
    for field in required_fields:
        if field not in input_data:
            errors.append(f"Missing required field: {field}")
    
    # 이메일 형식 검증
    email = input_data.get("email", "")
    if email and "@" not in email:
        errors.append("Invalid email format")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "status": "success" if len(errors) == 0 else "validation_failed"
    }

return validate_data(input, context)`,
  },
  javascript: {
    basic: `// Available variables:
// - input: Input from previous node
// - context: Workflow context

function main(inputData, context) {
  const result = inputData;
  return { output: result, status: "success" };
}

return main(input, context);`,
    dataTransform: `function transformData(inputData, context) {
  // 데이터 변환 템플릿
  const data = typeof inputData === 'string' ? JSON.parse(inputData) : inputData;
  
  const transformed = {
    items: (data.items || []).map(item => 
      typeof item === 'string' ? item.toUpperCase() : item
    ),
    count: (data.items || []).length,
    processedAt: context.timestamp || new Date().toISOString()
  };
  
  return { output: transformed, status: "success" };
}

return transformData(input, context);`,
    apiCall: `async function callApi(inputData, context) {
  // API 호출 템플릿
  const url = inputData.url || "https://api.example.com/data";
  const method = inputData.method || "GET";
  const headers = inputData.headers || { "Content-Type": "application/json" };
  const body = inputData.body || {};
  
  try {
    const options = { method, headers };
    if (method.toUpperCase() !== "GET") {
      options.body = JSON.stringify(body);
    }
    
    const response = await fetch(url, options);
    const data = await response.json();
    
    return { output: data, statusCode: response.status, status: "success" };
  } catch (error) {
    return { error: error.message, status: "error" };
  }
}

return callApi(input, context);`,
  },
  sql: {
    basic: `-- SQL Query Template
-- Available variables: {{input}}, {{context}}

SELECT * FROM table_name
WHERE column = '{{input.value}}'
LIMIT 100;`,
    selectJoin: `-- JOIN Query Template
SELECT 
    a.id,
    a.name,
    b.description
FROM table_a a
INNER JOIN table_b b ON a.id = b.a_id
WHERE a.status = 'active'
ORDER BY a.created_at DESC
LIMIT 100;`,
    aggregate: `-- Aggregation Query Template
SELECT 
    category,
    COUNT(*) as count,
    SUM(amount) as total,
    AVG(amount) as average
FROM transactions
WHERE created_at >= '{{input.start_date}}'
  AND created_at <= '{{input.end_date}}'
GROUP BY category
HAVING COUNT(*) > 10
ORDER BY total DESC;`,
  },
};

// 언어별 설정
const LANGUAGE_CONFIG = {
  python: {
    label: 'Python',
    icon: '🐍',
    libraries: ['json', 'datetime', 'math', 'random', 'requests', 'pandas', 'numpy', 'csv', 're'],
  },
  javascript: {
    label: 'JavaScript',
    icon: '📜',
    libraries: ['fetch', 'JSON', 'Date', 'Math', 'Array', 'Object', 'Promise'],
  },
  typescript: {
    label: 'TypeScript',
    icon: '💙',
    libraries: ['fetch', 'JSON', 'Date', 'Math', 'Array', 'Object', 'Promise'],
  },
  sql: {
    label: 'SQL',
    icon: '🗃️',
    libraries: ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'JOIN', 'GROUP BY'],
  },
};

interface TestResult {
  success: boolean;
  output?: any;
  error?: string;
  executionTime?: number;
  logs?: string[];
}

export default function EnhancedCodeConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    code: data.code || CODE_TEMPLATES.python.basic,
    language: data.language || 'python',
    timeout: data.timeout || 30,
    allow_imports: data.allow_imports !== false,
    env_vars: data.env_vars || {},
    ...data,
  });

  const [activeTab, setActiveTab] = useState('editor');
  const [testInput, setTestInput] = useState('{\n  "message": "Hello World",\n  "items": ["a", "b", "c"]\n}');
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [aiPrompt, setAiPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [copied, setCopied] = useState(false);
  const editorRef = useRef<any>(null);

  useEffect(() => {
    onChange(config);
  }, [config, onChange]);

  const updateConfig = useCallback((key: string, value: any) => {
    setConfig((prev: typeof config) => ({ ...prev, [key]: value }));
  }, []);

  const handleEditorMount: OnMount = (editor) => {
    editorRef.current = editor;
  };

  // 코드 실행 테스트
  const runTest = async () => {
    setIsRunning(true);
    setTestResult(null);

    try {
      let parsedInput;
      try {
        parsedInput = JSON.parse(testInput);
      } catch {
        parsedInput = testInput;
      }

      const result = await testCode({
        code: config.code,
        language: config.language as 'python' | 'javascript' | 'typescript' | 'sql',
        input: parsedInput,
        context: { timestamp: new Date().toISOString() },
        timeout: config.timeout,
        allow_imports: config.allow_imports,
      });

      setTestResult(result);

      if (result.success) {
        toast.success('코드 실행 성공!');
      } else {
        toast.error('코드 실행 실패');
      }
    } catch (error: any) {
      setTestResult({
        success: false,
        error: error.message || '실행 중 오류가 발생했습니다.',
      });
      toast.error('실행 오류');
    } finally {
      setIsRunning(false);
    }
  };

  // AI 코드 생성
  const handleGenerateCode = async () => {
    if (!aiPrompt.trim()) {
      toast.error('생성할 코드에 대한 설명을 입력해주세요.');
      return;
    }

    setIsGenerating(true);

    try {
      const result = await generateCode({
        prompt: aiPrompt,
        language: config.language as 'python' | 'javascript' | 'typescript' | 'sql',
        context: 'workflow_node',
      });

      if (result.code) {
        updateConfig('code', result.code);
        toast.success('코드가 생성되었습니다!');
        setAiPrompt('');
      } else {
        toast.error(result.error || '코드 생성에 실패했습니다.');
      }
    } catch (error: any) {
      toast.error('코드 생성 중 오류가 발생했습니다.');
    } finally {
      setIsGenerating(false);
    }
  };

  // 템플릿 적용
  const applyTemplate = (templateKey: string) => {
    const templates = CODE_TEMPLATES[config.language];
    if (templates && templates[templateKey]) {
      updateConfig('code', templates[templateKey]);
      setShowTemplates(false);
      toast.success('템플릿이 적용되었습니다.');
    }
  };

  // 코드 복사
  const copyCode = async () => {
    await navigator.clipboard.writeText(config.code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast.success('코드가 복사되었습니다.');
  };

  // 언어 변경
  const handleLanguageChange = (lang: string) => {
    updateConfig('language', lang);
    // 기본 템플릿으로 변경
    if (CODE_TEMPLATES[lang]) {
      updateConfig('code', CODE_TEMPLATES[lang].basic);
    }
  };

  const langConfig = LANGUAGE_CONFIG[config.language as keyof typeof LANGUAGE_CONFIG];

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-gradient-to-br from-purple-100 to-blue-100 dark:from-purple-950 dark:to-blue-950">
          <Code className="h-5 w-5 text-purple-600 dark:text-purple-400" />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold">Enhanced Code Block</h3>
          <p className="text-sm text-muted-foreground">VS Code 수준의 코드 편집기</p>
        </div>
        <Badge variant="secondary" className="bg-gradient-to-r from-purple-500 to-blue-500 text-white">
          Pro
        </Badge>
      </div>

      {/* Language & Template Selection */}
      <div className="flex gap-2">
        <Select value={config.language} onValueChange={handleLanguageChange}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {Object.entries(LANGUAGE_CONFIG).map(([key, cfg]) => (
              <SelectItem key={key} value={key}>
                <span className="flex items-center gap-2">
                  <span>{cfg.icon}</span>
                  <span>{cfg.label}</span>
                </span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowTemplates(!showTemplates)}
          className="gap-2"
        >
          <FileCode className="h-4 w-4" />
          템플릿
          {showTemplates ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        </Button>

        <Button variant="outline" size="sm" onClick={copyCode} className="gap-2 ml-auto">
          {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
        </Button>
      </div>

      {/* Template Dropdown */}
      {showTemplates && (
        <div className="p-3 bg-muted rounded-lg space-y-2 animate-in slide-in-from-top-2">
          <p className="text-xs font-medium text-muted-foreground">코드 템플릿 선택</p>
          <div className="grid grid-cols-2 gap-2">
            {Object.keys(CODE_TEMPLATES[config.language] || {}).map((key) => (
              <Button
                key={key}
                variant="outline"
                size="sm"
                onClick={() => applyTemplate(key)}
                className="justify-start text-xs"
              >
                <Zap className="h-3 w-3 mr-2" />
                {key.replace(/([A-Z])/g, ' $1').trim()}
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="editor" className="gap-1 text-xs">
            <Code className="h-3 w-3" />
            에디터
          </TabsTrigger>
          <TabsTrigger value="test" className="gap-1 text-xs">
            <Play className="h-3 w-3" />
            테스트
          </TabsTrigger>
          <TabsTrigger value="ai" className="gap-1 text-xs">
            <Sparkles className="h-3 w-3" />
            AI
          </TabsTrigger>
          <TabsTrigger value="debug" className="gap-1 text-xs">
            <Bug className="h-3 w-3" />
            디버그
          </TabsTrigger>
          <TabsTrigger value="analyze" className="gap-1 text-xs">
            <AlertCircle className="h-3 w-3" />
            분석
          </TabsTrigger>
          <TabsTrigger value="settings" className="gap-1 text-xs">
            <Settings className="h-3 w-3" />
            설정
          </TabsTrigger>
        </TabsList>

        {/* Editor Tab */}
        <TabsContent value="editor" className="space-y-3">
          <div className="border rounded-lg overflow-hidden">
            <Editor
              height="350px"
              language={config.language}
              value={config.code}
              onChange={(value) => updateConfig('code', value || '')}
              onMount={handleEditorMount}
              theme="vs-dark"
              options={{
                minimap: { enabled: false },
                fontSize: 13,
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                automaticLayout: true,
                tabSize: 2,
                wordWrap: 'on',
                folding: true,
                bracketPairColorization: { enabled: true },
                suggest: { showKeywords: true },
              }}
            />
          </div>

          {/* Available Libraries */}
          {langConfig && (
            <div className="p-3 bg-muted rounded-lg">
              <p className="text-xs font-medium mb-2">사용 가능한 라이브러리:</p>
              <div className="flex flex-wrap gap-1">
                {langConfig.libraries.map((lib) => (
                  <Badge key={lib} variant="outline" className="text-xs">
                    {lib}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </TabsContent>

        {/* Test Tab - Enhanced with TestRunner */}
        <TabsContent value="test" className="space-y-3">
          {/* Quick Test */}
          <div className="space-y-2 p-3 border rounded-lg">
            <Label className="flex items-center gap-2 text-sm font-medium">
              <Terminal className="h-4 w-4" />
              빠른 테스트
            </Label>
            <Textarea
              value={testInput}
              onChange={(e) => setTestInput(e.target.value)}
              rows={4}
              className="font-mono text-sm"
              placeholder='{"key": "value"}'
            />
            <Button onClick={runTest} disabled={isRunning} size="sm" className="w-full gap-2">
              {isRunning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              실행
            </Button>
            {testResult && (
              <div className={`p-2 rounded text-xs ${testResult.success ? 'bg-green-50 dark:bg-green-950/30' : 'bg-red-50 dark:bg-red-950/30'}`}>
                {testResult.success ? (
                  <pre className="overflow-auto max-h-20">{JSON.stringify(testResult.output, null, 2)}</pre>
                ) : (
                  <span className="text-red-600">{testResult.error}</span>
                )}
              </div>
            )}
          </div>
          
          {/* Test Runner - Phase 3 */}
          <TestRunner code={config.code} language={config.language} />
        </TabsContent>

        {/* AI Generation Tab - Phase 2 Enhanced */}
        <TabsContent value="ai" className="space-y-3">
          <AICopilot
            code={config.code}
            language={config.language}
            onCodeUpdate={(newCode) => updateConfig('code', newCode)}
          />
        </TabsContent>

        {/* Debug Tab - Phase 2 */}
        <TabsContent value="debug" className="space-y-3">
          <CodeDebugger
            code={config.code}
            language={config.language}
            input={(() => {
              try {
                return JSON.parse(testInput);
              } catch {
                return testInput;
              }
            })()}
          />
        </TabsContent>

        {/* Analyze Tab - Phase 2 & 3 */}
        <TabsContent value="analyze" className="space-y-3">
          {/* Error Analyzer */}
          <ErrorAnalyzer
            code={config.code}
            language={config.language}
            onApplyFix={(fixedCode) => updateConfig('code', fixedCode)}
            onGoToLine={(line) => {
              if (editorRef.current) {
                editorRef.current.revealLineInCenter(line);
                editorRef.current.setPosition({ lineNumber: line, column: 1 });
              }
            }}
          />
          
          {/* Performance Profiler - Phase 3 */}
          <PerformanceProfiler
            code={config.code}
            language={config.language}
            input={(() => {
              try { return JSON.parse(testInput); } catch { return testInput; }
            })()}
          />
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-4">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Import 허용</Label>
                <p className="text-xs text-muted-foreground">외부 라이브러리 import 허용</p>
              </div>
              <Switch
                checked={config.allow_imports}
                onCheckedChange={(v) => updateConfig('allow_imports', v)}
              />
            </div>

            <div className="space-y-2">
              <Label>실행 타임아웃 (초)</Label>
              <Input
                type="number"
                value={config.timeout}
                onChange={(e) => updateConfig('timeout', parseInt(e.target.value) || 30)}
                min={1}
                max={300}
              />
              <p className="text-xs text-muted-foreground">최대 실행 시간 (1-300초)</p>
            </div>

            <div className="space-y-2">
              <Label>환경 변수</Label>
              <Textarea
                value={JSON.stringify(config.env_vars, null, 2)}
                onChange={(e) => {
                  try {
                    updateConfig('env_vars', JSON.parse(e.target.value));
                  } catch {
                    // Invalid JSON, ignore
                  }
                }}
                rows={4}
                className="font-mono text-sm"
                placeholder='{"API_KEY": "your-key"}'
              />
              <p className="text-xs text-muted-foreground">코드에서 접근 가능한 환경 변수 (JSON)</p>
            </div>
          </div>

          {/* Package Manager - Phase 3 */}
          <PackageManager language={config.language} />

          {/* Secret Manager - Phase 4 */}
          <SecretManager />

          {/* Code Library - Phase 4 */}
          <CodeLibrary
            language={config.language}
            onInsertCode={(code) => {
              const currentCode = config.code;
              updateConfig('code', currentCode + '\n\n' + code);
              toast.success('코드가 삽입되었습니다.');
            }}
          />

          {/* Documentation Link */}
          <div className="p-3 bg-muted rounded-lg">
            <Button variant="ghost" size="sm" className="w-full justify-start gap-2">
              <BookOpen className="h-4 w-4" />
              코드 블록 문서 보기
            </Button>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
