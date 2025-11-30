'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Search, TestTube, Key, Globe, BookOpen, FileText, Video } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

interface SearchToolConfig {
  toolType: string;
  query: string;
  maxResults: number;
  apiKey: string;
  // Tavily specific
  searchDepth: string;
  includeAnswer: boolean;
  includeRawContent: boolean;
  includeDomains: string;
  excludeDomains: string;
  // Serper specific
  location: string;
  language: string;
  // YouTube specific
  channelId: string;
  orderBy: string;
  videoDuration: string;
  // Wikipedia specific
  wikiLanguage: string;
  // Arxiv specific
  sortBy: string;
  sortOrder: string;
  categories: string;
}

const SEARCH_TOOLS = [
  { id: 'tavily_search', name: 'Tavily Search', icon: Search, color: 'bg-purple-100 text-purple-600' },
  { id: 'serper_search', name: 'Serper (Google)', icon: Globe, color: 'bg-blue-100 text-blue-600' },
  { id: 'exa_search', name: 'Exa Search', icon: Search, color: 'bg-green-100 text-green-600' },
  { id: 'duckduckgo_search', name: 'DuckDuckGo', icon: Search, color: 'bg-orange-100 text-orange-600' },
  { id: 'wikipedia_search', name: 'Wikipedia', icon: BookOpen, color: 'bg-gray-100 text-gray-600' },
  { id: 'arxiv_search', name: 'Arxiv', icon: FileText, color: 'bg-red-100 text-red-600' },
  { id: 'youtube_search', name: 'YouTube', icon: Video, color: 'bg-red-100 text-red-600' },
  { id: 'bing_search', name: 'Bing Search', icon: Globe, color: 'bg-cyan-100 text-cyan-600' },
  { id: 'google_custom_search', name: 'Google Custom', icon: Globe, color: 'bg-blue-100 text-blue-600' },
];

