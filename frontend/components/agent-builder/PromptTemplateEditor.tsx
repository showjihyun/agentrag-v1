'use client';

import React from 'react';
import Editor from '@monaco-editor/react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  X,
  Sparkles,
  Eye,
  Copy,
  Check,
  FileText,
  Lightbulb,
  Zap,
} from 'lucide-react';
import { useToast } from '@/components/Toast';

interface PromptTemplateEditorProps {
  value: string;
  onChange: (value: string) => void;
  onClose?: () => void;
}

const PROMPT_TEMPLATES = [
  {
    id: 'general',
    name: 'General Assistant',
    description: 'A helpful AI assistant for general queries',
    template: `You are a helpful AI assistant. Your goal is to provide accurate, clear, and concise answers.

User Query: \${query}

Context: \${context}

Please provide a helpful response based on the query and context above.`,
  },
  {
    id: 'rag',
    name: 'RAG Assistant',
    description: 'Retrieval-augmented generation with citations',
    template: `You are an AI assistant that answers questions based on provided context.

Context Documents:
\${context}

User Question: \${query}

Instructions:
1. Answer the question using ONLY the information from the context
2. If the answer is not in the context, say "I don't have enough information"
3. Cite your sources by referencing the document names
4. Be concise and accurate

Answer:`,
  },
  {
    id: 'code',
    name: 'Code Assistant',
    description: 'Programming and code-related queries',
    template: `You are an expert programming assistant. Help users with code-related questions.

Programming Language: \${language}
Question: \${query}

Previous Code:
\${context}

Provide:
1. Clear explanation
2. Code examples with comments
3. Best practices
4. Potential issues to watch out for`,
  },
  {
    id: 'analysis',
    name: 'Data Analyst',
    description: 'Data analysis and insights',
    template: `You are a data analyst. Analyze the provided data and answer the user's question.

Data:
\${context}

Question: \${query}

Provide:
1. Key insights
2. Statistical analysis if relevant
3. Visualizations suggestions
4. Actionable recommendations`,
  },
];

const AVAILABLE_VARIABLES = [
  { name: 'query', description: 'User input or question', example: 'What is AI?' },
  { name: 'context', description: 'Retrieved context or documents', example: 'Document content...' },
  { name: 'history', description: 'Conversation history', example: 'Previous messages...' },
  { name: 'user_name', description: 'Current user name', example: 'John Doe' },
  { name: 'date', description: 'Current date', example: '2025-01-26' },
  { name: 'language', description: 'Programming language', example: 'Python' },
];

