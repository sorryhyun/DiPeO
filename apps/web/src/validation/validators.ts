import { z } from 'zod';
import { parseDiagram, parseNodeData } from './registry';
import { DomainPersonSchema } from './schemas';
import { ValidationError, formatZodError } from './errors';
import { DomainDiagram } from '@/types/domain';
import { NodeType } from '@/types/enums';
import { PersonID, NodeID } from '@/types/branded';

/**
 * Validate diagram from API response
 */
export function validateDiagramResponse(data: unknown): DomainDiagram {
  try {
    return parseDiagram(data);
  } catch (error) {
    if (error instanceof z.ZodError) {
      console.error('Diagram validation failed:', formatZodError(error));
      throw new ValidationError('Invalid diagram format', error);
    }
    throw error;
  }
}

/**
 * Validate node creation data
 * @public - Part of validation API for form inputs
 */
export function validateNodeCreation(type: NodeType, data: unknown): unknown {
  try {
    return parseNodeData(type, data);
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw new ValidationError(`Invalid ${type} node data`, error);
    }
    throw error;
  }
}

/**
 * Validate person creation data
 * @public - Part of validation API for form inputs
 */
export function validatePersonCreation(data: unknown): unknown {
  try {
    return DomainPersonSchema.parse(data);
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw new ValidationError('Invalid person data', error);
    }
    throw error;
  }
}

/**
 * Business rule validation for diagrams
 */
export function validateDiagramBusinessRules(diagram: DomainDiagram): void {
  const errors: string[] = [];

  // Check for orphaned handles
  for (const handle of Object.values(diagram.handles)) {
    if (!diagram.nodes[handle.nodeId]) {
      errors.push(`Handle ${handle.id} references non-existent node ${handle.nodeId}`);
    }
  }

  // Check for invalid arrow connections
  for (const arrow of Object.values(diagram.arrows)) {
    if (!diagram.handles[arrow.source]) {
      errors.push(`Arrow ${arrow.id} references non-existent source handle ${arrow.source}`);
    }
    if (!diagram.handles[arrow.target]) {
      errors.push(`Arrow ${arrow.id} references non-existent target handle ${arrow.target}`);
    }
  }

  // Check for missing persons in person_job nodes
  for (const node of Object.values(diagram.nodes)) {
    if ((node.type === 'person_job' || node.type === 'person_batch_job') && node.data.agent) {
      const agentId = node.data.agent as string;
      if (!diagram.persons[agentId as PersonID]) {
        errors.push(`Node ${node.id} references non-existent person ${agentId}`);
      }
    }
  }

  // Check for cycles in condition nodes with detect_max_iterations
  const conditionNodes = Object.values(diagram.nodes).filter(
    n => n.type === 'condition' && n.data.detect_max_iterations
  );
  
  if (conditionNodes.length > 0) {
    // TODO: Implement cycle detection
  }

  if (errors.length > 0) {
    throw new ValidationError(
      `Diagram validation failed:\n${errors.join('\n')}`
    );
  }
}

/**
 * Validate diagram before execution
 */
export function validateDiagramForExecution(diagram: DomainDiagram): void {
  // First validate structure
  validateDiagramResponse(diagram);
  
  // Then validate business rules
  validateDiagramBusinessRules(diagram);
  
  // Check for required start node
  const startNodes = Object.values(diagram.nodes).filter(n => n.type === 'start');
  if (startNodes.length === 0) {
    throw new ValidationError('Diagram must have at least one start node');
  }
  
  // Check for disconnected nodes
  const connectedNodes = new Set<string>();
  for (const arrow of Object.values(diagram.arrows)) {
    const sourceNode = arrow.source.split(':')[0];
    const targetNode = arrow.target.split(':')[0];
    if (sourceNode) connectedNodes.add(sourceNode);
    if (targetNode) connectedNodes.add(targetNode);
  }
  
  const disconnectedNodes = Object.keys(diagram.nodes).filter(
    nodeId => {
      const node = diagram.nodes[nodeId as NodeID];
      return node && !connectedNodes.has(nodeId) && node.type !== 'start';
    }
  );
  
  if (disconnectedNodes.length > 0) {
    console.warn('Disconnected nodes found:', disconnectedNodes);
  }
}