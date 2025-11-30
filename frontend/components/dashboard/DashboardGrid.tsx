'use client';

/**
 * DashboardGrid Component
 * 
 * Renders a customizable dashboard with draggable widgets.
 */

import React, { useState } from 'react';
import { Plus, Save, RotateCcw, Settings, GripVertical, X, Loader2 } from 'lucide-react';
import { useDashboard } from '@/hooks/useDashboard';
import { DashboardWidget, WIDGET_TYPES, AddWidgetRequest } from '@/lib/api/dashboard';
import { cn } from '@/lib/utils';

interface DashboardGridProps {
  className?: string;
}

export function DashboardGrid({ className }: DashboardGridProps) {
  const {
    widgets,
    loading,
    error,
    isDirty,
    saveLayout,
    resetLayout,
    addWidget,
    removeWidget,
    moveWidget,
    resizeWidget,
  } = useDashboard();

  const [showAddWidget, setShowAddWidget] = useState(false);
  const [editMode, setEditMode] = useState(false);

  if (loading && widgets.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Dashboard</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setEditMode(!editMode)}
            className={cn(
              'px-3 py-1.5 text-sm rounded-lg transition-colors',
              editMode ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            )}
          >
            <Settings className="w-4 h-4 inline mr-1" />
            {editMode ? 'Done' : 'Edit'}
          </button>
          {editMode && (
            <>
              <button
                onClick={() => setShowAddWidget(true)}
                className="px-3 py-1.5 text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200"
              >
                <Plus className="w-4 h-4 inline mr-1" />
                Add Widget
              </button>
              <button
                onClick={resetLayout}
                className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                <RotateCcw className="w-4 h-4 inline mr-1" />
                Reset
              </button>
            </>
          )}
          {isDirty && (
            <button
              onClick={saveLayout}
              className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Save className="w-4 h-4 inline mr-1" />
              Save
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>
      )}

      {/* Widget Grid */}
      <div className="grid grid-cols-12 gap-4 auto-rows-[100px]">
        {widgets.map((widget) => (
          <WidgetCard
            key={widget.id}
            widget={widget}
            editMode={editMode}
            onRemove={() => removeWidget(widget.id)}
          />
        ))}
      </div>

      {widgets.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <p>No widgets configured.</p>
          <button
            onClick={() => setShowAddWidget(true)}
            className="mt-2 text-blue-600 hover:text-blue-700"
          >
            Add your first widget
          </button>
        </div>
      )}

      {/* Add Widget Modal */}
      {showAddWidget && (
        <AddWidgetModal
          onAdd={async (request) => {
            await addWidget(request);
            setShowAddWidget(false);
          }}
          onClose={() => setShowAddWidget(false)}
        />
      )}
    </div>
  );
}

interface WidgetCardProps {
  widget: DashboardWidget;
  editMode: boolean;
  onRemove: () => void;
}

function WidgetCard({ widget, editMode, onRemove }: WidgetCardProps) {
  const gridStyle = {
    gridColumn: `span ${widget.width}`,
    gridRow: `span ${widget.height}`,
  };

  return (
    <div
      style={gridStyle}
      className={cn(
        'bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden',
        editMode && 'ring-2 ring-blue-300 ring-opacity-50'
      )}
    >
      {/* Widget Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
        {editMode && (
          <GripVertical className="w-4 h-4 text-gray-400 cursor-move mr-2" />
        )}
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 flex-1">
          {widget.title}
        </h3>
        {editMode && (
          <button
            onClick={onRemove}
            className="p-1 hover:bg-red-100 rounded text-gray-400 hover:text-red-500"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Widget Content */}
      <div className="p-4 h-[calc(100%-40px)] overflow-auto">
        <WidgetContent type={widget.type} config={widget.config} />
      </div>
    </div>
  );
}

interface WidgetContentProps {
  type: string;
  config?: Record<string, unknown>;
}

function WidgetContent({ type, config }: WidgetContentProps) {
  switch (type) {
    case WIDGET_TYPES.WORKFLOW_STATS:
      return <WorkflowStatsWidget />;
    case WIDGET_TYPES.RECENT_EXECUTIONS:
      return <RecentExecutionsWidget />;
    case WIDGET_TYPES.SYSTEM_HEALTH:
      return <SystemHealthWidget />;
    case WIDGET_TYPES.QUICK_ACTIONS:
      return <QuickActionsWidget />;
    case WIDGET_TYPES.NOTIFICATIONS:
      return <NotificationsWidget />;
    default:
      return <div className="text-gray-500 text-sm">Unknown widget type: {type}</div>;
  }
}

