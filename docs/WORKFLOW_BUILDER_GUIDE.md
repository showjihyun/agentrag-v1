# Workflow Builder Guide

## Overview

The Workflow Builder allows you to create complex, multi-step AI workflows by connecting blocks, agents, and tools in a visual interface - similar to sim.ai.

## Features

### 🎯 Node Types

#### 1. **Control Nodes**
- **Start Node** (▶️): Entry point of your workflow
- **End Node** (🏁): Exit point(s) of your workflow
- **Condition Node** (◆): Branch logic based on conditions

#### 2. **Agent Nodes** (🤖)
- AI agents that can process inputs and generate outputs
- Configurable with custom system prompts
- Support for multiple LLM providers

#### 3. **Block Nodes**
- Reusable logic blocks (LLM, Tool, Logic, Composite)
- Custom input/output schemas
- Configurable parameters

#### 4. **Tool Nodes** (🔧)
- Pre-built tools (Vector Search, Web Search, etc.)
- 35+ available tools
- Easy integration with external services

## Getting Started

### Creating a New Workflow

1. Navigate to **Agent Builder** → **Workflows** → **New Workflow**
2. Enter workflow name and description
3. Drag and drop nodes from the palette
4. Connect nodes by dragging from output handles to input handles
5. Click nodes to configure them
6. Save your workflow

### Node Palette Categories

```
┌─────────────────────────────────┐
│ Control | Agents | Blocks | Tools│
└─────────────────────────────────┘
```

- **Control**: Start, End, Condition nodes
- **Agents**: Your created AI agents
- **Blocks**: Custom reusable blocks
- **Tools**: Pre-built integrations

## Building Workflows

### Example 1: Simple Agent Workflow

```
Start → Agent (Research) → Agent (Summarize) → End
```

1. Add a **Start** node
2. Add an **Agent** node (e.g., Research Agent)
3. Add another **Agent** node (e.g., Summarize Agent)
4. Add an **End** node
5. Connect them in sequence
6. Configure each agent's system prompt

### Example 2: Conditional Workflow

```
Start → Agent → Condition → [True] → Agent A → End
                         └→ [False] → Agent B → End
```

1. Add **Start** node
2. Add an **Agent** node
3. Add a **Condition** node
4. Add two **Agent** nodes (A and B)
5. Add two **End** nodes
6. Connect:
   - Start → Agent → Condition
   - Condition (True) → Agent A → End
   - Condition (False) → Agent B → End
7. Configure condition expression (e.g., `output.confidence > 0.8`)

### Example 3: Tool Integration Workflow

```
Start → Agent → Tool (Web Search) → Agent (Analyze) → End
```

1. Add **Start** node
2. Add an **Agent** node (Query Generator)
3. Add a **Tool** node (Web Search)
4. Add an **Agent** node (Analyzer)
5. Add **End** node
6. Connect in sequence

## Node Configuration

### Agent Node Configuration

Click on an agent node to configure:

- **Name**: Display name
- **Description**: What the agent does
- **System Prompt**: Instructions for the AI agent

Example System Prompt:
```
You are a research assistant. Analyze the input query and provide 
comprehensive research findings with citations.
```

### Condition Node Configuration

- **Label**: Display name
- **Condition Expression**: JavaScript-like expression

Available variables:
- `input` - Input data from previous node
- `output` - Output from previous node
- `context` - Workflow context variables

Example Conditions:
```javascript
output.confidence > 0.8
output.sentiment === "positive"
input.length > 100
context.userRole === "admin"
```

### Block Node Configuration

- **Name**: Block name
- **Description**: Block description
- **Input Parameters**: View defined inputs
- **Output Parameters**: View defined outputs

## Keyboard Shortcuts

- **Ctrl/Cmd + Z**: Undo
- **Ctrl/Cmd + Y**: Redo
- **Ctrl/Cmd + Shift + Z**: Redo (alternative)
- **Delete/Backspace**: Delete selected node(s)
- **Shift + Click**: Multi-select nodes

## Canvas Controls

- **Zoom In/Out**: Use mouse wheel or zoom buttons
- **Pan**: Click and drag on empty space
- **Fit View**: Click maximize button to fit all nodes
- **Mini Map**: Navigate large workflows easily

