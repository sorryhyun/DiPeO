import {
  getNodeSpecification,
  nodeSpecificationRegistry,
  type NodeSpecification,
  type NodeType,
  type HandleConfiguration,
  type NodeCategory,
  NODE_TYPE_REVERSE_MAP
} from '@dipeo/models';

/**
 * NodeService - Facade for node-related operations and specifications
 * Provides a centralized interface for node metadata, configuration, and utilities
 */
export class NodeService {
  private static specCache = new Map<string, NodeSpecification>();
  
  /**
   * Get node specification by type with caching
   * @param type - Node type enum or string
   * @returns Node specification or undefined if not found
   */
  static getNodeSpec(type: NodeType | string): NodeSpecification | undefined {
    const typeKey = typeof type === 'string' ? type : NODE_TYPE_REVERSE_MAP[type];
    
    if (!typeKey) {
      console.warn(`Unknown node type: ${type}`);
      return undefined;
    }
    
    // Check cache first
    if (this.specCache.has(typeKey)) {
      return this.specCache.get(typeKey);
    }
    
    // Get from registry and cache
    const spec = getNodeSpecification(typeKey);
    if (spec) {
      this.specCache.set(typeKey, spec);
    }
    
    return spec;
  }
  
  /**
   * Get node category for a given type
   * @param type - Node type enum or string
   * @returns Node category or undefined
   */
  static getNodeCategory(type: NodeType | string): NodeCategory | undefined {
    const spec = this.getNodeSpec(type);
    return spec?.category;
  }
  
  /**
   * Get node handle configuration
   * @param type - Node type enum or string
   * @returns Handle configuration or empty handles
   */
  static getNodeHandles(type: NodeType | string): HandleConfiguration {
    const spec = this.getNodeSpec(type);
    return spec?.handles || { inputs: [], outputs: [] };
  }
  
  /**
   * Get default values for node data fields
   * @param type - Node type enum or string
   * @returns Object with default field values
   */
  static getNodeDefaults(type: NodeType | string): Record<string, unknown> {
    const spec = this.getNodeSpec(type);
    if (!spec) return {};
    
    const defaults: Record<string, unknown> = {};
    
    for (const field of spec.fields) {
      if (field.defaultValue !== undefined) {
        defaults[field.name] = field.defaultValue;
      }
    }
    
    return defaults;
  }
  
  /**
   * Get node icon
   * @param type - Node type enum or string
   * @returns Icon string or default icon
   */
  static getNodeIcon(type: NodeType | string): string {
    const spec = this.getNodeSpec(type);
    return spec?.icon || '📦';
  }
  
  /**
   * Get node color
   * @param type - Node type enum or string
   * @returns Color string or default color
   */
  static getNodeColor(type: NodeType | string): string {
    const spec = this.getNodeSpec(type);
    return spec?.color || '#808080';
  }
  
  /**
   * Get node display name
   * @param type - Node type enum or string
   * @returns Display name or type string
   */
  static getNodeDisplayName(type: NodeType | string): string {
    const spec = this.getNodeSpec(type);
    return spec?.displayName || String(type);
  }
  
  /**
   * Get node description
   * @param type - Node type enum or string
   * @returns Description or empty string
   */
  static getNodeDescription(type: NodeType | string): string {
    const spec = this.getNodeSpec(type);
    return spec?.description || '';
  }
  
  /**
   * Get all available node types
   * @returns Array of node type strings
   */
  static getAllNodeTypes(): string[] {
    return Object.keys(nodeSpecificationRegistry);
  }
  
  /**
   * Get nodes by category
   * @param category - Category to filter by
   * @returns Array of node type strings
   */
  static getNodesByCategory(category: NodeCategory): string[] {
    return this.getAllNodeTypes().filter(type => {
      const spec = this.getNodeSpec(type);
      return spec?.category === category;
    });
  }
  
  /**
   * Check if a node type exists
   * @param type - Node type to check
   * @returns True if node type exists
   */
  static nodeTypeExists(type: NodeType | string): boolean {
    return this.getNodeSpec(type) !== undefined;
  }
  
  /**
   * Get primary display field for a node type
   * @param type - Node type enum or string
   * @returns Field name or undefined
   */
  static getPrimaryDisplayField(type: NodeType | string): string | undefined {
    const spec = this.getNodeSpec(type);
    return spec?.primaryDisplayField;
  }
  
  /**
   * Clear the specification cache
   * Useful for hot reloading or testing
   */
  static clearCache(): void {
    this.specCache.clear();
  }
}