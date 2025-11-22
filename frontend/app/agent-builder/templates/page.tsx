'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { Plus, Search, Sparkles, Download, Eye, Zap } from 'lucide-react';

interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  blocks: any[];
  edges: any[];
  variables: any[];
  metadata: {
    author?: string;
    tags?: string[];
    usageCount?: number;
    rating?: number;
  };
  created_at: string;
  updated_at: string;
}

const categoryColors: Record<string, string> = {
  'data-processing': 'bg-blue-100 text-blue-700',
  'automation': 'bg-green-100 text-green-700',
  'ai-agents': 'bg-purple-100 text-purple-700',
  'integration': 'bg-orange-100 text-orange-700',
  'analytics': 'bg-indigo-100 text-indigo-700',
  'communication': 'bg-pink-100 text-pink-700',
  'productivity': 'bg-yellow-100 text-yellow-700',
  'development': 'bg-cyan-100 text-cyan-700',
};

export default function TemplatesPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);

  useEffect(() => {
    loadTemplates();
  }, [selectedCategory]);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams();
      if (selectedCategory) {
        params.append('category', selectedCategory);
      }
      
      const response = await fetch(`/api/agent-builder/templates?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (!response.ok) throw new Error('Failed to load templates');
      
      const data = await response.json();
      setTemplates(data.templates || []);
    } catch (error: any) {
      console.error('Failed to load templates:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to load templates',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const instantiateTemplate = async (templateId: string, templateName: string) => {
    try {
      toast({
        title: '⚡ Creating Workflow',
        description: `Creating workflow from template: ${templateName}`,
      });

      const response = await fetch(`/api/agent-builder/templates/${templateId}/instantiate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          workflow_name: `${templateName} (Copy)`,
          variable_values: {},
        }),
      });

      if (!response.ok) throw new Error('Failed to create workflow');

      const workflow = await response.json();

      toast({
        title: '✅ Workflow Created',
        description: `Successfully created workflow from template`,
      });

      // Navigate to the new workflow
      router.push(`/agent-builder/workflows/${workflow.id}`);

    } catch (error: any) {
      console.error('Failed to instantiate template:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to create workflow from template',
        variant: 'destructive',
      });
    }
  };

  const categories = Array.from(new Set(templates.map(t => t.category)));

  const filteredTemplates = templates.filter(template =>
    template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    template.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    template.metadata.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Sparkles className="h-8 w-8 text-purple-600" />
            Workflow Templates
          </h1>
          <p className="text-muted-foreground mt-1">
            Start with pre-built templates or create your own
          </p>
        </div>
        <Button onClick={() => router.push('/agent-builder/workflows/new')}>
          <Plus className="mr-2 h-4 w-4" />
          Create from Scratch
        </Button>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          <Button
            variant={selectedCategory === null ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedCategory(null)}
          >
            All
          </Button>
          {categories.map(category => (
            <Button
              key={category}
              variant={selectedCategory === category ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedCategory(category)}
              className="capitalize"
            >
              {category.replace('-', ' ')}
            </Button>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Templates</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{templates.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Categories</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{categories.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Installs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {templates.reduce((sum, t) => sum + (t.metadata.usageCount || 0), 0)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Avg Rating</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {templates.length > 0
                ? (templates.reduce((sum, t) => sum + (t.metadata.rating || 0), 0) / templates.length).toFixed(1)
                : '0.0'}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Templates Grid */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading templates...</p>
        </div>
      ) : filteredTemplates.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Sparkles className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No templates found</h3>
            <p className="text-muted-foreground mb-4">
              {searchQuery ? 'Try a different search term' : 'No templates available yet'}
            </p>
            <Button onClick={() => router.push('/agent-builder/workflows/new')}>
              <Plus className="mr-2 h-4 w-4" />
              Create Your First Template
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTemplates.map((template) => {
            const colorClass = categoryColors[template.category] || 'bg-gray-100 text-gray-700';
            
            return (
              <Card key={template.id} className="hover:shadow-lg transition-shadow cursor-pointer group">
                <CardHeader>
                  <div className="flex items-start justify-between mb-2">
                    <Badge className={`${colorClass} capitalize`}>
                      {template.category.replace('-', ' ')}
                    </Badge>
                    {template.metadata.rating && (
                      <div className="flex items-center gap-1 text-sm">
                        <span className="text-yellow-500">★</span>
                        <span className="font-medium">{template.metadata.rating.toFixed(1)}</span>
                      </div>
                    )}
                  </div>
                  <CardTitle className="text-lg group-hover:text-primary transition-colors">
                    {template.name}
                  </CardTitle>
                  <CardDescription className="line-clamp-2">
                    {template.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Stats */}
                    <div className="flex items-center justify-between text-sm text-muted-foreground">
                      <div className="flex items-center gap-4">
                        <span>{template.blocks.length} blocks</span>
                        <span>{template.edges.length} connections</span>
                      </div>
                      {template.metadata.usageCount && (
                        <span className="flex items-center gap-1">
                          <Download className="h-3 w-3" />
                          {template.metadata.usageCount}
                        </span>
                      )}
                    </div>

                    {/* Tags */}
                    {template.metadata.tags && template.metadata.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {template.metadata.tags.slice(0, 3).map((tag, idx) => (
                          <Badge key={idx} variant="secondary" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                        {template.metadata.tags.length > 3 && (
                          <Badge variant="secondary" className="text-xs">
                            +{template.metadata.tags.length - 3}
                          </Badge>
                        )}
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-2 pt-2">
                      <Button
                        className="flex-1"
                        onClick={() => instantiateTemplate(template.id, template.name)}
                      >
                        <Zap className="mr-2 h-4 w-4" />
                        Use Template
                      </Button>
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => setSelectedTemplate(template)}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Template Detail Modal */}
      {selectedTemplate && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedTemplate(null)}
        >
          <Card
            className="max-w-2xl w-full max-h-[80vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <Badge className={`${categoryColors[selectedTemplate.category]} capitalize mb-2`}>
                    {selectedTemplate.category.replace('-', ' ')}
                  </Badge>
                  <CardTitle className="text-2xl">{selectedTemplate.name}</CardTitle>
                  <CardDescription className="mt-2">
                    {selectedTemplate.description}
                  </CardDescription>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setSelectedTemplate(null)}
                >
                  ✕
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Metadata */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">Blocks</div>
                  <div className="text-lg font-semibold">{selectedTemplate.blocks.length}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Connections</div>
                  <div className="text-lg font-semibold">{selectedTemplate.edges.length}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Variables</div>
                  <div className="text-lg font-semibold">{selectedTemplate.variables.length}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Installs</div>
                  <div className="text-lg font-semibold">{selectedTemplate.metadata.usageCount || 0}</div>
                </div>
              </div>

              {/* Tags */}
              {selectedTemplate.metadata.tags && selectedTemplate.metadata.tags.length > 0 && (
                <div>
                  <div className="text-sm font-medium mb-2">Tags</div>
                  <div className="flex flex-wrap gap-2">
                    {selectedTemplate.metadata.tags.map((tag, idx) => (
                      <Badge key={idx} variant="secondary">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Author */}
              {selectedTemplate.metadata.author && (
                <div>
                  <div className="text-sm text-muted-foreground">Author</div>
                  <div className="font-medium">{selectedTemplate.metadata.author}</div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2 pt-4">
                <Button
                  className="flex-1"
                  onClick={() => {
                    instantiateTemplate(selectedTemplate.id, selectedTemplate.name);
                    setSelectedTemplate(null);
                  }}
                >
                  <Zap className="mr-2 h-4 w-4" />
                  Use This Template
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setSelectedTemplate(null)}
                >
                  Close
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
