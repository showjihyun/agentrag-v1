'use client';

import { Node } from 'reactflow';
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSeparator,
  ContextMenuTrigger,
  ContextMenuSub,
  ContextMenuSubContent,
  ContextMenuSubTrigger,
} from '@/components/ui/context-menu';
import {
  Edit,
  Copy,
  Trash,
  EyeOff,
  Eye,
  Lock,
  Unlock,
  Palette,
  Settings,
} from 'lucide-react';

interface NodeContextMenuProps {
  node: Node;
  children: React.ReactNode;
  onEdit?: (node: Node) => void;
  onDuplicate?: (node: Node) => void;
  onDelete?: (node: Node) => void;
  onToggleDisable?: (node: Node) => void;
  onToggleLock?: (node: Node) => void;
  onChangeColor?: (node: Node, color: string) => void;
}

const colorOptions = [
  { name: 'Default', value: 'default' },
  { name: 'Blue', value: 'blue' },
  { name: 'Green', value: 'green' },
  { name: 'Yellow', value: 'yellow' },
  { name: 'Red', value: 'red' },
  { name: 'Purple', value: 'purple' },
];

export const NodeContextMenu = ({
  node,
  children,
  onEdit,
  onDuplicate,
  onDelete,
  onToggleDisable,
  onToggleLock,
  onChangeColor,
}: NodeContextMenuProps) => {
  const isDisabled = node.data?.disabled || false;
  const isLocked = node.data?.locked || false;

  return (
    <ContextMenu>
      <ContextMenuTrigger asChild>
        {children}
      </ContextMenuTrigger>
      <ContextMenuContent className="w-56">
        <ContextMenuItem onClick={() => onEdit?.(node)}>
          <Edit className="mr-2 h-4 w-4" />
          Edit Properties
        </ContextMenuItem>
        
        <ContextMenuItem onClick={() => onDuplicate?.(node)}>
          <Copy className="mr-2 h-4 w-4" />
          Duplicate Node
        </ContextMenuItem>
        
        <ContextMenuSeparator />
        
        <ContextMenuItem onClick={() => onToggleDisable?.(node)}>
          {isDisabled ? (
            <>
              <Eye className="mr-2 h-4 w-4" />
              Enable Node
            </>
          ) : (
            <>
              <EyeOff className="mr-2 h-4 w-4" />
              Disable Node
            </>
          )}
        </ContextMenuItem>
        
        <ContextMenuItem onClick={() => onToggleLock?.(node)}>
          {isLocked ? (
            <>
              <Unlock className="mr-2 h-4 w-4" />
              Unlock Position
            </>
          ) : (
            <>
              <Lock className="mr-2 h-4 w-4" />
              Lock Position
            </>
          )}
        </ContextMenuItem>
        
        <ContextMenuSeparator />
        
        <ContextMenuSub>
          <ContextMenuSubTrigger>
            <Palette className="mr-2 h-4 w-4" />
            Change Color
          </ContextMenuSubTrigger>
          <ContextMenuSubContent>
            {colorOptions.map((color) => (
              <ContextMenuItem
                key={color.value}
                onClick={() => onChangeColor?.(node, color.value)}
              >
                <div
                  className={cn(
                    'mr-2 h-4 w-4 rounded-full border',
                    color.value === 'default' && 'bg-gray-500',
                    color.value === 'blue' && 'bg-blue-500',
                    color.value === 'green' && 'bg-green-500',
                    color.value === 'yellow' && 'bg-yellow-500',
                    color.value === 'red' && 'bg-red-500',
                    color.value === 'purple' && 'bg-purple-500'
                  )}
                />
                {color.name}
              </ContextMenuItem>
            ))}
          </ContextMenuSubContent>
        </ContextMenuSub>
        
        <ContextMenuSeparator />
        
        <ContextMenuItem
          className="text-destructive focus:text-destructive"
          onClick={() => onDelete?.(node)}
        >
          <Trash className="mr-2 h-4 w-4" />
          Delete Node
        </ContextMenuItem>
      </ContextMenuContent>
    </ContextMenu>
  );
};
