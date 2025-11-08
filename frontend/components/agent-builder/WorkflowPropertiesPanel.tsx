'use client';

import { useState, useEffect } from 'react';
import { Node } from 'reactflow';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Save, X } from 'lucide-react';

interface WorkflowPropertiesPanelProps {
  node: Node | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: (nodeId: string, updates: Partial<Node['data']>) => void;
}

export default function WorkflowPropertiesPanel({
  node,
  isOpen,
  onClose,
  onUpdate,
}: WorkflowPropertiesPanelProps) {
  const [localData, setLocalData] = useState<any>({});

  useEffect(() => {
    if (node) {
      setLocalData(node.data);
    }
  }, [node]);

  const handleSave = () => {
    if (node) {
      onUpdate(node.id, localData);
      onClose();
    }
  };

  const updateField = (field: string, value: any) => {
    setLocalData((prev: any) => ({ ...prev, [field]: value }));
  };

  if (!node) return null;

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent className="w-[400px] sm:w-[540px]">
        <SheetHeader>
          <SheetTitle>Node Properties</SheetTitle>
          <SheetDescription>
            Configure the selected {node.type} node
          </SheetDescription>
        </SheetHeader>

        <ScrollArea className="h-[calc(100vh-12rem)] mt-6">
          <div className="space-y-6 pr-4">
            {/* Basic Properties */}
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="node-name">Node Name</Label>
                <Input
                  id="node-name"
                  value={localData.label || ''}
                  onChange={(e) => updateField('label', e.target.value)}
                  placeholder="Enter node name"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="node-description">Description</Label>
                <Textarea
                  id="node-description"
                  value={localData.description || ''}
                  onChange={(e) => updateField('description', e.target.value)}
                  placeholder="Enter node description"
                  rows={3}
                />
              </div>
            </div>

            <Separator />

            {/* Agent-specific Configuration */}
            {node.type === 'agent' && (
              <div className="space-y-4">
                <h4 className="font-semibold">Agent Configuration</h4>
                
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Agent Details</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Agent ID:</span>
                      <code className="text-xs">{localData.id}</code>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Type:</span>
                      <Badge variant="outline">{localData.agent_type || 'custom'}</Badge>
                    </div>
                  </CardContent>
                </Card>

                <Accordion type="single" collapsible>
                  <AccordionItem value="input-mapping">
                    <AccordionTrigger>Input Mapping</AccordionTrigger>
                    <AccordionContent>
                      <div className="space-y-3">
                        <p className="text-sm text-muted-foreground">
                          Map workflow variables to agent inputs
                        </p>
                        <div className="space-y-2">
                          <Label htmlFor="query-mapping">Query Input</Label>
                          <Input
                            id="query-mapping"
                            placeholder="${'workflow.input.query'}"
                            value={localData.inputMapping?.query || ''}
                            onChange={(e) =>
                              updateField('inputMapping', {
                                ...localData.inputMapping,
                                query: e.target.value,
                              })
                            }
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="context-mapping">Context Input</Label>
                          <Input
                            id="context-mapping"
                            placeholder="${'workflow.context'}"
                            value={localData.inputMapping?.context || ''}
                            onChange={(e) =>
                              updateField('inputMapping', {
                                ...localData.inputMapping,
                                context: e.target.value,
                              })
                            }
                          />
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="output-mapping">
                    <AccordionTrigger>Output Mapping</AccordionTrigger>
                    <AccordionContent>
                      <div className="space-y-3">
                        <p className="text-sm text-muted-foreground">
                          Map agent outputs to workflow variables
                        </p>
                        <div className="space-y-2">
                          <Label htmlFor="output-var">Output Variable</Label>
                          <Input
                            id="output-var"
                            placeholder="agent_output"
                            value={localData.outputVariable || ''}
                            onChange={(e) => updateField('outputVariable', e.target.value)}
                          />
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
              </div>
            )}

            {/* Block-specific Configuration */}
            {node.type === 'block' && (
              <div className="space-y-4">
                <h4 className="font-semibold">Block Configuration</h4>
                
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Block Details</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Block ID:</span>
                      <code className="text-xs">{localData.id}</code>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Type:</span>
                      <Badge variant="outline" className="capitalize">
                        {localData.block_type}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>

                <Accordion type="single" collapsible>
                  <AccordionItem value="block-params">
                    <AccordionTrigger>Block Parameters</AccordionTrigger>
                    <AccordionContent>
                      <div className="space-y-3">
                        <p className="text-sm text-muted-foreground">
                          Configure block-specific parameters
                        </p>
                        <div className="space-y-2">
                          <Label htmlFor="block-config">Configuration (JSON)</Label>
                          <Textarea
                            id="block-config"
                            placeholder='{"param1": "value1"}'
                            className="font-mono text-sm"
                            rows={5}
                            value={
                              localData.configuration
                                ? JSON.stringify(localData.configuration, null, 2)
                                : ''
                            }
                            onChange={(e) => {
                              try {
                                const config = JSON.parse(e.target.value);
                                updateField('configuration', config);
                              } catch {
                                // Invalid JSON, don't update
                              }
                            }}
                          />
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="block-io">
                    <AccordionTrigger>Input/Output Mapping</AccordionTrigger>
                    <AccordionContent>
                      <div className="space-y-3">
                        <div className="space-y-2">
                          <Label htmlFor="block-input">Input Mapping</Label>
                          <Textarea
                            id="block-input"
                            placeholder="Map workflow variables to block inputs"
                            rows={3}
                            value={localData.inputMapping || ''}
                            onChange={(e) => updateField('inputMapping', e.target.value)}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="block-output">Output Variable</Label>
                          <Input
                            id="block-output"
                            placeholder="block_output"
                            value={localData.outputVariable || ''}
                            onChange={(e) => updateField('outputVariable', e.target.value)}
                          />
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
              </div>
            )}

            {/* Control-specific Configuration */}
            {node.type === 'control' && (
              <div className="space-y-4">
                <h4 className="font-semibold">Control Configuration</h4>
                
                <div className="space-y-2">
                  <Label htmlFor="control-type">Control Type</Label>
                  <Select
                    value={localData.controlType || 'conditional'}
                    onValueChange={(value) => updateField('controlType', value)}
                  >
                    <SelectTrigger id="control-type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="conditional">Conditional</SelectItem>
                      <SelectItem value="loop">Loop</SelectItem>
                      <SelectItem value="parallel">Parallel</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {localData.controlType === 'conditional' && (
                  <div className="space-y-2">
                    <Label htmlFor="condition">Condition Expression</Label>
                    <Textarea
                      id="condition"
                      placeholder="state['previous_output'] > 0"
                      className="font-mono text-sm"
                      rows={4}
                      value={localData.condition || ''}
                      onChange={(e) => updateField('condition', e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">
                      Python expression with access to workflow state
                    </p>
                  </div>
                )}

                {localData.controlType === 'loop' && (
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="loop-type">Loop Type</Label>
                      <Select
                        value={localData.loopType || 'for-each'}
                        onValueChange={(value) => updateField('loopType', value)}
                      >
                        <SelectTrigger id="loop-type">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="for-each">For Each</SelectItem>
                          <SelectItem value="while">While</SelectItem>
                          <SelectItem value="until">Until</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="loop-condition">Loop Condition</Label>
                      <Textarea
                        id="loop-condition"
                        placeholder="items in state['collection']"
                        className="font-mono text-sm"
                        rows={3}
                        value={localData.loopCondition || ''}
                        onChange={(e) => updateField('loopCondition', e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="max-iterations">Max Iterations</Label>
                      <Input
                        id="max-iterations"
                        type="number"
                        placeholder="100"
                        value={localData.maxIterations || ''}
                        onChange={(e) => updateField('maxIterations', parseInt(e.target.value))}
                      />
                    </div>
                  </>
                )}

                {localData.controlType === 'parallel' && (
                  <div className="space-y-2">
                    <Label htmlFor="parallel-branches">Number of Branches</Label>
                    <Input
                      id="parallel-branches"
                      type="number"
                      placeholder="2"
                      value={localData.parallelBranches || 2}
                      onChange={(e) =>
                        updateField('parallelBranches', parseInt(e.target.value))
                      }
                    />
                    <p className="text-xs text-muted-foreground">
                      Number of parallel execution branches
                    </p>
                  </div>
                )}
              </div>
            )}

            <Separator />

            {/* Error Handling */}
            <div className="space-y-4">
              <h4 className="font-semibold">Error Handling</h4>
              
              <Accordion type="single" collapsible>
                <AccordionItem value="error-config">
                  <AccordionTrigger>Error Configuration</AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-3">
                      <div className="space-y-2">
                        <Label htmlFor="retry-count">Retry Count</Label>
                        <Input
                          id="retry-count"
                          type="number"
                          placeholder="3"
                          value={localData.errorHandling?.retryCount || ''}
                          onChange={(e) =>
                            updateField('errorHandling', {
                              ...localData.errorHandling,
                              retryCount: parseInt(e.target.value),
                            })
                          }
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="fallback-value">Fallback Value</Label>
                        <Input
                          id="fallback-value"
                          placeholder="null"
                          value={localData.errorHandling?.fallbackValue || ''}
                          onChange={(e) =>
                            updateField('errorHandling', {
                              ...localData.errorHandling,
                              fallbackValue: e.target.value,
                            })
                          }
                        />
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </div>
          </div>
        </ScrollArea>

        {/* Footer Actions */}
        <div className="absolute bottom-0 left-0 right-0 border-t bg-background p-4">
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              <X className="mr-2 h-4 w-4" />
              Cancel
            </Button>
            <Button onClick={handleSave}>
              <Save className="mr-2 h-4 w-4" />
              Save Changes
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
