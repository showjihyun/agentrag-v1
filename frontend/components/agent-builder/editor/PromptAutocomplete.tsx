'use client';

import React from 'react';
import { editor } from 'monaco-editor';

interface Variable {
  name: string;
  type: string;
  description?: string;
}

interface PromptAutocompleteProps {
  variables?: Variable[];
  customCompletions?: editor.ICompletionItem[];
}

/**
 * Prompt template autocomplete provider
 */
export function createPromptAutocompleteProvider(
  variables: Variable[] = [],
  customCompletions: editor.ICompletionItem[] = []
): editor.ICompletionItemProvider {
  return {
    provideCompletionItems: (model, position) => {
      const textUntilPosition = model.getValueInRange({
        startLineNumber: position.lineNumber,
        startColumn: 1,
        endLineNumber: position.lineNumber,
        endColumn: position.column,
      });

      // Check if we're inside ${}
      const match = textUntilPosition.match(/\$\{([^}]*)$/);
      
      if (!match) {
        return { suggestions: [] };
      }

      const word = model.getWordUntilPosition(position);
      const range = {
        startLineNumber: position.lineNumber,
        endLineNumber: position.lineNumber,
        startColumn: word.startColumn,
        endColumn: word.endColumn,
      };

      // Variable suggestions
      const variableSuggestions: editor.ICompletionItem[] = variables.map((v) => ({
        label: v.name,
        kind: monaco.languages.CompletionItemKind.Variable,
        documentation: v.description || `Variable of type ${v.type}`,
        insertText: v.name,
        range,
        detail: v.type,
      }));

      // Common prompt patterns
      const patternSuggestions: editor.ICompletionItem[] = [
        {
          label: 'query',
          kind: monaco.languages.CompletionItemKind.Variable,
          documentation: 'User query or input',
          insertText: 'query',
          range,
        },
        {
          label: 'context',
          kind: monaco.languages.CompletionItemKind.Variable,
          documentation: 'Retrieved context from knowledge base',
          insertText: 'context',
          range,
        },
        {
          label: 'history',
          kind: monaco.languages.CompletionItemKind.Variable,
          documentation: 'Conversation history',
          insertText: 'history',
          range,
        },
        {
          label: 'system_prompt',
          kind: monaco.languages.CompletionItemKind.Variable,
          documentation: 'System-level instructions',
          insertText: 'system_prompt',
          range,
        },
      ];

      return {
        suggestions: [
          ...variableSuggestions,
          ...patternSuggestions,
          ...customCompletions,
        ],
      };
    },
  };
}

/**
 * Prompt template hover provider
 */
export function createPromptHoverProvider(
  variables: Variable[] = []
): editor.IHoverProvider {
  return {
    provideHover: (model, position) => {
      const word = model.getWordAtPosition(position);
      if (!word) return null;

      const variable = variables.find((v) => v.name === word.word);
      if (!variable) return null;

      return {
        range: new monaco.Range(
          position.lineNumber,
          word.startColumn,
          position.lineNumber,
          word.endColumn
        ),
        contents: [
          { value: `**${variable.name}** (${variable.type})` },
          { value: variable.description || 'No description available' },
        ],
      };
    },
  };
}

/**
 * Prompt template validation
 */
export function validatePromptTemplate(
  template: string,
  availableVariables: string[]
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  // Find all variables in template
  const variableRegex = /\$\{([^}]+)\}/g;
  const matches = template.matchAll(variableRegex);
  
  for (const match of matches) {
    const varName = match[1].trim();
    
    if (!availableVariables.includes(varName)) {
      errors.push(`Unknown variable: ${varName}`);
    }
  }
  
  // Check for unclosed variables
  const openBraces = (template.match(/\$\{/g) || []).length;
  const closeBraces = (template.match(/\}/g) || []).length;
  
  if (openBraces !== closeBraces) {
    errors.push('Unclosed variable syntax');
  }
  
  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Hook for prompt autocomplete
 */
export function usePromptAutocomplete(variables: Variable[] = []) {
  React.useEffect(() => {
    if (typeof window === 'undefined') return;

    const disposables: monaco.IDisposable[] = [];

    // Register completion provider
    disposables.push(
      monaco.languages.registerCompletionItemProvider('plaintext', 
        createPromptAutocompleteProvider(variables)
      )
    );

    // Register hover provider
    disposables.push(
      monaco.languages.registerHoverProvider('plaintext',
        createPromptHoverProvider(variables)
      )
    );

    return () => {
      disposables.forEach((d) => d.dispose());
    };
  }, [variables]);
}
