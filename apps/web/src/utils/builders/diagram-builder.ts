// apps/web/src/utils/builders/diagram-builder.ts
import { NodeID, HandleID, ArrowID, PersonID, nodeId, personId } from '@/types/branded';
import { NodeType } from '@/types/enums';
import { DiagramNode } from '@/types/nodes';
import { Vec2 } from '@/types/primitives';
import { DomainPerson } from '@/types/domain/person';
import { DomainDiagram } from '@/types/domain/diagram';
import { DomainHandle } from '@/types/domain/handle';
import { DomainArrow } from '@/types/domain/arrow';
import { createNode } from '@/utils/factories/node-factory';
import { connect, TypedArrow } from '@/utils/connection-helpers';
import { getAllHandles } from '@/utils/handle-utils';
import { OutputHandleNamesOf, InputHandleNamesOf } from '@/types/node-specs';
import { generateShortId } from '@/utils/id';

/**
 * Builder for constructing type-safe diagrams
 */
export class DiagramBuilder {
  private nodes: Map<NodeID, DiagramNode> = new Map();
  private arrows: Map<ArrowID, DomainArrow> = new Map();
  private handles: Map<HandleID, DomainHandle> = new Map();
  private persons: Map<PersonID, DomainPerson> = new Map();
  private metadata: DomainDiagram['metadata'];
  
  constructor(metadata?: Partial<DomainDiagram['metadata']>) {
    this.metadata = {
      version: metadata?.version || '2.0',
      created: metadata?.created || new Date().toISOString(),
      modified: new Date().toISOString(),
      name: metadata?.name,
      description: metadata?.description,
      tags: metadata?.tags || []
    };
  }
  
  /**
   * Add a node to the diagram
   */
  addNode<K extends NodeType>(
    type: K,
    data: Omit<Extract<DiagramNode, { type: K }>['data'], 'id' | 'type' | 'label'> & { label?: string },
    position?: Vec2
  ): Extract<DiagramNode, { type: K }> {
    const node = createNode(type, data, position);
    this.nodes.set(node.id, node);
    
    // Add handles to handle collection
    for (const handle of getAllHandles(node)) {
      const domainHandle: DomainHandle = {
        id: handle.id,
        nodeId: node.id,
        name: handle.name,
        direction: handle.kind as 'input' | 'output',
        dataType: handle.dataType,
        position: handle.position,
        label: handle.label,
        maxConnections: handle.maxConnections
      };
      this.handles.set(handle.id, domainHandle);
    }
    
    return node;
  }
  
  /**
   * Add an existing node to the diagram
   */
  addExistingNode(node: DiagramNode): this {
    this.nodes.set(node.id, node);
    
    // Add handles
    for (const handle of getAllHandles(node)) {
      const domainHandle: DomainHandle = {
        id: handle.id,
        nodeId: node.id,
        name: handle.name,
        direction: handle.kind as 'input' | 'output',
        dataType: handle.dataType,
        position: handle.position,
        label: handle.label,
        maxConnections: handle.maxConnections
      };
      this.handles.set(handle.id, domainHandle);
    }
    
    return this;
  }
  
  /**
   * Connect two nodes
   */
  connect<
    FromNode extends DiagramNode,
    FromHandle extends OutputHandleNamesOf<FromNode['type']>,
    ToNode extends DiagramNode,
    ToHandle extends InputHandleNamesOf<ToNode['type']>
  >(
    fromNodeId: NodeID,
    fromHandle: FromHandle,
    toNodeId: NodeID,
    toHandle: ToHandle,
    options?: {
      type?: TypedArrow['type'];
      animated?: boolean;
      label?: string;
    }
  ): TypedArrow {
    const fromNode = this.nodes.get(fromNodeId);
    const toNode = this.nodes.get(toNodeId);
    
    if (!fromNode || !toNode) {
      throw new Error(`Nodes not found: ${!fromNode ? fromNodeId : toNodeId}`);
    }
    
    const arrow = connect(
      { node: fromNode as FromNode, handle: fromHandle },
      { node: toNode as ToNode, handle: toHandle },
      options
    );
    
    const domainArrow: DomainArrow = {
      id: arrow.id,
      source: arrow.source,
      target: arrow.target,
      data: {
        type: arrow.type,
        animated: arrow.animated,
        label: arrow.label
      }
    };
    
    this.arrows.set(arrow.id, domainArrow);
    return arrow;
  }
  
  /**
   * Add a person (AI agent)
   */
  addPerson(
    name: string,
    config: Omit<DomainPerson, 'id' | 'name'>
  ): PersonID {
    const id = personId(`person-${generateShortId()}`);
    const person: DomainPerson = {
      id,
      name,
      ...config
    };
    this.persons.set(id, person);
    return id;
  }
  
  /**
   * Update an existing person
   */
  updatePerson(id: PersonID, updates: Partial<Omit<DomainPerson, 'id'>>): this {
    const person = this.persons.get(id);
    if (!person) {
      throw new Error(`Person not found: ${id}`);
    }
    
    this.persons.set(id, { ...person, ...updates });
    return this;
  }
  
