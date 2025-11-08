# Agent Builder UI/UX Design with shadcn/ui

This document provides detailed UI/UX specifications for the Agent Builder feature using shadcn/ui components.

## Design System

### shadcn/ui Components

The Agent Builder will use shadcn/ui components for consistent, accessible, and beautiful UI. All components follow the existing AgenticRAG design system with Tailwind CSS.

**Core shadcn/ui Components to Install:**
```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add input
npx shadcn-ui@latest add label
npx shadcn-ui@latest add select
npx shadcn-ui@latest add textarea
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add separator
npx shadcn-ui@latest add scroll-area
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add alert
npx shadcn-ui@latest add skeleton
npx shadcn-ui@latest add table
npx shadcn-ui@latest add form
npx shadcn-ui@latest add popover
npx shadcn-ui@latest add command
npx shadcn-ui@latest add sheet
npx shadcn-ui@latest add accordion
npx shadcn-ui@latest add switch
npx shadcn-ui@latest add slider
npx shadcn-ui@latest add progress
npx shadcn-ui@latest add avatar
npx shadcn-ui@latest add tooltip
npx shadcn-ui@latest add context-menu
npx shadcn-ui@latest add resizable
```

### Color Palette

Following AgenticRAG's existing theme:
- Primary: Blue (existing theme)
- Secondary: Gray
- Success: Green
- Warning: Yellow
- Error: Red
- Info: Blue

### Typography

- Headings: Inter font family
- Body: Inter font family
- Code: Fira Code / Monaco

---

## Page Layouts

### 1. Agent Builder Main Layout

**Route:** `/agent-builder`

**Layout Structure:**
```tsx
<div className="flex h-screen bg-background">
  {/* Sidebar Navigation */}
  <aside className="w-64 border-r bg-card">
    <ScrollArea className="h-full">
      <nav className="space-y-2 p-4">
        <Button variant="ghost" className="w-full justify-start">
          <Layers className="mr-2 h-4 w-4" />
          Agents
        </Button>
        <Button variant="ghost" className="w-full justify-start">
          <Box className="mr-2 h-4 w-4" />
          Blocks
        </Button>
        <Button variant="ghost" className="w-full justify-start">
          <GitBranch className="mr-2 h-4 w-4" />
          Workflows
        </Button>
        <Button variant="ghost" className="w-full justify-start">
          <Database className="mr-2 h-4 w-4" />
          Knowledgebases
        </Button>
        <Button variant="ghost" className="w-full justify-start">
          <Variable className="mr-2 h-4 w-4" />
          Variables
        </Button>
        <Button variant="ghost" className="w-full justify-start">
          <Activity className="mr-2 h-4 w-4" />
          Executions
        </Button>
      </nav>
    </ScrollArea>
  </aside>

  {/* Main Content */}
  <main className="flex-1 overflow-auto">
    {children}
  </main>
</div>
```

**shadcn/ui Components Used:**
- `Button` (variant: ghost)
- `ScrollArea`
- Lucide icons

---

## Component Designs

### 2. Agent List Page

**Route:** `/agent-builder/agents`

**UI Components:**

```tsx
<div className="container mx-auto p-6 space-y-6">
  {/* Header */}
  <div className="flex items-center justify-between">
    <div>
      <h1 className="text-3xl font-bold">Agents</h1>
      <p className="text-muted-foreground">
        Create and manage your AI agents
      </p>
    </div>
    <Button onClick={handleCreateAgent}>
      <Plus className="mr-2 h-4 w-4" />
      Create Agent
    </Button>
  </div>

  {/* Search and Filters */}
  <div className="flex gap-4">
    <div className="flex-1">
      <Input
        placeholder="Search agents..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        className="max-w-sm"
      />
    </div>
    <Select value={filterType} onValueChange={setFilterType}>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Filter by type" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">All Types</SelectItem>
        <SelectItem value="custom">Custom</SelectItem>
        <SelectItem value="template">From Template</SelectItem>
      </SelectContent>
    </Select>
  </div>

  {/* Agent Grid */}
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {agents.map((agent) => (
      <Card key={agent.id} className="hover:shadow-lg transition-shadow">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <Avatar className="h-10 w-10">
                <AvatarFallback>
                  {agent.name.substring(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div>
                <CardTitle className="text-lg">{agent.name}</CardTitle>
                <CardDescription className="text-sm">
                  {agent.agent_type}
                </CardDescription>
              </div>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => handleEdit(agent.id)}>
                  <Edit className="mr-2 h-4 w-4" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleClone(agent.id)}>
                  <Copy className="mr-2 h-4 w-4" />
                  Clone
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleExport(agent.id)}>
                  <Download className="mr-2 h-4 w-4" />
                  Export
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem 
                  onClick={() => handleDelete(agent.id)}
                  className="text-destructive"
                >
                  <Trash className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground line-clamp-2">
            {agent.description}
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {agent.tools.map((tool) => (
              <Badge key={tool} variant="secondary">
                {tool}
              </Badge>
            ))}
          </div>
        </CardContent>
        <CardFooter className="flex justify-between">
          <div className="text-xs text-muted-foreground">
            Updated {formatDate(agent.updated_at)}
          </div>
          <Button 
            size="sm" 
            variant="outline"
            onClick={() => handleTest(agent.id)}
          >
            <Play className="mr-2 h-3 w-3" />
            Test
          </Button>
        </CardFooter>
      </Card>
    ))}
  </div>
</div>
```

