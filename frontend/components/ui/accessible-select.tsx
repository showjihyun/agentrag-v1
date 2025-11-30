'use client';

/**
 * Accessible Select Component
 * 
 * WCAG 2.1 AA compliant select component with:
 * - Full keyboard navigation (Arrow keys, Enter, Escape, Home, End)
 * - Screen reader support with ARIA attributes
 * - Focus management
 * - High contrast support
 */

import * as React from 'react';
import { cn } from '@/lib/utils';
import { ChevronDown, Check } from 'lucide-react';

interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
  description?: string;
}

interface AccessibleSelectProps {
  id?: string;
  name?: string;
  value?: string;
  defaultValue?: string;
  options: SelectOption[];
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  error?: string;
  label?: string;
  helperText?: string;
  className?: string;
  onChange?: (value: string) => void;
  onBlur?: () => void;
  'aria-label'?: string;
  'aria-describedby'?: string;
}

export function AccessibleSelect({
  id,
  name,
  value: controlledValue,
  defaultValue,
  options,
  placeholder = 'Select an option',
  disabled = false,
  required = false,
  error,
  label,
  helperText,
  className,
  onChange,
  onBlur,
  'aria-label': ariaLabel,
  'aria-describedby': ariaDescribedBy,
}: AccessibleSelectProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const [internalValue, setInternalValue] = React.useState(defaultValue || '');
  const [highlightedIndex, setHighlightedIndex] = React.useState(-1);
  const [searchQuery, setSearchQuery] = React.useState('');
  const searchTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);
  
  const triggerRef = React.useRef<HTMLButtonElement>(null);
  const listboxRef = React.useRef<HTMLUListElement>(null);
  const optionRefs = React.useRef<(HTMLLIElement | null)[]>([]);
  
  const value = controlledValue ?? internalValue;
  const selectedOption = options.find(opt => opt.value === value);
  
  const generatedId = React.useId();
  const selectId = id || generatedId;
  const listboxId = `${selectId}-listbox`;
  const labelId = label ? `${selectId}-label` : undefined;
  const helperId = helperText ? `${selectId}-helper` : undefined;
  const errorId = error ? `${selectId}-error` : undefined;
  
  // Filter enabled options for keyboard navigation
  const enabledOptions = options.filter(opt => !opt.disabled);
  
  const handleValueChange = React.useCallback((newValue: string) => {
    if (controlledValue === undefined) {
      setInternalValue(newValue);
    }
    onChange?.(newValue);
    setIsOpen(false);
    triggerRef.current?.focus();
  }, [controlledValue, onChange]);
  
  const handleOpen = React.useCallback(() => {
    if (disabled) return;
    setIsOpen(true);
    // Set initial highlighted index to selected option or first enabled option
    const selectedIndex = options.findIndex(opt => opt.value === value);
    setHighlightedIndex(selectedIndex >= 0 ? selectedIndex : enabledOptions.length > 0 ? options.indexOf(enabledOptions[0]) : -1);
  }, [disabled, options, value, enabledOptions]);
  
  const handleClose = React.useCallback(() => {
    setIsOpen(false);
    setHighlightedIndex(-1);
    setSearchQuery('');
    onBlur?.();
  }, [onBlur]);
  
  // Type-ahead search
  const handleTypeAhead = React.useCallback((char: string) => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    const newQuery = searchQuery + char.toLowerCase();
    setSearchQuery(newQuery);
    
    // Find matching option
    const matchIndex = options.findIndex(opt => 
      !opt.disabled && opt.label.toLowerCase().startsWith(newQuery)
    );
    
    if (matchIndex >= 0) {
      setHighlightedIndex(matchIndex);
      optionRefs.current[matchIndex]?.scrollIntoView({ block: 'nearest' });
    }
    
    searchTimeoutRef.current = setTimeout(() => {
      setSearchQuery('');
    }, 500);
  }, [searchQuery, options]);
  
  // Keyboard navigation
  const handleKeyDown = React.useCallback((e: React.KeyboardEvent) => {
    if (disabled) return;
    
    switch (e.key) {
      case 'Enter':
      case ' ':
        e.preventDefault();
        if (isOpen && highlightedIndex >= 0) {
          const option = options[highlightedIndex];
          if (option && !option.disabled) {
            handleValueChange(option.value);
          }
        } else {
          handleOpen();
        }
        break;
        
      case 'Escape':
        e.preventDefault();
        handleClose();
        break;
        
      case 'ArrowDown':
        e.preventDefault();
        if (!isOpen) {
          handleOpen();
        } else {
          const nextIndex = highlightedIndex + 1;
          // Find next enabled option
          for (let i = nextIndex; i < options.length; i++) {
            if (!options[i].disabled) {
              setHighlightedIndex(i);
              optionRefs.current[i]?.scrollIntoView({ block: 'nearest' });
              break;
            }
          }
        }
        break;
        
      case 'ArrowUp':
        e.preventDefault();
        if (!isOpen) {
          handleOpen();
        } else {
          const prevIndex = highlightedIndex - 1;
          // Find previous enabled option
          for (let i = prevIndex; i >= 0; i--) {
            if (!options[i].disabled) {
              setHighlightedIndex(i);
              optionRefs.current[i]?.scrollIntoView({ block: 'nearest' });
              break;
            }
          }
        }
        break;
        
      case 'Home':
        e.preventDefault();
        if (isOpen) {
          const firstEnabled = options.findIndex(opt => !opt.disabled);
          if (firstEnabled >= 0) {
            setHighlightedIndex(firstEnabled);
            optionRefs.current[firstEnabled]?.scrollIntoView({ block: 'nearest' });
          }
        }
        break;
        
      case 'End':
        e.preventDefault();
        if (isOpen) {
          for (let i = options.length - 1; i >= 0; i--) {
            if (!options[i].disabled) {
              setHighlightedIndex(i);
              optionRefs.current[i]?.scrollIntoView({ block: 'nearest' });
              break;
            }
          }
        }
        break;
        
      case 'Tab':
        if (isOpen) {
          handleClose();
        }
        break;
        
      default:
        // Type-ahead search for printable characters
        if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
          if (!isOpen) handleOpen();
          handleTypeAhead(e.key);
        }
        break;
    }
  }, [disabled, isOpen, highlightedIndex, options, handleOpen, handleClose, handleValueChange, handleTypeAhead]);
  
  // Click outside to close
  React.useEffect(() => {
    if (!isOpen) return;
    
    const handleClickOutside = (e: MouseEvent) => {
      if (
        triggerRef.current && !triggerRef.current.contains(e.target as Node) &&
        listboxRef.current && !listboxRef.current.contains(e.target as Node)
      ) {
        handleClose();
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen, handleClose]);
  
  // Scroll highlighted option into view
  React.useEffect(() => {
    if (isOpen && highlightedIndex >= 0) {
      optionRefs.current[highlightedIndex]?.scrollIntoView({ block: 'nearest' });
    }
  }, [isOpen, highlightedIndex]);
  
  const describedByIds = [
    ariaDescribedBy,
    helperId,
    errorId,
  ].filter(Boolean).join(' ') || undefined;

  return (
    <div className={cn('relative', className)}>
      {/* Label */}
      {label && (
        <label
          id={labelId}
          htmlFor={selectId}
          className={cn(
            'block text-sm font-medium mb-1.5',
            disabled ? 'text-muted-foreground' : 'text-foreground',
            error && 'text-destructive'
          )}
        >
          {label}
          {required && <span className="text-destructive ml-1" aria-hidden="true">*</span>}
        </label>
      )}
      
      {/* Trigger Button */}
      <button
        ref={triggerRef}
        id={selectId}
        name={name}
        type="button"
        role="combobox"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-controls={listboxId}
        aria-labelledby={labelId}
        aria-label={ariaLabel}
        aria-describedby={describedByIds}
        aria-invalid={!!error}
        aria-required={required}
        aria-activedescendant={isOpen && highlightedIndex >= 0 ? `${selectId}-option-${highlightedIndex}` : undefined}
        disabled={disabled}
        className={cn(
          'flex h-10 w-full items-center justify-between rounded-md border px-3 py-2 text-sm',
          'bg-background ring-offset-background',
          'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
          'disabled:cursor-not-allowed disabled:opacity-50',
          'transition-colors duration-200',
          error
            ? 'border-destructive focus:ring-destructive'
            : 'border-input hover:border-primary/50',
          isOpen && 'ring-2 ring-ring ring-offset-2'
        )}
        onClick={() => isOpen ? handleClose() : handleOpen()}
        onKeyDown={handleKeyDown}
      >
        <span className={cn('truncate', !selectedOption && 'text-muted-foreground')}>
          {selectedOption?.label || placeholder}
        </span>
        <ChevronDown
          className={cn(
            'h-4 w-4 shrink-0 opacity-50 transition-transform duration-200',
            isOpen && 'rotate-180'
          )}
          aria-hidden="true"
        />
      </button>
      
      {/* Listbox */}
      {isOpen && (
        <ul
          ref={listboxRef}
          id={listboxId}
          role="listbox"
          aria-labelledby={labelId}
          aria-label={ariaLabel}
          tabIndex={-1}
          className={cn(
            'absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-md border bg-popover p-1 shadow-md',
            'animate-in fade-in-0 zoom-in-95 duration-200'
          )}
        >
          {options.length === 0 ? (
            <li className="px-3 py-2 text-sm text-muted-foreground text-center">
              No options available
            </li>
          ) : (
            options.map((option, index) => {
              const isSelected = option.value === value;
              const isHighlighted = index === highlightedIndex;
              
              return (
                <li
                  key={option.value}
                  ref={el => { optionRefs.current[index] = el; }}
                  id={`${selectId}-option-${index}`}
                  role="option"
                  aria-selected={isSelected}
                  aria-disabled={option.disabled}
                  className={cn(
                    'relative flex cursor-pointer select-none items-center rounded-sm px-3 py-2 text-sm outline-none',
                    'transition-colors duration-100',
                    isHighlighted && !option.disabled && 'bg-accent text-accent-foreground',
                    isSelected && 'font-medium',
                    option.disabled && 'cursor-not-allowed opacity-50'
                  )}
                  onClick={() => !option.disabled && handleValueChange(option.value)}
                  onMouseEnter={() => !option.disabled && setHighlightedIndex(index)}
                >
                  <span className="flex-1 truncate">{option.label}</span>
                  {option.description && (
                    <span className="ml-2 text-xs text-muted-foreground truncate max-w-[120px]">
                      {option.description}
                    </span>
                  )}
                  {isSelected && (
                    <Check className="ml-2 h-4 w-4 shrink-0" aria-hidden="true" />
                  )}
                </li>
              );
            })
          )}
        </ul>
      )}
      
      {/* Helper Text */}
      {helperText && !error && (
        <p id={helperId} className="mt-1.5 text-xs text-muted-foreground">
          {helperText}
        </p>
      )}
      
      {/* Error Message */}
      {error && (
        <p id={errorId} className="mt-1.5 text-xs text-destructive" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

export type { SelectOption, AccessibleSelectProps };
