'use client';

import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { ChevronDown, Check, RefreshCw, Cpu, AlertCircle } from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface OllamaModel {
  name: string;
  model: string;
  size: number;
  modified_at: string;
  digest: string;
  details: {
    format?: string;
    family?: string;
    parameter_size?: string;
    quantization_level?: string;
  };
}

interface ModelSelectorProps {
  onModelChange?: (model: string) => void;
}

export default function ModelSelector({ onModelChange }: ModelSelectorProps) {
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [currentModel, setCurrentModel] = useState<string>('');
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [provider, setProvider] = useState<string>('ollama');
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0, width: 0 });
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Load models on mount
  useEffect(() => {
    loadModels();
    loadCurrentModel();
  }, []);

  const loadModels = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await apiClient.getOllamaModels();
      setModels(data.models || []);
      setProvider(data.provider || 'ollama');
      
      // Load selected model from localStorage
      const saved = localStorage.getItem('selected-llm-model');
      if (saved) {
        setSelectedModel(saved);
      } else if (data.current) {
        setSelectedModel(data.current);
      }
    } catch (err: any) {
      console.error('Failed to load Ollama models:', err);
      setError(err.message || 'Failed to load models');
    } finally {
      setIsLoading(false);
    }
  };

  const loadCurrentModel = async () => {
    try {
      const data = await apiClient.getCurrentModel();
      setCurrentModel(data.model || '');
    } catch (err) {
      console.error('Failed to load current model:', err);
    }
  };

  const handleModelSelect = (modelName: string) => {
    setSelectedModel(modelName);
    setIsOpen(false);
    
    // Save to localStorage
    localStorage.setItem('selected-llm-model', modelName);
    
    // Notify parent component
    onModelChange?.(modelName);
  };

  const updateDropdownPosition = () => {
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      setDropdownPosition({
        top: rect.bottom + window.scrollY + 8,
        left: rect.left + window.scrollX,
        width: rect.width,
      });
    }
  };

  useEffect(() => {
    if (isOpen) {
      updateDropdownPosition();
      window.addEventListener('resize', updateDropdownPosition);
      window.addEventListener('scroll', updateDropdownPosition, true);
      return () => {
        window.removeEventListener('resize', updateDropdownPosition);
        window.removeEventListener('scroll', updateDropdownPosition, true);
      };
    }
  }, [isOpen]);

  const formatSize = (bytes: number): string => {
    const gb = bytes / (1024 * 1024 * 1024);
    return `${gb.toFixed(1)} GB`;
  };

  if (provider !== 'ollama') {
    return null; // Only show for Ollama provider
  }

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        onClick={() => {
          setIsOpen(!isOpen);
          if (!isOpen) {
            updateDropdownPosition();
          }
        }}
        disabled={isLoading}
        className="flex items-center gap-2 px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed min-w-[180px] sm:min-w-[220px]"
      >
        <Cpu className="w-4 h-4 text-gray-600 dark:text-gray-400 flex-shrink-0" />
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300 truncate flex-1 text-left">
          {isLoading ? 'Loading...' : selectedModel || 'Select Model'}
        </span>
        {!isLoading && (
          <ChevronDown className={`w-4 h-4 text-gray-500 transition-transform flex-shrink-0 ${isOpen ? 'rotate-180' : ''}`} />
        )}
      </button>

      {/* Refresh button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          loadModels();
        }}
        disabled={isLoading}
        className="absolute -right-1 -top-1 p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600"
        title="Refresh models"
      >
        <RefreshCw className={`w-3 h-3 text-gray-500 ${isLoading ? 'animate-spin' : ''}`} />
      </button>

      {/* Dropdown with Portal */}
      {isOpen && typeof window !== 'undefined' && createPortal(
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/10 dark:bg-black/30 z-[9998]"
            onClick={() => setIsOpen(false)}
          />
          
          {/* Dropdown */}
          <div 
            className="fixed bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-2xl max-h-96 overflow-y-auto z-[9999]"
            style={{
              top: `${dropdownPosition.top}px`,
              left: `${dropdownPosition.left}px`,
              minWidth: `${Math.max(dropdownPosition.width, 384)}px`,
              maxWidth: '90vw',
            }}
          >
          {error ? (
            <div className="p-4 text-center">
              <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              <button
                onClick={loadModels}
                className="mt-2 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
              >
                Try again
              </button>
            </div>
          ) : models.length === 0 ? (
            <div className="p-4 text-center text-sm text-gray-500">
              No Ollama models found. Please install models using:
              <code className="block mt-2 p-2 bg-gray-100 dark:bg-gray-700 rounded">
                ollama pull llama3.1
              </code>
            </div>
          ) : (
            <div className="py-2">
              {models.map((model) => (
                <button
                  key={model.name}
                  onClick={() => handleModelSelect(model.name)}
                  className="w-full px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-left flex items-start gap-3"
                >
                  <div className="flex-shrink-0 mt-1">
                    {selectedModel === model.name ? (
                      <Check className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                    ) : (
                      <div className="w-4 h-4" />
                    )}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-sm text-gray-900 dark:text-gray-100">
                        {model.name}
                      </span>
                      {currentModel === model.name && (
                        <span className="text-xs px-2 py-0.5 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded">
                          Current
                        </span>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-2 mt-1 text-xs text-gray-500 dark:text-gray-400 flex-wrap">
                      <span>{formatSize(model.size)}</span>
                      {model.details?.parameter_size && (
                        <>
                          <span>•</span>
                          <span>{model.details.parameter_size}</span>
                        </>
                      )}
                      {model.details?.quantization_level && (
                        <>
                          <span>•</span>
                          <span>{model.details.quantization_level}</span>
                        </>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
          </div>
        </>,
        document.body
      )}
    </div>
  );
}