**shadcn/ui Components:**
- `Button`
- `Input`
- `Select`, `SelectTrigger`, `SelectContent`, `SelectItem`
- `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`
- `Avatar`, `AvatarFallback`
- `DropdownMenu`, `DropdownMenuTrigger`, `DropdownMenuContent`, `DropdownMenuItem`, `DropdownMenuSeparator`
- `Badge`

---

### 3. Agent Creation/Edit Form

**Route:** `/agent-builder/agents/new` or `/agent-builder/agents/:id/edit`

```tsx
<div className="container mx-auto p-6 max-w-4xl">
  <Card>
    <CardHeader>
      <CardTitle>Create New Agent</CardTitle>
      <CardDescription>
        Configure your agent with tools, prompts, and settings
      </CardDescription>
    </CardHeader>
    <CardContent>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Basic Information</h3>
            
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Agent Name</FormLabel>
                  <FormControl>
                    <Input placeholder="My Custom Agent" {...field} />
                  </FormControl>
                  <FormDescription>
                    A unique name for your agent
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea 
                      placeholder="Describe what your agent does..."
                      className="resize-none"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <Separator />

          {/* LLM Configuration */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">LLM Configuration</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="llm_provider"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>LLM Provider</FormLabel>
                    <Select 
                      onValueChange={field.onChange} 
                      defaultValue={field.value}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select provider" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="ollama">Ollama</SelectItem>
                        <SelectItem value="openai">OpenAI</SelectItem>
                        <SelectItem value="claude">Claude</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="llm_model"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Model</FormLabel>
                    <Select 
                      onValueChange={field.onChange} 
                      defaultValue={field.value}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select model" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="llama3.1">Llama 3.1</SelectItem>
                        <SelectItem value="gpt-4">GPT-4</SelectItem>
                        <SelectItem value="claude-3">Claude 3</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          </div>

          <Separator />

          {/* Tool Selection */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Tools</h3>
              <Button 
                type="button" 
                variant="outline" 
                size="sm"
                onClick={handleAddTool}
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Tool
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {availableTools.map((tool) => (
                <Card 
                  key={tool.id}
                  className={cn(
                    "cursor-pointer transition-all",
                    selectedTools.includes(tool.id) && "ring-2 ring-primary"
                  )}
                  onClick={() => toggleTool(tool.id)}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm">{tool.name}</CardTitle>
                      <Switch 
                        checked={selectedTools.includes(tool.id)}
                        onCheckedChange={() => toggleTool(tool.id)}
                      />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-xs text-muted-foreground">
                      {tool.description}
                    </p>
                    <Badge variant="outline" className="mt-2">
                      {tool.category}
                    </Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          <Separator />

          {/* Prompt Template */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Prompt Template</h3>
              <Button 
                type="button" 
                variant="outline" 
                size="sm"
                onClick={handleOpenPromptEditor}
              >
                <Code className="mr-2 h-4 w-4" />
                Advanced Editor
              </Button>
            </div>

            <FormField
              control={form.control}
              name="prompt_template"
              render={({ field }) => (
                <FormItem>
                  <FormControl>
                    <Textarea 
                      placeholder="Enter your prompt template with variables like ${query}, ${context}..."
                      className="font-mono text-sm min-h-[200px]"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    Use ${"{variable_name}"} for variable substitution
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          {/* Form Actions */}
          <div className="flex justify-end gap-4">
            <Button type="button" variant="outline" onClick={handleCancel}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Create Agent
            </Button>
          </div>
        </form>
      </Form>
    </CardContent>
  </Card>
</div>
```

