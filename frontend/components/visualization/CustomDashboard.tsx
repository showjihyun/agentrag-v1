'use client';

/**
 * Custom Dashboard Component
 * Customizable dashboard with drag-and-drop widgets
 */

import React, { useState } from 'react';
import { cn } from '@/lib/utils';

interface Widget {
  id: string;
  type: 'chart' | 'stat' | 'list' | 'table';
  title: string;
  size: 'small' | 'medium' | 'large';
  position: { x: number; y: number };
  config: any;
}

interface CustomDashboardProps {
  userId?: string;
  className?: string;
}

export default function CustomDashboard({ userId, className }: CustomDashboardProps) {
  const [widgets, setWidgets] = useState<Widget[]>([
    {
      id: '1',
      type: 'stat',
      title: 'Total Queries',
      size: 'small',
      position: { x: 0, y: 0 },
      config: { value: 1234, trend: '+12%' },
    },
    {
      id: '2',
      type: 'chart',
      title: 'Usage Trend',
      size: 'medium',
      position: { x: 1, y: 0 },
      config: { chartType: 'line' },
    },
  ]);
  const [isEditMode, setIsEditMode] = useState(false);
  const [showWidgetPicker, setShowWidgetPicker] = useState(false);

  const availableWidgets = [
    { type: 'stat', title: 'Statistics Card', icon: '📊' },
    { type: 'chart', title: 'Chart Widget', icon: '📈' },
    { type: 'list', title: 'List Widget', icon: '📋' },
    { type: 'table', title: 'Table Widget', icon: '📑' },
  ];

  const handleAddWidget = (type: string) => {
    const newWidget: Widget = {
      id: Date.now().toString(),
      type: type as any,
      title: `New ${type}`,
      size: 'medium',
      position: { x: 0, y: widgets.length },
      config: {},
    };
    setWidgets([...widgets, newWidget]);
    setShowWidgetPicker(false);
  };

  const handleRemoveWidget = (widgetId: string) => {
    setWidgets(widgets.filter(w => w.id !== widgetId));
  };

  const handleSaveDashboard = async () => {
    try {
      const response = await fetch('/api/dashboard/layout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ widgets }),
      });
      
      if (!response.ok) throw new Error('Failed to save dashboard');
      
      alert('Dashboard saved successfully!');
      setIsEditMode(false);
    } catch (error) {
      console.error('Failed to save dashboard:', error);
      alert('Failed to save dashboard');
    }
  };

  const renderWidget = (widget: Widget) => {
    const sizeClasses = {
      small: 'col-span-1',
      medium: 'col-span-2',
      large: 'col-span-3',
    };

    return (
      <div
        key={widget.id}
        className={cn(
          'bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700',
          sizeClasses[widget.size],
          isEditMode && 'ring-2 ring-blue-500'
        )}
      >
        {/* Widget Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {widget.title}
          </h3>
          {isEditMode && (
            <div className="flex gap-2">
              <button
                onClick={() => handleRemoveWidget(widget.id)}
                className="p-1 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          )}
        </div>

        {/* Widget Content */}
        <div className="text-gray-600 dark:text-gray-400">
          {widget.type === 'stat' && (
            <div>
              <div className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                {widget.config.value || '0'}
              </div>
              {widget.config.trend && (
                <div className="text-sm text-green-600 dark:text-green-400">
                  {widget.config.trend}
                </div>
              )}
            </div>
          )}
          
          {widget.type === 'chart' && (
            <div className="h-48 flex items-center justify-center bg-gray-50 dark:bg-gray-900/50 rounded">
              <p className="text-sm">Chart visualization</p>
            </div>
          )}
          
          {widget.type === 'list' && (
            <ul className="space-y-2">
              <li className="p-2 bg-gray-50 dark:bg-gray-900/50 rounded">Item 1</li>
              <li className="p-2 bg-gray-50 dark:bg-gray-900/50 rounded">Item 2</li>
              <li className="p-2 bg-gray-50 dark:bg-gray-900/50 rounded">Item 3</li>
            </ul>
          )}
          
          {widget.type === 'table' && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left p-2">Column 1</th>
                    <th className="text-left p-2">Column 2</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <td className="p-2">Data 1</td>
                    <td className="p-2">Data 2</td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Custom Dashboard
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Customize your dashboard layout
          </p>
        </div>

        <div className="flex gap-2">
          {isEditMode ? (
            <>
              <button
                onClick={() => setShowWidgetPicker(true)}
                className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors"
              >
                <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Add Widget
              </button>
              <button
                onClick={handleSaveDashboard}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Save
              </button>
              <button
                onClick={() => setIsEditMode(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
            </>
          ) : (
            <button
              onClick={() => setIsEditMode(true)}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
            >
              <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              Edit Dashboard
            </button>
          )}
        </div>
      </div>

      {/* Widget Picker Modal */}
      {showWidgetPicker && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Add Widget
              </h3>
              <button
                onClick={() => setShowWidgetPicker(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {availableWidgets.map((widget) => (
                <button
                  key={widget.type}
                  onClick={() => handleAddWidget(widget.type)}
                  className="p-6 bg-gray-50 dark:bg-gray-900/50 rounded-lg border-2 border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-500 transition-colors text-left"
                >
                  <div className="text-4xl mb-3">{widget.icon}</div>
                  <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
                    {widget.title}
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Add a {widget.type} widget to your dashboard
                  </p>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Dashboard Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {widgets.map(renderWidget)}
      </div>

      {widgets.length === 0 && (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <p className="text-gray-600 dark:text-gray-400">No widgets added yet</p>
          <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
            Click "Edit Dashboard" to add widgets
          </p>
        </div>
      )}
    </div>
  );
}
