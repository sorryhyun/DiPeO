import {
  parseHandleId as domainParseHandleId,
  createHandleId as domainCreateHandleId,
  diagramArraysToMaps,
  diagramMapsToArrays,
  areHandlesCompatible,
  convertGraphQLPersonToDomain,
  convertGraphQLDiagramToDomain,
  NODE_TYPE_MAP,
  NODE_TYPE_REVERSE_MAP,
  nodeKindToDomainType,
  domainTypeToNodeKind,
  type NodeID,
  type ArrowID,
  type PersonID,
  type HandleID,
  type ApiKeyID,
  type DiagramID,
  type ExecutionID,
  type DomainDiagram,
  type DomainNode,
  type DomainArrow,
  type DomainHandle,
  type DomainPerson,
  type DomainApiKey,
  type DiagramMetadata,
  type NodeType,
  type ExecutionState,
  type NodeState,
  type LLMUsage,
  type ExecutionUpdate,
  type ContentType,
  Status,
  HandleDirection,
  HandleLabel,
  DataType,
  LLMService,
  EventType
} from '@dipeo/models';
import { nodeId, arrowId, personId, handleId, apiKeyId, diagramId, executionId } from '@/infrastructure/types/branded';
import type {
  DomainNodeType,
  DomainArrowType,
  DomainHandleType,
  DomainPersonType,
  DomainApiKeyType,
  DomainDiagramType,
  ExecutionUpdateType,
  ExecutionStateType,
  Vec2Input
} from '@/__generated__/graphql';

/**
 * Centralized Conversion Service
 *
 * This service provides all type conversions and transformations used across the frontend.
 * It centralizes conversion logic to reduce duplication and ensure consistency.
 *
 * Categories:
 * - ID Type Conversions: Safe casting between string and branded types
 * - Domain Conversions: GraphQL ↔ Domain ↔ Store transformations
 * - Collection Utilities: Array/Set/Map transformations
 * - Node System: Node type conversions and utilities
 * - Execution: Execution state transformations
 */
export class Converters {
  // ===== ID Type Conversions =====

  /**
   * Safely cast string to NodeID
   * Reduces repetitive 'as NodeID' casting
   */
  static toNodeId(id: string): NodeID {
    return nodeId(id);
  }

  /**
   * Safely cast string to ArrowID
   * Reduces repetitive 'as ArrowID' casting
   */
  static toArrowId(id: string): ArrowID {
    return arrowId(id);
  }

  /**
   * Safely cast string to PersonID
   * Reduces repetitive 'as PersonID' casting
   */
  static toPersonId(id: string): PersonID {
    return personId(id);
  }

  /**
   * Safely cast string to HandleID
   * Reduces repetitive 'as HandleID' casting
   */
  static toHandleId(id: string): HandleID {
    return handleId(id);
  }

  /**
   * Safely cast string to ApiKeyID
   */
  static toApiKeyId(id: string): ApiKeyID {
    return apiKeyId(id);
  }

  /**
   * Safely cast string to DiagramID
   */
  static toDiagramId(id: string): DiagramID {
    return diagramId(id);
  }

  /**
   * Safely cast string to ExecutionID
   */
  static toExecutionId(id: string): ExecutionID {
    return executionId(id);
  }

  // ===== Handle ID Operations =====

  /**
   * Parse handle ID into components
   * Centralizes handle ID parsing logic
   */
  static parseHandleId = domainParseHandleId;

  /**
   * Create handle ID from components
   * Centralizes handle ID creation logic
   */
  static createHandleId = domainCreateHandleId;

  // ===== Array/Set/Map Transformations =====

  /**
   * Convert array to Set of unique values based on property
   * Reduces repetitive pattern: new Set(array.map(item => item.prop).filter(Boolean))
   */
  static arrayToUniqueSet<T, K>(array: T[], selector: (item: T) => K | undefined): Set<K> {
    const values = array.map(selector).filter((value): value is K => value !== undefined && value !== null);
    return new Set(values);
  }

  /**
   * Convert array to Map keyed by property
   * Reduces repetitive reduce pattern
   */
  static arrayToMap<T, K extends string | number | symbol>(
    array: T[],
    keySelector: (item: T) => K
  ): Map<K, T> {
    const map = new Map<K, T>();
    array.forEach(item => {
      map.set(keySelector(item), item);
    });
    return map;
  }

  /**
   * Convert array to object keyed by property
   * Reduces repetitive reduce pattern
   */
  static arrayToObject<T, K extends string | number>(
    array: T[],
    keySelector: (item: T) => K
  ): Record<K, T> {
    return array.reduce((acc, item) => {
      acc[keySelector(item)] = item;
      return acc;
    }, {} as Record<K, T>);
  }