**shadcn/ui Components:**
- `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`
- `Form`, `FormField`, `FormItem`, `FormLabel`, `FormControl`, `FormDescription`, `FormMessage`
- `Input`
- `Textarea`
- `Select`, `SelectTrigger`, `SelectValue`, `SelectContent`, `SelectItem`
- `Button`
- `Separator`
- `Switch`
- `Badge`

---


### 4. Workflow Designer Canvas

**Route:** `/agent-builder/workflows/:id/designer`

```tsx
<div className="flex h-screen flex-col">
  {/* Toolbar */}
  <div className="border-b bg-card p-4">
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={handleBack}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h2 className="text-lg font-semibold">{workflow.name}</h2>
          <p className="text-sm text-muted-foreground">Workflow Designer</p>
        </div>
      </div>
      
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={handleValidate}>
          <CheckCircle className="mr-2 h-4 w-4" />
          Validate
        </Button>
        <Button variant="outline" size="sm" onClick={handleSave}>
          <Save className="mr-2 h-4 w-4" />
          Save
        </Button>
        <Button size="sm" onClick={handleRun}>
          <Play className="mr-2 h-4 w-4" />
          Run
        </Button>
      </div>
    </div>
  </div>

  <div className="flex flex-1 overflow-hidden">
    {/* Node Palette */}
    <aside className="w-64 border-r bg-card overflow-auto">
      <ScrollArea className="h-full">
        <div className="p-4 space-y-4">
          <div>
            <h3 className="text-sm font-semibold mb-2">Agents</h3>
            <div className="space-y-2">
              {agents.map((agent) => (
                <Card
                  key={agent.id}
                  className="cursor-move hover:shadow-md transition-shadow"
                  draggable
                  onDragStart={(e) => handleDragStart(e, 'agent', agent)}
                >
                  <CardContent className="p-3">
                    <div className="flex items-center gap-2">
                      <Bot className="h-4 w-4 text-primary" />
                      <span className="text-sm font-medium">{agent.name}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          <Separator />

          <div>
            <h3 className="text-sm font-semibold mb-2">Blocks</h3>
            <div className="space-y-2">
              {blocks.map((block) => (
                <Card
                  key={block.id}
                  className="cursor-move hover:shadow-md transition-shadow"
                  draggable
                  onDragStart={(e) => handleDragStart(e, 'block', block)}
                >
                  <CardContent className="p-3">
                    <div className="flex items-center gap-2">
                      <Box className="h-4 w-4 text-secondary" />
                      <span className="text-sm font-medium">{block.name}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          <Separator />

          <div>
            <h3 className="text-sm font-semibold mb-2">Control Flow</h3>
            <div className="space-y-2">
              <Card className="cursor-move" draggable>
                <CardContent className="p-3">
                  <div className="flex items-center gap-2">
                    <GitBranch className="h-4 w-4 text-yellow-500" />
                    <span className="text-sm font-medium">Conditional</span>
                  </div>
                </CardContent>
              </Card>
              <Card className="cursor-move" draggable>
                <CardContent className="p-3">
                  <div className="flex items-center gap-2">
                    <Repeat className="h-4 w-4 text-green-500" />
                    <span className="text-sm font-medium">Loop</span>
                  </div>
                </CardContent>
              </Card>
              <Card className="cursor-move" draggable>
                <CardContent className="p-3">
                  <div className="flex items-center gap-2">
                    <Layers className="h-4 w-4 text-purple-500" />
                    <span className="text-sm font-medium">Parallel</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </ScrollArea>
    </aside>

    {/* React Flow Canvas */}
    <div className="flex-1 bg-muted/20">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>

    {/* Properties Panel */}
    <Sheet open={selectedNode !== null} onOpenChange={handleCloseProperties}>
      <SheetContent className="w-[400px] sm:w-[540px]">
        <SheetHeader>
          <SheetTitle>Node Properties</SheetTitle>
          <SheetDescription>
            Configure the selected node
          </SheetDescription>
        </SheetHeader>
        
        {selectedNode && (
          <ScrollArea className="h-[calc(100vh-8rem)] mt-6">
            <div className="space-y-6">
              <div className="space-y-2">
                <Label>Node Name</Label>
                <Input 
                  value={selectedNode.data.label}
                  onChange={(e) => updateNodeLabel(e.target.value)}
                />
              </div>

              <Separator />

              {selectedNode.type === 'agent' && (
                <div className="space-y-4">
                  <h4 className="font-semibold">Agent Configuration</h4>
                  {/* Agent-specific config */}
                </div>
              )}

              {selectedNode.type === 'block' && (
                <div className="space-y-4">
                  <h4 className="font-semibold">Block Configuration</h4>
                  {/* Block-specific config */}
                </div>
              )}

              {selectedNode.type === 'conditional' && (
                <div className="space-y-4">
                  <h4 className="font-semibold">Condition</h4>
                  <Textarea
                    placeholder="Enter Python expression..."
                    className="font-mono text-sm"
                  />
                </div>
              )}
            </div>
          </ScrollArea>
        )}
      </SheetContent>
    </Sheet>
  </div>
</div>
```

