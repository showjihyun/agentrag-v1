# Agent Builder User Guide

Welcome to the Agent Builder! This guide will help you create, configure, and manage custom AI agents and workflows.

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Creating Your First Agent](#creating-your-first-agent)
4. [Building Workflows](#building-workflows)
5. [Working with Blocks](#working-with-blocks)
6. [Managing Knowledgebases](#managing-knowledgebases)
7. [Variables and Secrets](#variables-and-secrets)
8. [Monitoring Executions](#monitoring-executions)
9. [Sharing and Collaboration](#sharing-and-collaboration)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

## Introduction

The Agent Builder is a powerful platform for creating custom AI agents that can:
- Execute complex workflows
- Access multiple data sources
- Use specialized tools
- Maintain context across conversations
- Scale to handle production workloads

### Key Concepts

- **Agent**: A configured AI assistant with specific tools, prompts, and behaviors
- **Workflow**: A directed graph of agents and blocks that execute in sequence or parallel
- **Block**: A reusable component (LLM call, tool invocation, or logic)
- **Knowledgebase**: A collection of documents that agents can search
- **Tool**: A function that agents can use (e.g., web search, database query)
- **Variable**: A configurable value that can be used across agents and workflows

## Getting Started

### Prerequisites

- Access to the AgenticRAG platform
- User account with appropriate permissions
- Basic understanding of AI agents and workflows

### Accessing Agent Builder

1. Log in to the AgenticRAG platform
2. Navigate to the "Agent Builder" section from the main menu
3. You'll see the Agent Builder dashboard with navigation to:
   - Agents
   - Blocks
   - Workflows
   - Knowledgebases
   - Variables
   - Executions

## Creating Your First Agent

### Step 1: Navigate to Agents

Click on "Agents" in the Agent Builder sidebar.

### Step 2: Create New Agent

1. Click the "Create Agent" button
2. Fill in the agent details:
   - **Name**: Give your agent a descriptive name
   - **Description**: Explain what your agent does
   - **Agent Type**: Choose "Custom" for a new agent
   - **LLM Provider**: Select your LLM provider (Ollama, OpenAI, Claude)
   - **LLM Model**: Choose the model to use

### Step 3: Configure Tools

1. In the "Tools" section, select the tools your agent can use:
   - **Vector Search**: Search internal documents
   - **Web Search**: Search the web
   - **Local Data**: Access local files and databases
   - **Database Query**: Execute SQL queries
   - **File Operation**: Read/write files
   - **HTTP API Call**: Make API requests

2. Configure tool-specific parameters if needed

### Step 4: Write Prompt Template

1. In the "Prompt Template" section, write your agent's system prompt
2. Use variables with `${variable_name}` syntax
3. Available variables:
   - `${query}`: User's query
   - `${context}`: Retrieved context
   - `${history}`: Conversation history
   - Custom variables you define

Example prompt:
```
You are a helpful research assistant. Use the available tools to answer questions accurately.

Query: ${query}

Context: ${context}

Provide a detailed, well-researched answer with citations.
```

### Step 5: Test Your Agent

1. Click the "Test" button
2. Enter a test query
3. Review the agent's response and execution steps
4. Iterate on your prompt and tools as needed

### Step 6: Save Your Agent

Click "Save" to create your agent.

## Building Workflows

Workflows allow you to chain multiple agents and blocks together for complex tasks.

### Creating a Workflow

1. Navigate to "Workflows"
2. Click "Create Workflow"
3. Give your workflow a name and description

### Using the Workflow Designer

The workflow designer is a visual canvas where you can:
- Drag and drop nodes (agents, blocks, control flow)
- Connect nodes with edges
- Configure node properties
- Validate the workflow

### Adding Nodes

1. **Agent Nodes**: Drag an agent from the palette
2. **Block Nodes**: Drag a block from the palette
3. **Control Nodes**: Add conditional branches, loops, or parallel execution

### Connecting Nodes

1. Click and drag from an output port to an input port
2. The system validates that connections are compatible
3. Configure data mapping between nodes

### Conditional Branching

1. Add a "Conditional" control node
2. Write a Python expression to evaluate
3. Connect different branches based on the condition

Example:
```python
state['confidence'] > 0.8
```

### Parallel Execution

1. Add a "Parallel" control node
2. Connect multiple branches that should run concurrently
3. Results are aggregated when all branches complete

### Testing Workflows

1. Click "Validate" to check for errors
2. Click "Run" to execute the workflow
3. Watch nodes highlight as they execute
4. Review the final output and execution metrics

## Working with Blocks

Blocks are reusable components that can be used in workflows.

### Types of Blocks

1. **LLM Block**: Makes an LLM call with a prompt template
2. **Tool Block**: Invokes a specific tool
3. **Logic Block**: Executes custom Python code
4. **Composite Block**: A sub-workflow packaged as a block

### Creating a Block

1. Navigate to "Blocks"
2. Click "Create Block"
3. Choose the block type
4. Define input and output schemas
5. Implement the block logic

### Example: LLM Block

```json
{
  "name": "Summarize Text",
  "type": "llm",
  "input_schema": {
    "text": "string"
  },
  "output_schema": {
    "summary": "string"
  },
  "prompt_template": "Summarize the following text:\n\n${text}"
}
```

### Testing Blocks

1. Click "Test" on a block
2. Provide sample input
3. Review the output
4. Save test cases for regression testing

### Publishing Blocks

1. Mark a block as "Public" to share with others
2. Add tags and categories for discoverability
3. Provide usage examples and documentation

## Managing Knowledgebases

Knowledgebases provide domain-specific knowledge to your agents.

### Creating a Knowledgebase

1. Navigate to "Knowledgebases"
2. Click "Create Knowledgebase"
3. Configure:
   - Name and description
   - Embedding model
   - Chunk size and overlap

### Uploading Documents

1. Click "Upload Documents"
2. Drag and drop files or click to browse
3. Supported formats: PDF, DOCX, TXT, MD, HTML
4. Wait for processing to complete

### Searching a Knowledgebase

1. Use the search interface to test queries
2. Review results and relevance scores
3. Adjust chunk size or embedding model if needed

### Attaching to Agents

1. Edit an agent
2. In the "Knowledgebases" section, select knowledgebases to attach
3. Set priority if using multiple knowledgebases

### Versioning

1. Knowledgebases are automatically versioned
2. View version history to see changes
3. Rollback to a previous version if needed

## Variables and Secrets

Variables allow you to configure agents without modifying code.

### Variable Scopes

1. **Global**: Available to all agents
2. **Workspace**: Available to all agents in a workspace
3. **User**: Available to your agents only
4. **Agent**: Specific to one agent

### Creating Variables

1. Navigate to "Variables"
2. Click "Create Variable"
3. Configure:
   - Name
   - Scope
   - Type (string, number, boolean, JSON)
   - Value

### Using Variables

Reference variables in prompts or configurations:
```
API_KEY: ${api_key}
MAX_RESULTS: ${max_results}
```

### Secrets

1. Toggle "Secret" when creating a variable
2. Values are encrypted and never displayed
3. Use for API keys, passwords, tokens

### Variable Precedence

When multiple scopes define the same variable:
1. Agent-level (highest priority)
2. User-level
3. Workspace-level
4. Global-level (lowest priority)

## Monitoring Executions

Track and debug agent and workflow executions.

### Execution Dashboard

1. Navigate to "Executions"
2. View metrics:
   - Total executions
   - Success rate
   - Average duration
   - Token usage

### Filtering Executions

Filter by:
- Status (running, completed, failed)
- Agent or workflow
- Date range
- User

### Viewing Execution Details

1. Click on an execution
2. Review:
   - Input and output
   - Execution steps
   - Tool calls
   - LLM requests
   - Errors and warnings

### Execution Metrics

- Duration
- Token usage
- Tool call count
- Cache hits
- Cost estimate

### Replaying Executions

1. Click "Replay" on a past execution
2. The agent runs with the same inputs
3. Compare results to debug issues

## Sharing and Collaboration

Share agents, workflows, and blocks with others.

### Sharing Resources

1. Open the resource (agent, workflow, block)
2. Click "Share"
3. Configure:
   - Permissions (read, execute, edit)
   - Expiration date
   - Access token

### Cloning Shared Resources

1. Access a shared resource via link
2. Click "Clone" to create your own copy
3. Customize as needed

### Publishing to Marketplace

1. Mark a resource as "Public"
2. Add description, tags, and examples
3. Submit for review
4. Once approved, it appears in the marketplace

### Installing from Marketplace

1. Browse the marketplace
2. Click "Install" on a resource
3. It's added to your library
4. Customize and use in your workflows

## Best Practices

### Agent Design

1. **Clear Purpose**: Each agent should have a specific, well-defined purpose
2. **Minimal Tools**: Only include tools the agent actually needs
3. **Specific Prompts**: Write clear, specific prompts with examples
4. **Test Thoroughly**: Test with various inputs before deploying

### Workflow Design

1. **Modular**: Break complex workflows into smaller, reusable blocks
2. **Error Handling**: Add error handling and fallback paths
3. **Timeouts**: Set appropriate timeouts for each step
4. **Parallel When Possible**: Use parallel execution for independent tasks

### Performance

1. **Cache Results**: Enable caching for repeated queries
2. **Optimize Prompts**: Shorter prompts use fewer tokens
3. **Batch Operations**: Process multiple items together when possible
4. **Monitor Quotas**: Track token usage and execution counts

### Security

1. **Use Secrets**: Never hardcode API keys or passwords
2. **Least Privilege**: Grant minimum necessary permissions
3. **Audit Logs**: Review audit logs regularly
4. **Validate Inputs**: Always validate user inputs

## Troubleshooting

### Common Issues

#### Agent Not Responding

**Symptoms**: Agent execution hangs or times out

**Solutions**:
- Check LLM service status
- Reduce prompt complexity
- Increase timeout settings
- Review execution logs for errors

#### Tool Execution Fails

**Symptoms**: Tool calls return errors

**Solutions**:
- Verify tool configuration
- Check API keys and credentials
- Test tool independently
- Review tool documentation

#### Low Quality Responses

**Symptoms**: Agent responses are inaccurate or incomplete

**Solutions**:
- Improve prompt template
- Add more context or examples
- Attach relevant knowledgebases
- Try a different LLM model

#### Quota Exceeded

**Symptoms**: Executions fail with quota error

**Solutions**:
- Wait for quota reset
- Optimize token usage
- Upgrade plan
- Use caching to reduce calls

### Getting Help

1. **Documentation**: Check the full documentation
2. **Community**: Ask in the community forum
3. **Support**: Contact support for technical issues
4. **Status Page**: Check service status

### Reporting Bugs

When reporting bugs, include:
- Steps to reproduce
- Expected vs actual behavior
- Execution ID
- Screenshots or logs
- Browser and OS information

## Conclusion

You're now ready to build powerful AI agents and workflows! Start simple, test thoroughly, and iterate based on results.

For more information:
- API Documentation: `/docs/api`
- Video Tutorials: `/tutorials`
- Community Forum: `/community`
- Support: `support@agenticrag.com`

Happy building! 🚀
