'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Filter, X } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface WorkflowFilters {
  nodeTypes: string[];
  triggerTypes: string[];
  complexity: 'all' | 'simple' | 'medium' | 'complex';
  tags: string[];
  hasErrors: boolean;
}

interface AdvancedWorkflowFiltersProps {
  filters: WorkflowFilters;
  onFiltersChange: (filters: WorkflowFilters) => void;
  availableTags?: string[];
}

const nodeTypeOptions = [
  { value: 'agent', label: 'Agent Nodes' },
  { value: 'block', label: 'Block Nodes' },
  { value: 'control', label: 'Control Nodes' },
  { value: 'trigger', label: 'Trigger Nodes' },
];

const triggerTypeOptions = [
  { value: 'webhook', label: 'Webhook' },
  { value: 'schedule', label: 'Schedule' },
  { value: 'manual', label: 'Manual' },
  { value: 'api', label: 'API' },
];

const complexityOptions = [
  { value: 'all', label: 'All' },
  { value: 'simple', label: 'Simple (<5 nodes)' },
  { value: 'medium', label: 'Medium (5-10 nodes)' },
  { value: 'complex', label: 'Complex (>10 nodes)' },
];

export const AdvancedWorkflowFilters = ({
  filters,
  onFiltersChange,
  availableTags = [],
}: AdvancedWorkflowFiltersProps) => {
  const [isOpen, setIsOpen] = useState(false);

  const activeFiltersCount = 
    filters.nodeTypes.length +
    filters.triggerTypes.length +
    (filters.complexity !== 'all' ? 1 : 0) +
    filters.tags.length +
    (filters.hasErrors ? 1 : 0);

  const toggleNodeType = (type: string) => {
    const newTypes = filters.nodeTypes.includes(type)
      ? filters.nodeTypes.filter((t) => t !== type)
      : [...filters.nodeTypes, type];
    onFiltersChange({ ...filters, nodeTypes: newTypes });
  };

  const toggleTriggerType = (type: string) => {
    const newTypes = filters.triggerTypes.includes(type)
      ? filters.triggerTypes.filter(t => t !== type)
      : [...filters.triggerTypes, type];
    onFiltersChange({ ...filters, triggerTypes: newTypes });
  };
  const toggleTag = (tag: string) => {
    const newTags = filters.tags.includes(tag)
      ? filters.tags.filter(t => t !== tag)
      : [...filters.tags, tag];
    onFiltersChange({ ...filters, tags: newTags });
  };

  const clearAllFilters = () => {
    onFiltersChange({
      nodeTypes: [],
      triggerTypes: [],
      complexity: 'all',
      tags: [],
      hasErrors: false,
    });
  };

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" className="relative">
          <Filter className="h-4 w-4 mr-2" />
          Filters
          {activeFiltersCount > 0 && (
            <Badge
              variant="secondary"
              className="ml-2 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
            >
              {activeFiltersCount}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80" align="start">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-medium">Advanced Filters</h4>
            {activeFiltersCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearAllFilters}
                className="h-auto p-1 text-xs"
              >
                Clear all
              </Button>
            )}
          </div>

          {/* Node Types */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Node Types</Label>
            <div className="grid grid-cols-2 gap-2">
              {nodeTypeOptions.map((option) => (
                <div key={option.value} className="flex items-center space-x-2">
                  <Checkbox
                    id={`node-${option.value}`}
                    checked={filters.nodeTypes.includes(option.value)}
                    onCheckedChange={() => toggleNodeType(option.value)}
                  />
                  <Label
                    htmlFor={`node-${option.value}`}
                    className="text-sm cursor-pointer"
                  >
                    {option.label}
                  </Label>
                </div>
              ))}
            </div>
          </div>

          <Separator />

          {/* Trigger Types */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Trigger Types</Label>
            <div className="grid grid-cols-2 gap-2">
              {triggerTypeOptions.map((option) => (
                <div key={option.value} className="flex items-center space-x-2">
                  <Checkbox
                    id={`trigger-${option.value}`}
                    checked={filters.triggerTypes.includes(option.value)}
                    onCheckedChange={() => toggleTriggerType(option.value)}
                  />
                  <Label
                    htmlFor={`trigger-${option.value}`}
                    className="text-sm cursor-pointer"
                  >
                    {option.label}
                  </Label>
                </div>
              ))}
            </div>
          </div>

          <Separator />

          {/* Complexity */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Complexity</Label>
            <div className="space-y-1">
              {complexityOptions.map((option) => (
                <div key={option.value} className="flex items-center space-x-2">
                  <Checkbox
                    id={`complexity-${option.value}`}
                    checked={filters.complexity === option.value}
                    onCheckedChange={() =>
                      onFiltersChange({
                        ...filters,
                        complexity: option.value as WorkflowFilters['complexity'],
                      })
                    }
                  />
                  <Label
                    htmlFor={`complexity-${option.value}`}
                    className="text-sm cursor-pointer"
                  >
                    {option.label}
                  </Label>
                </div>
              ))}
            </div>
          </div>

          {/* Tags */}
          {availableTags.length > 0 && (
            <>
              <Separator />
              <div className="space-y-2">
                <Label className="text-sm font-medium">Tags</Label>
                <div className="flex flex-wrap gap-1">
                  {availableTags.map((tag) => (
                    <Badge
                      key={tag}
                      variant={filters.tags.includes(tag) ? "default" : "outline"}
                      className={cn(
                        "cursor-pointer text-xs",
                        filters.tags.includes(tag) && "bg-primary text-primary-foreground"
                      )}
                      onClick={() => toggleTag(tag)}
                    >
                      {tag}
                      {filters.tags.includes(tag) && (
                        <X className="h-3 w-3 ml-1" />
                      )}
                    </Badge>
                  ))}
                </div>
              </div>
            </>
          )}

          <Separator />

          {/* Error Filter */}
          <div className="flex items-center space-x-2">
            <Checkbox
              id="has-errors"
              checked={filters.hasErrors}
              onCheckedChange={(checked) =>
                onFiltersChange({ ...filters, hasErrors: !!checked })
              }
            />
            <Label htmlFor="has-errors" className="text-sm cursor-pointer">
              Show only workflows with errors
            </Label>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
};