## Best Practices

### 1. **Start with Start, End with End**
Every workflow should have exactly one Start node and at least one End node.

### 2. **Name Your Nodes**
Give descriptive names to agents and blocks for clarity.

### 3. **Use Conditions Wisely**
Conditions should have clear true/false paths. Always connect both outputs.

### 4. **Test Incrementally**
Build and test small workflows before creating complex ones.

### 5. **Document Your Workflow**
Use the workflow description to explain the overall purpose.

### 6. **Reuse Blocks**
Create reusable blocks for common operations.

## Workflow Execution

### Running a Workflow

1. Save your workflow
2. Navigate to the workflow detail page
3. Click **Run Workflow**
4. Provide input data
5. Monitor execution in real-time
6. View results and logs

### Execution Flow

```
1. Start Node → Initialize workflow context
2. Process each node in sequence
3. Evaluate conditions at branch points
4. Execute agents/blocks/tools
5. Pass outputs to next nodes
6. End Node → Return final results
```

## Advanced Features

### Variable Passing

Data flows between nodes automatically:
- Each node receives `input` from previous node
- Each node produces `output` for next node
- Workflow maintains `context` for global variables

### Error Handling

- Nodes can have validation errors (shown in red)
- Failed nodes stop execution
- Error messages displayed in execution logs

### Parallel Execution

Multiple branches can execute in parallel:
```
Start → Agent → [Branch A] → End
              → [Branch B] → End
```

## Troubleshooting

### Node Won't Connect
- Check handle compatibility (output → input)
- Ensure no circular dependencies
- Verify node types are compatible

### Workflow Won't Save
- Ensure workflow has a name
- Check for validation errors on nodes
- Verify at least one node exists

### Execution Fails
- Check node configurations
- Verify all required inputs are provided
- Review execution logs for errors

## API Integration

### Programmatic Workflow Creation

```typescript
import { agentBuilderAPI } from '@/lib/api/agent-builder';

const workflow = await agentBuilderAPI.createWorkflow({
  name: 'My Workflow',
  description: 'Automated research workflow',
  graph_definition: {
    nodes: [
      { id: 'start', type: 'start', position: { x: 0, y: 0 }, data: {} },
      { id: 'agent1', type: 'agent', position: { x: 200, y: 0 }, data: { agentId: 'xxx' } },
      { id: 'end', type: 'end', position: { x: 400, y: 0 }, data: {} },
    ],
    edges: [
      { id: 'e1', source: 'start', target: 'agent1' },
      { id: 'e2', source: 'agent1', target: 'end' },
    ],
  },
});
```

### Executing Workflows

```typescript
const execution = await agentBuilderAPI.executeWorkflow(workflowId, {
  input: { query: 'Research AI trends' },
});
```

## Examples

### Customer Support Workflow

```
Start 
  → Agent (Classify Intent)
  → Condition (intent === "technical")
    → [True] → Agent (Technical Support) → End
    → [False] → Condition (intent === "billing")
      → [True] → Agent (Billing Support) → End
      → [False] → Agent (General Support) → End
```

### Content Generation Workflow

```
Start
  → Agent (Topic Generator)
  → Tool (Web Search)
  → Agent (Content Writer)
  → Agent (SEO Optimizer)
  → Block (Format Content)
  → End
```

### Data Analysis Workflow

```
Start
  → Tool (Fetch Data)
  → Block (Clean Data)
  → Agent (Analyze)
  → Condition (needs_visualization)
    → [True] → Block (Create Chart) → End
    → [False] → End
```

## Next Steps

1. **Create Your First Workflow**: Start with a simple 2-3 node workflow
2. **Explore Templates**: Check out pre-built workflow templates
3. **Join Community**: Share your workflows and learn from others
4. **Read API Docs**: Learn about programmatic workflow creation

## Support

- **Documentation**: `/docs`
- **API Reference**: `/docs/api`
- **GitHub Issues**: Report bugs and request features
- **Community Forum**: Ask questions and share workflows

---

**Happy Building! 🚀**
