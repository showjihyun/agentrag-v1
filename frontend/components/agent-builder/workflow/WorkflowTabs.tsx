import { memo, ReactNode } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Bug, Activity, Sparkles, Workflow } from 'lucide-react';

export type WorkflowTabValue = 'canvas' | 'debug' | 'performance' | 'ai';

interface WorkflowTabsProps {
  activeTab: WorkflowTabValue;
  onTabChange: (tab: WorkflowTabValue) => void;
  canvasContent: ReactNode;
  debugContent: ReactNode;
  performanceContent: ReactNode;
  aiContent: ReactNode;
}

export const WorkflowTabs = memo(function WorkflowTabs({
  activeTab,
  onTabChange,
  canvasContent,
  debugContent,
  performanceContent,
  aiContent,
}: WorkflowTabsProps) {
  return (
    <Tabs 
      value={activeTab} 
      onValueChange={(v) => onTabChange(v as WorkflowTabValue)}
      className="flex-1 flex flex-col"
    >
      <TabsList className="w-full justify-start border-b rounded-none h-12 bg-background">
        <TabsTrigger 
          value="canvas" 
          className="gap-2"
          aria-label="Workflow canvas"
        >
          <Workflow className="h-4 w-4" aria-hidden="true" />
          Canvas
        </TabsTrigger>
        <TabsTrigger 
          value="debug" 
          className="gap-2"
          aria-label="Debug panel"
        >
          <Bug className="h-4 w-4" aria-hidden="true" />
          Debug
        </TabsTrigger>
        <TabsTrigger 
          value="performance" 
          className="gap-2"
          aria-label="Performance metrics"
        >
          <Activity className="h-4 w-4" aria-hidden="true" />
          Performance
        </TabsTrigger>
        <TabsTrigger 
          value="ai" 
          className="gap-2"
          aria-label="AI assistant"
        >
          <Sparkles className="h-4 w-4" aria-hidden="true" />
          AI Assistant
        </TabsTrigger>
      </TabsList>

      <TabsContent value="canvas" className="flex-1 m-0">
        {canvasContent}
      </TabsContent>

      <TabsContent value="debug" className="flex-1 m-0 p-4">
        {debugContent}
      </TabsContent>

      <TabsContent value="performance" className="flex-1 m-0 p-4">
        {performanceContent}
      </TabsContent>

      <TabsContent value="ai" className="flex-1 m-0 p-4">
        {aiContent}
      </TabsContent>
    </Tabs>
  );
});
