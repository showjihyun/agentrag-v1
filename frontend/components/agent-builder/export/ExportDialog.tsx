'use client';

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Checkbox } from '@/components/ui/checkbox';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { Download, FileJson, FileCode, FileText, Package } from 'lucide-react';

interface ExportDialogProps {
  resourceType: 'agent' | 'workflow' | 'block';
  resourceId: string;
  resourceName: string;
}

export function ExportDialog({ resourceType, resourceId, resourceName }: ExportDialogProps) {
  const { toast } = useToast();
  const [open, setOpen] = useState(false);
  const [format, setFormat] = useState<'json' | 'yaml' | 'python' | 'typescript'>('json');
  const [includeMetadata, setIncludeMetadata] = useState(true);
  const [includeHistory, setIncludeHistory] = useState(false);
  const [includeMetrics, setIncludeMetrics] = useState(false);
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    setExporting(true);
    try {
      const blob = await agentBuilderAPI.exportResource(resourceType, resourceId, {
        format,
        include_metadata: includeMetadata,
        include_history: includeHistory,
        include_metrics: includeMetrics,
      });

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${resourceName}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: 'Export Successful',
        description: `${resourceName} has been exported as ${format.toUpperCase()}`,
      });

      setOpen(false);
    } catch (error: any) {
      toast({
        title: 'Export Failed',
        description: error.message || 'Failed to export resource',
        variant: 'destructive',
      });
    } finally {
      setExporting(false);
    }
  };

  const getFormatIcon = (fmt: string) => {
    switch (fmt) {
      case 'json':
        return <FileJson className="h-4 w-4" />;
      case 'yaml':
        return <FileText className="h-4 w-4" />;
      case 'python':
      case 'typescript':
        return <FileCode className="h-4 w-4" />;
      default:
        return <Package className="h-4 w-4" />;
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">
          <Download className="mr-2 h-4 w-4" />
          Export
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Export {resourceType}</DialogTitle>
          <DialogDescription>
            Export "{resourceName}" in your preferred format
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Format Selection */}
          <div className="space-y-3">
            <Label>Export Format</Label>
            <RadioGroup value={format} onValueChange={(v: any) => setFormat(v)}>
              <div className="flex items-center space-x-2 p-3 border rounded-md hover:bg-accent cursor-pointer">
                <RadioGroupItem value="json" id="json" />
                <Label htmlFor="json" className="flex items-center gap-2 cursor-pointer flex-1">
                  {getFormatIcon('json')}
                  <div>
                    <div className="font-medium">JSON</div>
                    <div className="text-xs text-muted-foreground">
                      Standard JSON format, easy to parse
                    </div>
                  </div>
                </Label>
              </div>

              <div className="flex items-center space-x-2 p-3 border rounded-md hover:bg-accent cursor-pointer">
                <RadioGroupItem value="yaml" id="yaml" />
                <Label htmlFor="yaml" className="flex items-center gap-2 cursor-pointer flex-1">
                  {getFormatIcon('yaml')}
                  <div>
                    <div className="font-medium">YAML</div>
                    <div className="text-xs text-muted-foreground">
                      Human-readable configuration format
                    </div>
                  </div>
                </Label>
              </div>

              <div className="flex items-center space-x-2 p-3 border rounded-md hover:bg-accent cursor-pointer">
                <RadioGroupItem value="python" id="python" />
                <Label htmlFor="python" className="flex items-center gap-2 cursor-pointer flex-1">
                  {getFormatIcon('python')}
                  <div>
                    <div className="font-medium">Python Code</div>
                    <div className="text-xs text-muted-foreground">
                      Ready-to-use Python implementation
                    </div>
                  </div>
                </Label>
              </div>

              <div className="flex items-center space-x-2 p-3 border rounded-md hover:bg-accent cursor-pointer">
                <RadioGroupItem value="typescript" id="typescript" />
                <Label htmlFor="typescript" className="flex items-center gap-2 cursor-pointer flex-1">
                  {getFormatIcon('typescript')}
                  <div>
                    <div className="font-medium">TypeScript Code</div>
                    <div className="text-xs text-muted-foreground">
                      Ready-to-use TypeScript implementation
                    </div>
                  </div>
                </Label>
              </div>
            </RadioGroup>
          </div>

          {/* Options */}
          <div className="space-y-3">
            <Label>Include Additional Data</Label>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="metadata"
                  checked={includeMetadata}
                  onCheckedChange={(checked) => setIncludeMetadata(checked as boolean)}
                />
                <Label htmlFor="metadata" className="cursor-pointer">
                  Metadata (author, timestamps, etc.)
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="history"
                  checked={includeHistory}
                  onCheckedChange={(checked) => setIncludeHistory(checked as boolean)}
                />
                <Label htmlFor="history" className="cursor-pointer">
                  Version history
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="metrics"
                  checked={includeMetrics}
                  onCheckedChange={(checked) => setIncludeMetrics(checked as boolean)}
                />
                <Label htmlFor="metrics" className="cursor-pointer">
                  Performance metrics
                </Label>
              </div>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleExport} disabled={exporting}>
            {exporting ? 'Exporting...' : 'Export'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
