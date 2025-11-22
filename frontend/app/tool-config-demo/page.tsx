"use client";

/**
 * Tool Config Demo Page
 * 
 * 50+ Tools의 상세한 Config UI 데모
 * 각 Tool별로 맞춤형 Select Box와 입력 필드 테스트
 */

import React, { useState } from 'react';
import { 
  TOOL_CONFIG_REGISTRY, 
  getAllCategories, 
  getToolsByCategory,
  AdvancedToolConfigUI 
} from '@/components/agent-builder/tool-configs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Search, Settings, CheckCircle2 } from 'lucide-react';

export default function ToolConfigDemoPage() {
  const [selectedTool, setSelectedTool] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [savedConfigs, setSavedConfigs] = useState<Record<string, any>>({});

  const categories = getAllCategories();
  const allTools = Object.values(TOOL_CONFIG_REGISTRY);

  // Filter tools
  const filteredTools = allTools.filter(tool => {
    const matchesSearch = 
      tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || tool.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleSave = (toolId: string, config: Record<string, any>, credentials: Record<string, any>) => {
    setSavedConfigs(prev => ({
      ...prev,
      [toolId]: { config, credentials, timestamp: new Date().toISOString() }
    }));
    setSelectedTool(null);
    console.log('Saved config for', toolId, { config, credentials });
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      ai: 'bg-purple-100 text-purple-800',
      search: 'bg-blue-100 text-blue-800',
      communication: 'bg-green-100 text-green-800',
      developer: 'bg-orange-100 text-orange-800',
      productivity: 'bg-yellow-100 text-yellow-800',
      data: 'bg-cyan-100 text-cyan-800',
      code: 'bg-indigo-100 text-indigo-800',
      file: 'bg-gray-100 text-gray-800',
      image: 'bg-pink-100 text-pink-800',
      utility: 'bg-teal-100 text-teal-800',
      crm: 'bg-red-100 text-red-800',
      marketing: 'bg-amber-100 text-amber-800',
      analytics: 'bg-lime-100 text-lime-800',
      storage: 'bg-sky-100 text-sky-800',
      webhook: 'bg-violet-100 text-violet-800',
      control: 'bg-fuchsia-100 text-fuchsia-800',
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Tool Configuration Gallery
          </h1>
          <p className="text-lg text-gray-600">
            50+ Tools with Advanced Config UI • Select Boxes • Real-time Validation
          </p>
          <div className="flex items-center justify-center gap-4 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <Settings className="w-4 h-4" />
              {allTools.length} Tools
            </span>
            <span className="flex items-center gap-1">
              <CheckCircle2 className="w-4 h-4" />
              {Object.keys(savedConfigs).length} Configured
            </span>
          </div>
        </div>

        {/* Search and Filter */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row gap-4">
              {/* Search */}
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  placeholder="Search tools..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>

              {/* Category Filter */}
              <div className="flex flex-wrap gap-2">
                <Badge
                  variant={selectedCategory === 'all' ? 'default' : 'outline'}
                  className="cursor-pointer"
                  onClick={() => setSelectedCategory('all')}
                >
                  All ({allTools.length})
                </Badge>
                {categories.map(category => {
                  const count = getToolsByCategory(category).length;
                  return (
                    <Badge
                      key={category}
                      variant={selectedCategory === category ? 'default' : 'outline'}
                      className={`cursor-pointer ${selectedCategory === category ? '' : getCategoryColor(category)}`}
                      onClick={() => setSelectedCategory(category)}
                    >
                      {category} ({count})
                    </Badge>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tools Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTools.map(tool => (
            <Card
              key={tool.id}
              className="hover:shadow-lg transition-all cursor-pointer group"
              onClick={() => setSelectedTool(tool.id)}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div 
                    className="w-12 h-12 rounded-lg flex items-center justify-center text-2xl group-hover:scale-110 transition-transform"
                    style={{ backgroundColor: tool.bg_color }}
                  >
                    {tool.icon}
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <Badge className={getCategoryColor(tool.category)}>
                      {tool.category}
                    </Badge>
                    {savedConfigs[tool.id] && (
                      <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                        <CheckCircle2 className="w-3 h-3 mr-1" />
                        Configured
                      </Badge>
                    )}
                  </div>
                </div>
                <CardTitle className="text-lg">{tool.name}</CardTitle>
                <CardDescription className="line-clamp-2">
                  {tool.description}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-xs text-gray-500">
                  <div className="flex items-center justify-between">
                    <span>Parameters:</span>
                    <span className="font-medium">{Object.keys(tool.params).length}</span>
                  </div>
                  {tool.credentials && (
                    <div className="flex items-center justify-between">
                      <span>Credentials:</span>
                      <span className="font-medium">{Object.keys(tool.credentials).length}</span>
                    </div>
                  )}
                  {tool.examples && (
                    <div className="flex items-center justify-between">
                      <span>Examples:</span>
                      <span className="font-medium">{tool.examples.length}</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredTools.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center text-gray-500">
              No tools found matching your search criteria
            </CardContent>
          </Card>
        )}

        {/* Tool Config Modal */}
        {selectedTool && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
            <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] overflow-y-auto">
              <AdvancedToolConfigUI
                toolId={selectedTool}
                initialConfig={savedConfigs[selectedTool]?.config || {}}
                initialCredentials={savedConfigs[selectedTool]?.credentials || {}}
                onSave={(config, credentials) => handleSave(selectedTool, config, credentials)}
                onCancel={() => setSelectedTool(null)}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
