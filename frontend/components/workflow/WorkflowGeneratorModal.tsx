'use client';

import React, { useState } from 'react';
import { X, Sparkles, Loader2, Lightbulb, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';

interface WorkflowGeneratorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onGenerate: (workflow: any) => void;
}

const EXAMPLE_PROMPTS = [
  {
    title: 'Customer Support Automation',
    description: 'When customers send emails, classify issues and generate AI responses for replies',
    category: 'customer-service',
  },
  {
    title: 'Slack Notifications',
    description: 'When webhook is triggered, send Slack message to #alerts channel',
    category: 'notifications',
  },
  {
    title: 'Document Analysis',
    description: 'When PDF is uploaded, extract text and AI summarize, then email to team',
    category: 'document-processing',
  },
  {
    title: 'Approval Workflow',
    description: 'When purchase request comes in, if amount is over $1000 require manager approval, then process payment',
    category: 'approval',
  },
];

export function WorkflowGeneratorModal({
  isOpen,
  onClose,
  onGenerate,
}: WorkflowGeneratorModalProps) {
  const [description, setDescription] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedWorkflow, setGeneratedWorkflow] = useState<any>(null);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const { toast } = useToast();

  if (!isOpen) return null;

  const handleGenerate = async () => {
    if (!description.trim()) {
      toast({
        title: '❌ Description Required',
        description: 'Please enter a workflow description',
        duration: 2000,
      });
      return;
    }

    setIsGenerating(true);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout

      const response = await fetch('/api/workflow-generator/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          description: description,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to generate workflow');
      }

      const data = await response.json();
      
      // Validate response
      if (!data.workflow || !data.workflow.nodes) {
        throw new Error('Invalid workflow response');
      }

      setGeneratedWorkflow(data.workflow);
      setSuggestions(data.suggestions || []);

      toast({
        title: '✨ Workflow Generated',
        description: `"${data.workflow.name}" workflow has been created`,
        duration: 3000,
      });
    } catch (error: any) {
      console.error('Failed to generate workflow:', error);
      
      let errorMessage = 'An error occurred while generating workflow';
      if (error.name === 'AbortError') {
        errorMessage = 'Generation timed out. Please try a simpler description';
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast({
        title: '❌ Generation Failed',
        description: errorMessage,
        duration: 4000,
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApply = () => {
    if (generatedWorkflow) {
      // Validate workflow before applying
      if (!generatedWorkflow.nodes || generatedWorkflow.nodes.length === 0) {
        toast({
          title: '❌ Apply Failed',
          description: 'Workflow has no nodes',
          duration: 2000,
        });
        return;
      }

      onGenerate(generatedWorkflow);
      onClose();
      
      // Reset state
      setDescription('');
      setGeneratedWorkflow(null);
      setSuggestions([]);
      
      toast({
        title: '✅ Workflow Applied',
        description: 'Generated workflow has been applied to canvas',
        duration: 2000,
      });
    }
  };

  const handleUseExample = (example: typeof EXAMPLE_PROMPTS[0]) => {
    setDescription(example.description);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                AI Workflow Generator
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Describe in natural language and AI will automatically generate workflows
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Input Section */}
          {!generatedWorkflow && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Workflow Description
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Example: When customers submit inquiries, analyze sentiment, if positive send auto-reply, if negative notify staff"
                  className="w-full h-32 p-4 border border-gray-300 dark:border-gray-600 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                  disabled={isGenerating}
                />
              </div>

              {/* Examples */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Lightbulb className="w-4 h-4 text-yellow-500" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Example Prompts
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {EXAMPLE_PROMPTS.map((example, index) => (
                    <button
                      key={index}
                      onClick={() => handleUseExample(example)}
                      className="p-3 text-left border border-gray-200 dark:border-gray-700 rounded-lg hover:border-purple-500 hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-all group"
                      disabled={isGenerating}
                    >
                      <div className="font-medium text-sm text-gray-900 dark:text-white mb-1 group-hover:text-purple-600 dark:group-hover:text-purple-400">
                        {example.title}
                      </div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                        {example.description}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Generated Workflow Preview */}
          {generatedWorkflow && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                    {generatedWorkflow.name}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {generatedWorkflow.description}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setGeneratedWorkflow(null);
                    setSuggestions([]);
                  }}
                >
                  Regenerate
                </Button>
              </div>

              {/* Workflow Stats */}
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                    {generatedWorkflow.nodes?.length || 0}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Nodes</div>
                </div>
                <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                    {generatedWorkflow.edges?.length || 0}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Connections</div>
                </div>
                <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                    {new Set(generatedWorkflow.nodes?.map((n: any) => n.node_type || n.type) || []).size}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">Node Types</div>
                </div>
              </div>

              {/* Node List */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Included Nodes
                </h4>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {generatedWorkflow.nodes?.map((node: any, index: number) => {
                    // Handle both backend and frontend formats
                    const nodeType = node.node_type || node.type;
                    const nodeName = node.configuration?.name || node.data?.label || node.data?.name || nodeType;
                    
                    return (
                      <div
                        key={node.id || index}
                        className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                      >
                        <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center text-white text-sm font-bold">
                          {index + 1}
                        </div>
                        <div className="flex-1">
                          <div className="font-medium text-sm text-gray-900 dark:text-white">
                            {nodeName}
                          </div>
                          <div className="text-xs text-gray-600 dark:text-gray-400">
                            {nodeType}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Suggestions */}
              {suggestions.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Zap className="w-4 h-4 text-yellow-500" />
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Improvement Suggestions
                    </h4>
                  </div>
                  <div className="space-y-2">
                    {suggestions.map((suggestion, index) => (
                      <div
                        key={index}
                        className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg"
                      >
                        <div className="flex items-start gap-2">
                          <span className="text-yellow-600 dark:text-yellow-400 text-xs font-medium uppercase">
                            {suggestion.severity}
                          </span>
                          <p className="text-sm text-gray-700 dark:text-gray-300 flex-1">
                            {suggestion.message}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
          <Button variant="ghost" onClick={onClose} disabled={isGenerating}>
            Cancel
          </Button>
          <div className="flex gap-2">
            {!generatedWorkflow ? (
              <Button
                onClick={handleGenerate}
                disabled={isGenerating || !description.trim()}
                className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
              >
                {isGenerating ? (
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
            ) : (
              <Button
                onClick={handleApply}
                className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600"
              >
                Apply Workflow
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