**shadcn/ui Components:**
- `Button`
- `Card`, `CardContent`
- `ScrollArea`
- `Separator`
- `Sheet`, `SheetContent`, `SheetHeader`, `SheetTitle`, `SheetDescription`
- `Label`
- `Input`
- `Textarea`
- React Flow (external library)

---

### 5. Agent Test Panel (Dialog)

```tsx
<Dialog open={isTestOpen} onOpenChange={setIsTestOpen}>
  <DialogContent className="max-w-4xl max-h-[80vh]">
    <DialogHeader>
      <DialogTitle>Test Agent: {agent.name}</DialogTitle>
      <DialogDescription>
        Run a test execution and see real-time results
      </DialogDescription>
    </DialogHeader>

    <div className="grid grid-cols-2 gap-6 overflow-auto">
      {/* Input Panel */}
      <div className="space-y-4">
        <div>
          <Label htmlFor="test-query">Query</Label>
          <Textarea
            id="test-query"
            placeholder="Enter your test query..."
            value={testQuery}
            onChange={(e) => setTestQuery(e.target.value)}
            className="mt-2"
          />
        </div>

        <div>
          <Label>Context Variables</Label>
          <Accordion type="single" collapsible className="mt-2">
            <AccordionItem value="variables">
              <AccordionTrigger>
                <span className="text-sm">Add context variables</span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-2">
                  {contextVars.map((v, i) => (
                    <div key={i} className="flex gap-2">
                      <Input 
                        placeholder="Key" 
                        value={v.key}
                        onChange={(e) => updateContextVar(i, 'key', e.target.value)}
                      />
                      <Input 
                        placeholder="Value" 
                        value={v.value}
                        onChange={(e) => updateContextVar(i, 'value', e.target.value)}
                      />
                      <Button 
                        variant="ghost" 
                        size="icon"
                        onClick={() => removeContextVar(i)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={addContextVar}
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Add Variable
                  </Button>
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>

        <Button 
          className="w-full" 
          onClick={handleRunTest}
          disabled={isRunning}
        >
          {isRunning ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Running...
            </>
          ) : (
            <>
              <Play className="mr-2 h-4 w-4" />
              Run Test
            </>
          )}
        </Button>
      </div>

      {/* Results Panel */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <Label>Execution Steps</Label>
          {executionMetrics && (
            <Badge variant="outline">
              {executionMetrics.duration}ms
            </Badge>
          )}
        </div>

        <ScrollArea className="h-[400px] rounded-md border p-4">
          {executionSteps.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
              <Activity className="h-8 w-8 mb-2" />
              <p className="text-sm">No execution yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {executionSteps.map((step, index) => (
                <Card key={step.step_id}>
                  <CardHeader className="pb-3">
                    <div className="flex items-center gap-2">
                      {step.type === 'thought' && (
                        <Brain className="h-4 w-4 text-blue-500" />
                      )}
                      {step.type === 'action' && (
                        <Zap className="h-4 w-4 text-yellow-500" />
                      )}
                      {step.type === 'observation' && (
                        <Eye className="h-4 w-4 text-green-500" />
                      )}
                      {step.type === 'response' && (
                        <MessageSquare className="h-4 w-4 text-purple-500" />
                      )}
                      <span className="text-sm font-medium capitalize">
                        {step.type}
                      </span>
                      <Badge variant="outline" className="ml-auto">
                        Step {index + 1}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm whitespace-pre-wrap">
                      {step.content}
                    </p>
                    {step.metadata && Object.keys(step.metadata).length > 0 && (
                      <Collapsible className="mt-2">
                        <CollapsibleTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <ChevronDown className="h-4 w-4 mr-2" />
                            Metadata
                          </Button>
                        </CollapsibleTrigger>
                        <CollapsibleContent>
                          <pre className="text-xs bg-muted p-2 rounded mt-2 overflow-auto">
                            {JSON.stringify(step.metadata, null, 2)}
                          </pre>
                        </CollapsibleContent>
                      </Collapsible>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </ScrollArea>

        {executionMetrics && (
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Execution Metrics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Duration:</span>
                <span className="font-medium">{executionMetrics.duration}ms</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Tokens:</span>
                <span className="font-medium">{executionMetrics.tokens}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Tool Calls:</span>
                <span className="font-medium">{executionMetrics.toolCalls}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Status:</span>
                <Badge variant={executionMetrics.status === 'success' ? 'default' : 'destructive'}>
                  {executionMetrics.status}
                </Badge>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  </DialogContent>
</Dialog>
```

