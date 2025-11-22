/**
 * API client for tool configuration
 */

export interface ParamConfig {
  type: string;
  description: string;
  required?: boolean;
  default?: any;
  enum?: string[];
  min?: number;
  max?: number;
  pattern?: string;
}

export interface Tool {
  id: string;
  name: string;
  description: string;
  category: string;
  params: Record<string, ParamConfig>;
  outputs: Record<string, any>;
  icon?: string;
  bg_color?: string;
  docs_link?: string;
}

export interface ToolValidationResult {
  valid: boolean;
  errors: Record<string, string>;
  warnings: Record<string, string>;
}

export interface ToolSchema {
  tool_id: string;
  name: string;
  description: string;
  params: Record<string, any>;
  outputs: Record<string, any>;
  examples?: Record<string, any>;
}

/**
 * Fetch all available tools
 */
export async function fetchTools(params?: {
  category?: string;
  search?: string;
}): Promise<{ tools: Tool[]; total: number; categories: string[] }> {
  const queryParams = new URLSearchParams();
  if (params?.category) queryParams.append("category", params.category);
  if (params?.search) queryParams.append("search", params.search);

  const response = await fetch(
    `/api/agent-builder/tools?${queryParams.toString()}`
  );
  if (!response.ok) throw new Error("Failed to fetch tools");
  return response.json();
}

/**
 * Fetch tool details
 */
export async function fetchTool(toolId: string): Promise<Tool> {
  const response = await fetch(`/api/agent-builder/tools/${toolId}`);
  if (!response.ok) throw new Error("Failed to fetch tool");
  return response.json();
}

/**
 * Validate tool configuration
 */
export async function validateToolConfig(
  toolId: string,
  configuration: Record<string, any>
): Promise<ToolValidationResult> {
  const response = await fetch("/api/agent-builder/tool-config/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tool_id: toolId, configuration }),
  });
  if (!response.ok) throw new Error("Failed to validate configuration");
  return response.json();
}

/**
 * Get tool schema with examples
 */
export async function fetchToolSchema(toolId: string): Promise<ToolSchema> {
  const response = await fetch(`/api/agent-builder/tool-config/schema/${toolId}`);
  if (!response.ok) throw new Error("Failed to fetch tool schema");
  return response.json();
}

/**
 * Fetch agent tools
 */
export async function fetchAgentTools(agentId: string): Promise<{
  tools: Array<{
    tool_id: string;
    tool: Tool;
    configuration: Record<string, any>;
    order: number;
  }>;
}> {
  const response = await fetch(`/api/agent-builder/agents/${agentId}/tools`);
  if (!response.ok) throw new Error("Failed to fetch agent tools");
  return response.json();
}

/**
 * Update agent tools
 */
export async function updateAgentTools(
  agentId: string,
  tools: Array<{
    tool_id: string;
    configuration: Record<string, any>;
    order: number;
  }>
): Promise<void> {
  const response = await fetch(`/api/agent-builder/agents/${agentId}/tools`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tools }),
  });
  if (!response.ok) throw new Error("Failed to update agent tools");
}

/**
 * Tool execution interfaces
 */
export interface ToolExecutionRequest {
  tool_name: string;
  parameters: Record<string, any>;
  config?: Record<string, any>;
}

export interface ToolExecutionResponse {
  success: boolean;
  result?: any;
  error?: string;
  execution_time?: number;
}

/**
 * Execute a tool with given parameters
 */
export async function executeTool(
  request: ToolExecutionRequest
): Promise<ToolExecutionResponse> {
  const response = await fetch("/api/agent-builder/tool-execution/execute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error("Failed to execute tool");
  return response.json();
}

/**
 * Get available tools by category
 */
export async function getAvailableTools(): Promise<Record<string, string[]>> {
  const response = await fetch("/api/agent-builder/tool-execution/available-tools");
  if (!response.ok) throw new Error("Failed to fetch available tools");
  return response.json();
}

/**
 * Validate tool configuration
 */
export async function validateToolExecution(
  request: ToolExecutionRequest
): Promise<{ valid: boolean; tool_name: string; message: string }> {
  const response = await fetch("/api/agent-builder/tool-execution/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error("Failed to validate tool");
  return response.json();
}