  /**
   * Map array with spread to add/modify properties
   * Reduces repetitive map spread pattern
   */
  static mapWithUpdate<T, U extends Partial<T>>(
    array: T[],
    updater: (item: T) => U
  ): Array<T & U> {
    return array.map(item => ({ ...item, ...updater(item) }));
  }

  // ===== Collection Utilities =====

  /**
   * Check if collection is empty
   * Works with arrays, Maps, Sets, and objects
   */
  static isEmpty(collection: unknown): boolean {
    if (!collection) return true;
    if (Array.isArray(collection)) return collection.length === 0;
    if (collection instanceof Map || collection instanceof Set) return collection.size === 0;
    if (typeof collection === 'object') return Object.keys(collection).length === 0;
    return false;
  }

  /**
   * Get unique values from array
   */
  static unique<T>(array: T[]): T[] {
    return Array.from(new Set(array));
  }

  /**
   * Group array items by key
   */
  static groupBy<T, K extends string | number>(
    array: T[],
    keySelector: (item: T) => K
  ): Record<K, T[]> {
    return array.reduce((groups, item) => {
      const key = keySelector(item);
      if (!groups[key]) groups[key] = [];
      groups[key].push(item);
      return groups;
    }, {} as Record<K, T[]>);
  }

  // ===== Data Transformations =====

  /**
   * Convert tools array to comma-separated string
   * Centralizes this common transformation
   */
  static toolsArrayToString(tools: Array<{ type: string }> | null | undefined): string {
    if (!tools || !Array.isArray(tools)) return '';
    return tools.map(tool => tool.type).join(', ');
  }

  /**
   * Convert comma-separated string to tools array
   * Centralizes this common transformation
   */
  static stringToToolsArray(toolsString: string): Array<{ type: string; enabled: boolean }> {
    if (!toolsString || !toolsString.trim()) return [];
    return toolsString.split(',').map(type => ({
      type: type.trim(),
      enabled: true
    }));
  }

  // ===== Domain Conversions =====

  /**
   * Convert diagram with arrays to diagram with maps for efficient lookups
   * Centralizes the conversion logic from @dipeo/models
   */
  static diagramArraysToMaps(diagram: Partial<DomainDiagram>): {
    nodes: Map<NodeID, DomainNode>;
    arrows: Map<ArrowID, DomainArrow>;
    handles: Map<HandleID, DomainHandle>;
    persons: Map<PersonID, DomainPerson>;
  } {
    return diagramArraysToMaps(diagram);
  }

  /**
   * Convert diagram with maps back to arrays for storage/transmission
   * Centralizes the conversion logic from @dipeo/models
   */
  static diagramMapsToArrays(maps: {
    nodes: Map<NodeID, DomainNode>;
    arrows: Map<ArrowID, DomainArrow>;
    handles: Map<HandleID, DomainHandle>;
    persons: Map<PersonID, DomainPerson>;
  }): DomainDiagram {
    return diagramMapsToArrays(maps) as DomainDiagram;
  }

  /**
   * Check if two handles are compatible for connection
   * Centralizes handle compatibility logic from @dipeo/models
   */
  static areHandlesCompatible(source: DomainHandle, target: DomainHandle): boolean {
    return areHandlesCompatible(source, target);
  }

  /**
   * Convert GraphQL person response to domain person model
   * Centralizes GraphQL conversion logic
   */
  static convertGraphQLPerson(person: any): DomainPerson {
    return convertGraphQLPersonToDomain(person);
  }

  /**
   * Convert GraphQL diagram response to domain diagram model
   * Centralizes GraphQL conversion logic
   */
  static convertGraphQLDiagram(diagram: any): Partial<DomainDiagram> {
    return convertGraphQLDiagramToDomain(diagram);
  }

  /**
   * Convert node type enum to string representation
   * Uses the reverse map from @dipeo/models
   */
  static nodeTypeToString(type: NodeType): string {
    return domainTypeToNodeKind(type);
  }

  /**
   * Convert string to node type enum
   * Uses the node type map from @dipeo/models
   */
  static stringToNodeType(str: string): NodeType {
    return nodeKindToDomainType(str);
  }

  // ===== GraphQL to Domain Conversions =====

  /**
   * Convert GraphQL node to domain node
   */
  static graphQLNodeToDomain(node: DomainNodeType): DomainNode {
    return {
      id: this.toNodeId(node.id),
      type: this.stringToNodeType(node.type),
      position: node.position,
      data: node.data || {}
    };
  }

  /**
   * Convert domain node to GraphQL format
   */
  static domainNodeToGraphQL(node: DomainNode): Partial<DomainNodeType> {
    return {
      id: node.id,
      type: node.type,
      position: node.position,
      data: node.data
    };
  }

  /**
   * Convert GraphQL arrow to domain arrow
   */
  static graphQLArrowToDomain(arrow: DomainArrowType): DomainArrow {
    return {
      id: this.toArrowId(arrow.id),
      source: this.toHandleId(arrow.source),
      target: this.toHandleId(arrow.target),
      content_type: (arrow.content_type as unknown as ContentType) || null,
      label: arrow.label || null,
      data: arrow.data || null
    };
  }

