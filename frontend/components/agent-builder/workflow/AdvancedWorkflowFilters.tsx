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

  const toggleTriggerT