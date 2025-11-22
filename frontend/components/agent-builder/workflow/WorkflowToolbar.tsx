import { memo } from 'react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import {
  Play,
  Square,
  RotateCcw,
  Save,
  Undo2,
  Redo2,
} from 'lucide-react';

interface WorkflowToolbarProps {
  onSave: () => void;
  onUndo: () => void;
  onRedo: () => void;
  onExecute: () => void;
  onStop: () => void;
  onReset: () => void;
  canUndo: boolean;
  canRedo: boolean;
  isSaving: boolean;
  isExecuting: boolean;
}

export const WorkflowToolbar = memo(function WorkflowToolbar({
  onSave,
  onUndo,
  onRedo,
  onExecute,
  onStop,
  onReset,
  canUndo,
  canRedo,
  isSaving,
  isExecuting,
}: WorkflowToolbarProps) {
  return (
    <div className="p-4 border-b bg-background flex items-center gap-2">
      {/* Save */}
      <Button
        onClick={onSave}
        disabled={isSaving}
        variant="default"
        size="sm"
        aria-label="Save workflow"
        aria-busy={isSaving}
      >
        <Save className="h-4 w-4 mr-2" aria-hidden="true" />
        {isSaving ? 'Saving...' : 'Save'}
      </Button>

      <Separator orientation="vertical" className="h-6" />

      {/* Undo/Redo */}
      <Button
        onClick={onUndo}
        disabled={!canUndo}
        variant="outline"
        size="sm"
        aria-label="Undo last action"
        title="Undo (Ctrl+Z)"
      >
        <Undo2 className="h-4 w-4" aria-hidden="true" />
      </Button>
      <Button
        onClick={onRedo}
        disabled={!canRedo}
        variant="outline"
        size="sm"
        aria-label="Redo last action"
        title="Redo (Ctrl+Y)"
      >
        <Redo2 className="h-4 w-4" aria-hidden="true" />
      </Button>

      <Separator orientation="vertical" className="h-6" />

      {/* Execution controls */}
      {!isExecuting ? (
        <Button
          onClick={onExecute}
          variant="default"
          size="sm"
          className="bg-green-600 hover:bg-green-700"
          aria-label="Execute workflow"
          title="Execute (Ctrl+Enter)"
        >
          <Play className="h-4 w-4 mr-2" aria-hidden="true" />
          Execute
        </Button>
      ) : (
        <Button
          onClick={onStop}
          variant="destructive"
          size="sm"
          aria-label="Stop execution"
          title="Stop (Ctrl+.)"
        >
          <Square className="h-4 w-4 mr-2" aria-hidden="true" />
          Stop
        </Button>
      )}

      <Button
        onClick={onReset}
        disabled={isExecuting}
        variant="outline"
        size="sm"
        aria-label="Reset workflow"
        title="Reset (Ctrl+R)"
      >
        <RotateCcw className="h-4 w-4 mr-2" aria-hidden="true" />
        Reset
      </Button>
    </div>
  );
});