// Placeholder widget components
function WorkflowStatsWidget() {
  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="text-center">
        <div className="text-2xl font-bold text-blue-600">12</div>
        <div className="text-xs text-gray-500">Total Workflows</div>
      </div>
      <div className="text-center">
        <div className="text-2xl font-bold text-green-600">89%</div>
        <div className="text-xs text-gray-500">Success Rate</div>
      </div>
    </div>
  );
}

function RecentExecutionsWidget() {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-600">Data Pipeline</span>
        <span className="text-green-600">✓ Completed</span>
      </div>
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-600">Email Automation</span>
        <span className="text-green-600">✓ Completed</span>
      </div>
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-600">Report Generator</span>
        <span className="text-yellow-600">⏳ Running</span>
      </div>
    </div>
  );
}

function SystemHealthWidget() {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-600">API</span>
        <span className="w-2 h-2 bg-green-500 rounded-full"></span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-600">Database</span>
        <span className="w-2 h-2 bg-green-500 rounded-full"></span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-600">Redis</span>
        <span className="w-2 h-2 bg-green-500 rounded-full"></span>
      </div>
    </div>
  );
}

function QuickActionsWidget() {
  return (
    <div className="grid grid-cols-2 gap-2">
      <button className="p-2 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100">
        New Workflow
      </button>
      <button className="p-2 text-xs bg-green-50 text-green-700 rounded hover:bg-green-100">
        Run All
      </button>
      <button className="p-2 text-xs bg-purple-50 text-purple-700 rounded hover:bg-purple-100">
        View Logs
      </button>
      <button className="p-2 text-xs bg-gray-50 text-gray-700 rounded hover:bg-gray-100">
        Settings
      </button>
    </div>
  );
}

function NotificationsWidget() {
  return (
    <div className="text-sm text-gray-500 text-center py-4">
      No new notifications
    </div>
  );
}

interface AddWidgetModalProps {
  onAdd: (request: AddWidgetRequest) => Promise<void>;
  onClose: () => void;
}

function AddWidgetModal({ onAdd, onClose }: AddWidgetModalProps) {
  const [selectedType, setSelectedType] = useState<string>('');
  const [title, setTitle] = useState('');

  const widgetOptions = [
    { type: WIDGET_TYPES.WORKFLOW_STATS, label: 'Workflow Statistics', icon: '📊' },
    { type: WIDGET_TYPES.RECENT_EXECUTIONS, label: 'Recent Executions', icon: '📋' },
    { type: WIDGET_TYPES.SYSTEM_HEALTH, label: 'System Health', icon: '💚' },
    { type: WIDGET_TYPES.QUICK_ACTIONS, label: 'Quick Actions', icon: '⚡' },
    { type: WIDGET_TYPES.NOTIFICATIONS, label: 'Notifications', icon: '🔔' },
  ];

  const handleAdd = async () => {
    if (!selectedType) return;
    const option = widgetOptions.find(o => o.type === selectedType);
    await onAdd({
      type: selectedType,
      title: title || option?.label || 'Widget',
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md p-6">
        <h3 className="text-lg font-semibold mb-4">Add Widget</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Widget Type</label>
            <div className="grid grid-cols-2 gap-2">
              {widgetOptions.map((option) => (
                <button
                  key={option.type}
                  onClick={() => {
                    setSelectedType(option.type);
                    setTitle(option.label);
                  }}
                  className={cn(
                    'p-3 text-left rounded-lg border transition-colors',
                    selectedType === option.type
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 hover:border-gray-300 dark:border-gray-600'
                  )}
                >
                  <span className="text-lg mr-2">{option.icon}</span>
                  <span className="text-sm">{option.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg dark:bg-gray-700 dark:border-gray-600"
              placeholder="Widget title"
            />
          </div>
        </div>

        <div className="flex justify-end gap-2 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg"
          >
            Cancel
          </button>
          <button
            onClick={handleAdd}
            disabled={!selectedType}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            Add Widget
          </button>
        </div>
      </div>
    </div>
  );
}

export default DashboardGrid;
