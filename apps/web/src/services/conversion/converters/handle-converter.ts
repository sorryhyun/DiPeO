/**
 * Handle Converter Module
 * 
 * Handles all conversions related to node handles (connection points).
 * Manages handle ID parsing, creation, and compatibility checks.
 */

import {
  type HandleID,
  type NodeID,
  type DomainHandle,
  type HandleLabel,
  type DataType,
  HandleDirection,
  parseHandleId,
  createHandleId,
  areHandlesCompatible
} from '@dipeo/models';
import type { DomainHandleType } from '@/__generated__/graphql';
import { handleId, nodeId } from '@/core/types/branded';

export class HandleConverter {
  /**
   * Convert GraphQL handle to domain handle
   */
  static toDomain(graphqlHandle: DomainHandleType): DomainHandle {
    return {
      id: handleId(graphqlHandle.id),
      node_id: nodeId(graphqlHandle.node_id),
      label: graphqlHandle.label as HandleLabel,
      direction: graphqlHandle.direction as HandleDirection,
      data_type: graphqlHandle.data_type as DataType,
      position: graphqlHandle.position
    };
  }
  
  /**
   * Convert domain handle to GraphQL input
   */
  static toGraphQL(domainHandle: DomainHandle): Partial<DomainHandleType> {
    return {
      id: domainHandle.id,
      node_id: domainHandle.node_id,
      label: domainHandle.label,
      direction: domainHandle.direction,
      data_type: domainHandle.data_type,
      position: domainHandle.position
    };
  }
  
  /**
   * Batch convert GraphQL handles to domain
   */
  static batchToDomain(graphqlHandles: DomainHandleType[]): DomainHandle[] {
    return graphqlHandles.map(handle => this.toDomain(handle));
  }
  
  /**
   * Batch convert domain handles to GraphQL
   */
  static batchToGraphQL(domainHandles: DomainHandle[]): Partial<DomainHandleType>[] {
    return domainHandles.map(handle => this.toGraphQL(handle));
  }
  
  /**
   * Convert array to Map for efficient lookups
   */
  static arrayToMap(handles: DomainHandle[]): Map<HandleID, DomainHandle> {
    return new Map(handles.map(handle => [handle.id, handle]));
  }
  
  /**
   * Parse handle ID into components
   */
  static parseId(id: HandleID): {
    node_id: NodeID;
    handle_label: HandleLabel;
    direction: HandleDirection;
  } {
    return parseHandleId(id);
  }
  
  /**
   * Create handle ID from components
   */
  static createId(
    nodeId: NodeID,
    label: HandleLabel,
    direction: HandleDirection
  ): HandleID {
    return createHandleId(nodeId, label, direction);
  }
  
  /**
   * Check if two handles can be connected
   */
  static areCompatible(source: DomainHandle, target: DomainHandle): boolean {
    return areHandlesCompatible(source, target);
  }
  
  /**
   * Find handles by node ID
   */
  static findByNode(handles: DomainHandle[], nodeId: NodeID): DomainHandle[] {
    return handles.filter(handle => handle.node_id === nodeId);
  }
  
  /**
   * Find handles by direction
   */
  static findByDirection(
    handles: DomainHandle[],
    direction: HandleDirection
  ): DomainHandle[] {
    return handles.filter(handle => handle.direction === direction);
  }
  
  /**
   * Group handles by node
   */
  static groupByNode(handles: DomainHandle[]): Map<NodeID, DomainHandle[]> {
    const groups = new Map<NodeID, DomainHandle[]>();
    handles.forEach(handle => {
      const group = groups.get(handle.node_id) || [];
      group.push(handle);
      groups.set(handle.node_id, group);
    });
    return groups;
  }
  
  /**
   * Get input/output handles for a node
   */
  static getNodeHandles(handles: DomainHandle[], nodeId: NodeID): {
    inputs: DomainHandle[];
    outputs: DomainHandle[];
  } {
    const nodeHandles = this.findByNode(handles, nodeId);
    return {
      inputs: nodeHandles.filter(h => h.direction === HandleDirection.INPUT),
      outputs: nodeHandles.filter(h => h.direction === HandleDirection.OUTPUT)
    };
  }
  
  /**
   * Create a minimal handle
   */
  static createHandle(
    nodeId: NodeID,
    label: HandleLabel,
    direction: HandleDirection,
    dataType: DataType = 'any' as DataType
  ): DomainHandle {
    return {
      id: this.createId(nodeId, label, direction),
      node_id: nodeId,
      label,
      direction,
      data_type: dataType,
      position: JSON.stringify({ x: 0, y: 0 })
    };
  }
}