**shadcn/ui Components:**
- `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle`, `DialogDescription`
- `Label`
- `Textarea`
- `Input`
- `Button`
- `Accordion`, `AccordionItem`, `AccordionTrigger`, `AccordionContent`
- `ScrollArea`
- `Card`, `CardHeader`, `CardTitle`, `CardContent`
- `Badge`
- `Collapsible`, `CollapsibleTrigger`, `CollapsibleContent`

---

### 6. Block Library Page

**Route:** `/agent-builder/blocks`

```tsx
<div className="container mx-auto p-6 space-y-6">
  {/* Header */}
  <div className="flex items-center justify-between">
    <div>
      <h1 className="text-3xl font-bold">Block Library</h1>
      <p className="text-muted-foreground">
        Reusable components for your workflows
      </p>
    </div>
    <Button onClick={handleCreateBlock}>
      <Plus className="mr-2 h-4 w-4" />
      Create Block
    </Button>
  </div>

  {/* Tabs for Categories */}
  <Tabs defaultValue="all" className="w-full">
    <TabsList>
      <TabsTrigger value="all">All Blocks</TabsTrigger>
      <TabsTrigger value="llm">LLM Blocks</TabsTrigger>
      <TabsTrigger value="tool">Tool Blocks</TabsTrigger>
      <TabsTrigger value="logic">Logic Blocks</TabsTrigger>
      <TabsTrigger value="composite">Composite Blocks</TabsTrigger>
    </TabsList>

    <TabsContent value="all" className="space-y-4">
      {/* Search */}
      <div className="flex gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search blocks..."
              className="pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline">
              <Filter className="mr-2 h-4 w-4" />
              Filter
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>Sort by</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuRadioGroup value={sortBy} onValueChange={setSortBy}>
              <DropdownMenuRadioItem value="name">Name</DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="recent">Recently Used</DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="popular">Most Popular</DropdownMenuRadioItem>
            </DropdownMenuRadioGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Block Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {blocks.map((block) => (
          <Card key={block.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  {getBlockIcon(block.block_type)}
                  <div>
                    <CardTitle className="text-base">{block.name}</CardTitle>
                    <CardDescription className="text-xs">
                      {block.block_type}
                    </CardDescription>
                  </div>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => handleEdit(block.id)}>
                      <Edit className="mr-2 h-4 w-4" />
                      Edit
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleTest(block.id)}>
                      <Play className="mr-2 h-4 w-4" />
                      Test
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleDuplicate(block.id)}>
                      <Copy className="mr-2 h-4 w-4" />
                      Duplicate
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem 
                      onClick={() => handleDelete(block.id)}
                      className="text-destructive"
                    >
                      <Trash className="mr-2 h-4 w-4" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground line-clamp-2">
                {block.description}
              </p>
              <div className="mt-3 flex items-center gap-2">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Badge variant="outline" className="text-xs">
                        <ArrowDownToLine className="mr-1 h-3 w-3" />
                        {block.input_schema?.properties ? 
                          Object.keys(block.input_schema.properties).length : 0
                        } inputs
                      </Badge>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Number of input parameters</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
                
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Badge variant="outline" className="text-xs">
                        <ArrowUpFromLine className="mr-1 h-3 w-3" />
                        {block.output_schema?.properties ? 
                          Object.keys(block.output_schema.properties).length : 0
                        } outputs
                      </Badge>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Number of output parameters</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
            </CardContent>
            <CardFooter className="flex justify-between text-xs text-muted-foreground">
              <span>v{block.version}</span>
              <span>{formatDate(block.updated_at)}</span>
            </CardFooter>
          </Card>
        ))}
      </div>
    </TabsContent>
  </Tabs>
</div>
```

**shadcn/ui Components:**
- `Button`
- `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent`
- `Input`
- `DropdownMenu`, `DropdownMenuTrigger`, `DropdownMenuContent`, `DropdownMenuLabel`, `DropdownMenuSeparator`, `DropdownMenuRadioGroup`, `DropdownMenuRadioItem`, `DropdownMenuItem`
- `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`
- `Badge`
- `Tooltip`, `TooltipProvider`, `TooltipTrigger`, `TooltipContent`

