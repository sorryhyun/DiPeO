/**
 * Optimized diagram store with pre-computed lookups for performance
 */

import type { NodeID, HandleID, ArrowID, PersonID, ApiKeyID } from '@/types/branded';
import type { DomainNode, DomainHandle, DomainArrow, DomainPerson, DomainApiKey } from '@/types/domain';
import type { HandleDirection } from '@/types';

export class DiagramCanvasStore {
  // Primary storage
  private nodes: Map<NodeID, DomainNode> = new Map();
  private handles: Map<HandleID, DomainHandle> = new Map();
  private arrows: Map<ArrowID, DomainArrow> = new Map();
  private persons: Map<PersonID, DomainPerson> = new Map();
  private apiKeys: Map<ApiKeyID, DomainApiKey> = new Map();
  
  // Pre-computed lookups for O(1) access
  private handlesByNode: Map<NodeID, Set<HandleID>> = new Map();
  private handlesByDirection: Map<HandleDirection, Set<HandleID>> = new Map();
  private arrowsBySource: Map<HandleID, Set<ArrowID>> = new Map();
  private arrowsByTarget: Map<HandleID, Set<ArrowID>> = new Map();
  private nodesByType: Map<string, Set<NodeID>> = new Map();
  private apiKeysByService: Map<string, Set<ApiKeyID>> = new Map();
  
  constructor() {
    // Initialize direction maps
    this.handlesByDirection.set('input', new Set());
    this.handlesByDirection.set('output', new Set());
  }
  
  // Node operations
  addNode(node: DomainNode): void {
    this.nodes.set(node.id, node);
    
    // Update type lookup
    const typeNodes = this.nodesByType.get(node.type) || new Set();
    typeNodes.add(node.id);
    this.nodesByType.set(node.type, typeNodes);
    
    // Initialize handle set for this node
    this.handlesByNode.set(node.id, new Set());
  }
  
  removeNode(nodeId: NodeID): void {
    const node = this.nodes.get(nodeId);
    if (!node) return;
    
    // Remove from type lookup
    const typeNodes = this.nodesByType.get(node.type);
    if (typeNodes) {
      typeNodes.delete(nodeId);
      if (typeNodes.size === 0) {
        this.nodesByType.delete(node.type);
      }
    }
    
    // Remove all handles for this node
    const nodeHandles = this.handlesByNode.get(nodeId);
    if (nodeHandles) {
      for (const handleId of nodeHandles) {
        this.removeHandle(handleId);
      }
    }
    
    this.handlesByNode.delete(nodeId);
    this.nodes.delete(nodeId);
  }
  
  getNode(nodeId: NodeID): DomainNode | undefined {
    return this.nodes.get(nodeId);
  }
  
  getNodesByType(type: string): DomainNode[] {
    const nodeIds = this.nodesByType.get(type);
    if (!nodeIds) return [];
    
    return Array.from(nodeIds)
      .map(id => this.nodes.get(id))
      .filter((node): node is DomainNode => node !== undefined);
  }
  
  // Handle operations
  addHandle(handle: DomainHandle): void {
    this.handles.set(handle.id, handle);
    
    // Update node lookup
    const nodeHandles = this.handlesByNode.get(handle.nodeId) || new Set();
    nodeHandles.add(handle.id);
    this.handlesByNode.set(handle.nodeId, nodeHandles);
    
    // Update direction lookup
    const directionHandles = this.handlesByDirection.get(handle.direction) || new Set();
    directionHandles.add(handle.id);
    this.handlesByDirection.set(handle.direction, directionHandles);
  }
  
  removeHandle(handleId: HandleID): void {
    const handle = this.handles.get(handleId);
    if (!handle) return;
    
    // Remove from node lookup
    const nodeHandles = this.handlesByNode.get(handle.nodeId);
    if (nodeHandles) {
      nodeHandles.delete(handleId);
    }
    
    // Remove from direction lookup
    const directionHandles = this.handlesByDirection.get(handle.direction);
    if (directionHandles) {
      directionHandles.delete(handleId);
    }
    
    // Remove all arrows connected to this handle
    const sourceArrows = this.arrowsBySource.get(handleId);
    if (sourceArrows) {
      for (const arrowId of sourceArrows) {
        this.removeArrow(arrowId);
      }
    }
    
    const targetArrows = this.arrowsByTarget.get(handleId);
    if (targetArrows) {
      for (const arrowId of targetArrows) {
        this.removeArrow(arrowId);
      }
    }
    
    this.handles.delete(handleId);
  }
  
  getHandle(handleId: HandleID): DomainHandle | undefined {
    return this.handles.get(handleId);
  }
  
  getNodeHandles(nodeId: NodeID): DomainHandle[] {
    const handleIds = this.handlesByNode.get(nodeId) || new Set();
    return Array.from(handleIds)
      .map(id => this.handles.get(id))
      .filter((handle): handle is DomainHandle => handle !== undefined);
  }
  
  getHandlesByDirection(direction: HandleDirection): DomainHandle[] {
    const handleIds = this.handlesByDirection.get(direction) || new Set();
    return Array.from(handleIds)
      .map(id => this.handles.get(id))
      .filter((handle): handle is DomainHandle => handle !== undefined);
  }
  
  // Arrow operations
  addArrow(arrow: DomainArrow): void {
    this.arrows.set(arrow.id, arrow);
    
    // Update source lookup
    const sourceArrows = this.arrowsBySource.get(arrow.source) || new Set();
    sourceArrows.add(arrow.id);
    this.arrowsBySource.set(arrow.source, sourceArrows);
    
    // Update target lookup
    const targetArrows = this.arrowsByTarget.get(arrow.target) || new Set();
    targetArrows.add(arrow.id);
    this.arrowsByTarget.set(arrow.target, targetArrows);
  }
  
