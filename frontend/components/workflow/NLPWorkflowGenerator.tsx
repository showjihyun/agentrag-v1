'use client';

import React, { useState, useCallback } from 'react';
import {
  Sparkles,
  Wand2,
  ArrowRight,
  Loader2,
  CheckCircle,
  AlertCircle,
  Lightbulb,
  Copy,
  Play,
  RefreshCw,
  Settings,
  Zap,
  Clock,
  BarChart3,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { cn } from '@/lib/utils';

interface GeneratedWorkflow {
  success: boolean;
  workflow_name: string;
  workflow_description: string;
  graph_definition: {
    nodes: any[];
    edges: any[];
  };
  explanation: string;
  confidence: number;
  suggestions: string[];
  complexity: string;
  estimated_execution_time: string;
  error?: string;
}

interface NLPWorkflowGeneratorProps {
  onGenerate?: (workflow: GeneratedWorkflow) => void;
  onApply?: (graphDefinition: any, name: string) => void;
}

const EXAMPLE_PROMPTS = [
  {
    text: "Fetch news from HTTP API every morning at 9 AM, summarize with OpenAI, and send to Slack",
    category: "Automation",
    complexity: "moderate",
  },
  {
    text: "Receive data via webhook, branch based on conditions to send Gmail notification or save to PostgreSQL",
    category: "Data Processing",
    complexity: "complex",
  },
  {
    text: "Receive user question, find related documents with vector search, and generate answer with OpenAI",
    category: "RAG",
    complexity: "moderate",
  },
  {
    text: "Start manually, fetch data via HTTP request, and process with Python code",
    category: "Data Transform",
    complexity: "simple",
  },
  {
    text: "Run hourly on schedule, call multiple APIs in parallel, merge results, and analyze with AI",
    category: "Analysis",
    complexity: "complex",
  },
];

const COMPLEXITY_COLORS = {
  simple: "bg-green-100 text-green-700",
  moderate: "bg-yellow-100 text-yellow-700",
  complex: "bg-red-100 text-red-700",
};

const COMPLEXITY_LABELS = {
  simple: "Simple",
  moderate: "Moderate",
  complex: "Complex",
};

export const NLPWorkflowGenerator: React.FC<NLPWorkflowGeneratorProps> = ({
  onGenerate,
  onApply,
}) => {
  const [prompt, setPrompt] = useState('');
  const [workflowName, setWorkflowName] = useState('');
  const [loading, setLoading] = useState(false);
  const [refining, setRefining] = useState(false);
  const [result, setResult] = useState<GeneratedWorkflow | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [useLLM, setUseLLM] = useState(true);
  const [refinementInput, setRefinementInput] = useState('');
  const [history, setHistory] = useState<GeneratedWorkflow[]>([]);
  const [activeTab, setActiveTab] = useState('generate');

  const handleGenerate = useCallback(async () => {
    if (!prompt.trim() || prompt.length < 10) {
      setError('Please enter a description of at least 10 characters');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('/api/agent-builder/workflow-nlp/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          description: prompt,
          language: 'ko',
          use_llm: useLLM,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to generate workflow');
      }

      const data = await response.json();
      console.log('AI workflow generated: ', data);
      setResult(data);
      setWorkflowName(data.workflow_name);
      
      // Add to history
      setHistory(prev => [data, ...prev.slice(0, 4)]);
      
      // 자동으로 결과 탭으로 전환
      setActiveTab('result');
      
      onGenerate?.(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [prompt, useLLM, onGenerate]);

  const handleRefine = useCallback(async () => {
    if (!result || !refinementInput.trim()) return;

    setRefining(true);
    setError(null);

    try {
      const response = await fetch('/api/agent-builder/workflow-nlp/refine', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          workflow: result.graph_definition,
          refinement: refinementInput,
          language: 'ko',
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to refine workflow');
      }

      const data = await response.json();
      setResult(data);
      setRefinementInput('');
      
      // Add to history
      setHistory(prev => [data, ...prev.slice(0, 4)]);
      
      onGenerate?.(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setRefining(false);
    }
  }, [result, refinementInput, onGenerate]);

  const handleApply = useCallback(() => {
    console.log('🎯 [NLPWorkflowGenerator] handleApply called');
    console.log('🎯 [NLPWorkflowGenerator] result:', result);
    console.log('🎯 [NLPWorkflowGenerator] graph_definition:', result?.graph_definition);
    
    if (result?.graph_definition) {
      console.log('🎯 [NLPWorkflowGenerator] Calling onApply with:', {
        nodes: result.graph_definition.nodes,
        edges: result.graph_definition.edges,
        workflowName: workflowName || result.workflow_name,
      });
      onApply?.(result.graph_definition, workflowName || result.workflow_name);
    } else {
      console.error('🎯 [NLPWorkflowGenerator] No graph_definition available');
    }
  }, [result, workflowName, onApply]);

  const handleExampleClick = (example: typeof EXAMPLE_PROMPTS[0]) => {
    setPrompt(example.text);
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const copyToClipboard = () => {
    if (result?.graph_definition) {
      navigator.clipboard.writeText(JSON.stringify(result.graph_definition, null, 2));
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500">
          <Sparkles className="h-6 w-6 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-bold">AI Workflow Generator</h2>
          <p className="text-sm text-muted-foreground">
            Describe in natural language and LLM will automatically generate a workflow
          </p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="generate">Generate</TabsTrigger>
          <TabsTrigger value="result" disabled={!result}>Result</TabsTrigger>
          <TabsTrigger value="history" disabled={history.length === 0}>
            History ({history.length})
          </TabsTrigger>
        </TabsList>

        {/* Generate Tab */}
        <TabsContent value="generate" className="space-y-4">
          <Card>
            <CardContent className="pt-6 space-y-4">
              <div className="space-y-2">
                <Label>Workflow Description</Label>
                <Textarea
                  placeholder="e.g., Search for news every morning, summarize with AI, and send to Slack"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  rows={4}
                  className="text-base resize-none"
                />
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>{prompt.length} chars / min 10 chars</span>
                  <div className="flex items-center gap-2">
                    <span>Use LLM</span>
                    <Switch checked={useLLM} onCheckedChange={setUseLLM} />
                  </div>
                </div>
              </div>

              <Button
                onClick={handleGenerate}
                disabled={loading || prompt.length < 10}
                className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Wand2 className="h-4 w-4 mr-2" />
                )}
                {loading ? 'Generating...' : 'Generate Workflow'}
              </Button>
            </CardContent>
          </Card>

          {/* Example Prompts */}
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-muted-foreground">Example Prompts</h3>
            <div className="grid gap-2">
              {EXAMPLE_PROMPTS.map((example, index) => (
                <button
                  key={index}
                  onClick={() => handleExampleClick(example)}
                  className="p-3 text-left bg-muted/50 hover:bg-muted rounded-lg transition-colors"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="outline" className="text-xs">
                      {example.category}
                    </Badge>
                    <Badge className={cn("text-xs", COMPLEXITY_COLORS[example.complexity as keyof typeof COMPLEXITY_COLORS])}>
                      {COMPLEXITY_LABELS[example.complexity as keyof typeof COMPLEXITY_LABELS]}
                    </Badge>
                  </div>
                  <p className="text-sm">{example.text}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Error */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </TabsContent>

        {/* Result Tab */}
        <TabsContent value="result" className="space-y-4">
          {result && (
            <>
              <Card className="border border-purple-200 bg-white shadow-sm">
                <CardHeader className="pb-3 bg-gradient-to-br from-purple-50 to-pink-50">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1 flex-1">
                      <CardTitle className="flex items-center gap-2">
                        {result.success ? (
                          <div className="p-1 rounded-full bg-green-100">
                            <CheckCircle className="h-5 w-5 text-green-600" />
                          </div>
                        ) : (
                          <div className="p-1 rounded-full bg-red-100">
                            <AlertCircle className="h-5 w-5 text-red-600" />
                          </div>
                        )}
                        <Input
                          value={workflowName}
                          onChange={(e) => setWorkflowName(e.target.value)}
                          className="text-lg font-semibold border-none bg-transparent p-0 h-auto focus-visible:ring-0 text-slate-900"
                          placeholder="Workflow Name"
                        />
                      </CardTitle>
                      <p className="text-sm text-slate-600">{result.workflow_description}</p>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <Badge className={cn(
                        "text-xs border-0",
                        result.confidence >= 0.8 ? "bg-green-100 text-green-700" :
                        result.confidence >= 0.6 ? "bg-yellow-100 text-yellow-700" :
                        "bg-red-100 text-red-700"
                      )}>
                        Confidence {Math.round(result.confidence * 100)}%
                      </Badge>
                      <Badge className={cn(
                        "text-xs border-0",
                        result.complexity === 'simple' ? "bg-green-100 text-green-700" :
                        result.complexity === 'moderate' ? "bg-yellow-100 text-yellow-700" :
                        "bg-red-100 text-red-700"
                      )}>
                        {COMPLEXITY_LABELS[result.complexity as keyof typeof COMPLEXITY_LABELS]}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-3">
                    <div className="flex items-center gap-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <div className="p-1.5 rounded-md bg-blue-100">
                        <Zap className="h-4 w-4 text-blue-600" />
                      </div>
                      <div>
                        <div className="text-xs text-slate-600">Nodes</div>
                        <div className="font-semibold text-slate-900">{result.graph_definition.nodes.length}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                      <div className="p-1.5 rounded-md bg-green-100">
                        <ArrowRight className="h-4 w-4 text-green-600" />
                      </div>
                      <div>
                        <div className="text-xs text-slate-600">Edges</div>
                        <div className="font-semibold text-slate-900">{result.graph_definition.edges.length}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 p-3 bg-orange-50 border border-orange-200 rounded-lg">
                      <div className="p-1.5 rounded-md bg-orange-100">
                        <Clock className="h-4 w-4 text-orange-600" />
                      </div>
                      <div>
                        <div className="text-xs text-slate-600">Est. Time</div>
                        <div className="font-semibold text-slate-900">{result.estimated_execution_time}</div>
                      </div>
                    </div>
                  </div>

                  {/* Explanation */}
                  {result.explanation && (
                    <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                      <p className="text-sm text-slate-700">{result.explanation}</p>
                    </div>
                  )}

                  {/* Generated Nodes */}
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-slate-700">Generated Nodes</h4>
                    <div className="flex flex-wrap gap-2">
                      {result.graph_definition.nodes.map((node, index) => (
                        <div
                          key={node.id}
                          className="flex items-center gap-1.5 px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-sm shadow-sm"
                        >
                          <span className="text-purple-600 text-xs font-medium">{index + 1}.</span>
                          <span className="text-slate-900">{node.data?.label || node.type}</span>
                          <Badge className="text-xs ml-1 bg-purple-100 text-purple-700 border-0">{node.type}</Badge>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Suggestions */}
                  {result.suggestions.length > 0 && (
                    <div className="space-y-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <h4 className="text-sm font-medium flex items-center gap-2 text-yellow-700">
                        <Lightbulb className="h-4 w-4" />
                        Suggestions
                      </h4>
                      <ul className="space-y-1">
                        {result.suggestions.map((suggestion, index) => (
                          <li key={index} className="text-sm text-slate-700 flex items-start gap-2">
                            <span className="text-yellow-600">•</span>
                            {suggestion}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Refinement */}
                  <div className="space-y-2 pt-3 border-t border-slate-200">
                    <h4 className="text-sm font-medium flex items-center gap-2 text-slate-700">
                      <Settings className="h-4 w-4 text-slate-500" />
                      Refine Workflow
                    </h4>
                    <div className="flex gap-2">
                      <Input
                        placeholder="e.g., Add error handling, Change to parallel execution"
                        value={refinementInput}
                        onChange={(e) => setRefinementInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleRefine()}
                        className="bg-white border-slate-300 text-slate-900 placeholder:text-slate-400"
                      />
                      <Button
                        onClick={handleRefine}
                        disabled={refining || !refinementInput.trim()}
                        className="bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300"
                      >
                        {refining ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 pt-3">
                    <Button 
                      onClick={handleApply} 
                      className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white border-0 shadow-lg shadow-purple-500/25"
                    >
                      <Play className="h-4 w-4 mr-2" />
                      Apply to Editor
                    </Button>
                    <Button 
                      onClick={copyToClipboard}
                      className="bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300"
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-4">
          {history.map((item, index) => (
            <Card key={index} className="cursor-pointer hover:border-purple-300" onClick={() => setResult(item)}>
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">{item.workflow_name}</h4>
                    <p className="text-sm text-muted-foreground truncate max-w-md">
                      {item.workflow_description}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={cn("text-xs", COMPLEXITY_COLORS[item.complexity as keyof typeof COMPLEXITY_COLORS])}>
                      {COMPLEXITY_LABELS[item.complexity as keyof typeof COMPLEXITY_LABELS]}
                    </Badge>
                    <Badge variant="outline">{item.graph_definition.nodes.length} nodes</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>

      {/* Tips */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-4">
          <h4 className="text-sm font-medium text-blue-700 mb-2">💡 Tips for Better Results</h4>
          <ul className="text-sm text-blue-600 space-y-1">
            <li>• Specify the <strong>trigger</strong>: "Every day at 9 AM", "Via webhook", "Manually"</li>
            <li>• Mention <strong>specific services</strong>: "Slack", "Email", "PostgreSQL"</li>
            <li>• Describe <strong>conditions</strong> if any: "If urgent", "When error occurs"</li>
            <li>• Explain the <strong>data flow</strong> in order</li>
            <li>• Use the <strong>refine feature</strong> after generation for fine-tuning</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
};

export default NLPWorkflowGenerator;