---


### 7. Execution Monitor Dashboard

**Route:** `/agent-builder/executions`

```tsx
<div className="container mx-auto p-6 space-y-6">
  {/* Header with Stats */}
  <div>
    <h1 className="text-3xl font-bold mb-6">Execution Monitor</h1>
    
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Active Executions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="text-2xl font-bold">{stats.active}</div>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Success Rate</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="text-2xl font-bold">{stats.successRate}%</div>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </div>
          <Progress value={stats.successRate} className="mt-2" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Avg Duration</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="text-2xl font-bold">{stats.avgDuration}s</div>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Total Executions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="text-2xl font-bold">{stats.total}</div>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    </div>
  </div>

  {/* Filters */}
  <Card>
    <CardContent className="pt-6">
      <div className="flex flex-wrap gap-4">
        <div className="flex-1 min-w-[200px]">
          <Label className="text-xs mb-2">Status</Label>
          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger>
              <SelectValue placeholder="All statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="running">Running</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
              <SelectItem value="timeout">Timeout</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex-1 min-w-[200px]">
          <Label className="text-xs mb-2">Agent</Label>
          <Select value={filterAgent} onValueChange={setFilterAgent}>
            <SelectTrigger>
              <SelectValue placeholder="All agents" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Agents</SelectItem>
              {agents.map((agent) => (
                <SelectItem key={agent.id} value={agent.id}>
                  {agent.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex-1 min-w-[200px]">
          <Label className="text-xs mb-2">Time Range</Label>
          <Select value={filterTimeRange} onValueChange={setFilterTimeRange}>
            <SelectTrigger>
              <SelectValue placeholder="Last 24 hours" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1h">Last Hour</SelectItem>
              <SelectItem value="24h">Last 24 Hours</SelectItem>
              <SelectItem value="7d">Last 7 Days</SelectItem>
              <SelectItem value="30d">Last 30 Days</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-end">
          <Button variant="outline" onClick={handleResetFilters}>
            <X className="mr-2 h-4 w-4" />
            Reset
          </Button>
        </div>
      </div>
    </CardContent>
  </Card>

  {/* Executions Table */}
  <Card>
    <CardHeader>
      <CardTitle>Recent Executions</CardTitle>
    </CardHeader>
    <CardContent>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Execution ID</TableHead>
            <TableHead>Agent</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead>Started</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {executions.map((execution) => (
            <TableRow key={execution.id}>
              <TableCell className="font-mono text-xs">
                {execution.id.substring(0, 8)}...
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <Avatar className="h-6 w-6">
                    <AvatarFallback className="text-xs">
                      {execution.agent_name.substring(0, 2).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <span className="text-sm">{execution.agent_name}</span>
                </div>
              </TableCell>
              <TableCell>
                <Badge 
                  variant={
                    execution.status === 'completed' ? 'default' :
                    execution.status === 'running' ? 'secondary' :
                    execution.status === 'failed' ? 'destructive' :
                    'outline'
                  }
                >
                  {execution.status === 'running' && (
                    <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                  )}
                  {execution.status}
                </Badge>
              </TableCell>
              <TableCell className="text-sm">
                {execution.duration_ms ? 
                  `${(execution.duration_ms / 1000).toFixed(2)}s` : 
                  '-'
                }
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {formatRelativeTime(execution.started_at)}
              </TableCell>
              <TableCell className="text-right">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => handleViewDetails(execution.id)}>
                      <Eye className="mr-2 h-4 w-4" />
                      View Details
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleReplay(execution.id)}>
                      <RotateCcw className="mr-2 h-4 w-4" />
                      Replay
                    </DropdownMenuItem>
                    {execution.status === 'running' && (
                      <DropdownMenuItem 
                        onClick={() => handleCancel(execution.id)}
                        className="text-destructive"
                      >
                        <XCircle className="mr-2 h-4 w-4" />
                        Cancel
                      </DropdownMenuItem>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </CardContent>
  </Card>
</div>
```

**shadcn/ui Components:**
- `Card`, `CardHeader`, `CardDescription`, `CardContent`, `CardTitle`
- `Progress`
- `Label`
- `Select`, `SelectTrigger`, `SelectValue`, `SelectContent`, `SelectItem`
- `Button`
- `Table`, `TableHeader`, `TableRow`, `TableHead`, `TableBody`, `TableCell`
- `Avatar`, `AvatarFallback`
- `Badge`
- `DropdownMenu`, `DropdownMenuTrigger`, `DropdownMenuContent`, `DropdownMenuItem`

