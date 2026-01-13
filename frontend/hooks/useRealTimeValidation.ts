/**
 * Real-time Validation Hook
 * Provides real-time configuration validation and feedback
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { debounce } from 'lodash';
import { apiClient } from '@/lib/api-client';

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  suggestions: string[];
  security?: {
    risk_level: string;
    warnings: string[];
  };
  performance?: {
    estimated_execution_time: number;
    resource_usage: string;
    optimization_suggestions: string[];
  };
}

export interface UseRealTimeValidationOptions {
  debounceMs?: number;
  enableAutoSave?: boolean;
  autoSaveDelayMs?: number;
  enablePerformanceAnalysis?: boolean;
  enableSecurityCheck?: boolean;
  onValidationChange?: (result: ValidationResult) => void;
  onAutoSave?: (config: any) => void;
  onError?: (error: Error) => void;
}

export interface UseRealTimeValidationReturn {
  validationResult: ValidationResult | null;
  isValidating: boolean;
  hasChanges: boolean;
  lastValidated: Date | null;
  validationHistory: ValidationResult[];
  validate: (patternType: string, config: any) -> Promise<void>;
  validateImmediate: (patternType: string, config: any) -> Promise<ValidationResult>;
  saveConfig: () -> Promise<void>;
  resetValidation: () -> void;
  getValidationSummary: () -> {
    status: 'valid' | 'warning' | 'error' | 'unknown';
    message: string;
    count: number;
  };
}

export function useRealTimeValidation(
  options: UseRealTimeValidationOptions = {}
): UseRealTimeValidationReturn {
  const {
    debounceMs = 500,
    enableAutoSave = false,
    autoSaveDelayMs = 2000,
    enablePerformanceAnalysis = true,
    enableSecurityCheck = true,
    onValidationChange,
    onAutoSave,
    onError
  } = options;

  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [lastValidated, setLastValidated] = useState<Date | null>(null);
  const [validationHistory, setValidationHistory] = useState<ValidationResult[]>([]);
  
  const lastConfigRef = useRef<any>(null);
  const lastPatternTypeRef = useRef<string>('');
  const autoSaveTimeoutRef = useRef<NodeJS.Timeout>();
  const validationCounterRef = useRef<number>(0);

  // Enhanced validation function with debouncing
  const debouncedValidate = useCallback(
    debounce(async (patternType: string, config: any) => {
      if (!patternType || !config) return;

      setIsValidating(true);
      const validationId = ++validationCounterRef.current;
      
      try {
        const requestBody = {
          ...config,
          options: {
            enable_performance_analysis: enablePerformanceAnalysis,
            enable_security_check: enableSecurityCheck,
            validation_level: 'comprehensive'
          }
        };

        const response = await apiClient.post(
          `/api/agent-builder/orchestration/patterns/${patternType}/validate`,
          requestBody
        );
        
        // Check if this is still the latest validation request
        if (validationId !== validationCounterRef.current) {
          return; // Ignore outdated responses
        }

        const result: ValidationResult = response.data;
        setValidationResult(result);
        setLastValidated(new Date());
        
        // Update validation history (keep last 10 results)
        setValidationHistory(prev => {
          const newHistory = [result, ...prev];
          return newHistory.slice(0, 10);
        });
        
        // Validation result callback
        if (onValidationChange) {
          onValidationChange(result);
        }

        // Auto-save handling
        if (enableAutoSave && result.valid && hasChanges) {
          if (autoSaveTimeoutRef.current) {
            clearTimeout(autoSaveTimeoutRef.current);
          }
          
          autoSaveTimeoutRef.current = setTimeout(async () => {
            try {
              if (onAutoSave) {
                await onAutoSave(config);
                setHasChanges(false);
              }
            } catch (error) {
              console.error('Auto-save failed:', error);
              if (onError) {
                onError(error as Error);
              }
            }
          }, autoSaveDelayMs);
        }
        
      } catch (error) {
        console.error('Validation error:', error);
        
        const errorResult: ValidationResult = {
          valid: false,
          errors: ['Validation request failed. Please check your connection and try again.'],
          warnings: [],
          suggestions: ['Check network connection', 'Verify API endpoint availability']
        };
        
        setValidationResult(errorResult);
        
        if (onError) {
          onError(error as Error);
        }
      } finally {
        // Only clear loading if this is still the latest request
        if (validationId === validationCounterRef.current) {
          setIsValidating(false);
        }
      }
    }, debounceMs),
    [debounceMs, enableAutoSave, autoSaveDelayMs, enablePerformanceAnalysis, enableSecurityCheck, hasChanges, onValidationChange, onAutoSave, onError]
  );

  // Immediate validation function (no debouncing)
  const validate = useCallback(async (patternType: string, config: any) => {
    // Detect changes
    const configChanged = JSON.stringify(config) !== JSON.stringify(lastConfigRef.current);
    const patternChanged = patternType !== lastPatternTypeRef.current;
    
    if (configChanged || patternChanged) {
      setHasChanges(true);
      lastConfigRef.current = config;
      lastPatternTypeRef.current = patternType;
    }

    await debouncedValidate(patternType, config);
  }, [debouncedValidate]);

  // Immediate validation without debouncing
  const validateImmediate = useCallback(async (patternType: string, config: any): Promise<ValidationResult> => {
    if (!patternType || !config) {
      throw new Error('Pattern type and config are required');
    }

    setIsValidating(true);
    
    try {
      const requestBody = {
        ...config,
        options: {
          enable_performance_analysis: enablePerformanceAnalysis,
          enable_security_check: enableSecurityCheck,
          validation_level: 'comprehensive'
        }
      };

      const response = await apiClient.post(
        `/api/agent-builder/orchestration/patterns/${patternType}/validate`,
        requestBody
      );
      
      const result: ValidationResult = response.data;
      setValidationResult(result);
      setLastValidated(new Date());
      
      // Update validation history
      setValidationHistory(prev => {
        const newHistory = [result, ...prev];
        return newHistory.slice(0, 10);
      });
      
      if (onValidationChange) {
        onValidationChange(result);
      }

      return result;
      
    } catch (error) {
      console.error('Immediate validation error:', error);
      
      const errorResult: ValidationResult = {
        valid: false,
        errors: ['Validation request failed. Please check your connection and try again.'],
        warnings: [],
        suggestions: ['Check network connection', 'Verify API endpoint availability']
      };
      
      setValidationResult(errorResult);
      
      if (onError) {
        onError(error as Error);
      }
      
      throw error;
    } finally {
      setIsValidating(false);
    }
  }, [enablePerformanceAnalysis, enableSecurityCheck, onValidationChange, onError]);

  // Manual save function
  const saveConfig = useCallback(async () => {
    if (!hasChanges || !lastConfigRef.current) return;

    try {
      if (onAutoSave) {
        await onAutoSave(lastConfigRef.current);
        setHasChanges(false);
        
        // Clear auto-save timer
        if (autoSaveTimeoutRef.current) {
          clearTimeout(autoSaveTimeoutRef.current);
        }
      }
    } catch (error) {
      console.error('Save error:', error);
      if (onError) {
        onError(error as Error);
      }
      throw error;
    }
  }, [hasChanges, onAutoSave, onError]);

  // Reset validation state
  const resetValidation = useCallback(() => {
    setValidationResult(null);
    setIsValidating(false);
    setHasChanges(false);
    setLastValidated(null);
    setValidationHistory([]);
    lastConfigRef.current = null;
    lastPatternTypeRef.current = '';
    validationCounterRef.current = 0;
    
    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current);
    }
  }, []);

  // Get validation summary
  const getValidationSummary = useCallback(() => {
    if (!validationResult) {
      return {
        status: 'unknown' as const,
        message: 'Not validated',
        count: 0
      };
    }

    if (validationResult.errors.length > 0) {
      return {
        status: 'error' as const,
        message: `${validationResult.errors.length} error${validationResult.errors.length > 1 ? 's' : ''}`,
        count: validationResult.errors.length
      };
    }

    if (validationResult.warnings.length > 0) {
      return {
        status: 'warning' as const,
        message: `${validationResult.warnings.length} warning${validationResult.warnings.length > 1 ? 's' : ''}`,
        count: validationResult.warnings.length
      };
    }

    return {
      status: 'valid' as const,
      message: 'Validation passed',
      count: 0
    };
  }, [validationResult]);

  // Component unmount cleanup
  useEffect(() => {
    return () => {
      debouncedValidate.cancel();
      if (autoSaveTimeoutRef.current) {
        clearTimeout(autoSaveTimeoutRef.current);
      }
    };
  }, [debouncedValidate]);

  return {
    validationResult,
    isValidating,
    hasChanges,
    lastValidated,
    validationHistory,
    validate,
    validateImmediate,
    saveConfig,
    resetValidation,
    getValidationSummary
  };
}

/**
 * Generate validation result summary
 */