  removeArrow(arrowId: ArrowID): void {
    const arrow = this.arrows.get(arrowId);
    if (!arrow) return;
    
    // Remove from source lookup
    const sourceArrows = this.arrowsBySource.get(arrow.source);
    if (sourceArrows) {
      sourceArrows.delete(arrowId);
      if (sourceArrows.size === 0) {
        this.arrowsBySource.delete(arrow.source);
      }
    }
    
    // Remove from target lookup
    const targetArrows = this.arrowsByTarget.get(arrow.target);
    if (targetArrows) {
      targetArrows.delete(arrowId);
      if (targetArrows.size === 0) {
        this.arrowsByTarget.delete(arrow.target);
      }
    }
    
    this.arrows.delete(arrowId);
  }
  
  getArrow(arrowId: ArrowID): DomainArrow | undefined {
    return this.arrows.get(arrowId);
  }
  
  getArrowsFromHandle(handleId: HandleID): DomainArrow[] {
    const arrowIds = this.arrowsBySource.get(handleId) || new Set();
    return Array.from(arrowIds)
      .map(id => this.arrows.get(id))
      .filter((arrow): arrow is DomainArrow => arrow !== undefined);
  }
  
  getArrowsToHandle(handleId: HandleID): DomainArrow[] {
    const arrowIds = this.arrowsByTarget.get(handleId) || new Set();
    return Array.from(arrowIds)
      .map(id => this.arrows.get(id))
      .filter((arrow): arrow is DomainArrow => arrow !== undefined);
  }
  
  // Bulk operations
  getAllNodes(): DomainNode[] {
    return Array.from(this.nodes.values());
  }
  
  getAllHandles(): DomainHandle[] {
    return Array.from(this.handles.values());
  }
  
  getAllArrows(): DomainArrow[] {
    return Array.from(this.arrows.values());
  }
  
  // Person operations
  addPerson(person: DomainPerson): void {
    this.persons.set(person.id, person);
  }
  
  removePerson(personId: PersonID): void {
    this.persons.delete(personId);
  }
  
  getPerson(personId: PersonID): DomainPerson | undefined {
    return this.persons.get(personId);
  }
  
  getAllPersons(): DomainPerson[] {
    return Array.from(this.persons.values());
  }
  
  // API Key operations
  addApiKey(apiKey: DomainApiKey): void {
    this.apiKeys.set(apiKey.id, apiKey);
    
    // Update service lookup
    const serviceKeys = this.apiKeysByService.get(apiKey.service) || new Set();
    serviceKeys.add(apiKey.id);
    this.apiKeysByService.set(apiKey.service, serviceKeys);
  }
  
  removeApiKey(apiKeyId: ApiKeyID): void {
    const apiKey = this.apiKeys.get(apiKeyId);
    if (!apiKey) return;
    
    // Remove from service lookup
    const serviceKeys = this.apiKeysByService.get(apiKey.service);
    if (serviceKeys) {
      serviceKeys.delete(apiKeyId);
      if (serviceKeys.size === 0) {
        this.apiKeysByService.delete(apiKey.service);
      }
    }
    
    this.apiKeys.delete(apiKeyId);
  }
  
  getApiKey(apiKeyId: ApiKeyID): DomainApiKey | undefined {
    return this.apiKeys.get(apiKeyId);
  }
  
  getApiKeysByService(service: string): DomainApiKey[] {
    const keyIds = this.apiKeysByService.get(service) || new Set();
    return Array.from(keyIds)
      .map(id => this.apiKeys.get(id))
      .filter((key): key is DomainApiKey => key !== undefined);
  }
  
  getAllApiKeys(): DomainApiKey[] {
    return Array.from(this.apiKeys.values());
  }
  
  // Statistics
  getStats(): {
    nodeCount: number;
    handleCount: number;
    arrowCount: number;
    personCount: number;
    apiKeyCount: number;
    nodesByType: Record<string, number>;
    handlesByDirection: Record<HandleDirection, number>;
    apiKeysByService: Record<string, number>;
  } {
    const nodesByType: Record<string, number> = {};
    for (const [type, nodes] of this.nodesByType) {
      nodesByType[type] = nodes.size;
    }
    
    const handlesByDirection: Record<HandleDirection, number> = {
      input: this.handlesByDirection.get('input')?.size || 0,
      output: this.handlesByDirection.get('output')?.size || 0,
    };
    
    const apiKeysByService: Record<string, number> = {};
    for (const [service, keys] of this.apiKeysByService) {
      apiKeysByService[service] = keys.size;
    }
    
    return {
      nodeCount: this.nodes.size,
      handleCount: this.handles.size,
      arrowCount: this.arrows.size,
      personCount: this.persons.size,
      apiKeyCount: this.apiKeys.size,
      nodesByType,
      handlesByDirection,
      apiKeysByService,
    };
  }
  
  // Clear all data
  clear(): void {
    this.nodes.clear();
    this.handles.clear();
    this.arrows.clear();
    this.persons.clear();
    this.apiKeys.clear();
    this.handlesByNode.clear();
    this.handlesByDirection.clear();
    this.arrowsBySource.clear();
    this.arrowsByTarget.clear();
    this.nodesByType.clear();
    this.apiKeysByService.clear();
    
    // Re-initialize direction maps
    this.handlesByDirection.set('input', new Set());
    this.handlesByDirection.set('output', new Set());
  }
}