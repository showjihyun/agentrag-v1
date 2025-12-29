'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Loader2, Sparkles, Lightbulb, ArrowRight } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface WorkflowIntent {
  workflow_type: string;
  name: string;
  description: string;
  nodes: any[];
  edges: any[];
  confidence: number;
}

interface Example {
  prompt: string;
  workflow_type: string;
  description: string;
}

export default function NLPGeneratorPage() {
  const router = useRouter();
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    workflow: WorkflowIntent;
    suggestions: string[];
  } | null>(null);
  const [examples, setExamples] = useState<Example[]>([]);
  const [showExamples, setShowExamples] = useState(false);

  const loadExamples = async () => {
    try {
      const response = await fetch('/api/agent-builder/nlp/examples');
      const data = await response.json();
      setExamples(data.examples);
      setShowExamples(true);
    } catch (error) {
      console.error('Failed to load examples:', error);
    }
  };

  const generateWorkflow = async () => {
    if (!description.trim() || description.length < 10) {
      alert('Please provide a description (at least 10 characters)');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/agent-builder/nlp/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description }),
      });

      if (!response.ok) throw new Error('Failed to generate workflow');

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Generation failed:', error);
      alert('Failed to generate workflow. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const createWorkflow = () => {
    if (!result) return;

    const { workflow } = result;
    const route =
      workflow.workflow_type === 'chatflow'
        ? '/agent-builder/chatflows/new'
        : '/agent-builder/agentflows/new';

    // Store generated workflow in sessionStorage
    sessionStorage.setItem('generatedWorkflow', JSON.stringify(workflow));
    router.push(route);
  };

  const useExample = (example: Example) => {
    setDescription(example.prompt);
    setShowExamples(false);
  };

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
          <Sparkles className="w-8 h-8 text-purple-500" />
          NLP Workflow Generator
        </h1>
        <p className="text-gray-600">
          Describe your workflow in natural language and let AI generate it for you
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Section */}
        <div className="space-y-4">
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Describe Your Workflow</h2>

            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Example: Create a chatbot that answers questions about products and can check inventory status..."
              rows={8}
              className="mb-4"
            />

            <div className="flex gap-2">
              <Button
                onClick={generateWorkflow}
                disabled={loading || description.length < 10}
                className="flex-1"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Generate Workflow
                  </>
                )}
              </Button>

              <Button
                onClick={loadExamples}
                variant="outline"
                disabled={loading}
              >
                <Lightbulb className="w-4 h-4 mr-2" />
                Examples
              </Button>
            </div>
          </Card>

          {/* Examples */}
          {showExamples && examples.length > 0 && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-3">Example Prompts</h3>
              <div className="space-y-2">
                {examples.map((example, idx) => (
                  <div
                    key={idx}
                    onClick={() => useExample(example)}
                    className="p-3 border rounded-lg hover:bg-gray-50 cursor-pointer transition"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="text-sm font-medium">{example.prompt}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {example.description}
                        </p>
                      </div>
                      <Badge variant={example.workflow_type === 'chatflow' ? 'default' : 'secondary'}>
                        {example.workflow_type}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        {/* Result Section */}
        <div className="space-y-4">
          {result && (
            <>
              <Card className="p-6">
                <h2 className="text-xl font-semibold mb-4">Generated Workflow</h2>

                <div className="space-y-3">
                  <div>
                    <label className="text-sm font-medium text-gray-700">Name</label>
                    <p className="text-lg">{result.workflow.name}</p>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-700">Type</label>
                    <div className="mt-1">
                      <Badge variant={result.workflow.workflow_type === 'chatflow' ? 'default' : 'secondary'}>
                        {result.workflow.workflow_type}
                      </Badge>
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-700">Description</label>
                    <p className="text-sm text-gray-600">{result.workflow.description}</p>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-700">Structure</label>
                    <div className="flex gap-4 mt-2">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">
                          {result.workflow.nodes.length}
                        </div>
                        <div className="text-xs text-gray-500">Nodes</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">
                          {result.workflow.edges.length}
                        </div>
                        <div className="text-xs text-gray-500">Connections</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-purple-600">
                          {Math.round(result.workflow.confidence * 100)}%
                        </div>
                        <div className="text-xs text-gray-500">Confidence</div>
                      </div>
                    </div>
                  </div>

                  <Button onClick={createWorkflow} className="w-full mt-4">
                    Create Workflow
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </Card>

              {result.suggestions.length > 0 && (
                <Card className="p-6">
                  <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                    <Lightbulb className="w-5 h-5 text-yellow-500" />
                    Suggestions
                  </h3>
                  <ul className="space-y-2">
                    {result.suggestions.map((suggestion, idx) => (
                      <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                        <span className="text-yellow-500 mt-0.5">•</span>
                        <span>{suggestion}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}
            </>
          )}

          {!result && !loading && (
            <Card className="p-6 text-center text-gray-400">
              <Sparkles className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>Your generated workflow will appear here</p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
