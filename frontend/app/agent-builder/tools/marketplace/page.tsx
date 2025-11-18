'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Search,
  Star,
  Download,
  Settings,
  CheckCircle,
  Globe,
  Database,
  Code,
  Bot,
  Calculator,
  Zap
} from 'lucide-react';
import { toast } from 'sonner';

const CATEGORY_ICONS: Record<string, any> = {
  search: Search,
  api: Globe,
  data: Database,
  code: Code,
  ai: Bot,
  utility: Calculator,
};

export default function ToolMarketplacePage() {
  const router = useRouter();
  const [tools, setTools] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState('downloads');

  useEffect(() => {
    fetchTools();
    fetchCategories();
  }, [selectedCategory, sortBy]);

  const fetchTools = async () => {
    try {
      const params = new URLSearchParams();
      if (selectedCategory) params.append('category', selectedCategory);
      if (searchQuery) params.append('search', searchQuery);
      params.append('sort_by', sortBy);

      const response = await fetch(`/api/agent-builder/marketplace?${params}`);
      if (!response.ok) throw new Error('Failed to fetch tools');

      const data = await response.json();
      setTools(data);
    } catch (error: any) {
      toast.error(error.message || 'Failed to load tools');
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await fetch('/api/agent-builder/marketplace/categories');
      if (!response.ok) throw new Error('Failed to fetch categories');

      const data = await response.json();
      setCategories(data);
    } catch (error) {
      console.error('Failed to load categories:', error);
    }
  };

  const handleSearch = () => {
    fetchTools();
  };

  const handleInstall = async (toolId: string) => {
    try {
      const response = await fetch(`/api/agent-builder/marketplace/${toolId}/install`, {
        method: 'POST',
      });

      if (!response.ok) throw new Error('Failed to install tool');

      toast.success('Tool installed successfully!');
      fetchTools(); // Refresh list
    } catch (error: any) {
      toast.error(error.message || 'Failed to install tool');
    }
  };

  const handleConfigure = (toolId: string) => {
    router.push(`/agent-builder/tools/configure/${toolId}`);
  };

  if (loading) {
    return (
      <div className="container mx-auto py-8">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Tool Marketplace</h1>
        <p className="text-muted-foreground">
          Browse and install 400+ tools for your agents
        </p>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1 flex gap-2">
          <Input
            placeholder="Search tools..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            className="flex-1"
          />
          <Button onClick={handleSearch}>
            <Search className="h-4 w-4" />
          </Button>
        </div>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="px-3 py-2 border rounded-md"
        >
          <option value="downloads">Most Downloaded</option>
          <option value="rating">Highest Rated</option>
          <option value="name">Name (A-Z)</option>
        </select>
      </div>

      {/* Categories */}
      <div className="flex flex-wrap gap-2">
        <Button
          variant={selectedCategory === null ? 'default' : 'outline'}
          size="sm"
          onClick={() => setSelectedCategory(null)}
        >
          All Tools
        </Button>
        {categories.map((category) => {
          const Icon = CATEGORY_ICONS[category.id] || Zap;
          return (
            <Button
              key={category.id}
              variant={selectedCategory === category.id ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedCategory(category.id)}
            >
              <Icon className="h-3 w-3 mr-2" />
              {category.name} ({category.tool_count})
            </Button>
          );
        })}
      </div>

      {/* Tools Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {tools.map((tool) => {
          const Icon = CATEGORY_ICONS[tool.category] || Zap;
          return (
            <Card key={tool.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Icon className="h-5 w-5 text-primary" />
                    <div>
                      <CardTitle className="text-lg">{tool.name}</CardTitle>
                      <CardDescription className="text-xs">
                        v{tool.version} by {tool.author}
                      </CardDescription>
                    </div>
                  </div>
                  {tool.is_installed && (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  )}
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {tool.description}
                </p>

                {/* Stats */}
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                    {tool.rating.toFixed(1)}
                  </div>
                  <div className="flex items-center gap-1">
                    <Download className="h-3 w-3" />
                    {tool.downloads.toLocaleString()}
                  </div>
                </div>

                {/* Tags */}
                <div className="flex flex-wrap gap-1">
                  {tool.tags.slice(0, 3).map((tag: string) => (
                    <Badge key={tag} variant="secondary" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  {tool.is_installed ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleConfigure(tool.id)}
                      className="flex-1"
                    >
                      <Settings className="h-3 w-3 mr-2" />
                      Configure
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      onClick={() => handleInstall(tool.id)}
                      className="flex-1"
                    >
                      <Download className="h-3 w-3 mr-2" />
                      Install
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => router.push(`/agent-builder/tools/details/${tool.id}`)}
                  >
                    Details
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {tools.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No tools found</p>
        </div>
      )}
    </div>
  );
}
