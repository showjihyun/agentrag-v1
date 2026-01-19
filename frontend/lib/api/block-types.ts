/**
 * Block Types API Client
 * 
 * Provides type-safe access to the Block Registry API for fetching
 * available block types and their configurations.
 */

export interface BlockSubBlock {
  id: string;
  type: 'text' | 'textarea' | 'number' | 'dropdown' | 'toggle' | 'slider' | 'multi-select';
  title: string;
  required?: boolean;
  placeholder?: string;
  default?: any;
  min?: number;
  max?: number;
  step?: number;
  options?: Array<{ label: string; value: string }> | string[];
}

export interface BlockTypeConfig {
  type: string;
  name: string;
  description: string;
  category: string;
  bg_color: string;
  icon: string;
  sub_blocks: BlockSubBlock[];
  inputs: Record<string, any>;
  outputs: Record<string, any>;
  auth_mode?: string;
  docs_link?: string;
}

export interface BlockTypesByCategory {
  [category: string]: BlockTypeConfig[];
}

export interface BlockTypeStats {
  total_blocks: number;
  by_category: Record<string, number>;
  block_types: string[];
  categories: string[];
}

class BlockTypesAPI {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  /**
   * Get all block types grouped by category
   */
  async getAllBlockTypes(): Promise<BlockTypesByCategory> {
    const response = await fetch(`${this.baseUrl}/api/agent-builder/block-types`);
    if (!response.ok) {
      throw new Error('Failed to fetch block types');
    }
    return response.json();
  }

  /**
   * Get block types for a specific category
   */
  async getBlockTypesByCategory(category: string): Promise<BlockTypeConfig[]> {
    const response = await fetch(
      `${this.baseUrl}/api/agent-builder/block-types/category/${category}`
    );
    if (!response.ok) {
      throw new Error(`Failed to fetch block types for category: ${category}`);
    }
    return response.json();
  }

  /**
   * Get configuration for a specific block type
   */
  async getBlockType(blockType: string): Promise<BlockTypeConfig> {
    const response = await fetch(
      `${this.baseUrl}/api/agent-builder/block-types/${blockType}`
    );
    if (!response.ok) {
      throw new Error(`Failed to fetch block type: ${blockType}`);
    }
    return response.json();
  }

  /**
   * Get input/output schema for a specific block type
   */
  async getBlockTypeSchema(blockType: string): Promise<{
    inputs: Record<string, any>;
    outputs: Record<string, any>;
  }> {
    const response = await fetch(
      `${this.baseUrl}/api/agent-builder/block-types/${blockType}/schema`
    );
    if (!response.ok) {
      throw new Error(`Failed to fetch schema for block type: ${blockType}`);
    }
    return response.json();
  }

  /**
   * Get block registry statistics
   */
  async getStats(): Promise<BlockTypeStats> {
    const response = await fetch(
      `${this.baseUrl}/api/agent-builder/block-types/stats/summary`
    );
    if (!response.ok) {
      throw new Error('Failed to fetch block type stats');
    }
    return response.json();
  }

  /**
   * Get agentic block types (convenience method)
   */
  async getAgenticBlocks(): Promise<BlockTypeConfig[]> {
    return this.getBlockTypesByCategory('agentic');
  }
}

// Export singleton instance
export const blockTypesAPI = new BlockTypesAPI();

// Export for testing
export { BlockTypesAPI };