  /**
   * Remove a node and its connections
   */
  removeNode(nodeId: NodeID): this {
    const node = this.nodes.get(nodeId);
    if (!node) return this;
    
    // Remove handles
    for (const handle of getAllHandles(node)) {
      this.handles.delete(handle.id);
    }
    
    // Remove connected arrows
    for (const [arrowId, arrow] of this.arrows) {
      const sourceNodeId = this.handles.get(arrow.source)?.nodeId;
      const targetNodeId = this.handles.get(arrow.target)?.nodeId;
      
      if (sourceNodeId === nodeId || targetNodeId === nodeId) {
        this.arrows.delete(arrowId);
      }
    }
    
    // Remove node
    this.nodes.delete(nodeId);
    return this;
  }
  
  /**
   * Remove an arrow
   */
  removeArrow(arrowId: ArrowID): this {
    this.arrows.delete(arrowId);
    return this;
  }
  
  /**
   * Get a node by ID
   */
  getNode(nodeId: NodeID): DiagramNode | undefined {
    return this.nodes.get(nodeId);
  }
  
  /**
   * Get all nodes of a specific type
   */
  getNodesByType<K extends NodeType>(type: K): Extract<DiagramNode, { type: K }>[] {
    const result: Extract<DiagramNode, { type: K }>[] = [];
    for (const node of this.nodes.values()) {
      if (node.type === type) {
        result.push(node as Extract<DiagramNode, { type: K }>);
      }
    }
    return result;
  }
  
  /**
   * Get all arrows connected to a node
   */
  getNodeConnections(nodeId: NodeID): {
    incoming: DomainArrow[];
    outgoing: DomainArrow[];
  } {
    const incoming: DomainArrow[] = [];
    const outgoing: DomainArrow[] = [];
    
    for (const arrow of this.arrows.values()) {
      const sourceNodeId = this.handles.get(arrow.source)?.nodeId;
      const targetNodeId = this.handles.get(arrow.target)?.nodeId;
      
      if (sourceNodeId === nodeId) {
        outgoing.push(arrow);
      }
      if (targetNodeId === nodeId) {
        incoming.push(arrow);
      }
    }
    
    return { incoming, outgoing };
  }
  
  /**
   * Update metadata
   */
  setMetadata(metadata: Partial<DomainDiagram['metadata']>): this {
    this.metadata = {
      ...this.metadata,
      ...metadata,
      modified: new Date().toISOString()
    };
    return this;
  }
  
  /**
   * Validate the diagram
   */
  validate(): { valid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    // Check for start nodes
    const startNodes = this.getNodesByType(NodeType.Start);
    if (startNodes.length === 0) {
      errors.push('Diagram must have at least one start node');
    }
    
    // Check for endpoint nodes
    const endpointNodes = this.getNodesByType(NodeType.Endpoint);
    if (endpointNodes.length === 0) {
      errors.push('Diagram must have at least one endpoint node');
    }
    
    // Check for orphaned nodes (except start nodes)
    for (const node of this.nodes.values()) {
      if (node.type !== NodeType.Start) {
        const connections = this.getNodeConnections(node.id);
        if (connections.incoming.length === 0) {
          errors.push(`Node ${node.id} has no incoming connections`);
        }
      }
    }
    
    // Check for person references
    const personJobNodes = [
      ...this.getNodesByType(NodeType.PersonJob),
      ...this.getNodesByType(NodeType.PersonBatchJob)
    ];
    
    for (const node of personJobNodes) {
      if (!this.persons.has(node.data.personId)) {
        errors.push(`Node ${node.id} references non-existent person: ${node.data.personId}`);
      }
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
  
  /**
   * Build the final diagram
   */
  build(): DomainDiagram {
    // Convert maps to objects
    const nodes: Record<NodeID, DiagramNode> = {};
    for (const [id, node] of this.nodes) {
      nodes[id] = node;
    }
    
    const arrows: Record<ArrowID, DomainArrow> = {};
    for (const [id, arrow] of this.arrows) {
      arrows[id] = arrow;
    }
    
    const handles: Record<HandleID, DomainHandle> = {};
    for (const [id, handle] of this.handles) {
      handles[id] = handle;
    }
    
    const persons: Record<PersonID, DomainPerson> = {};
    for (const [id, person] of this.persons) {
      persons[id] = person;
    }
    
    return {
      nodes,
      arrows,
      handles,
      persons,
      metadata: {
        ...this.metadata,
        modified: new Date().toISOString()
      }
    };
  }
  
  /**
   * Create a builder from an existing diagram
   */
  static fromDiagram(diagram: DomainDiagram): DiagramBuilder {
    const builder = new DiagramBuilder(diagram.metadata);
    
    // Add persons
    for (const person of Object.values(diagram.persons)) {
      builder.persons.set(person.id, person);
    }
    
    // Add nodes
    for (const node of Object.values(diagram.nodes)) {
      builder.nodes.set(node.id, node as DiagramNode);
    }
    
    // Add handles
    for (const handle of Object.values(diagram.handles)) {
      builder.handles.set(handle.id, handle);
    }
    
    // Add arrows
    for (const arrow of Object.values(diagram.arrows)) {
      builder.arrows.set(arrow.id, arrow);
    }
    
    return builder;
  }
}