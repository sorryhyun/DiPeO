import { z, type ZodError, type SafeParseReturnType } from 'zod';
import { NODE_DATA_SCHEMAS } from '@/__generated__/schemas';
import {
  type NodeType,
  type DomainHandle,
  type DomainDiagram,
  type DomainNode,
  type DomainArrow,
  areHandlesCompatible,
  NODE_TYPE_REVERSE_MAP
} from '@dipeo/models';
import { Converters } from '../converters';

// Type aliases for clarity
type SafeParseResult<T = any> = SafeParseReturnType<T, T>;
type FieldErrors = Record<string, string[]>;

interface ValidationResult {
  valid: boolean;
  errors: string[];
}

export interface DiagramValidationResult {
  valid: boolean;
  nodeErrors: Map<string, FieldErrors>;
  connectionErrors: string[];
  generalErrors: string[];
}

/**
 * ValidationService - Centralized validation for nodes, connections, and diagrams
 * Uses generated Zod schemas for type-safe validation
 */
export class ValidationService {
  /**
   * Validate node data against its schema
   * @param type - Node type enum or string
   * @param data - Data to validate
   * @returns Zod SafeParseResult
   */
  static validateNodeData(type: NodeType | string, data: unknown): SafeParseResult {
    const typeKey = typeof type === 'string' ? type : NODE_TYPE_REVERSE_MAP[type];
    const schema = NODE_DATA_SCHEMAS[typeKey as keyof typeof NODE_DATA_SCHEMAS];

    if (!schema) {
      return {
        success: false,
        error: new z.ZodError([{
          code: 'custom',
          message: `No validation schema found for node type: ${typeKey}`,
          path: []
        }])
      } as SafeParseResult;
    }

    return schema.safeParse(data);
  }

  /**
   * Get field-level errors from validation result
   * @param type - Node type enum or string
   * @param data - Data that was validated
   * @returns Object mapping field names to error messages
   */
  static getFieldErrors(type: NodeType | string, data: unknown): FieldErrors {
    const result = this.validateNodeData(type, data);

    if (result.success) {
      return {};
    }

    const errors: FieldErrors = {};

    if (result.error instanceof z.ZodError) {
      for (const issue of result.error.issues) {
        const path = issue.path.join('.');
        if (!errors[path]) {
          errors[path] = [];
        }
        errors[path].push(issue.message);
      }
    }

    return errors;
  }

  /**
   * Validate a connection between two handles
   * @param source - Source handle
   * @param target - Target handle
   * @returns Validation result with error messages
   */
  static validateConnection(source: DomainHandle, target: DomainHandle): ValidationResult {
    const errors: string[] = [];

    if (!source || !target) {
      errors.push('Both source and target handles are required');
      return { valid: false, errors };
    }

    if (source.id === target.id) {
      errors.push('Cannot connect a handle to itself');
      return { valid: false, errors };
    }

    if (!areHandlesCompatible(source, target)) {
      const sourceInfo = Converters.parseHandleId(source.id);
      const targetInfo = Converters.parseHandleId(target.id);

      if (source.direction === target.direction) {
        errors.push(`Cannot connect two ${source.direction} handles`);
      } else if (source.direction !== 'output') {
        errors.push('Connections must originate from output handles');
      } else if (source.data_type !== target.data_type &&
                 source.data_type !== 'any' &&
                 target.data_type !== 'any') {
        errors.push(
          `Incompatible data types: ${source.data_type} (source) and ${target.data_type} (target)`
        );
      }
    }

    return { valid: errors.length === 0, errors };
  }

