import { useCallback } from 'react';
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSeparator,
  ContextMenuShortcut,
  ContextMenuTrigger,
} from '@/components/ui/context-menu';
import {
  Copy,
  Trash,
  Bug,
  FileText,
  Play,
  Settings,
  Eye,
  EyeOff,
  Lock,
  Unlock,
} from 'lucide-react';
import { Node } from 'reactflow';
import { toast } from 'sonner';

interface EnhancedNodeContextMenuProps {
  children: React.ReactNode;
  node: Node;
  onDuplicate?: (node: Node) => void;
  onDelete?: (node: Node) => void;
  onAddBreakpoint?: (node: Node) => void;
  onViewLogs?: (node: Node) => void;
  onExecute?: (node: Node) => void;
  onConfigure?: (node: Node) => void;
  onToggleVisibility?: (node: Node) => void;
  onToggleLock?: (node: Node) => void;
}

export function EnhancedNodeContextMenu({
  children,
  node,
  onDuplicate,
  onDelete,
  onAddBreakpoint,
  onViewLogs,
  onExecute,
  onConfigure,
  onToggleVisibility,
  onToggleLock,
}: EnhancedNodeContextMenuProps) {
  const handleDuplicate = useCallback(() => {
    if (onDuplicate) {
      onDuplicate(node);
      toast.success('Node duplicated');
    }
  }, [node, onDuplicate]);

  const handleDelete = useCallback(() => {
    if (onDelete) {
      onDelete(node);
      toast.success('Node deleted');
    }
  }, [node, onDelete]);

  const handleAddBreakpoint = useCallback(() => {
    if (onAddBreakpoint) {
      onAddBreakpoint(node);
      toast.success('Breakpoint added');
    }
  }, [node, onAddBreakpoint]);

  const handleViewLogs = useCallback(() => {
    if (onViewLogs) {
      onViewLogs(node);
    }
  }, [node, onViewLogs]);

  const handleExecute = useCallback(() => {
    if (onExecute) {
      onExecute(node);
      toast.success('Executing node...');
    }
  }, [node, onExecute]);

  const handleConfigure = useCallback(() => {
    if (onConfigure) {
      onConfigure(node);
    }
  }, [node, onConfigure]);

  const handleToggleVisibility = useCallback(() => {
    if (onToggleVisibility) {
      onToggleVisibility(node);
      toast.success(node.hidden ? 'Node shown' : 'Node hidden');
    }
  }, [node, onToggleVisibility]);

  const handleToggleLock = useCallback(() => {
    if (onToggleLock) {
      onToggleLock(node);
      toast.success(node.data.locked ? 'Node unlocked' : 'Node locked');
    }
  }, [node, onToggleLock]);

  return (
    <ContextMenu>
      <ContextMenuTrigger asChild>{children}</ContextMenuTrigger>
      <ContextMenuContent className="w-56">
        <ContextMenuItem onClick={handleExecute}>
          <Play className="h-4 w-4 mr-2" />
          Execute Node
          <ContextMenuShortcut>⌘E</ContextMenuShortcut>
        </ContextMenuItem>

        <ContextMenuItem onClick={handleConfigure}>
          <Settings className="h-4 w-4 mr-2" />
          Configure
          <ContextMenuShortcut>⌘,</ContextMenuShortcut>
        </ContextMenuItem>

        <ContextMenuSeparator />

        <ContextMenuItem onClick={handleDuplicate}>
          <Copy className="h-4 w-4 mr-2" />
          Duplicate
          <ContextMenuShortcut>⌘D</ContextMenuShortcut>
        </ContextMenuItem>

        <ContextMenuItem onClick={handleDelete} className="text-destructive">
          <Trash className="h-4 w-4 mr-2" />
          Delete
          <ContextMenuShortcut>⌫</ContextMenuShortcut>
        </ContextMenuItem>

        <ContextMenuSeparator />

        <ContextMenuItem onClick={handleAddBreakpoint}>
          <Bug className="h-4 w-4 mr-2" />
          Add Breakpoint
          <ContextMenuShortcut>⌘B</ContextMenuShortcut>
        </ContextMenuItem>

        <ContextMenuItem onClick={handleViewLogs}>
          <FileText className="h-4 w-4 mr-2" />
          View Logs
          <ContextMenuShortcut>⌘L</ContextMenuShortcut>
        </ContextMenuItem>

        <ContextMenuSeparator />

        <ContextMenuItem onClick={handleToggleVisibility}>
          {node.hidden ? (
            <>
              <Eye className="h-4 w-4 mr-2" />
              Show Node
            </>
          ) : (
            <>
              <EyeOff className="h-4 w-4 mr-2" />
              Hide Node
            </>
          )}
          <ContextMenuShortcut>⌘H</ContextMenuShortcut>
        </ContextMenuItem>

        <ContextMenuItem onClick={handleToggleLock}>
          {node.data.locked ? (
            <>
              <Unlock className="h-4 w-4 mr-2" />
              Unlock Node
            </>
          ) : (
            <>
              <Lock className="h-4 w-4 mr-2" />
              Lock Node
            </>
          )}
          <ContextMenuShortcut>⌘⇧L</ContextMenuShortcut>
        </ContextMenuItem>
      </ContextMenuContent>
    </ContextMenu>
  );
}
