'use client';

import { useState, useRef, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Code, Play, Info, Sparkles } from 'lucide-react';

interface Variable {
  name: string;
  description: string;
  type: string;
  example?: string;
}

interface Function {
  name: string;
  description: string;
  syntax: string;
  example: string;
}

const VARIABLES: Variable[] = [
  {
    name: '$input',
    description: 'Input data from previous node',
    type: 'object',
    example: '$input.data.name'
  },
  {
    name: '$node',
    description: 'Access data from specific node',
    type: 'object',
    example: '$node["Node Name"].data'
  },
  {
    name: '$workflow',
    description: 'Workflow metadata',
    type: 'object',
    example: '$workflow.id'
  },
  {
    name: '$env',
    description: 'Environment variables',
    type: 'object',
    example: '$env.API_KEY'
  },
  {
    name: '$execution',
    description: 'Current execution context',
    type: 'object',
    example: '$execution.id'
  },
];

const FUNCTIONS: Function[] = [
  {
    name: 'now()',
    description: 'Current timestamp',
    syntax: 'now()',
    example: 'now() // 2024-01-01T00:00:00Z'
  },
  {
    name: 'uuid()',
    description: 'Generate UUID',
    syntax: 'uuid()',
    example: 'uuid() // "123e4567-e89b-12d3-a456-426614174000"'
  },
  {
    name: 'json()',
    description: 'Parse JSON string',
    syntax: 'json(string)',
    example: 'json(\'{"key": "value"}\') // {key: "value"}'
  },
  {
    name: 'base64()',
    description: 'Encode to base64',
    syntax: 'base64(string)',
    example: 'base64("hello") // "aGVsbG8="'
  },
  {
    name: 'length()',
    description: 'Get array/string length',
    syntax: 'length(value)',
    example: 'length([1,2,3]) // 3'
  },
  {
    name: 'upper()',
    description: 'Convert to uppercase',
    syntax: 'upper(string)',
    example: 'upper("hello") // "HELLO"'
  },
  {
    name: 'lower()',
    description: 'Convert to lowercase',
    syntax: 'lower(string)',
    example: 'lower("HELLO") // "hello"'
  },
  {
    name: 'trim()',
    description: 'Remove whitespace',
    syntax: 'trim(string)',
    example: 'trim("  hello  ") // "hello"'
  },
  {
    name: 'split()',
    description: 'Split string',
    syntax: 'split(string, separator)',
    example: 'split("a,b,c", ",") // ["a","b","c"]'
  },
  {
    name: 'join()',
    description: 'Join array',
    syntax: 'join(array, separator)',
    example: 'join(["a","b"], ",") // "a,b"'
  },
];

interface ExpressionEditorProps {
  value: string;
  onChange: (value: string) => void;
  context?: Record<string, any>;
  placeholder?: string;
  height?: string;
}