export function getValidationSummary(result: ValidationResult | null): {
  status: 'valid' | 'warning' | 'error' | 'unknown';
  message: string;
  count: number;
  details?: {
    errors: number;
    warnings: number;
    suggestions: number;
  };
} {
  if (!result) {
    return {
      status: 'unknown',
      message: 'Not validated',
      count: 0
    };
  }

  const details = {
    errors: result.errors.length,
    warnings: result.warnings.length,
    suggestions: result.suggestions.length
  };

  if (result.errors.length > 0) {
    return {
      status: 'error',
      message: `${result.errors.length} error${result.errors.length > 1 ? 's' : ''}`,
      count: result.errors.length,
      details
    };
  }

  if (result.warnings.length > 0) {
    return {
      status: 'warning',
      message: `${result.warnings.length} warning${result.warnings.length > 1 ? 's' : ''}`,
      count: result.warnings.length,
      details
    };
  }

  return {
    status: 'valid',
    message: 'Validation passed',
    count: 0,
    details
  };
}

/**
 * Security risk level color mapping
 */
export function getSecurityRiskColor(riskLevel?: string): string {
  switch (riskLevel?.toLowerCase()) {
    case 'high':
      return 'text-red-600';
    case 'medium':
      return 'text-yellow-600';
    case 'low':
      return 'text-green-600';
    default:
      return 'text-gray-600';
  }
}

