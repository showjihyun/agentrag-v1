'use client';

import { useState, useEffect } from 'react';
import { Plus, Search, Filter, MoreVertical, Edit, Play, Copy, Trash, Box, Zap, Code, Layers, ArrowDownToLine, ArrowUpFromLine } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI, Block } from '@/lib/api/agent-builder';
import { useRouter } from 'next/navigation';

export default function BlockLibraryPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('name');
  const [activeTab, setActiveTab] = useState('all');

  useEffect(() => {
    loadBlocks();
  }, []);

  // Reload blocks when returning to this page
  useEffect(() => {
    const handleFocus = () => {
      loadBlocks();
    };
    
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, []);

  const loadBlocks = async () => {
    try {
      setLoading(true);
      const data = await agentBuilderAPI.getBlocks();
      setBlocks(Array.isArray(data) ? data : []);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load blocks',
        variant: 'destructive',
      });
      setBlocks([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBlock = () => {
    router.push('/agent-builder/blocks/new');
  };

  const handleEdit = (blockId: string) => {
    router.push(`/agent-builder/blocks/${blockId}/edit`);
  };

  const handleTest = (blockId: string) => {
    router.push(`/agent-builder/blocks/${blockId}/test`);
  };

  const handleDuplicate = async (blockId: string) => {
    try {
      await agentBuilderAPI.duplicateBlock(blockId);
      toast({
        title: 'Success',
        description: 'Block duplicated successfully',
      });
      loadBlocks();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to duplicate block',
        variant: 'destructive',
      });
    }
  };

  const handleDelete = async (blockId: string) => {
    if (!confirm('Are you sure you want to delete this block?')) return;

    try {
      await agentBuilderAPI.deleteBlock(blockId);
      toast({
        title: 'Success',
        description: 'Block deleted successfully',
      });
      loadBlocks();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete block',
        variant: 'destructive',
      });
    }
  };

  const getBlockIcon = (blockType: string) => {
    switch (blockType) {
      case 'llm':
        return <Zap className="h-5 w-5 text-blue-500" />;
      case 'tool':
        return <Box className="h-5 w-5 text-green-500" />;
      case 'logic':
        return <Code className="h-5 w-5 text-purple-500" />;
      case 'composite':
        return <Layers className="h-5 w-5 text-orange-500" />;
      default:
        return <Box className="h-5 w-5 text-gray-500" />;
    }
  };

  const filteredBlocks = (Array.isArray(blocks) ? blocks : [])
    .filter((block) => {
      if (activeTab !== 'all' && block.block_type !== activeTab) return false;
      if (searchQuery && !block.name.toLowerCase().includes(searchQuery.toLowerCase()) && 
          !block.description?.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'name') return a.name.localeCompare(b.name);
      if (sortBy === 'recent') return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
      return 0;
    });

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Block Library</h1>
          <p className="text-muted-foreground">
            Reusable components for your workflows
          </p>
        </div>
        <Button onClick={handleCreateBlock}>
          <Plus className="mr-2 h-4 w-4" />
          Create Block
        </Button>
      </div>

      {/* Tabs for Categories */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList>
          <TabsTrigger value="all">All Blocks</TabsTrigger>
          <TabsTrigger value="llm">LLM Blocks</TabsTrigger>
          <TabsTrigger value="tool">Tool Blocks</TabsTrigger>
          <TabsTrigger value="logic">Logic Blocks</TabsTrigger>
          <TabsTrigger value="composite">Composite Blocks</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="space-y-4">
          {/* Search and Filter */}
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search blocks..."
                  className="pl-10"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="name">Name (A-Z)</SelectItem>
                <SelectItem value="recent">Recently Updated</SelectItem>
                <SelectItem value="popular">Most Popular</SelectItem>
                <SelectItem value="created_desc">Newest First</SelectItem>
                <SelectItem value="created_asc">Oldest First</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Block Grid */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[...Array(6)].map((_, i) => (
                <Card key={i}>
                  <CardHeader>
                    <Skeleton className="h-6 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-16 w-full" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : filteredBlocks.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Box className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No blocks found</h3>
              <p className="text-sm text-muted-foreground mb-4">
                {searchQuery ? 'Try adjusting your search' : 'Create your first block to get started'}
              </p>
              {!searchQuery && (
                <Button onClick={handleCreateBlock}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Block
                </Button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredBlocks.map((block) => (
                <Card key={block.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        {getBlockIcon(block.block_type)}
                        <div>
                          <CardTitle className="text-base">{block.name}</CardTitle>
                          <CardDescription className="text-xs capitalize">
                            {block.block_type}
                          </CardDescription>
                        </div>
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleEdit(block.id)}>
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleTest(block.id)}>
                            <Play className="mr-2 h-4 w-4" />
                            Test
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleDuplicate(block.id)}>
                            <Copy className="mr-2 h-4 w-4" />
                            Duplicate
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem 
                            onClick={() => handleDelete(block.id)}
                            className="text-destructive"
                          >
                            <Trash className="mr-2 h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {block.description || 'No description provided'}
                    </p>
                    <div className="mt-3 flex items-center gap-2">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Badge variant="outline" className="text-xs">
                              <ArrowDownToLine className="mr-1 h-3 w-3" />
                              {block.input_schema?.properties ? 
                                Object.keys(block.input_schema.properties).length : 0
                              } inputs
                            </Badge>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>Number of input parameters</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                      
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Badge variant="outline" className="text-xs">
                              <ArrowUpFromLine className="mr-1 h-3 w-3" />
                              {block.output_schema?.properties ? 
                                Object.keys(block.output_schema.properties).length : 0
                              } outputs
                            </Badge>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>Number of output parameters</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                  </CardContent>
                  <CardFooter className="flex justify-between text-xs text-muted-foreground">
                    <span>v{block.version || '1.0.0'}</span>
                    <span>{formatDate(block.updated_at)}</span>
                  </CardFooter>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
