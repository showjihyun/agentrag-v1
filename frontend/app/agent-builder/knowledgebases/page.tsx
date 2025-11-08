'use client';

import { useState, useEffect } from 'react';
import { Plus, Database, MoreVertical, Edit, Trash, Upload, Search as SearchIcon, History, FileText } from 'lucide-react';
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

  useEffect(() => {
    loadKnowledgebases();
  }, []);

  const loadKnowledgebases = async () => {
    try {
      setLoading(true);
      const data = await agentBuilderAPI.getKnowledgebases();
      setKnowledgebases(data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load knowledgebases',
        variant: 'destructive',
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
    });
    setCreateDialogOpen(true);
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      
      if (editingKb) {
        await agentBuilderAPI.updateKnowledgebase(editingKb.id, {
          name: formData.name,
          description: formData.description,
        });
        toast({
          title: 'Success',
          description: 'Knowledgebase updated successfully',
        });
      } else {
        await agentBuilderAPI.createKnowledgebase(formData);
        toast({
          title: 'Success',
          description: 'Knowledgebase created successfully',
        });
      }
      
      setCreateDialogOpen(false);
      loadKnowledgebases();
    } catch (error) {
      toast({
        title: 'Error',
        description: editingKb ? 'Failed to update knowledgebase' : 'Failed to create knowledgebase',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (kbId: string) => {
    if (!confirm('Are you sure you want to delete this knowledgebase? This action cannot be undone.')) {
      return;
    }

    try {
      await agentBuilderAPI.deleteKnowledgebase(kbId);
      toast({
        title: 'Success',
        description: 'Knowledgebase deleted successfully',
      });
      loadKnowledgebases();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete knowledgebase',
        variant: 'destructive',
      });
    }
  };

  const handleUploadDocuments = (kbId: string) => {
    router.push(`/agent-builder/knowledgebases/${kbId}/upload`);
  };

  const handleSearch = (kbId: string) => {
    router.push(`/agent-builder/knowledgebases/${kbId}/search`);
  };

  const handleViewVersions = (kbId: string) => {
    router.push(`/agent-builder/knowledgebases/${kbId}/versions`);
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

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Knowledgebases</h1>
          <p className="text-muted-foreground">
            Manage document collections for your agents
          </p>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="mr-2 h-4 w-4" />
          Create Knowledgebase
        </Button>
      </div>

      {/* Knowledgebases Table */}
      <Card>
        <CardHeader>
          <CardTitle>Your Knowledgebases</CardTitle>
          <CardDescription>
            View and manage your document collections
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : knowledgebases.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Database className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No knowledgebases yet</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Create your first knowledgebase to get started
              </p>
              <Button onClick={handleCreate}>
                <Plus className="mr-2 h-4 w-4" />
                Create Knowledgebase
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Documents</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Embedding Model</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {knowledgebases.map((kb) => (
                  <TableRow key={kb.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{kb.name}</div>
                        {kb.description && (
                          <div className="text-sm text-muted-foreground line-clamp-1">
                            {kb.description}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-muted-foreground" />
                        <span>{kb.document_count || 0}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {formatBytes(kb.total_size)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <code className="text-xs bg-muted px-2 py-1 rounded">
                        {kb.embedding_model}
                      </code>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDate(kb.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleUploadDocuments(kb.id)}>
                            <Upload className="mr-2 h-4 w-4" />
                            Upload Documents
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleSearch(kb.id)}>
                            <SearchIcon className="mr-2 h-4 w-4" />
                            Search
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleViewVersions(kb.id)}>
                            <History className="mr-2 h-4 w-4" />
                            Version History
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onClick={() => handleEdit(kb)}>
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleDelete(kb.id)}
                            className="text-destructive"
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
          )}
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingKb ? 'Edit Knowledgebase' : 'Create New Knowledgebase'}
            </DialogTitle>
            <DialogDescription>
              {editingKb 
                ? 'Update the knowledgebase details' 
                : 'Configure your new document collection'
              }
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="My Knowledgebase"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Describe what this knowledgebase contains..."
                rows={3}
              />
            </div>

            {!editingKb && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="embedding_model">Embedding Model</Label>
                  <Input
                    id="embedding_model"
                    value={formData.embedding_model}
                    onChange={(e) => setFormData({ ...formData, embedding_model: e.target.value })}
                    placeholder="text-embedding-3-small"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="chunk_size">Chunk Size</Label>
                    <Input
                      id="chunk_size"
                      type="number"
                      value={formData.chunk_size}
                      onChange={(e) => setFormData({ ...formData, chunk_size: parseInt(e.target.value) })}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="chunk_overlap">Chunk Overlap</Label>
                    <Input
                      id="chunk_overlap"
                      type="number"
                      value={formData.chunk_overlap}
                      onChange={(e) => setFormData({ ...formData, chunk_overlap: parseInt(e.target.value) })}
                    />
                  </div>
                </div>
              </>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={saving || !formData.name}>
              {saving ? 'Saving...' : editingKb ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
