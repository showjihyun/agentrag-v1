import { useState, useCallback, useRef, useEffect } from 'react';

interface UseChatInputOptions {
  onSubmit: (content: string) => void;
  isProcessing: boolean;
}

export function useChatInput({ onSubmit, isProcessing }: UseChatInputOptions) {
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || isProcessing) {
      return;
    }

    onSubmit(input.trim());
    setInput('');
  }, [input, isProcessing, onSubmit]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }, [handleSubmit]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
  }, []);

  const clearInput = useCallback(() => {
    setInput('');
  }, []);

  const focusInput = useCallback(() => {
    inputRef.current?.focus();
  }, []);

  // Handle example selection
  useEffect(() => {
    const handleExampleSelected = (event: CustomEvent) => {
      setInput(event.detail);
      focusInput();
    };

    window.addEventListener('example-selected', handleExampleSelected as EventListener);
    return () => {
      window.removeEventListener('example-selected', handleExampleSelected as EventListener);
    };
  }, [focusInput]);

  return {
    input,
    inputRef,
    handleSubmit,
    handleKeyDown,
    handleInputChange,
    clearInput,
    focusInput,
  };
}
