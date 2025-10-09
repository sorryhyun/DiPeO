/**
 * Node Converter Module
 *
 * Handles all conversions related to diagram nodes.
 * Provides consistent transformations between GraphQL, Domain, and UI representations.
 */

import {
  type NodeID,
  type DomainNode,
  type NodeType,
  nodeKindToDomainType,
  domainTypeToNodeKind,
  NODE_TYPE_MAP
} from '@dipeo/models';
import type { DomainNodeType } from '@/__generated__/graphql';
import { nodeId } from '@/infrastructure/types/branded';

export class NodeConverter {
  /**
   * Convert GraphQL node to domain node
   */
  static toDomain(graphqlNode: DomainNodeType): DomainNode {
    return {
      id: nodeId(graphqlNode.id),
      type: nodeKindToDomainType(graphqlNode.type),
      position: graphqlNode.position,
      data: (graphqlNode.data || {}) as any
    };
  }

  /**
   * Convert domain node to GraphQL input
   */
  static toGraphQL(domainNode: DomainNode): Partial<DomainNodeType> {
    return {
      id: domainNode.id,
      type: domainNode.type,
      position: domainNode.position,
      data: domainNode.data
    };
  }

  /**
   * Batch convert GraphQL nodes to domain
   */
  static batchToDomain(graphqlNodes: DomainNodeType[]): DomainNode[] {
    return graphqlNodes.map(node => this.toDomain(node));
  }

  /**
   * Batch convert domain nodes to GraphQL
   */
  static batchToGraphQL(domainNodes: DomainNode[]): Partial<DomainNodeType>[] {
    return domainNodes.map(node => this.toGraphQL(node));
  }

  /**
   * Convert array to Map for efficient lookups
   */
  static arrayToMap(nodes: DomainNode[]): Map<NodeID, DomainNode> {
    return new Map(nodes.map(node => [node.id, node]));
  }

  /**
   * Filter nodes by type
   */
  static filterByType(nodes: DomainNode[], type: NodeType): DomainNode[] {
    return nodes.filter(node => node.type === type);
  }

  /**
   * Group nodes by type
   */
  static groupByType(nodes: DomainNode[]): Map<NodeType, DomainNode[]> {
    const groups = new Map<NodeType, DomainNode[]>();
    nodes.forEach(node => {
      const group = groups.get(node.type) || [];
      group.push(node);
      groups.set(node.type, group);
    });
    return groups;
  }

  /**
   * Check if string is valid node type
   */
  static isValidNodeType(type: string): boolean {
    return type.toLowerCase() in NODE_TYPE_MAP;
  }

  /**
   * Get node type from string safely
   */
  static parseNodeType(type: string): NodeType | null {
    try {
      return nodeKindToDomainType(type);
    } catch {
      return null;
    }
  }

  /**
   * Create a minimal node with defaults
   */
  static createNode(id: string, type: NodeType, position: { x: number; y: number }): DomainNode {
    return {
      id: nodeId(id),
      type,
      position,
      data: {}
    };
  }
}
