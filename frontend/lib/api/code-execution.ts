/**
 * Code Execution API Client
 * API client for Enhanced Code Block functionality
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============== Types ==============

export interface CodeTestRequest {
  code: string;
  language: 'python' | 'javascript' | 'typescript' | 'sql';
  input?: any;
  context?: Record<string, any>;
  timeout?: number;
  allow_imports?: boolean;
}

export interface CodeTestResponse {
  success: boolean;
  output?: any;
  error?: string;
  executionTime?: number;
  logs?: string[];
}

export interface CodeGenerateRequest {
  prompt: string;
  language: 'python' | 'javascript' | 'typescript' | 'sql';
  context?: string;
}

export interface CodeGenerateResponse {
  code?: string;
  error?: string;
  explanation?: string;
}

export interface CodeTemplate {
  name: string;
  description: string;
  code: string;
}

export interface CodeTemplatesResponse {
  language: string;
  templates: Record<string, CodeTemplate>;
}

// ============== API Functions ==============

/**
 * Execute code test
 */
export async function testCode(request: CodeTestRequest): Promise<CodeTestResponse> {
  const token = localStorage.getItem('token');
  
  const response = await fetch(`${API_BASE}/api/workflow/test-code`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * AI code generation
 */
export async function generateCode(request: CodeGenerateRequest): Promise<CodeGenerateResponse> {
  const token = localStorage.getItem('token');
  
  const response = await fetch(`${API_BASE}/api/workflow/generate-code`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Get code templates list
 */
export async function getCodeTemplates(language: string = 'python'): Promise<CodeTemplatesResponse> {
  const token = localStorage.getItem('token');
  
  const response = await fetch(`${API_BASE}/api/workflow/code-templates?language=${language}`, {
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// ============== React Query Hooks ==============

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

/**
 * Code test execution mutation hook
 */
export function useTestCode() {
  return useMutation({
    mutationFn: testCode,
  });
}

/**
 * AI code generation mutation hook
 */
export function useGenerateCode() {
  return useMutation({
    mutationFn: generateCode,
  });
}

/**
 * Code templates query hook
 */
export function useCodeTemplates(language: string = 'python') {
  return useQuery({
    queryKey: ['code-templates', language],
    queryFn: () => getCodeTemplates(language),
    staleTime: 1000 * 60 * 60, // 1 hour
  });
}