  /**
   * Validate an entire diagram
   * @param diagram - Diagram to validate
   * @returns Comprehensive validation results
   */
  static validateDiagram(diagram: DomainDiagram): DiagramValidationResult {
    const nodeErrors = new Map<string, FieldErrors>();
    const connectionErrors: string[] = [];
    const generalErrors: string[] = [];

    // Convert to maps for efficient lookups
    const { nodes, handles, arrows } = Converters.diagramArraysToMaps(diagram);

    // Validate each node
    for (const [nodeId, node] of nodes) {
      const fieldErrors = this.getFieldErrors(node.type, node.data);
      if (Object.keys(fieldErrors).length > 0) {
        nodeErrors.set(nodeId, fieldErrors);
      }
    }

    // Validate connections
    for (const [arrowId, arrow] of arrows) {
      const sourceHandle = handles.get(arrow.source);
      const targetHandle = handles.get(arrow.target);

      if (!sourceHandle) {
        connectionErrors.push(`Arrow ${arrowId}: Source handle ${arrow.source} not found`);
        continue;
      }

      if (!targetHandle) {
        connectionErrors.push(`Arrow ${arrowId}: Target handle ${arrow.target} not found`);
        continue;
      }

      const connectionResult = this.validateConnection(sourceHandle, targetHandle);
      if (!connectionResult.valid) {
        connectionErrors.push(
          `Arrow ${arrowId}: ${connectionResult.errors.join(', ')}`
        );
      }
    }

    // Check for orphaned nodes (no connections)
    const connectedNodes = new Set<string>();
    for (const arrow of arrows.values()) {
      const sourceHandleInfo = Converters.parseHandleId(arrow.source);
      const targetHandleInfo = Converters.parseHandleId(arrow.target);
      connectedNodes.add(sourceHandleInfo.node_id);
      connectedNodes.add(targetHandleInfo.node_id);
    }

    // Start nodes don't need incoming connections
    const startNodes = Array.from(nodes.values()).filter(n => n.type === 'start');
    startNodes.forEach(n => connectedNodes.add(n.id));

    for (const [nodeId, node] of nodes) {
      if (!connectedNodes.has(nodeId) && node.type !== 'start') {
        generalErrors.push(`Node ${nodeId} (${node.type}) has no connections`);
      }
    }

    // Check for required start node
    if (startNodes.length === 0) {
      generalErrors.push('Diagram must have at least one start node');
    }

    return {
      valid: nodeErrors.size === 0 && connectionErrors.length === 0 && generalErrors.length === 0,
      nodeErrors,
      connectionErrors,
      generalErrors
    };
  }

  /**
   * Check if a value is valid for a specific field
   * @param type - Node type
   * @param fieldName - Field name to validate
   * @param value - Value to check
   * @returns True if valid
   */
  static isFieldValid(type: NodeType | string, fieldName: string, value: unknown): boolean {
    const typeKey = typeof type === 'string' ? type : NODE_TYPE_REVERSE_MAP[type];
    const schema = NODE_DATA_SCHEMAS[typeKey as keyof typeof NODE_DATA_SCHEMAS];

    if (!schema || !(schema instanceof z.ZodObject)) {
      return false;
    }

    const fieldSchema = (schema as any).shape[fieldName];
    if (!fieldSchema) {
      return false;
    }

    const result = fieldSchema.safeParse(value);
    return result.success;
  }

  /**
   * Get validation messages for a specific field
   * @param type - Node type
   * @param fieldName - Field name
   * @param value - Value that was validated
   * @returns Array of error messages
   */
  static getFieldValidationMessages(
    type: NodeType | string,
    fieldName: string,
    value: unknown
  ): string[] {
    const typeKey = typeof type === 'string' ? type : NODE_TYPE_REVERSE_MAP[type];
    const schema = NODE_DATA_SCHEMAS[typeKey as keyof typeof NODE_DATA_SCHEMAS];

    if (!schema || !(schema instanceof z.ZodObject)) {
      return [`No validation schema found for ${typeKey}.${fieldName}`];
    }

    const fieldSchema = (schema as any).shape[fieldName];
    if (!fieldSchema) {
      return [`Field ${fieldName} not found in schema for ${typeKey}`];
    }

    const result = fieldSchema.safeParse(value);
    if (result.success) {
      return [];
    }

    return result.error.issues.map((issue: any) => issue.message);
  }
}
