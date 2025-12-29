'use client';

import { useState, useEffect } from 'react';
import {
  Plus,
  Lock,
  Eye,
  MoreVertical,
  Edit,
  Copy,
  Trash,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI, Variable } from '@/lib/api/agent-builder';
import { VariableEditor } from '@/components/agent-builder/VariableEditor';

export default function VariablesManagerPage() {
  const { toast } = useToast();
  const [variables, setVariables] = useState<Variable[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingVariable, setEditingVariable] = useState<Variable | null>(null);
  const [expandedScopes, setExpandedScopes] = useState<string[]>(['global', 'workspace', 'user', 'agent']);
  const [revealedSecrets, setRevealedSecrets] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadVariables();
  }, []);

  const loadVariables = async () => {
    try {
      const variablesData = await agentBuilderAPI.getVariables();
      // Ensure variablesData is an array
      setVariables(Array.isArray(variablesData) ? variablesData : []);
    } catch (error) {
      console.error('Failed to load variables:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to load variables',
      });
      setVariables([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

  const groupedVariables = (Array.isArray(variables) ? variables : []).reduce((acc, variable) => {
    if (!acc[variable.scope]) {
      acc[variable.scope] = [];
    }
    acc[variable.scope]!.push(variable);
    return acc;
  }, {} as Record<string, Variable[]>);

  const toggleScope = (scope: string) => {
    setExpandedScopes((prev) =>
      prev.includes(scope) ? prev.filter((s) => s !== scope) : [...prev, scope]
    );
  };

  const handleCreateVariable = () => {
    setEditingVariable(null);
    setIsCreateOpen(true);
  };

  const handleEdit = (variable: Variable) => {
    setEditingVariable(variable);
    setIsCreateOpen(true);
  };

  const handleCopy = (name: string) => {
    navigator.clipboard.writeText(`\${${name}}`);
    toast({
      title: 'Copied',
      description: 'Variable reference copied to clipboard',
    });
  };

  const handleDelete = async (variableId: string) => {
    try {
      await agentBuilderAPI.deleteVariable(variableId);
      toast({
        title: 'Variable deleted',
        description: 'The variable has been deleted successfully',
      });
      loadVariables();
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to delete variable',
      });
    }
  };

  const handleRevealSecret = async (variableId: string) => {
    if (revealedSecrets.has(variableId)) {
      setRevealedSecrets((prev) => {
        const newSet = new Set(prev);
        newSet.delete(variableId);
        return newSet;
      });
      return;
    }

    try {
      const { value } = await agentBuilderAPI.revealSecret(variableId);
      // Store the revealed value temporarily
      setRevealedSecrets((prev) => new Set(prev).add(variableId));
      
      // Update the variable in the list with the revealed value
      setVariables((prev) =>
        prev.map((v) => (v.id === variableId ? { ...v, value } : v))
      );

      toast({
        title: 'Secret revealed',
        description: 'The secret value is now visible',
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to reveal secret',
      });
    }
  };

  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const handleVariableSaved = () => {
    setIsCreateOpen(false);
    setEditingVariable(null);
    loadVariables();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-muted-foreground">Loading variables...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Variables</h1>
          <p className="text-muted-foreground">Manage global variables and secrets</p>
        </div>
        <Button onClick={handleCreateVariable}>
          <Plus className="mr-2 h-4 w-4" />
          Create Variable
        </Button>
      </div>

      {/* Scope Tabs */}
      <Tabs defaultValue="all" className="w-full">
        <TabsList>
          <TabsTrigger value="all">All Variables</TabsTrigger>
          <TabsTrigger value="global">Global</TabsTrigger>
          <TabsTrigger value="workspace">Workspace</TabsTrigger>
          <TabsTrigger value="user">User</TabsTrigger>
          <TabsTrigger value="agent">Agent</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4">
          {Object.keys(groupedVariables).length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center p-12 text-center">
                <div className="rounded-full bg-muted p-3 mb-4">
                  <Lock className="h-6 w-6 text-muted-foreground" />
                </div>
                <h3 className="text-lg font-semibold mb-2">No variables yet</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Get started by creating your first variable
                </p>
                <Button onClick={handleCreateVariable}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Variable
                </Button>
              </CardContent>
            </Card>
          ) : (
            Object.entries(groupedVariables).map(([scope, vars]) => (
              <Card key={scope}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-lg capitalize">{scope} Scope</CardTitle>
                      <Badge variant="outline">{vars.length}</Badge>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => toggleScope(scope)}>
                      {expandedScopes.includes(scope) ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </CardHeader>

                {expandedScopes.includes(scope) && (
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Name</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead>Value</TableHead>
                          <TableHead>Updated</TableHead>
                          <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {vars.map((variable) => (
                          <TableRow key={variable.id}>
                            <TableCell className="font-medium">
                              <div className="flex items-center gap-2">
                                {variable.is_secret && (
                                  <Lock className="h-3 w-3 text-muted-foreground" />
                                )}
                                <code className="text-sm">{variable.name}</code>
                              </div>
                            </TableCell>
                            <TableCell>
                              <Badge variant="outline">{variable.value_type}</Badge>
                            </TableCell>
                            <TableCell className="max-w-xs">
                              {variable.is_secret ? (
                                <div className="flex items-center gap-2">
                                  <span className="text-muted-foreground">
                                    {revealedSecrets.has(variable.id)
                                      ? variable.value
                                      : '••••••••'}
                                  </span>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={() => handleRevealSecret(variable.id)}
                                  >
                                    <Eye className="h-3 w-3" />
                                  </Button>
                                </div>
                              ) : (
                                <code className="text-xs text-muted-foreground truncate block">
                                  {variable.value}
                                </code>
                              )}
                            </TableCell>
                            <TableCell className="text-sm text-muted-foreground">
                              {formatRelativeTime(variable.updated_at)}
                            </TableCell>
                            <TableCell className="text-right">
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="icon">
                                    <MoreVertical className="h-4 w-4" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  <DropdownMenuItem onClick={() => handleEdit(variable)}>
                                    <Edit className="mr-2 h-4 w-4" />
                                    Edit
                                  </DropdownMenuItem>
                                  <DropdownMenuItem onClick={() => handleCopy(variable.name)}>
                                    <Copy className="mr-2 h-4 w-4" />
                                    Copy Name
                                  </DropdownMenuItem>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem
                                    onClick={() => handleDelete(variable.id)}
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
                  </CardContent>
                )}
              </Card>
            ))
          )}
        </TabsContent>

        {['global', 'workspace', 'user', 'agent'].map((scope) => {
          const scopeVariables = groupedVariables[scope] || [];
          return (
            <TabsContent key={scope} value={scope} className="space-y-4">
              {scopeVariables.length > 0 ? (
              <Card>
                <CardContent className="pt-6">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Value</TableHead>
                        <TableHead>Updated</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {scopeVariables.map((variable) => (
                        <TableRow key={variable.id}>
                          <TableCell className="font-medium">
                            <div className="flex items-center gap-2">
                              {variable.is_secret && (
                                <Lock className="h-3 w-3 text-muted-foreground" />
                              )}
                              <code className="text-sm">{variable.name}</code>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">{variable.value_type}</Badge>
                          </TableCell>
                          <TableCell className="max-w-xs">
                            {variable.is_secret ? (
                              <div className="flex items-center gap-2">
                                <span className="text-muted-foreground">
                                  {revealedSecrets.has(variable.id) ? variable.value : '••••••••'}
                                </span>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handleRevealSecret(variable.id)}
                                >
                                  <Eye className="h-3 w-3" />
                                </Button>
                              </div>
                            ) : (
                              <code className="text-xs text-muted-foreground truncate block">
                                {variable.value}
                              </code>
                            )}
                          </TableCell>
                          <TableCell className="text-sm text-muted-foreground">
                            {formatRelativeTime(variable.updated_at)}
                          </TableCell>
                          <TableCell className="text-right">
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon">
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => handleEdit(variable)}>
                                  <Edit className="mr-2 h-4 w-4" />
                                  Edit
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleCopy(variable.name)}>
                                  <Copy className="mr-2 h-4 w-4" />
                                  Copy Name
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  onClick={() => handleDelete(variable.id)}
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
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="flex flex-col items-center justify-center p-12 text-center">
                  <p className="text-sm text-muted-foreground mb-4">
                    No variables in {scope} scope
                  </p>
                  <Button onClick={handleCreateVariable}>
                    <Plus className="mr-2 h-4 w-4" />
                    Create Variable
                  </Button>
                </CardContent>
              </Card>
            )}
            </TabsContent>
          );
        })}
      </Tabs>

      {/* Variable Editor Dialog */}
      <VariableEditor
        open={isCreateOpen}
        onOpenChange={setIsCreateOpen}
        variable={editingVariable}
        onSaved={handleVariableSaved}
      />
    </div>
  );
}
