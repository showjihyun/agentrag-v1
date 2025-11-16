'use client';

import { useState, useEffect } from 'react';
import { Plus, Database, MoreVertical, Edit, Trash, Upload, Search as SearchIcon, History, FileText, Download, Copy, Grid, List, Filter, CheckSquare, Square } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Skeleton } from '@/components/ui/skeleton';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI, Knowledgebase, KnowledgebaseCreate } from '@/lib/api/agent-builder';
import { useRouter } from 'next/navigation';

export default function KnowledgebaseManagerPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [knowledgebases, setKnowledgebases] = useState<Knowledgebase[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editingKb, setEditingKb] = useState<Knowledgebase | null>(null);
  const [formData, setFormData] = useState<KnowledgebaseCreate>({
    name: '',
    description: '',
    embedding_model: 'text-embedding-3-small',
    chunk_size: 500,
    chunk_overlap: 50,
  });
  const [saving, setSaving] = useState(false);
  
  // 1. Search functionality
  const [searchQuery, setSearchQuery] = useState('');
  
  // 2. Sort functionality
  const [sortBy, setSortBy] = useState<'name' | 'created' | 'size' | 'documents'>('created');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  
  // 3. Filter functionality
  const [filterModel, setFilterModel] = useState<string>('all');
  
  // 4. Bulk operations
  const [selectedKbs, setSelectedKbs] = useState<Set<string>>(new Set());
  
  // 5. View mode
  const [viewMode, setViewMode] = useState<'table' | 'grid'>('table');

  useEffect(() => {
    loadKnowledgebases();
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+N or Cmd+N to create new KB
      if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        handleCreate();
      }
      // Escape to close dialog
      if (e.key === 'Escape' && createDialogOpen) {
        setCreateDialogOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [createDialogOpen]);

  const loadKnowledgebases = async () => {
    try {
      setLoading(true);
      const data = await agentBuilderAPI.getKnowledgebases();
      setKnowledgebases(data);
    } catch (error: any) {
      console.error('Failed to load knowledgebases:', error);
      toast({
        title: 'Failed to Load Knowledgebases',
        description: error.message || 'Please check your connection and try again',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingKb(null);
    setFormData({
      name: '',
      description: '',
      embedding_model: 'text-embedding-3-small',
      chunk_size: 500,
      chunk_overlap: 50,
    });
    setCreateDialogOpen(true);
  };

  const handleEdit = (kb: Knowledgebase) => {
    setEditingKb(kb);
    setFormData({
      name: kb.name,
      description: kb.description || '',
      embedding_model: kb.embedding_model,
    });
    setCreateDialogOpen(true);
  };

  const handleSave = async () => {
    // Validation
    if (!formData.name.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Please enter a knowledgebase name',
      });
      return;
    }

    if (!editingKb && (formData.chunk_size || 0) < 100) {
      toast({
        title: 'Validation Error',
        description: 'Chunk size must be at least 100 characters',
      });
      return;
    }

    try {
      setSaving(true);
      
      if (editingKb) {
        await agentBuilderAPI.updateKnowledgebase(editingKb.id, {
          name: formData.name,
          description: formData.description,
          embedding_model: formData.embedding_model,
        });
        
        const modelChanged = editingKb.embedding_model !== formData.embedding_model;
        toast({
          title: '✅ Updated Successfully',
          description: modelChanged 
            ? `"${formData.name}" has been updated. Documents will be re-embedded with the new model.`
            : `"${formData.name}" has been updated`,
        });
      } else {
        await agentBuilderAPI.createKnowledgebase(formData);
        toast({
          title: '✅ Created Successfully',
          description: `"${formData.name}" is ready for documents`,
        });
      }
      
      setCreateDialogOpen(false);
      loadKnowledgebases();
    } catch (error: any) {
      console.error('Save error:', error);
      const action = editingKb ? 'update' : 'create';
      toast({
        title: `Failed to ${action} knowledgebase`,
        description: error.message || `Please try again or contact support if the issue persists`,
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (kbId: string) => {
    const kb = knowledgebases.find(k => k.id === kbId);
    const kbName = kb?.name || 'this knowledgebase';
    const docCount = kb?.document_count || 0;
    
    const confirmMessage = docCount > 0
      ? `Are you sure you want to delete "${kbName}"?\n\nThis will permanently delete ${docCount} document${docCount !== 1 ? 's' : ''} and cannot be undone.`
      : `Are you sure you want to delete "${kbName}"?\n\nThis action cannot be undone.`;
    
    if (!confirm(confirmMessage)) {
      return;
    }

    try {
      await agentBuilderAPI.deleteKnowledgebase(kbId);
      toast({
        title: '🗑️ Deleted Successfully',
        description: `"${kbName}" has been permanently deleted`,
      });
      loadKnowledgebases();
    } catch (error: any) {
      console.error('Delete error:', error);
      toast({
        title: 'Failed to Delete',
        description: error.message || 'The knowledgebase may be in use. Please try again later.',
      });
    }
  };

  const handleUploadDocuments = (kbId: string) => {
    router.push(`/agent-builder/knowledgebases/${kbId}/upload`);
  };

  const handleSearch = (kbId: string) => {
    router.push(`/agent-builder/knowledgebases/${kbId}/search`);
  };

  const handleViewVersions = async (kbId: string) => {
    try {
      const versions = await agentBuilderAPI.getKnowledgebaseVersions(kbId);
      // TODO: Show versions in a modal or dialog
      console.log('Versions:', versions);
      toast({
        title: 'Versions',
        description: `Found ${versions.length} version(s)`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load versions',
      });
    }
  };

  const handleSelectAll = () => {
    if (selectedKbs.size === filteredAndSortedKbs.length) {
      setSelectedKbs(new Set());
    } else {
      setSelectedKbs(new Set(filteredAndSortedKbs.map(kb => kb.id)));
    }
  };

  const handleSelectKb = (kbId: string) => {
    const newSelected = new Set(selectedKbs);
    if (newSelected.has(kbId)) {
      newSelected.delete(kbId);
    } else {
      newSelected.add(kbId);
    }
    setSelectedKbs(newSelected);
  };

  const handleBulkDelete = async () => {
    if (selectedKbs.size === 0) return;
    
    const confirmMessage = `Are you sure you want to delete ${selectedKbs.size} knowledgebase${selectedKbs.size !== 1 ? 's' : ''}?\n\nThis action cannot be undone.`;
    
    if (!confirm(confirmMessage)) return;

    try {
      await Promise.all(
        Array.from(selectedKbs).map(id => agentBuilderAPI.deleteKnowledgebase(id))
      );
      
      toast({
        title: '🗑️ Bulk Delete Successful',
        description: `${selectedKbs.size} knowledgebase${selectedKbs.size !== 1 ? 's' : ''} deleted`,
      });
      
      setSelectedKbs(new Set());
      loadKnowledgebases();
    } catch (error: any) {
      toast({
        title: 'Bulk Delete Failed',
        description: 'Some knowledgebases could not be deleted',
      });
    }
  };

  const handleDuplicate = async (kbId: string) => {
    const kb = knowledgebases.find(k => k.id === kbId);
    if (!kb) return;

    setFormData({
      name: `${kb.name} (Copy)`,
      description: kb.description || '',
      embedding_model: kb.embedding_model,
      chunk_size: kb.chunk_size,
      chunk_overlap: kb.chunk_overlap,
    });
    setEditingKb(null);
    setCreateDialogOpen(true);
  };

  const handleExport = () => {
    const exportData = knowledgebases.map(kb => ({
      name: kb.name,
      description: kb.description,
      embedding_model: kb.embedding_model,
      document_count: kb.document_count,
      total_size: kb.total_size,
      created_at: kb.created_at,
    }));

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `knowledgebases-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast({
      title: '📥 Export Successful',
      description: `${knowledgebases.length} knowledgebases exported`,
    });
  };

  const formatBytes = (bytes: number = 0) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Get unique embedding models for filter
  const embeddingModels = Array.from(new Set(knowledgebases.map(kb => kb.embedding_model)));

  // Filter and sort knowledgebases
  const filteredAndSortedKbs = knowledgebases
    .filter(kb => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchesSearch = (
          kb.name.toLowerCase().includes(query) ||
          kb.description?.toLowerCase().includes(query) ||
          kb.embedding_model.toLowerCase().includes(query)
        );
        if (!matchesSearch) return false;
      }
      
      // Model filter
      if (filterModel !== 'all' && kb.embedding_model !== filterModel) {
        return false;
      }
      
      return true;
    })
    .sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'created':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
        case 'size':
          comparison = (a.total_size || 0) - (b.total_size || 0);
          break;
        case 'documents':
          comparison = (a.document_count || 0) - (b.document_count || 0);
          break;
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });

  // Calculate statistics
  const stats = {
    total: knowledgebases.length,
    totalDocuments: knowledgebases.reduce((sum, kb) => sum + (kb.document_count || 0), 0),
    totalSize: knowledgebases.reduce((sum, kb) => sum + (kb.total_size || 0), 0),
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Knowledgebases</h1>
          <p className="text-muted-foreground">
            Manage document collections for your agents
            <kbd className="ml-2 px-2 py-0.5 text-xs bg-muted rounded border">Ctrl+N</kbd> to create
          </p>
        </div>
        <div className="flex items-center gap-2">
          {knowledgebases.length > 0 && (
            <>
              <Button variant="outline" size="sm" onClick={handleExport}>
                <Download className="mr-2 h-4 w-4" />
                Export
              </Button>
              {selectedKbs.size > 0 && (
                <Button variant="destructive" size="sm" onClick={handleBulkDelete}>
                  <Trash className="mr-2 h-4 w-4" />
                  Delete ({selectedKbs.size})
                </Button>
              )}
            </>
          )}
          <Button onClick={handleCreate}>
            <Plus className="mr-2 h-4 w-4" />
            Create Knowledgebase
          </Button>
        </div>
      </div>

      {/* Statistics Dashboard */}
      {!loading && knowledgebases.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Knowledgebases
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="text-3xl font-bold">{stats.total}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Documents
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="text-3xl font-bold">{stats.totalDocuments.toLocaleString()}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Size
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="text-3xl font-bold">{formatBytes(stats.totalSize)}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Knowledgebases Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Your Knowledgebases</CardTitle>
              <CardDescription>
                View and manage your document collections
              </CardDescription>
            </div>
            {!loading && knowledgebases.length > 0 && (
              <div className="flex items-center gap-2">
                {/* Search */}
                <div className="relative w-64">
                  <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search knowledgebases..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
                
                {/* Filter by Model */}
                {embeddingModels.length > 1 && (
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="outline" size="sm">
                        <Filter className="mr-2 h-4 w-4" />
                        {filterModel === 'all' ? 'All Models' : 'Filtered'}
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => setFilterModel('all')}>
                        All Models ({knowledgebases.length})
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      {embeddingModels.map(model => (
                        <DropdownMenuItem key={model} onClick={() => setFilterModel(model)}>
                          {model} ({knowledgebases.filter(kb => kb.embedding_model === model).length})
                        </DropdownMenuItem>
                      ))}
                    </DropdownMenuContent>
                  </DropdownMenu>
                )}
                
                {/* Sort */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm">
                      Sort: {sortBy.charAt(0).toUpperCase() + sortBy.slice(1)}
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => setSortBy('name')}>
                      Name
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => setSortBy('created')}>
                      Created Date
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => setSortBy('size')}>
                      Size
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => setSortBy('documents')}>
                      Documents
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}>
                      {sortOrder === 'asc' ? '↑ Ascending' : '↓ Descending'}
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
                
                {/* View Mode Toggle */}
                <div className="flex border rounded-md">
                  <Button
                    variant={viewMode === 'table' ? 'secondary' : 'ghost'}
                    size="sm"
                    onClick={() => setViewMode('table')}
                    className="rounded-r-none"
                  >
                    <List className="h-4 w-4" />
                  </Button>
                  <Button
                    variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
                    size="sm"
                    onClick={() => setViewMode('grid')}
                    className="rounded-l-none"
                  >
                    <Grid className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="overflow-visible">
          {loading ? (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : filteredAndSortedKbs.length === 0 && searchQuery ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <SearchIcon className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No results found</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Try adjusting your search query
              </p>
              <Button variant="outline" onClick={() => setSearchQuery('')}>
                Clear Search
              </Button>
            </div>
          ) : knowledgebases.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                <Database className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Create Your First Knowledgebase</h3>
              <p className="text-sm text-muted-foreground mb-6 max-w-md">
                Knowledgebases store your documents and make them searchable for AI agents. 
                Upload PDFs, Word docs, or text files to get started.
              </p>
              <div className="flex flex-col gap-3 items-center">
                <Button onClick={handleCreate} size="lg">
                  <Plus className="mr-2 h-5 w-5" />
                  Create Your First Knowledgebase
                </Button>
                <div className="flex items-center gap-4 text-xs text-muted-foreground mt-4">
                  <div className="flex items-center gap-1">
                    <FileText className="h-4 w-4" />
                    <span>Multiple formats</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <SearchIcon className="h-4 w-4" />
                    <span>AI-powered search</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Database className="h-4 w-4" />
                    <span>Vector storage</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="relative overflow-visible">
              <Table>
                <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <button
                      onClick={handleSelectAll}
                      className="flex items-center justify-center w-full"
                    >
                      {selectedKbs.size === filteredAndSortedKbs.length && filteredAndSortedKbs.length > 0 ? (
                        <CheckSquare className="h-4 w-4" />
                      ) : (
                        <Square className="h-4 w-4" />
                      )}
                    </button>
                  </TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Documents</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Embedding Model</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredAndSortedKbs.map((kb) => (
                  <TableRow 
                    key={kb.id}
                    className={`h-20 ${selectedKbs.has(kb.id) ? 'bg-muted/50' : ''}`}
                  >
                    <TableCell className="py-4">
                      <button
                        onClick={() => handleSelectKb(kb.id)}
                        className="flex items-center justify-center w-full hover:opacity-70 transition-opacity"
                      >
                        {selectedKbs.has(kb.id) ? (
                          <CheckSquare className="h-5 w-5 text-primary" />
                        ) : (
                          <Square className="h-5 w-5" />
                        )}
                      </button>
                    </TableCell>
                    <TableCell className="py-4">
                      <div className="space-y-1">
                        <div className="font-medium text-base">{kb.name}</div>
                        {kb.description && (
                          <div className="text-sm text-muted-foreground line-clamp-1">
                            {kb.description}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="py-4">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{kb.document_count || 0}</span>
                      </div>
                    </TableCell>
                    <TableCell className="py-4">
                      <Badge variant="outline" className="font-medium">
                        {formatBytes(kb.total_size)}
                      </Badge>
                    </TableCell>
                    <TableCell className="py-4">
                      <code className="text-xs bg-muted px-2.5 py-1.5 rounded font-mono">
                        {kb.embedding_model}
                      </code>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground py-4">
                      {formatDate(kb.created_at)}
                    </TableCell>
                    <TableCell className="text-right py-4">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent 
                          align="end" 
                          className="w-56 max-h-[400px] overflow-y-auto z-50"
                        >
                          <DropdownMenuItem 
                            onClick={() => handleUploadDocuments(kb.id)}
                            className="cursor-pointer"
                          >
                            <Upload className="mr-2 h-4 w-4" />
                            Upload Documents
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleSearch(kb.id)}
                            className="cursor-pointer"
                          >
                            <SearchIcon className="mr-2 h-4 w-4" />
                            Search
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleViewVersions(kb.id)}
                            className="cursor-pointer"
                          >
                            <History className="mr-2 h-4 w-4" />
                            Version History
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem 
                            onClick={() => handleDuplicate(kb.id)}
                            className="cursor-pointer"
                          >
                            <Copy className="mr-2 h-4 w-4" />
                            Duplicate
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleEdit(kb)}
                            className="cursor-pointer"
                          >
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleDelete(kb.id)}
                            className="text-destructive cursor-pointer"
                          >
                            <Trash className="mr-2 h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader className="space-y-3">
            <DialogTitle className="text-2xl">
              {editingKb ? 'Edit Knowledgebase' : 'Create New Knowledgebase'}
            </DialogTitle>
            <DialogDescription className="text-base">
              {editingKb 
                ? 'Update the knowledgebase details' 
                : 'Configure your new document collection'
              }
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-5 py-4">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-sm font-medium">
                Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="My Knowledgebase"
                className="h-11"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description" className="text-sm font-medium">
                Description
              </Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Describe what this knowledgebase contains..."
                rows={4}
                className="resize-none"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="embedding_model" className="text-sm font-medium">
                Embedding Model
                {editingKb && (
                  <span className="ml-2 text-xs text-muted-foreground">(Changing will re-embed all documents)</span>
                )}
              </Label>
              <Select
                value={formData.embedding_model}
                onValueChange={(value) => setFormData({ ...formData, embedding_model: value })}
              >
                <SelectTrigger className="h-11">
                  <SelectValue placeholder="Select an embedding model" />
                </SelectTrigger>
                <SelectContent>
                  <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">OpenAI</div>
                  <SelectItem value="text-embedding-3-small">
                    text-embedding-3-small (Recommended)
                      </SelectItem>
                      <SelectItem value="text-embedding-3-large">
                        text-embedding-3-large (High Quality)
                      </SelectItem>
                      <SelectItem value="text-embedding-ada-002">
                        text-embedding-ada-002 (Legacy)
                      </SelectItem>
                      
                      <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground mt-2">Korean Optimized</div>
                      <SelectItem value="jhgan/ko-sroberta-multitask">
                        ko-sroberta-multitask (Korean)
                      </SelectItem>
                      
                      <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground mt-2">Open Source</div>
                      <SelectItem value="sentence-transformers/all-MiniLM-L6-v2">
                        all-MiniLM-L6-v2 (Fast)
                      </SelectItem>
                      <SelectItem value="sentence-transformers/all-mpnet-base-v2">
                        all-mpnet-base-v2 (Balanced)
                      </SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground mt-2">
                Choose an embedding model based on your language and quality requirements
              </p>
            </div>

            {!editingKb && (
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="chunk_size" className="text-sm font-medium">
                    Chunk Size
                  </Label>
                  <Input
                    id="chunk_size"
                    type="number"
                    value={formData.chunk_size}
                    onChange={(e) => setFormData({ ...formData, chunk_size: parseInt(e.target.value) })}
                    className="h-11"
                  />
                  <p className="text-xs text-muted-foreground">
                    Characters per chunk
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="chunk_overlap" className="text-sm font-medium">
                    Chunk Overlap
                  </Label>
                  <Input
                    id="chunk_overlap"
                    type="number"
                    value={formData.chunk_overlap}
                    onChange={(e) => setFormData({ ...formData, chunk_overlap: parseInt(e.target.value) })}
                    className="h-11"
                  />
                  <p className="text-xs text-muted-foreground">
                    Overlapping characters
                  </p>
                </div>
              </div>
            )}
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button 
              variant="outline" 
              onClick={() => setCreateDialogOpen(false)}
              className="h-11"
            >
              Cancel
            </Button>
            <Button 
              onClick={handleSave} 
              disabled={saving || !formData.name}
              className="h-11"
            >
              {saving ? 'Saving...' : editingKb ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
