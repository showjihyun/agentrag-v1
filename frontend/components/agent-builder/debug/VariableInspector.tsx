'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Search, ChevronRight, ChevronDown } from 'lucide-react';

interface Variable {
  name: string;
  value: any;
  type: string;
  scope: 'global' | 'local' | 'agent';
}

interface VariableInspectorProps {
  variables: Variable[];
  onVariableChange?: (name: string, value: any) => void;
}

export function VariableInspector({ variables, onVariableChange }: VariableInspectorProps) {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [expandedVars, setExpandedVars] = React.useState<Set<string>>(new Set());

  const filteredVariables = React.useMemo(() => {
    if (!searchQuery) return variables;
    
    return variables.filter((v) =>
      v.name.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [variables, searchQuery]);

  const toggleExpand = (name: string) => {
    setExpandedVars((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  const renderValue = (value: any, depth: number = 0): React.ReactNode => {
    if (value === null) return <span className="text-muted-foreground">null</span>;
    if (value === undefined) return <span className="text-muted-foreground">undefined</span>;
    
    const type = typeof value;
    
    if (type === 'string') {
      return <span className="text-green-600 dark:text-green-400">"{value}"</span>;
    }
    
    if (type === 'number' || type === 'boolean') {
      return <span className="text-blue-600 dark:text-blue-400">{String(value)}</span>;
    }
    
    if (Array.isArray(value)) {
      return (
        <span className="text-muted-foreground">
          Array({value.length})
        </span>
      );
    }
    
    if (type === 'object') {
      return (
        <span className="text-muted-foreground">
          Object({Object.keys(value).length})
        </span>
      );
    }
    
    return String(value);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Variable Inspector</CardTitle>
        <CardDescription>
          View and inspect execution variables
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search variables..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8"
          />
        </div>

        {/* Variables List */}
        <ScrollArea className="h-[400px] w-full rounded-md border">
          <div className="p-4 space-y-2">
            {filteredVariables.length === 0 ? (
              <div className="text-center text-sm text-muted-foreground py-8">
                No variables found
              </div>
            ) : (
              filteredVariables.map((variable) => {
                const isExpanded = expandedVars.has(variable.name);
                const isComplex = typeof variable.value === 'object' && variable.value !== null;

                return (
                  <div
                    key={variable.name}
                    className="border rounded-lg p-3 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 flex-1">
                        {isComplex && (
                          <button
                            onClick={() => toggleExpand(variable.name)}
                            className="hover:bg-accent rounded p-0.5"
                          >
                            {isExpanded ? (
                              <ChevronDown className="h-4 w-4" />
                            ) : (
                              <ChevronRight className="h-4 w-4" />
                            )}
                          </button>
                        )}
                        <span className="font-mono text-sm font-semibold">
                          {variable.name}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {variable.type}
                        </Badge>
                        <Badge variant="secondary" className="text-xs">
                          {variable.scope}
                        </Badge>
                      </div>
                    </div>

                    <div className="font-mono text-sm pl-6">
                      {isExpanded && isComplex ? (
                        <pre className="text-xs overflow-x-auto">
                          {JSON.stringify(variable.value, null, 2)}
                        </pre>
                      ) : (
                        renderValue(variable.value)
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </ScrollArea>

        {/* Summary */}
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>{filteredVariables.length} variable(s)</span>
          <span>
            {filteredVariables.filter((v) => v.scope === 'global').length} global,{' '}
            {filteredVariables.filter((v) => v.scope === 'local').length} local
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
