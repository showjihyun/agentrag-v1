'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';

interface ExpressionEditorProps {
  value: string;
  onChange: (value: string) => void;
  availableVariables?: Record<string, any>;
  placeholder?: string;
  multiline?: boolean;
}

const FUNCTIONS = [
  { name: '$now', description: '현재 시간', example: '{{$now}}', category: 'Time' },
  { name: '$json', description: '이전 노드 출력', example: '{{$json.field}}', category: 'Data' },
  { name: '$env', description: '환경 변수', example: '{{$env.API_KEY}}', category: 'Environment' },
  { name: '$node', description: '특정 노드 출력', example: '{{$node["NodeName"].json}}', category: 'Data' },
  { name: '$workflow', description: '워크플로우 정보', example: '{{$workflow.id}}', category: 'Workflow' },
  { name: '$input', description: '워크플로우 입력', example: '{{$input.data}}', category: 'Data' },
  { name: '$prev', description: '이전 단계 결과', example: '{{$prev}}', category: 'Data' },
];

const STRING_FUNCTIONS = [
  { name: 'toUpperCase()', description: '대문자 변환', example: '{{$json.name.toUpperCase()}}' },
  { name: 'toLowerCase()', description: '소문자 변환', example: '{{$json.name.toLowerCase()}}' },
  { name: 'trim()', description: '공백 제거', example: '{{$json.text.trim()}}' },
  { name: 'length', description: '길이', example: '{{$json.text.length}}' },
];

export function ExpressionEditor({
  value,
  onChange,
  availableVariables = {},
  placeholder = 'Enter expression...',
  multiline = false
}: ExpressionEditorProps) {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState<typeof FUNCTIONS>([]);
  const [cursorPosition, setCursorPosition] = useState(0);
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null);
  
  // 자동완성 로직
  useEffect(() => {
    const text = value.slice(0, cursorPosition);
    const match = text.match(/\{\{([^}]*)$/);
    
    if (match) {
      const query = match[1].toLowerCase();
      const filtered = FUNCTIONS.filter(f => 
        f.name.toLowerCase().includes(query) ||
        f.description.toLowerCase().includes(query)
      );
      setSuggestions(filtered);
      setShowSuggestions(filtered.length > 0);
    } else {
      setShowSuggestions(false);
    }
  }, [value, cursorPosition]);
  
  const insertSuggestion = (suggestion: typeof FUNCTIONS[0]) => {
    const before = value.slice(0, cursorPosition);
    const after = value.slice(cursorPosition);
    const match = before.match(/\{\{([^}]*)$/);
    
    if (match) {
      const newValue = before.slice(0, -match[0].length) + suggestion.example + after;
      onChange(newValue);
      setShowSuggestions(false);
    }
  };
  
  // 미리보기 (간단한 평가)
  const preview = React.useMemo(() => {
    try {
      let result = value;
      
      // {{$now}} -> 현재 시간
      result = result.replace(/\{\{\$now\}\}/g, new Date().toISOString());
      
      // {{$json.field}} -> availableVariables에서 가져오기
      result = result.replace(/\{\{\$json\.(\w+)\}\}/g, (_, field) => {
        return availableVariables[field] !== undefined 
          ? String(availableVariables[field]) 
          : `[${field}]`;
      });
      
      // {{$env.VAR}} -> 환경 변수 (예시)
      result = result.replace(/\{\{\$env\.(\w+)\}\}/g, (_, varName) => {
        return `[env.${varName}]`;
      });
      
      return result;
    } catch {
      return value;
    }
  }, [value, availableVariables]);
  
  const hasExpressions = value.includes('{{');
  const showPreview = hasExpressions && value !== preview;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    onChange(e.target.value);
    setCursorPosition(e.target.selectionStart || 0);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };
  
  return (
    <div className="relative space-y-2">
      {multiline ? (
        <Textarea
          ref={inputRef as React.RefObject<HTMLTextAreaElement>}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="font-mono text-sm min-h-[100px]"
          rows={4}
        />
      ) : (
        <Input
          ref={inputRef as React.RefObject<HTMLInputElement>}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="font-mono text-sm"
        />
      )}
      
      {/* 자동완성 제안 */}
      {showSuggestions && (
        <Card className="absolute z-50 mt-1 w-full max-h-60 overflow-auto shadow-lg">
          <div className="p-2">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => insertSuggestion(suggestion)}
                className="w-full text-left px-3 py-2 hover:bg-accent rounded-md transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm font-medium">{suggestion.name}</span>
                  <Badge variant="outline" className="text-xs">
                    {suggestion.category}
                  </Badge>
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  {suggestion.description}
                </div>
                <div className="text-xs font-mono text-muted-foreground mt-1 bg-muted px-2 py-1 rounded">
                  {suggestion.example}
                </div>
              </button>
            ))}
          </div>
        </Card>
      )}
      
      {/* 미리보기 */}
      {showPreview && (
        <div className="p-3 bg-muted rounded-md border">
          <div className="text-xs font-medium text-muted-foreground mb-2 flex items-center gap-2">
            <span>Preview:</span>
            <Badge variant="secondary" className="text-xs">Live</Badge>
          </div>
          <div className="text-sm font-mono break-all">{preview}</div>
        </div>
      )}
      
      {/* 도움말 */}
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span>💡 Tip: Type</span>
        <code className="bg-muted px-1.5 py-0.5 rounded font-mono">{'{{'}</code>
        <span>to see available expressions</span>
      </div>

      {/* 사용 가능한 변수 표시 */}
      {Object.keys(availableVariables).length > 0 && (
        <div className="text-xs">
          <div className="font-medium text-muted-foreground mb-1">Available variables:</div>
          <div className="flex flex-wrap gap-1">
            {Object.keys(availableVariables).map(key => (
              <Badge 
                key={key} 
                variant="outline" 
                className="text-xs cursor-pointer hover:bg-accent"
                onClick={() => {
                  const expr = `{{$json.${key}}}`;
                  onChange(value + expr);
                }}
              >
                {key}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