export default function SearchToolsConfig({ data, onChange, onTest }: ToolConfigProps) {
  const [config, setConfig] = useState<SearchToolConfig>({
    toolType: data.toolType || data.tool_id || 'tavily_search',
    query: data.query || '',
    maxResults: data.maxResults || data.max_results || 10,
    apiKey: data.apiKey || data.api_key || '',
    searchDepth: data.searchDepth || data.search_depth || 'basic',
    includeAnswer: data.includeAnswer ?? data.include_answer ?? true,
    includeRawContent: data.includeRawContent ?? data.include_raw_content ?? false,
    includeDomains: data.includeDomains || data.include_domains || '',
    excludeDomains: data.excludeDomains || data.exclude_domains || '',
    location: data.location || 'us',
    language: data.language || 'en',
    channelId: data.channelId || data.channel_id || '',
    orderBy: data.orderBy || data.order_by || 'relevance',
    videoDuration: data.videoDuration || data.video_duration || 'any',
    wikiLanguage: data.wikiLanguage || data.wiki_language || 'en',
    sortBy: data.sortBy || data.sort_by || 'relevance',
    sortOrder: data.sortOrder || data.sort_order || 'descending',
    categories: data.categories || '',
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: keyof SearchToolConfig, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  const currentTool = SEARCH_TOOLS.find(t => t.id === config.toolType) || SEARCH_TOOLS[0];
  const IconComponent = currentTool.icon;

  const needsApiKey = !['duckduckgo_search', 'wikipedia_search', 'arxiv_search'].includes(config.toolType);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className={`p-2 rounded-lg ${currentTool.color}`}>
          <IconComponent className="h-5 w-5" />
        </div>
        <div>
          <h3 className="font-semibold">{currentTool.name}</h3>
          <p className="text-sm text-muted-foreground">Search the web for information</p>
        </div>
        {!needsApiKey && <Badge variant="secondary" className="ml-auto">No API Key</Badge>}
      </div>

      {/* Search Tool Selection */}
      <div className="space-y-2">
        <Label>Search Provider</Label>
        <Select value={config.toolType} onValueChange={(v) => updateConfig('toolType', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SEARCH_TOOLS.map(tool => (
              <SelectItem key={tool.id} value={tool.id}>
                <div className="flex items-center gap-2">
                  <tool.icon className="h-4 w-4" />
                  {tool.name}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Query */}
      <div className="space-y-2">
        <Label>Search Query</Label>
        <Input
          placeholder="Enter search query or use {{variable}}"
          value={config.query}
          onChange={(e) => updateConfig('query', e.target.value)}
        />
      </div>

      {/* Max Results */}
      <div className="space-y-2">
        <Label>Max Results: {config.maxResults}</Label>
        <Slider
          value={[config.maxResults]}
          onValueChange={([v]) => updateConfig('maxResults', v)}
          min={1}
          max={50}
          step={1}
        />
      </div>

      {/* API Key (if needed) */}
      {needsApiKey && (
        <div className="space-y-2">
          <Label className="flex items-center gap-2">
            <Key className="h-4 w-4" />
            API Key
          </Label>
          <Input
            type="password"
            placeholder={`Enter ${currentTool.name} API key`}
            value={config.apiKey}
            onChange={(e) => updateConfig('apiKey', e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            Or use environment variable via {'{{env.API_KEY}}'}
          </p>
        </div>
      )}

      {/* Tavily Specific Options */}
      {config.toolType === 'tavily_search' && (
        <div className="space-y-4 p-4 bg-muted/50 rounded-lg">
          <h4 className="font-medium text-sm">Tavily Options</h4>
          
          <div className="space-y-2">
            <Label>Search Depth</Label>
            <Select value={config.searchDepth} onValueChange={(v) => updateConfig('searchDepth', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="basic">Basic (Fast)</SelectItem>
                <SelectItem value="advanced">Advanced (Thorough)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center justify-between">
            <Label>Include AI Answer</Label>
            <Switch
              checked={config.includeAnswer}
              onCheckedChange={(v) => updateConfig('includeAnswer', v)}
            />
          </div>

          <div className="flex items-center justify-between">
            <Label>Include Raw Content</Label>
            <Switch
              checked={config.includeRawContent}
              onCheckedChange={(v) => updateConfig('includeRawContent', v)}
            />
          </div>

          <div className="space-y-2">
            <Label>Include Domains (comma-separated)</Label>
            <Input
              placeholder="example.com, docs.example.com"
              value={config.includeDomains}
              onChange={(e) => updateConfig('includeDomains', e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label>Exclude Domains (comma-separated)</Label>
            <Input
              placeholder="spam.com, ads.example.com"
              value={config.excludeDomains}
              onChange={(e) => updateConfig('excludeDomains', e.target.value)}
            />
          </div>
        </div>
      )}

      {/* Serper/Google Specific Options */}
      {(config.toolType === 'serper_search' || config.toolType === 'google_custom_search') && (
        <div className="space-y-4 p-4 bg-muted/50 rounded-lg">
          <h4 className="font-medium text-sm">Google Search Options</h4>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Location</Label>
              <Select value={config.location} onValueChange={(v) => updateConfig('location', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="us">United States</SelectItem>
                  <SelectItem value="kr">South Korea</SelectItem>
                  <SelectItem value="jp">Japan</SelectItem>
                  <SelectItem value="gb">United Kingdom</SelectItem>
                  <SelectItem value="de">Germany</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Language</Label>
              <Select value={config.language} onValueChange={(v) => updateConfig('language', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="ko">Korean</SelectItem>
                  <SelectItem value="ja">Japanese</SelectItem>
                  <SelectItem value="de">German</SelectItem>
                  <SelectItem value="fr">French</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      )}

      {/* YouTube Specific Options */}
      {config.toolType === 'youtube_search' && (
        <div className="space-y-4 p-4 bg-muted/50 rounded-lg">
          <h4 className="font-medium text-sm">YouTube Options</h4>
          
          <div className="space-y-2">
            <Label>Channel ID (optional)</Label>
            <Input
              placeholder="UCxxxxxx"
              value={config.channelId}
              onChange={(e) => updateConfig('channelId', e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Order By</Label>
              <Select value={config.orderBy} onValueChange={(v) => updateConfig('orderBy', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="relevance">Relevance</SelectItem>
                  <SelectItem value="date">Date</SelectItem>
                  <SelectItem value="viewCount">View Count</SelectItem>
                  <SelectItem value="rating">Rating</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Duration</Label>
              <Select value={config.videoDuration} onValueChange={(v) => updateConfig('videoDuration', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="any">Any</SelectItem>
                  <SelectItem value="short">Short (&lt;4 min)</SelectItem>
                  <SelectItem value="medium">Medium (4-20 min)</SelectItem>
                  <SelectItem value="long">Long (&gt;20 min)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      )}

      {/* Wikipedia Specific Options */}
      {config.toolType === 'wikipedia_search' && (
        <div className="space-y-4 p-4 bg-muted/50 rounded-lg">
          <h4 className="font-medium text-sm">Wikipedia Options</h4>
          
          <div className="space-y-2">
            <Label>Language</Label>
            <Select value={config.wikiLanguage} onValueChange={(v) => updateConfig('wikiLanguage', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en">English</SelectItem>
                <SelectItem value="ko">Korean</SelectItem>
                <SelectItem value="ja">Japanese</SelectItem>
                <SelectItem value="de">German</SelectItem>
                <SelectItem value="fr">French</SelectItem>
                <SelectItem value="zh">Chinese</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      )}

      {/* Arxiv Specific Options */}
      {config.toolType === 'arxiv_search' && (
        <div className="space-y-4 p-4 bg-muted/50 rounded-lg">
          <h4 className="font-medium text-sm">Arxiv Options</h4>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Sort By</Label>
              <Select value={config.sortBy} onValueChange={(v) => updateConfig('sortBy', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="relevance">Relevance</SelectItem>
                  <SelectItem value="lastUpdatedDate">Last Updated</SelectItem>
                  <SelectItem value="submittedDate">Submitted Date</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Sort Order</Label>
              <Select value={config.sortOrder} onValueChange={(v) => updateConfig('sortOrder', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="descending">Descending</SelectItem>
                  <SelectItem value="ascending">Ascending</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Categories (comma-separated)</Label>
            <Input
              placeholder="cs.AI, cs.LG, stat.ML"
              value={config.categories}
              onChange={(e) => updateConfig('categories', e.target.value)}
            />
          </div>
        </div>
      )}

      {/* Test Button */}
      {onTest && (
        <Button 
          onClick={onTest} 
          variant="outline" 
          className="w-full"
          disabled={!config.query}
        >
          <TestTube className="h-4 w-4 mr-2" />
          Test Search
        </Button>
      )}
    </div>
  );
}
