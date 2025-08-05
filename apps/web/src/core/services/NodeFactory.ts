import { v4 as uuidv4 } from 'uuid';
import {
  type NodeType,
  type DomainNode,
  type Vec2,
  type NodeID,
  NODE_TYPE_REVERSE_MAP,
  type NodeSpecification,
  type DomainHandle,
  type HandleID,
  HandleDirection,
  DataType,
  HandleLabel,
} from '@dipeo/models';
import { NodeService } from './NodeService';
import { ValidationService } from './ValidationService';

// Result type for validation
export interface ValidationError {
  field?: string;
  message: string;
}

export type Result<T, E> = 
  | { success: true; data: T }
  | { success: false; error: E };

/**
 * NodeFactory - Factory service for creating domain nodes with validation
 * Provides type-safe node creation with automatic default values and validation
 */
export class NodeFactory {
  /**
   * Create a node with default values and validation
   * @param type - Node type enum
   * @param position - Node position
   * @param data - Optional partial node data
   * @returns Created DomainNode
   */
  static createNode<T extends NodeType>(
    type: T,
    position: Vec2,
    data?: Partial<Record<string, any>>
  ): DomainNode {
    const spec = NodeService.getNodeSpec(type);
    if (!spec) {
      throw new Error(`Unknown node type: ${type}`);
    }

    // Get defaults from node specification
    const defaults = NodeService.getNodeDefaults(type);
    
    // Merge provided data with defaults
    const nodeData = {
      ...defaults,
      ...(data || {}),
    };

    // Generate unique ID
    const nodeId = uuidv4() as NodeID;

    // Create the node
    const node: DomainNode = {
      id: nodeId,
      type: NODE_TYPE_REVERSE_MAP[type] as any,
      position,
      data: nodeData,
    };

    return node;
  }

  /**
   * Create a node with validation
   * @param type - Node type enum
   * @param position - Node position
   * @param data - Optional partial node data
   * @returns Result with created node or validation error
   */
  static createNodeWithValidation<T extends NodeType>(
    type: T,
    position: Vec2,
    data?: Partial<Record<string, any>>
  ): Result<DomainNode, ValidationError[]> {
    try {
      // Create the node
      const node = this.createNode(type, position, data);

      // Validate the node data
      const validationResult = ValidationService.validateNodeData(type, node.data);
      
      if (!validationResult.success) {
        const errors: ValidationError[] = [];
        
        if ('error' in validationResult && validationResult.error) {
          const zodError = validationResult.error as any;
          if (zodError.issues) {
            for (const issue of zodError.issues) {
              errors.push({
                field: issue.path.join('.'),
                message: issue.message,
              });
            }
          }
        }

        return { success: false, error: errors };
      }

      return { success: true, data: node };
    } catch (error) {
      return {
        success: false,
        error: [{
          message: error instanceof Error ? error.message : 'Unknown error creating node',
        }],
      };
    }
  }

  /**
   * Create a node from a specification
   * @param spec - Node specification
   * @param position - Node position
   * @returns Created DomainNode
   */
  static createNodeFromSpec(
    spec: NodeSpecification,
    position: Vec2
  ): DomainNode {
    // Extract defaults from specification fields
    const defaults: Record<string, any> = {};
    
    for (const field of spec.fields) {
      if (field.defaultValue !== undefined) {
        defaults[field.name] = field.defaultValue;
      }
    }

    // Generate unique ID
    const nodeId = uuidv4() as NodeID;

    // Create the node
    const node: DomainNode = {
      id: nodeId,
      type: spec.nodeType as any,
      position,
      data: defaults,
    };

    return node;
  }

  /**
   * Create handles for a node based on its specification
   * @param nodeId - ID of the node
   * @param type - Node type
   * @returns Array of domain handles
   */
  static createNodeHandles(nodeId: NodeID, type: NodeType | string): DomainHandle[] {
    const spec = NodeService.getNodeSpec(type);
    if (!spec) {
      return [];
    }

    const handles: DomainHandle[] = [];
    const handleConfig = spec.handles;

    // Create input handles
    for (const inputName of handleConfig.inputs) {
      const handleLabel = inputName as HandleLabel; // Cast since we know it's from spec
      const handleId = `${nodeId}_${handleLabel}_input` as HandleID;
      handles.push({
        id: handleId,
        node_id: nodeId,
        direction: HandleDirection.INPUT,
        data_type: DataType.ANY,
        label: handleLabel,
        position: null,
      });
    }

    // Create output handles
    for (const outputName of handleConfig.outputs) {
      const handleLabel = outputName as HandleLabel; // Cast since we know it's from spec
      const handleId = `${nodeId}_${handleLabel}_output` as HandleID;
      handles.push({
        id: handleId,
        node_id: nodeId,
        direction: HandleDirection.OUTPUT,
        data_type: DataType.ANY,
        label: handleLabel,
        position: null,
      });
    }

    return handles;
  }

  /**
   * Clone a node with a new ID and position
   * @param node - Node to clone
   * @param position - New position
   * @returns Cloned node
   */
  static cloneNode(node: DomainNode, position: Vec2): DomainNode {
    const newId = uuidv4() as NodeID;
    
    return {
      ...node,
      id: newId,
      position,
      data: { ...node.data }, // Shallow clone of data
    };
  }

  /**
   * Create a batch of nodes efficiently
   * @param specs - Array of node creation specs
   * @returns Array of created nodes
   */
  static createBatch(
    specs: Array<{
      type: NodeType;
      position: Vec2;
      data?: Partial<Record<string, any>>;
    }>
  ): DomainNode[] {
    return specs.map(spec => this.createNode(spec.type, spec.position, spec.data));
  }

  /**
   * Create a batch of nodes with validation
   * @param specs - Array of node creation specs
   * @returns Result with created nodes or validation errors
   */
  static createBatchWithValidation(
    specs: Array<{
      type: NodeType;
      position: Vec2;
      data?: Partial<Record<string, any>>;
    }>
  ): Result<DomainNode[], Map<number, ValidationError[]>> {
    const nodes: DomainNode[] = [];
    const errors = new Map<number, ValidationError[]>();
    
    for (let i = 0; i < specs.length; i++) {
      const spec = specs[i];
      const result = spec ? this.createNodeWithValidation(spec.type, spec.position, spec.data) : { success: false, error: [{ message: 'Invalid spec' }] };
      
      if ('data' in result && result.success) {
        nodes.push(result.data);
      } else {
        errors.set(i, result.error);
      }
    }

    if (errors.size > 0) {
      return { success: false, error: errors };
    }

    return { success: true, data: nodes };
  }
}