export function ExpressionEditor({
  value,
  onChange,
  context = {},
  placeholder = 'Enter expression... e.g., $input.data.name',
  height = 'h-32'
}: ExpressionEditorProps) {
  const [preview, setPreview] = useState<any>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [showAutocomplete, setShowAutocomplete] = useState(false);
  const [autocompleteFilter, setAutocompleteFilter] = useState('');
  const [cursorPosition, setCursorPosition] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Filter suggestions based on current input
  const filteredVariables = VARIABLES.filter(v =>
    v.name.toLowerCase().includes(autocompleteFilter.toLowerCase())
  );
  
  const filteredFunctions = FUNCTIONS.filter(f =>
    f.name.toLowerCase().includes(autocompleteFilter.toLowerCase())
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    onChange(newValue);
    
    // Check if we should show autocomplete
    const cursorPos = e.target.selectionStart;
    setCursorPosition(cursorPos);
    
    // Get word at cursor
    const textBeforeCursor = newValue.substring(0, cursorPos);
    const lastWord = textBeforeCursor.split(/\s/).pop() || '';
    
    if (lastWord.startsWith('$') || lastWord.includes('(')) {
      setAutocompleteFilter(lastWord);
      setShowAutocomplete(true);
    } else {
      setShowAutocomplete(false);
    }
  };

  const insertSuggestion = (text: string) => {
    if (!textareaRef.current) return;
    
    const textarea = textareaRef.current;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const textBefore = value.substring(0, start);
    const textAfter = value.substring(end);
    
    // Find the start of the current word
    const words = textBefore.split(/\s/);
    const currentWord = words[words.length - 1];
    const wordStart = start - currentWord.length;
    
    const newValue = value.substring(0, wordStart) + text + textAfter;
    onChange(newValue);
    setShowAutocomplete(false);
    
    // Set cursor position after inserted text
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(wordStart + text.length, wordStart + text.length);
    }, 0);
  };

  const evaluateExpression = async () => {
    setIsEvaluating(true);
    try {
      // In production, call backend API
      // For now, simulate evaluation
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Simple evaluation for demo
      let result: any;
      try {
        // Replace variables with context values
        let expr = value;
        Object.keys(context).forEach(key => {
          expr = expr.replace(new RegExp(`\\$${key}`, 'g'), JSON.stringify(context[key]));
        });
        
        // Simulate result
        result = {
          value: expr,
          type: typeof expr,
          preview: expr.substring(0, 100)
        };
      } catch (e) {
        result = { error: 'Invalid expression' };
      }
      
      setPreview(result);
    } catch (error) {
      setPreview({ error: 'Evaluation failed' });
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <div className="space-y-3">
      {/* Editor Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Code className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Expression</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative group">
            <Button variant="ghost" size="sm" className="h-7 px-2">
              <Info className="h-3 w-3 mr-1" />
              Help
            </Button>
            <div className="absolute right-0 top-full mt-1 w-80 bg-white border rounded-lg shadow-lg p-4 z-50 hidden group-hover:block">
              <div className="space-y-3">
                <div>
                  <h4 className="font-semibold text-sm mb-2">Expression Syntax</h4>
                  <ul className="text-xs space-y-1 text-muted-foreground">
                    <li>• Use <code className="bg-muted px-1 rounded">$variable</code> to access data</li>
                    <li>• Use <code className="bg-muted px-1 rounded">function()</code> for operations</li>
                    <li>• Chain with <code className="bg-muted px-1 rounded">.</code> for nested access</li>
                    <li>• Use <code className="bg-muted px-1 rounded">[]</code> for array indexing</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-sm mb-2">Examples</h4>
                  <ul className="text-xs space-y-1 text-muted-foreground">
                    <li><code className="bg-muted px-1 rounded">$input.data.name</code></li>
                    <li><code className="bg-muted px-1 rounded">upper($input.email)</code></li>
                    <li><code className="bg-muted px-1 rounded">$node["HTTP Request"].data</code></li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={evaluateExpression}
            disabled={isEvaluating || !value}
            className="h-7 px-2"
          >
            {isEvaluating ? (
              <>
                <Sparkles className="h-3 w-3 mr-1 animate-spin" />
                Testing...
              </>
            ) : (
              <>
                <Play className="h-3 w-3 mr-1" />
                Test
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Editor */}
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleInputChange}
          className={`w-full ${height} p-3 font-mono text-sm border rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-primary`}
          placeholder={placeholder}
          spellCheck={false}
        />
        
        {/* Autocomplete Dropdown */}
        {showAutocomplete && (filteredVariables.length > 0 || filteredFunctions.length > 0) && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border rounded-md shadow-lg z-10 max-h-64 overflow-y-auto">
            {/* Variables */}
            {filteredVariables.length > 0 && (
              <div className="p-2">
                <p className="text-xs font-semibold text-gray-500 mb-1 px-2">Variables</p>
                {filteredVariables.map((v) => (
                  <div
                    key={v.name}
                    className="px-2 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded cursor-pointer"
                    onClick={() => insertSuggestion(v.name)}
                  >
                    <div className="flex items-center justify-between">
                      <code className="text-sm font-mono text-primary">{v.name}</code>
                      <Badge variant="outline" className="text-xs">{v.type}</Badge>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{v.description}</p>
                    {v.example && (
                      <code className="text-xs text-gray-400 mt-1 block">{v.example}</code>
                    )}
                  </div>
                ))}
              </div>
            )}
            
            {/* Functions */}
            {filteredFunctions.length > 0 && (
              <div className="p-2 border-t">
                <p className="text-xs font-semibold text-gray-500 mb-1 px-2">Functions</p>
                {filteredFunctions.map((f) => (
                  <div
                    key={f.name}
                    className="px-2 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded cursor-pointer"
                    onClick={() => insertSuggestion(f.syntax)}
                  >
                    <code className="text-sm font-mono text-primary">{f.name}</code>
                    <p className="text-xs text-gray-500 mt-1">{f.description}</p>
                    <code className="text-xs text-gray-400 mt-1 block">{f.example}</code>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* Preview */}
      {preview && (
        <Card className="p-3 bg-muted/50">
          <div className="flex items-start justify-between mb-2">
            <p className="text-xs font-semibold">Preview Result:</p>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setPreview(null)}
              className="h-5 w-5 p-0"
            >
              ×
            </Button>
          </div>
          {preview.error ? (
            <div className="text-xs text-destructive">{preview.error}</div>
          ) : (
            <pre className="text-xs bg-background p-2 rounded overflow-x-auto">
              {JSON.stringify(preview, null, 2)}
            </pre>
          )}
        </Card>
      )}
      
      {/* Quick Reference */}
      <div className="flex flex-wrap gap-2">
        <span className="text-xs text-muted-foreground">Quick insert:</span>
        {VARIABLES.slice(0, 4).map((v) => (
          <Button
            key={v.name}
            variant="outline"
            size="sm"
            onClick={() => insertSuggestion(v.name)}
            className="h-6 px-2 text-xs"
          >
            {v.name}
          </Button>
        ))}
      </div>
    </div>
  );
}
