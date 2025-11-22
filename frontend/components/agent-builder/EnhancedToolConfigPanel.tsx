"use client";

/**
 * Enhanced Tool Config Panel
 * 
 * 50+ Tools의 상세한 Config를 위한 고급 패널
 * AdvancedToolConfigUI를 사용하여 Tool별 맞춤형 UI 제공
 */

import React from "react";
import { AdvancedToolConfigUI } from "./tool-configs";
import { getToolConfig } from "./tool-configs";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface Tool {
  id: string;
  name: string;
  description: string;
  category: string;
  params: Record<string, any>;
  outputs: Record<string, any>;
  icon?: string;
  bg_color?: string;
  docs_link?: string;
}

interface EnhancedToolConfigPanelProps {
  tool: Tool;
  initialConfig?: Record<string, any>;
  initialCredentials?: Record<string, any>;
  onSave: (config: Record<string, any>, credentials?: Record<string, any>) => void;
  onClose: () => void;
  open?: boolean;
}

export function EnhancedToolConfigPanel({
  tool,
  initialConfig = {},
  initialCredentials = {},
  onSave,
  onClose,
  open = true,
}: EnhancedToolConfigPanelProps) {
  // Check if we have a detailed config schema for this tool
  const hasDetailedSchema = !!getToolConfig(tool.id);

  const handleSave = (config: Record<string, any>, credentials: Record<string, any>) => {
    // Merge config and credentials for backward compatibility
    onSave(config, credentials);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span className="text-2xl">{tool.icon}</span>
            Configure {tool.name}
          </DialogTitle>
        </DialogHeader>
        
        {hasDetailedSchema ? (
          <AdvancedToolConfigUI
            toolId={tool.id}
            initialConfig={initialConfig}
            initialCredentials={initialCredentials}
            onSave={handleSave}
            onCancel={onClose}
          />
        ) : (
          <div className="p-6 space-y-4">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-sm text-yellow-800">
                ⚠️ Detailed configuration schema not available for this tool yet.
                Using basic configuration mode.
              </p>
            </div>
            
            {/* Fallback: Basic JSON editor */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Configuration (JSON)</label>
              <textarea
                className="w-full h-64 p-3 border rounded-md font-mono text-sm"
                defaultValue={JSON.stringify(initialConfig, null, 2)}
                onChange={(e) => {
                  try {
                    const config = JSON.parse(e.target.value);
                    // Store for save
                    (e.target as any)._parsedConfig = config;
                  } catch {
                    // Invalid JSON
                  }
                }}
              />
            </div>
            
            <div className="flex justify-end gap-2">
              <button
                onClick={onClose}
                className="px-4 py-2 border rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={(e) => {
                  const textarea = e.currentTarget.parentElement?.previousElementSibling?.querySelector('textarea');
                  const config = (textarea as any)?._parsedConfig || initialConfig;
                  handleSave(config, {});
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Save
              </button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
