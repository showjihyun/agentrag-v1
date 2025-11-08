import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { PromptTemplateEditor } from '@/components/agent-builder/PromptTemplateEditor';

// Mock Monaco Editor
jest.mock('@monaco-editor/react', () => ({
  __esModule: true,
  default: ({ value, onChange }: any) => (
    <textarea
      data-testid="monaco-editor"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  ),
}));

describe('PromptTemplateEditor', () => {
  describe('Basic Rendering', () => {
    it('should render the editor', () => {
      render(<PromptTemplateEditor value="" onChange={jest.fn()} />);

      expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
    });

    it('should display the provided value', () => {
      const value = 'Answer the question: ${query}';
      render(<PromptTemplateEditor value={value} onChange={jest.fn()} />);

      const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;
      expect(editor.value).toBe(value);
    });

    it('should call onChange when value changes', () => {
      const onChange = jest.fn();
      render(<PromptTemplateEditor value="" onChange={onChange} />);

      const editor = screen.getByTestId('monaco-editor');
      fireEvent.change(editor, { target: { value: 'New prompt' } });

      expect(onChange).toHaveBeenCalledWith('New prompt');
    });
  });

  describe('Variable Suggestions', () => {
    it('should show available variables', () => {
      const variables = ['query', 'context', 'history'];
      render(
        <PromptTemplateEditor
          value=""
          onChange={jest.fn()}
          availableVariables={variables}
        />
      );

      expect(screen.getByText(/available variables/i)).toBeInTheDocument();
      expect(screen.getByText('query')).toBeInTheDocument();
      expect(screen.getByText('context')).toBeInTheDocument();
      expect(screen.getByText('history')).toBeInTheDocument();
    });

    it('should insert variable when clicked', () => {
      const onChange = jest.fn();
      const variables = ['query', 'context'];
      render(
        <PromptTemplateEditor
          value=""
          onChange={onChange}
          availableVariables={variables}
        />
      );

      const queryButton = screen.getByRole('button', { name: /insert query/i });
      fireEvent.click(queryButton);

      expect(onChange).toHaveBeenCalledWith('${query}');
    });

    it('should append variable to existing content', () => {
      const onChange = jest.fn();
      const variables = ['query'];
      render(
        <PromptTemplateEditor
          value="Answer: "
          onChange={onChange}
          availableVariables={variables}
        />
      );

      const queryButton = screen.getByRole('button', { name: /insert query/i });
      fireEvent.click(queryButton);

      expect(onChange).toHaveBeenCalledWith('Answer: ${query}');
    });

    it('should show default variables when none provided', () => {
      render(<PromptTemplateEditor value="" onChange={jest.fn()} />);

      expect(screen.getByText('query')).toBeInTheDocument();
      expect(screen.getByText('context')).toBeInTheDocument();
      expect(screen.getByText('history')).toBeInTheDocument();
    });
  });

  describe('Prompt Preview', () => {
    it('should show preview with sample variable substitution', () => {
      const value = 'Answer the question: ${query}';
      render(<PromptTemplateEditor value={value} onChange={jest.fn()} />);

      expect(screen.getByText(/preview/i)).toBeInTheDocument();
      expect(screen.getByText(/answer the question:/i)).toBeInTheDocument();
    });

    it('should substitute variables with sample values', () => {
      const value = 'Query: ${query}, Context: ${context}';
      render(<PromptTemplateEditor value={value} onChange={jest.fn()} />);

      const preview = screen.getByTestId('prompt-preview');
      expect(preview).toHaveTextContent('Query: [sample query]');
      expect(preview).toHaveTextContent('Context: [sample context]');
    });

    it('should update preview when value changes', async () => {
      const { rerender } = render(
        <PromptTemplateEditor value="Initial: ${query}" onChange={jest.fn()} />
      );

      expect(screen.getByText(/initial:/i)).toBeInTheDocument();

      rerender(<PromptTemplateEditor value="Updated: ${query}" onChange={jest.fn()} />);

      await waitFor(() => {
        expect(screen.getByText(/updated:/i)).toBeInTheDocument();
      });
    });
  });

  describe('Token Count', () => {
    it('should display token count', () => {
      const value = 'Answer the question: ${query}';
      render(<PromptTemplateEditor value={value} onChange={jest.fn()} />);

      expect(screen.getByText(/tokens/i)).toBeInTheDocument();
    });

    it('should update token count when value changes', async () => {
      const { rerender } = render(
        <PromptTemplateEditor value="Short" onChange={jest.fn()} />
      );

      const initialTokenCount = screen.getByText(/\d+ tokens/i).textContent;

      rerender(
        <PromptTemplateEditor
          value="This is a much longer prompt template with more tokens"
          onChange={jest.fn()}
        />
      );

      await waitFor(() => {
        const newTokenCount = screen.getByText(/\d+ tokens/i).textContent;
        expect(newTokenCount).not.toBe(initialTokenCount);
      });
    });

    it('should show warning when token count is high', () => {
      const longValue = 'word '.repeat(1000); // Create a long prompt
      render(<PromptTemplateEditor value={longValue} onChange={jest.fn()} />);

      expect(screen.getByText(/token limit warning/i)).toBeInTheDocument();
    });
  });

  describe('Advanced Editor', () => {
    it('should open full-screen dialog when clicking advanced button', () => {
      render(<PromptTemplateEditor value="" onChange={jest.fn()} />);

      const advancedButton = screen.getByRole('button', { name: /advanced editor/i });
      fireEvent.click(advancedButton);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('should close dialog when clicking close button', async () => {
      render(<PromptTemplateEditor value="" onChange={jest.fn()} />);

      const advancedButton = screen.getByRole('button', { name: /advanced editor/i });
      fireEvent.click(advancedButton);

      const closeButton = screen.getByRole('button', { name: /close/i });
      fireEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });

    it('should sync changes between normal and advanced editor', () => {
      const onChange = jest.fn();
      render(<PromptTemplateEditor value="" onChange={onChange} />);

      const advancedButton = screen.getByRole('button', { name: /advanced editor/i });
      fireEvent.click(advancedButton);

      const editor = screen.getByTestId('monaco-editor');
      fireEvent.change(editor, { target: { value: 'New prompt in advanced mode' } });

      expect(onChange).toHaveBeenCalledWith('New prompt in advanced mode');
    });
  });

  describe('Validation', () => {
    it('should show error for invalid variable syntax', () => {
      const value = 'Invalid variable: ${unclosed';
      render(<PromptTemplateEditor value={value} onChange={jest.fn()} />);

      expect(screen.getByText(/invalid variable syntax/i)).toBeInTheDocument();
    });

    it('should show warning for undefined variables', () => {
      const value = 'Using undefined: ${undefined_var}';
      const variables = ['query', 'context'];
      render(
        <PromptTemplateEditor
          value={value}
          onChange={jest.fn()}
          availableVariables={variables}
        />
      );

      expect(screen.getByText(/undefined variable/i)).toBeInTheDocument();
    });

    it('should not show errors for valid variables', () => {
      const value = 'Valid: ${query} and ${context}';
      const variables = ['query', 'context'];
      render(
        <PromptTemplateEditor
          value={value}
          onChange={jest.fn()}
          availableVariables={variables}
        />
      );

      expect(screen.queryByText(/invalid variable/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/undefined variable/i)).not.toBeInTheDocument();
    });
  });

  describe('Syntax Highlighting', () => {
    it('should highlight variables in the editor', () => {
      const value = 'Answer: ${query}';
      render(<PromptTemplateEditor value={value} onChange={jest.fn()} />);

      // Monaco editor should be configured with syntax highlighting
      const editor = screen.getByTestId('monaco-editor');
      expect(editor).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper labels', () => {
      render(<PromptTemplateEditor value="" onChange={jest.fn()} />);

      expect(screen.getByLabelText(/prompt template/i)).toBeInTheDocument();
    });

    it('should support keyboard navigation', () => {
      render(<PromptTemplateEditor value="" onChange={jest.fn()} />);

      const editor = screen.getByTestId('monaco-editor');
      editor.focus();

      expect(document.activeElement).toBe(editor);
    });
  });

  describe('Templates', () => {
    it('should show template suggestions', () => {
      render(<PromptTemplateEditor value="" onChange={jest.fn()} showTemplates />);

      expect(screen.getByText(/templates/i)).toBeInTheDocument();
    });

    it('should load template when selected', () => {
      const onChange = jest.fn();
      render(<PromptTemplateEditor value="" onChange={onChange} showTemplates />);

      const ragTemplate = screen.getByRole('button', { name: /rag template/i });
      fireEvent.click(ragTemplate);

      expect(onChange).toHaveBeenCalledWith(
        expect.stringContaining('${context}')
      );
    });

    it('should show multiple template options', () => {
      render(<PromptTemplateEditor value="" onChange={jest.fn()} showTemplates />);

      expect(screen.getByText(/rag template/i)).toBeInTheDocument();
      expect(screen.getByText(/react template/i)).toBeInTheDocument();
      expect(screen.getByText(/chain of thought/i)).toBeInTheDocument();
    });
  });
});