  /**
   * Convert domain arrow to GraphQL format
   */
  static domainArrowToGraphQL(arrow: DomainArrow): Partial<DomainArrowType> {
    return {
      id: arrow.id,
      source: arrow.source,
      target: arrow.target,
      content_type: arrow.content_type as any,
      label: arrow.label,
      data: arrow.data
    };
  }

  /**
   * Convert GraphQL handle to domain handle
   */
  static graphQLHandleToDomain(handle: DomainHandleType): DomainHandle {
    return {
      id: this.toHandleId(handle.id),
      node_id: this.toNodeId(handle.node_id),
      label: handle.label as HandleLabel,
      direction: handle.direction as HandleDirection,
      data_type: handle.data_type as DataType,
      position: handle.position
    };
  }

  /**
   * Convert domain handle to GraphQL format
   */
  static domainHandleToGraphQL(handle: DomainHandle): Partial<DomainHandleType> {
    return {
      id: handle.id,
      node_id: handle.node_id,
      label: handle.label,
      direction: handle.direction,
      data_type: handle.data_type,
      position: handle.position
    };
  }

  /**
   * Convert GraphQL API key to domain
   */
  static graphQLApiKeyToDomain(apiKey: DomainApiKeyType): DomainApiKey {
    return {
      id: this.toApiKeyId(apiKey.id),
      label: apiKey.label,
      service: apiKey.service as any,
      key: ''
    };
  }

  // ===== Execution State Conversions =====

  /**
   * Convert GraphQL execution state to domain
   */
  static graphQLExecutionStateToDomain(execution: ExecutionStateType): ExecutionState {
    const nodeStates: Record<string, NodeState> = {};
    if (execution.node_states) {
      Object.entries(execution.node_states).forEach(([nodeId, state]) => {
        if (state) {
          const nodeState = state as any;
          nodeStates[nodeId] = {
            status: nodeState.status as Status,
            started_at: nodeState.started_at,
            ended_at: nodeState.ended_at,
            error: nodeState.error,
            llm_usage: nodeState.llm_usage as LLMUsage | null
          };
        }
      });
    }

    return {
      id: this.toExecutionId(execution.id),
      status: execution.status as Status,
      diagram_id: execution.diagram_id ? this.toDiagramId(execution.diagram_id) : null,
      started_at: execution.started_at || new Date().toISOString(),
      ended_at: execution.ended_at || null,
      node_states: nodeStates,
      node_outputs: execution.node_outputs || {},
      variables: execution.variables || {},
      llm_usage: execution.llm_usage as LLMUsage,
      error: execution.error || null,
      exec_counts: {},
      executed_nodes: []
    };
  }

  /**
   * Convert GraphQL execution update to domain
   */
  static graphQLExecutionUpdateToDomain(update: ExecutionUpdateType): ExecutionUpdate {
    return {
      type: (update as any).type as EventType,  // type field comes from subscription query
      execution_id: this.toExecutionId(update.execution_id),
      data: update.data,
      timestamp: update.timestamp ?? undefined
    };
  }

  // ===== Batch Conversions =====

  /**
   * Convert array of GraphQL nodes to domain nodes
   */
  static graphQLNodesToDomain(nodes: DomainNodeType[]): DomainNode[] {
    return nodes.map(node => this.graphQLNodeToDomain(node));
  }

  /**
   * Convert array of GraphQL arrows to domain arrows
   */
  static graphQLArrowsToDomain(arrows: DomainArrowType[]): DomainArrow[] {
    return arrows.map(arrow => this.graphQLArrowToDomain(arrow));
  }

  /**
   * Convert array of GraphQL handles to domain handles
   */
  static graphQLHandlesToDomain(handles: DomainHandleType[]): DomainHandle[] {
    return handles.map(handle => this.graphQLHandleToDomain(handle));
  }

  /**
   * Convert array of GraphQL persons to domain persons
   */
  static graphQLPersonsToDomain(persons: DomainPersonType[]): DomainPerson[] {
    return persons.map(person => this.convertGraphQLPerson(person));
  }

  /**
   * Convert complete GraphQL diagram to domain with Maps
   */
  static graphQLDiagramToDomainMaps(diagram: DomainDiagramType): {
    nodes: Map<NodeID, DomainNode>;
    arrows: Map<ArrowID, DomainArrow>;
    handles: Map<HandleID, DomainHandle>;
    persons: Map<PersonID, DomainPerson>;
    metadata?: DiagramMetadata;
  } {
    const domainDiagram = this.convertGraphQLDiagram(diagram);
    const maps = diagramArraysToMaps(domainDiagram);

    return {
      ...maps,
      metadata: diagram.metadata as DiagramMetadata | undefined
    };
  }
}