---

### 8. Variables Manager Page

**Route:** `/agent-builder/variables`

```tsx
<div className="container mx-auto p-6 space-y-6">
  {/* Header */}
  <div className="flex items-center justify-between">
    <div>
      <h1 className="text-3xl font-bold">Variables</h1>
      <p className="text-muted-foreground">
        Manage global variables and secrets
      </p>
    </div>
    <Button onClick={handleCreateVariable}>
      <Plus className="mr-2 h-4 w-4" />
      Create Variable
    </Button>
  </div>

  {/* Scope Tabs */}
  <Tabs defaultValue="all" className="w-full">
    <TabsList>
      <TabsTrigger value="all">All Variables</TabsTrigger>
      <TabsTrigger value="global">Global</TabsTrigger>
      <TabsTrigger value="workspace">Workspace</TabsTrigger>
      <TabsTrigger value="user">User</TabsTrigger>
      <TabsTrigger value="agent">Agent</TabsTrigger>
    </TabsList>

    <TabsContent value="all" className="space-y-4">
      {/* Variables by Scope */}
      {Object.entries(groupedVariables).map(([scope, vars]) => (
        <Card key={scope}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CardTitle className="text-lg capitalize">{scope} Scope</CardTitle>
                <Badge variant="outline">{vars.length}</Badge>
              </div>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => toggleScope(scope)}
              >
                {expandedScopes.includes(scope) ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </Button>
            </div>
          </CardHeader>
          
          {expandedScopes.includes(scope) && (
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Value</TableHead>
                    <TableHead>Updated</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {vars.map((variable) => (
                    <TableRow key={variable.id}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          {variable.is_secret && (
                            <Lock className="h-3 w-3 text-muted-foreground" />
                          )}
                          <code className="text-sm">{variable.name}</code>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{variable.value_type}</Badge>
                      </TableCell>
                      <TableCell className="max-w-xs">
                        {variable.is_secret ? (
                          <div className="flex items-center gap-2">
                            <span className="text-muted-foreground">••••••••</span>
                            <Button 
                              variant="ghost" 
                              size="icon"
                              onClick={() => handleRevealSecret(variable.id)}
                            >
                              <Eye className="h-3 w-3" />
                            </Button>
                          </div>
                        ) : (
                          <code className="text-xs text-muted-foreground truncate block">
                            {variable.value}
                          </code>
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatRelativeTime(variable.updated_at)}
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleEdit(variable.id)}>
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleCopy(variable.name)}>
                              <Copy className="mr-2 h-4 w-4" />
                              Copy Name
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem 
                              onClick={() => handleDelete(variable.id)}
                              className="text-destructive"
                            >
                              <Trash className="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          )}
        </Card>
      ))}
    </TabsContent>
  </Tabs>

  {/* Variable Creation Dialog */}
  <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Create Variable</DialogTitle>
        <DialogDescription>
          Add a new variable or secret to your workspace
        </DialogDescription>
      </DialogHeader>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Variable Name</FormLabel>
                <FormControl>
                  <Input placeholder="MY_VARIABLE" {...field} />
                </FormControl>
                <FormDescription>
                  Use UPPER_SNAKE_CASE for variable names
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="scope"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Scope</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select scope" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="global">Global</SelectItem>
                    <SelectItem value="workspace">Workspace</SelectItem>
                    <SelectItem value="user">User</SelectItem>
                    <SelectItem value="agent">Agent</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="value_type"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Type</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="string">String</SelectItem>
                    <SelectItem value="number">Number</SelectItem>
                    <SelectItem value="boolean">Boolean</SelectItem>
                    <SelectItem value="json">JSON</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="value"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Value</FormLabel>
                <FormControl>
                  <Textarea 
                    placeholder="Enter value..."
                    className="font-mono text-sm"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="is_secret"
            render={({ field }) => (
              <FormItem className="flex items-center justify-between rounded-lg border p-4">
                <div className="space-y-0.5">
                  <FormLabel className="text-base">Secret</FormLabel>
                  <FormDescription>
                    Encrypt this variable value
                  </FormDescription>
                </div>
                <FormControl>
                  <Switch
                    checked={field.value}
                    onCheckedChange={field.onChange}
                  />
                </FormControl>
              </FormItem>
            )}
          />

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Create Variable</Button>
          </DialogFooter>
        </form>
      </Form>
    </DialogContent>
  </Dialog>
</div>
```

