'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { useToast } from '@/hooks/use-toast';
import { flowsAPI } from '@/lib/api/flows';
import type { Chatflow } from '@/lib/types/flows';

// Import improved UX components
import {
  QuickActionBar,
  SmartEmptyState,
  EnhancedSearchFilters,
  ImprovedFlowCard,
  FlowListView,
  CardGridSkeleton
} from '@/components/agent-builder';

// Statistics component
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { MessageSquare, CheckCircle2, TrendingUp, Database } from 'lucide-react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

interface FilterState {
  status: 'all' | 'active' | 'inactive';
  sortBy: 'name' | 'created_at' | 'updated_at' | 'execution_count';
  tags: string[];
  dateRange: 'all' | 'week' | 'month' | 'quarter';
}

export default function ImprovedChatflowsPage() {
  const router = useRouter();
  const { toast } = useToast();
  
  // State management
  const [chatflows, setChatflows] = useState<Chatflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showTemplates, setShowTemplates] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [flowToDelete, setFlowToDelete] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterState>({
    status: 'all',
    sortBy: 'updated_at',
    tags: [],
    dateRange: 'all'
  });

  // Load data
  useEffect(() => {
    loadChatflows();
  }, []);

  const loadChatflows = async () => {
    try {
      setLoading(true);
      const response = await flowsAPI.getChatflows();
      setChatflows(response.flows as Chatflow[]);
    } catch (error: any) {
      console.error('Failed to load chatflows:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to load chatflow list',
        variant: 'destructive',
      });
      setChatflows([]);
    } finally {
      setLoading(false);
    }
  };

  // Extract available tags from flows
  const availableTags = useMemo(() => {
    const tags = new Set<string>();
    chatflows.forEach(flow => {
      flow.tags?.forEach(tag => tags.add(tag));
    });
    return Array.from(tags);
  }, [chatflows]);

  // Filter and sort flows
  const filteredFlows = useMemo(() => {
    return chatflows
      .filter((flow) => {
        // Search filter
        const matchesSearch = !searchQuery || 
          flow.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          flow.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          flow.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));

        // Status filter
        const matchesStatus = filters.status === 'all' ||
          (filters.status === 'active' && flow.is_active) ||
          (filters.status === 'inactive' && !flow.is_active);

        // Tags filter
        const matchesTags = filters.tags.length === 0 ||
          filters.tags.some(tag => flow.tags?.includes(tag));

        // Date range filter
        const matchesDateRange = filters.dateRange === 'all' || (() => {
          const flowDate = new Date(flow.created_at);
          const now = new Date();
          const daysDiff = (now.getTime() - flowDate.getTime()) / (1000 * 60 * 60 * 24);
          
          switch (filters.dateRange) {
            case 'week': return daysDiff <= 7;
            case 'month': return daysDiff <= 30;
            case 'quarter': return daysDiff <= 90;
            default: return true;
          }
        })();

        return matchesSearch && matchesStatus && matchesTags && matchesDateRange;
      })
      .sort((a, b) => {
        switch (filters.sortBy) {
          case 'name':
            return a.name.localeCompare(b.name);
          case 'created_at':
            return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
          case 'updated_at':
            return new Date(b.updated_at || b.created_at).getTime() - new Date(a.updated_at || a.created_at).getTime();
          case 'execution_count':
            return (b.execution_count || 0) - (a.execution_count || 0);
          default:
            return 0;
        }
      });
  }, [chatflows, searchQuery, filters]);

  // Action handlers
  const handleAction = async (action: string, flowId: string, flow?: Chatflow) => {
    switch (action) {
      case 'view':
        router.push(`/agent-builder/chatflows/${flowId}`);
        break;
      case 'edit':
        router.push(`/agent-builder/chatflows/${flowId}/edit`);
        break;
      case 'chat':
        router.push(`/agent-builder/chatflows/${flowId}/chat`);
        break;
      case 'duplicate':
        if (flow) {
          try {
            const duplicatedFlow = {
              ...flow,
              name: `${flow.name} (Copy)`,
              id: undefined,
            };
            await flowsAPI.createChatflow(duplicatedFlow);
            toast({
              title: 'Duplicated',
              description: `"${flow.name}" has been duplicated`,
            });
            loadChatflows();
          } catch (error: any) {
            toast({
              title: 'Error',
              description: error.message || 'Failed to duplicate',
              variant: 'destructive',
            });
          }
        }
        break;
      case 'delete':
        setFlowToDelete(flowId);
        setDeleteDialogOpen(true);
        break;
      case 'embed':
        router.push(`/agent-builder/chatflows/${flowId}/embed`);
        break;
      case 'api':
        router.push(`/agent-builder/chatflows/${flowId}/api`);
        break;
    }
  };

  const handleDelete = async () => {
    if (!flowToDelete) return;

    try {
      await flowsAPI.deleteFlow(flowToDelete);
      toast({
        title: 'Deleted',
        description: 'Chatflow has been deleted',
      });
      loadChatflows();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete',
        variant: 'destructive',
      });
    } finally {
      setDeleteDialogOpen(false);
      setFlowToDelete(null);
    }
  };

  // Statistics calculation
  const stats = useMemo(() => {
    const total = chatflows.length;
    const active = chatflows.filter(f => f.is_active).length;
    const totalConversations = chatflows.reduce((sum, f) => sum + (f.execution_count || 0), 0);
    const ragEnabled = chatflows.filter(f => f.rag_config?.enabled).length;

    return { total, active, totalConversations, ragEnabled };
  }, [chatflows]);

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      {/* Enhanced Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
            <MessageSquare className="h-8 w-8 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
              Chatflows
            </h1>
            <p className="text-muted-foreground text-lg">
              Build RAG-based chatbots and AI assistants
            </p>
          </div>
        </div>
      </div>

      {/* Quick Action Bar */}
      <QuickActionBar
        type="chatflow"
        onNewFlow={() => router.push('/agent-builder/chatflows/new')}
        onToggleTemplates={() => setShowTemplates(!showTemplates)}
        showTemplates={showTemplates}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
      />

      {/* Enhanced Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Total Chatflows
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              Active
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.active}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Total Conversations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalConversations}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Database className="h-4 w-4" />
              RAG Enabled
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats.ragEnabled}</div>
          </CardContent>
        </Card>
      </div>

      {/* Enhanced Search and Filters */}
      <EnhancedSearchFilters
        type="chatflow"
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        filters={filters}
        onFiltersChange={setFilters}
        availableTags={availableTags}
      />

      {/* Content */}
      {loading ? (
        <CardGridSkeleton count={6} />
      ) : filteredFlows.length === 0 ? (
        <SmartEmptyState
          type="chatflow"
          hasSearch={!!searchQuery || filters.status !== 'all' || filters.tags.length > 0 || filters.dateRange !== 'all'}
          searchQuery={searchQuery}
          onNewFlow={() => router.push('/agent-builder/chatflows/new')}
          onShowTemplates={() => setShowTemplates(true)}
          onClearSearch={() => {
            setSearchQuery('');
            setFilters({
              status: 'all',
              sortBy: 'updated_at',
              tags: [],
              dateRange: 'all'
            });
          }}
        />
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredFlows.map((flow) => (
            <ImprovedFlowCard
              key={flow.id}
              flow={flow}
              type="chatflow"
              onAction={handleAction}
            />
          ))}
        </div>
      ) : (
        <FlowListView
          flows={filteredFlows}
          type="chatflow"
          onAction={handleAction}
        />
      )}

      {/* Delete Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Chatflow</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this Chatflow? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
