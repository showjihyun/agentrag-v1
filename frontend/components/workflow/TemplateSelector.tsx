'use client';

import React, { useState } from 'react';
import { Search, FileText } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { getAllTemplates, instantiateTemplate, WorkflowTemplate } from '@/lib/workflow-templates';
import { cn } from '@/lib/utils';

interface TemplateSelectorProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelectTemplate: (nodes: any[], edges: any[]) => void;
}

export function TemplateSelector({ open, onOpenChange, onSelectTemplate }: TemplateSelectorProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const templates = getAllTemplates();

  // Filter templates
  const filteredTemplates = templates.filter((template) => {
    const matchesSearch =
      searchQuery === '' ||
      template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.description.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesCategory = !selectedCategory || template.category === selectedCategory;

    return matchesSearch && matchesCategory;
  });

  // Get unique categories
  const categories = Array.from(new Set(templates.map((t) => t.category)));

  const handleSelectTemplate = (templateId: string) => {
    const result = instantiateTemplate(templateId);
    if (result) {
      onSelectTemplate(result.nodes, result.edges);
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Choose a Template</DialogTitle>
          <DialogDescription>
            Start with a pre-built workflow template or create from scratch
          </DialogDescription>
        </DialogHeader>

        {/* Search and Filter */}
        <div className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search templates..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Category Filter */}
          <div className="flex gap-2 flex-wrap">
            <Button
              variant={selectedCategory === null ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedCategory(null)}
            >
              All
            </Button>
            {categories.map((category) => (
              <Button
                key={category}
                variant={selectedCategory === category ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedCategory(category)}
              >
                {category}
              </Button>
            ))}
          </div>
        </div>

        {/* Templates Grid */}
        <ScrollArea className="h-[400px] pr-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Blank Template */}
            <button
              onClick={() => {
                onSelectTemplate([], []);
                onOpenChange(false);
              }}
              className={cn(
                'text-left p-4 rounded-lg border-2 border-dashed transition-all',
                'hover:border-primary hover:bg-accent',
                'focus:outline-none focus:ring-2 focus:ring-primary'
              )}
            >
              <div className="flex items-start gap-3">
                <div className="text-3xl">📄</div>
                <div className="flex-1">
                  <h3 className="font-semibold mb-1">Blank Workflow</h3>
                  <p className="text-sm text-muted-foreground">
                    Start from scratch with an empty canvas
                  </p>
                  <Badge variant="outline" className="mt-2">
                    Basic
                  </Badge>
                </div>
              </div>
            </button>

            {/* Template Cards */}
            {filteredTemplates.map((template) => (
              <button
                key={template.id}
                onClick={() => handleSelectTemplate(template.id)}
                className={cn(
                  'text-left p-4 rounded-lg border-2 transition-all',
                  'hover:border-primary hover:bg-accent',
                  'focus:outline-none focus:ring-2 focus:ring-primary'
                )}
              >
                <div className="flex items-start gap-3">
                  <div className="text-3xl">{template.icon}</div>
                  <div className="flex-1">
                    <h3 className="font-semibold mb-1">{template.name}</h3>
                    <p className="text-sm text-muted-foreground mb-2">
                      {template.description}
                    </p>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{template.category}</Badge>
                      <span className="text-xs text-muted-foreground">
                        {template.nodes.length} nodes
                      </span>
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>

          {filteredTemplates.length === 0 && (
            <div className="text-center py-12 text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No templates found</p>
              <p className="text-sm mt-2">Try a different search term or category</p>
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