/**
 * Validation status icon mapping
 */
export function getValidationIcon(status: string): string {
  switch (status) {
    case 'valid':
      return '✅';
    case 'warning':
      return '⚠️';
    case 'error':
      return '❌';
    default:
      return '❓';
  }
}

/**
 * Performance level color mapping
 */
export function getPerformanceLevelColor(level?: string): string {
  switch (level?.toLowerCase()) {
    case 'excellent':
      return 'text-green-600';
    case 'good':
      return 'text-blue-600';
    case 'fair':
      return 'text-yellow-600';
    case 'poor':
      return 'text-red-600';
    default:
      return 'text-gray-600';
  }
}

/**
 * Format execution time estimate
 */
export function formatExecutionTime(seconds: number): string {
  if (seconds < 1) {
    return `${Math.round(seconds * 1000)}ms`;
  } else if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  } else {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  }
}

/**
 * Get validation trend from history
 */
export function getValidationTrend(history: ValidationResult[]): {
  trend: 'improving' | 'stable' | 'degrading' | 'unknown';
  message: string;
} {
  if (history.length < 2) {
    return {
      trend: 'unknown',
      message: 'Insufficient data'
    };
  }

  const recent = history.slice(0, 3);
  const errorCounts = recent.map(r => r.errors.length);
  const warningCounts = recent.map(r => r.warnings.length);

  const errorTrend = errorCounts[0] - errorCounts[errorCounts.length - 1];
  const warningTrend = warningCounts[0] - warningCounts[warningCounts.length - 1];

  if (errorTrend < 0 || (errorTrend === 0 && warningTrend < 0)) {
    return {
      trend: 'degrading',
      message: 'Validation issues increasing'
    };
  } else if (errorTrend > 0 || (errorTrend === 0 && warningTrend > 0)) {
    return {
      trend: 'improving',
      message: 'Validation issues decreasing'
    };
  } else {
    return {
      trend: 'stable',
      message: 'Validation status stable'
    };
  }
}