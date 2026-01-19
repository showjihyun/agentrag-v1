'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AgenticBlockPalette } from '@/components/agent-builder/blocks/AgenticBlockPalette';
import { AgenticBlockConfigPanel } from '@/components/agent-builder/blocks/AgenticBlockConfigPanel';
import { BlockTypeConfig } from '@/lib/api/block-types';
import { Sparkles, Workflow, Settings, CheckCircle2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { Alert, AlertDescription } from '@/components/ui/alert';

export default function AgenticWorkflowDemoPage() {
  const [selectedBlock, setSelectedBlock] = useState<BlockTypeConfig | null>(null);
  const [blockConfig, setBlockConfig] = useState<Record<string, any>>({});
  const [savedConfigs, setSavedConfigs] = useState<Array<{ block: string; config: Record<string, any>; timestamp: Date }>>([]);
  const { toast } = useToast();

  const handleBlockSelect = (block: BlockTypeConfig) => {
    setSelectedBlock(block);
    // Initialize with default values
    const defaultConfig: Record<string, any> = {};
    block.sub_blocks.forEach((subBlock) => {
      if (subBlock.default !== undefined) {
        defaultConfig[subBlock.id] = subBlock.default;
      }
    });
    setBlockConfig(defaultConfig);
  };

  const handleConfigSave = (config: Record<string, any>) => {
    setBlockConfig(config);
    
    // Save to history
    if (selectedBlock) {
      setSavedConfigs(prev => [
        {
          block: selectedBlock.name,
          config,
          timestamp: new Date()
        },
        ...prev.slice(0, 4) // Keep last 5 configs
      ]);
    }
    
    // Show success toast
    toast({
      title: "Configuration Saved",
      description: `${selectedBlock?.name} configuration has been saved successfully.`,
      duration: 3000,
    });
    
    console.log('Saved configuration:', {
      block: selectedBlock?.name,
      config,
      timestamp: new Date().toISOString()
    });
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500">
            <Sparkles className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-4xl font-bold">Agentic Workflow Builder</h1>
            <p className="text-lg text-muted-foreground">
              Build intelligent workflows with self-improving AI blocks
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 mt-4">
          <Badge variant="outline" className="bg-purple-500/10 text-purple-700">
            4 Agentic Blocks
          </Badge>
          <Badge variant="outline" className="bg-blue-500/10 text-blue-700">
            Drag & Drop
          </Badge>
          <Badge variant="outline" className="bg-green-500/10 text-green-700">
            Production Ready
          </Badge>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Panel - Block Palette */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Workflow className="h-5 w-5 text-primary" />
                <CardTitle>Available Blocks</CardTitle>
              </div>
              <CardDescription>
                Select a block to configure or drag it onto your workflow canvas
              </CardDescription>
            </CardHeader>
            <CardContent>
              <AgenticBlockPalette
                onBlockSelect={handleBlockSelect}
                onBlockDragStart={(block) => console.log('Drag started:', block)}
              />
            </CardContent>
          </Card>
        </div>

        {/* Right Panel - Configuration */}
        <div className="lg:col-span-1">
          <Card className="sticky top-4">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Settings className="h-5 w-5 text-primary" />
                <CardTitle>Configuration</CardTitle>
              </div>
              <CardDescription>
                {selectedBlock
                  ? `Configure ${selectedBlock.name}`
                  : 'Select a block to configure'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {selectedBlock ? (
                <AgenticBlockConfigPanel
                  block={selectedBlock}
                  initialConfig={blockConfig}
                  onSave={handleConfigSave}
                  onCancel={() => setSelectedBlock(null)}
                />
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Select a block from the palette to configure it</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-950 dark:to-purple-900 border-purple-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Reflection</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              Self-evaluate and iteratively improve responses with quality scoring
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950 dark:to-green-900 border-green-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Planning</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              Decompose complex tasks into subtasks with dependency management
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-50 to-amber-100 dark:from-amber-950 dark:to-amber-900 border-amber-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Tool Selector</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              Dynamically select the best tool based on task requirements
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-pink-50 to-pink-100 dark:from-pink-950 dark:to-pink-900 border-pink-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Agentic RAG</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              Intelligent retrieval with query decomposition and reflection
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Saved Configurations */}
      {savedConfigs.length > 0 && (
        <Card className="mt-8 border-green-200 bg-green-50/50 dark:bg-green-950/20">
          <CardHeader>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              <CardTitle className="text-lg">Saved Configurations</CardTitle>
            </div>
            <CardDescription>
              Recently saved block configurations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {savedConfigs.map((saved, index) => (
                <Alert key={index} className="bg-white dark:bg-gray-900">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <AlertDescription>
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-semibold">{saved.block}</span>
                        <span className="text-xs text-muted-foreground ml-2">
                          {saved.timestamp.toLocaleTimeString()}
                        </span>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {Object.keys(saved.config).length} params
                      </Badge>
                    </div>
                    <div className="mt-2 text-xs text-muted-foreground">
                      {Object.entries(saved.config).slice(0, 3).map(([key, value]) => (
                        <div key={key}>
                          <span className="font-medium">{key}:</span> {String(value)}
                        </div>
                      ))}
                      {Object.keys(saved.config).length > 3 && (
                        <div className="text-xs italic">
                          +{Object.keys(saved.config).length - 3} more...
                        </div>
                      )}
                    </div>
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Usage Example */}
      <Card className="mt-8 bg-muted/50">
        <CardHeader>
          <CardTitle className="text-lg">💡 Quick Start</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            <strong>1. Select a block</strong> from the palette above
          </p>
          <p>
            <strong>2. Configure</strong> the block parameters in the right panel
          </p>
          <p>
            <strong>3. Save</strong> the configuration to add it to your workflow
          </p>
          <p>
            <strong>4. Connect blocks</strong> to create intelligent multi-step workflows
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