export function PromptTemplateEditor({ value, onChange, onClose }: PromptTemplateEditorProps) {
  const { toast } = useToast();
  const [localValue, setLocalValue] = React.useState(value);
  const [previewData, setPreviewData] = React.useState({
    query: 'What is artificial intelligence?',
    context: 'AI is the simulation of human intelligence by machines...',
    history: 'User: Hello\nAssistant: Hi! How can I help you?',
    user_name: 'John Doe',
    date: new Date().toISOString().split('T')[0],
    language: 'Python',
  });
  const [copied, setCopied] = React.useState(false);
  const [tokenCount, setTokenCount] = React.useState(0);

  // Simple token counter (approximate)
  React.useEffect(() => {
    const words = localValue.split(/\s+/).length;
    const chars = localValue.length;
    // Rough estimate: ~4 chars per token
    setTokenCount(Math.ceil(chars / 4));
  }, [localValue]);

  const handleEditorChange = (newValue: string | undefined) => {
    if (newValue !== undefined) {
      setLocalValue(newValue);
    }
  };

  const handleSave = () => {
    onChange(localValue);
    toast({
      title: 'Prompt saved',
      description: 'Your prompt template has been updated.',
    });
    onClose?.();
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(localValue);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast({
      title: 'Copied',
      description: 'Prompt template copied to clipboard.',
    });
  };

  const handleUseTemplate = (template: string) => {
    setLocalValue(template);
    toast({
      title: 'Template applied',
      description: 'You can now customize the template.',
    });
  };

  const renderPreview = () => {
    let preview = localValue;
    Object.entries(previewData).forEach(([key, val]) => {
      const regex = new RegExp(`\\$\\{${key}\\}`, 'g');
      preview = preview.replace(regex, val);
    });
    return preview;
  };

  const insertVariable = (varName: string) => {
    const variable = `\${${varName}}`;
    setLocalValue(localValue + variable);
  };

  return (
    <Dialog open={true} onOpenChange={() => onClose?.()}>
      <DialogContent 
        className="max-w-6xl h-[90vh] flex flex-col dark:bg-gray-900"
        aria-labelledby="prompt-editor-title"
        aria-describedby="prompt-editor-description"
      >
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle id="prompt-editor-title">Advanced Prompt Editor</DialogTitle>
              <DialogDescription id="prompt-editor-description">
                Create and customize your prompt template with variables
              </DialogDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge 
                variant="secondary"
                aria-label={`Approximately ${tokenCount} tokens`}
              >
                ~{tokenCount} tokens
              </Badge>
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={handleCopy}
                aria-label={copied ? 'Copied to clipboard' : 'Copy to clipboard'}
              >
                {copied ? <Check className="h-4 w-4" aria-hidden="true" /> : <Copy className="h-4 w-4" aria-hidden="true" />}
              </Button>
            </div>
          </div>
        </DialogHeader>

        <Tabs defaultValue="editor" className="flex-1 flex flex-col">
          <TabsList className="grid w-full grid-cols-3" role="tablist" aria-label="Prompt editor sections">
            <TabsTrigger value="editor" role="tab" aria-controls="editor-panel">
              <FileText className="mr-2 h-4 w-4" aria-hidden="true" />
              Editor
            </TabsTrigger>
            <TabsTrigger value="preview" role="tab" aria-controls="preview-panel">
              <Eye className="mr-2 h-4 w-4" aria-hidden="true" />
              Preview
            </TabsTrigger>
            <TabsTrigger value="templates" role="tab" aria-controls="templates-panel">
              <Lightbulb className="mr-2 h-4 w-4" aria-hidden="true" />
              Templates
            </TabsTrigger>
          </TabsList>

          <TabsContent value="editor" className="flex-1 flex gap-4 mt-4" role="tabpanel" id="editor-panel">
            <div 
              className="flex-1 border rounded-lg overflow-hidden dark:border-gray-700"
              role="region"
              aria-label="Prompt template code editor"
            >
              <Editor
                height="100%"
                defaultLanguage="markdown"
                value={localValue}
                onChange={handleEditorChange}
                theme="vs-dark"
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  lineNumbers: 'on',
                  wordWrap: 'on',
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                  accessibilitySupport: 'on',
                  ariaLabel: 'Prompt template editor',
                }}
              />
            </div>

            <Card className="w-80">
              <CardHeader>
                <CardTitle className="text-sm">Variables</CardTitle>
                <CardDescription className="text-xs">
                  Click to insert into prompt
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  <div className="space-y-3">
                    {AVAILABLE_VARIABLES.map((variable) => (
                      <div
                        key={variable.name}
                        className="p-3 rounded-lg border hover:bg-accent cursor-pointer transition-colors"
                        onClick={() => insertVariable(variable.name)}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <code className="text-sm font-mono text-primary">
                            ${'{' + variable.name + '}'}
                          </code>
                          <Zap className="h-3 w-3 text-muted-foreground" />
                        </div>
                        <p className="text-xs text-muted-foreground mb-1">
                          {variable.description}
                        </p>
                        <p className="text-xs font-mono bg-muted px-2 py-1 rounded">
                          {variable.example}
                        </p>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="preview" className="flex-1 mt-4" role="tabpanel" id="preview-panel">
            <Card className="h-full dark:bg-gray-800">
              <CardHeader>
                <CardTitle className="text-sm">Preview with Sample Data</CardTitle>
                <CardDescription className="text-xs">
                  See how your prompt looks with actual values
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[500px]">
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <pre 
                      className="whitespace-pre-wrap bg-muted dark:bg-gray-900 p-4 rounded-lg text-sm"
                      role="region"
                      aria-label="Prompt preview with sample data"
                    >
                      {renderPreview()}
                    </pre>
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="templates" className="flex-1 mt-4" role="tabpanel" id="templates-panel">
            <ScrollArea className="h-[500px]">
              <div className="grid grid-cols-2 gap-4" role="list" aria-label="Prompt templates">
                {PROMPT_TEMPLATES.map((template) => (
                  <Card 
                    key={template.id} 
                    className="hover:shadow-lg transition-shadow dark:bg-gray-800 dark:hover:bg-gray-750"
                    role="listitem"
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-base">{template.name}</CardTitle>
                          <CardDescription className="text-xs mt-1">
                            {template.description}
                          </CardDescription>
                        </div>
                        <Sparkles className="h-4 w-4 text-primary dark:text-primary-400" aria-hidden="true" />
                      </div>
                    </CardHeader>
                    <CardContent>
                      <pre 
                        className="text-xs bg-muted dark:bg-gray-900 p-3 rounded-lg mb-3 max-h-32 overflow-auto"
                        aria-label={`Template preview for ${template.name}`}
                      >
                        {template.template.substring(0, 150)}...
                      </pre>
                      <Button
                        size="sm"
                        variant="outline"
                        className="w-full focus-visible:ring-2 focus-visible:ring-primary"
                        onClick={() => handleUseTemplate(template.template)}
                        aria-label={`Use ${template.name} template`}
                      >
                        Use Template
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>

        <Separator />

        <div className="flex justify-between items-center">
          <div className="text-sm text-muted-foreground">
            Tip: Use Ctrl+Space for autocomplete
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={handleSave}>
              Save Changes
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