**shadcn/ui Components:**
- `Button`
- `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent`
- `Card`, `CardHeader`, `CardTitle`, `CardContent`
- `Badge`
- `Table`, `TableHeader`, `TableRow`, `TableHead`, `TableBody`, `TableCell`
- `DropdownMenu`, `DropdownMenuTrigger`, `DropdownMenuContent`, `DropdownMenuItem`, `DropdownMenuSeparator`
- `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle`, `DialogDescription`, `DialogFooter`
- `Form`, `FormField`, `FormItem`, `FormLabel`, `FormControl`, `FormDescription`, `FormMessage`
- `Input`
- `Select`, `SelectTrigger`, `SelectValue`, `SelectContent`, `SelectItem`
- `Textarea`
- `Switch`

---

## Component Patterns

### Loading States

```tsx
// Skeleton Loading
<Card>
  <CardHeader>
    <Skeleton className="h-4 w-[250px]" />
    <Skeleton className="h-4 w-[200px]" />
  </CardHeader>
  <CardContent>
    <Skeleton className="h-[125px] w-full" />
  </CardContent>
</Card>

// Spinner Loading
<div className="flex items-center justify-center p-8">
  <Loader2 className="h-8 w-8 animate-spin text-primary" />
</div>
```

### Empty States

```tsx
<div className="flex flex-col items-center justify-center p-12 text-center">
  <div className="rounded-full bg-muted p-3 mb-4">
    <Inbox className="h-6 w-6 text-muted-foreground" />
  </div>
  <h3 className="text-lg font-semibold mb-2">No agents yet</h3>
  <p className="text-sm text-muted-foreground mb-4">
    Get started by creating your first agent
  </p>
  <Button onClick={handleCreate}>
    <Plus className="mr-2 h-4 w-4" />
    Create Agent
  </Button>
</div>
```

### Error States

```tsx
<Alert variant="destructive">
  <AlertCircle className="h-4 w-4" />
  <AlertTitle>Error</AlertTitle>
  <AlertDescription>
    Failed to load agents. Please try again.
  </AlertDescription>
</Alert>
```

### Toast Notifications

```tsx
// Success
toast({
  title: "Agent created",
  description: "Your agent has been created successfully.",
})

// Error
toast({
  variant: "destructive",
  title: "Uh oh! Something went wrong.",
  description: "There was a problem with your request.",
})

// With action
toast({
  title: "Execution completed",
  description: "Your agent execution finished successfully.",
  action: (
    <ToastAction altText="View details">View</ToastAction>
  ),
})
```

---

## Responsive Design

All components should be responsive using Tailwind's responsive prefixes:

```tsx
// Mobile-first approach
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
  {/* Cards */}
</div>

// Responsive padding
<div className="p-4 md:p-6 lg:p-8">
  {/* Content */}
</div>

// Responsive text
<h1 className="text-2xl md:text-3xl lg:text-4xl font-bold">
  Title
</h1>
```

---

## Accessibility

All shadcn/ui components are built with accessibility in mind:

- Proper ARIA labels
- Keyboard navigation support
- Focus management
- Screen reader support
- Color contrast compliance

**Example:**
```tsx
<Button aria-label="Create new agent" onClick={handleCreate}>
  <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
  Create Agent
</Button>
```

---

## Dark Mode Support

All components automatically support dark mode through Tailwind's dark mode classes:

```tsx
// Automatic dark mode support
<Card className="bg-card text-card-foreground">
  <CardContent>
    {/* Content automatically adapts to dark mode */}
  </CardContent>
</Card>
```

---

## Animation and Transitions

Use Tailwind's transition utilities for smooth interactions:

```tsx
<Card className="hover:shadow-lg transition-shadow duration-200">
  {/* Card content */}
</Card>

<Button className="transition-all hover:scale-105">
  Click me
</Button>
```

---

## Summary

This UI/UX design document provides comprehensive shadcn/ui-based component specifications for the Agent Builder feature. All components follow:

1. **Consistent Design System**: Using shadcn/ui components
2. **Accessibility**: WCAG 2.1 AA compliance
3. **Responsive**: Mobile-first approach
4. **Dark Mode**: Full dark mode support
5. **Performance**: Optimized rendering and interactions
6. **User Experience**: Intuitive and efficient workflows

**Next Steps:**
1. Install required shadcn/ui components
2. Implement components following these specifications
3. Test across different screen sizes and themes
4. Ensure accessibility compliance
5. Gather user feedback and iterate
