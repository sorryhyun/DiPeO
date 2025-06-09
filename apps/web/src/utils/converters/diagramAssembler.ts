import { generateShortId } from '@/types/primitives/id-generation';
import { NodeKind } from '@/types/primitives/enums';
import { 
  DomainNode, 
  DomainArrow, 
  DomainPerson, 
  DomainApiKey, 
  DomainHandle,
  DomainDiagram,
  createHandleId 
} from '@/types/domain';
import { nodeId, arrowId, personId, apiKeyId, NodeID, ArrowID, PersonID, ApiKeyID } from '@/types/branded';
import { generateNodeHandles, getDefaultHandles } from '@/utils/node';
import { getNodeConfig } from '@/config/helpers';
import { buildNode as buildNodeFromInfo, NodeInfo as NodeBuilderInfo } from './nodeBuilders';

// Extended Node type with handles for converters
export interface NodeWithHandles extends DomainNode {
  handles: DomainHandle[];
  // ReactFlow properties
  draggable?: boolean;
  selectable?: boolean;
  connectable?: boolean;
}

// Converter diagram format with arrays
export interface ConverterDiagram {
  id: string;
  name: string;
  description?: string;
  nodes: NodeWithHandles[];
  arrows: DomainArrow[];
  persons: DomainPerson[];
  apiKeys: DomainApiKey[];
}

// Edge type for graph representation
export interface Edge {
  source: string;
  target: string;
  condition: string | null;
  variable: string | null;
}

// Node information for analysis
export interface NodeAnalysis {
  name: string;
  type: string;
  incoming: Edge[];
  outgoing: Edge[];
  [key: string]: any;
}

// Position calculation result
export interface NodePosition {
  x: number;
  y: number;
}

// Callbacks for format-specific logic
// Use NodeInfo from nodeBuilders
export type NodeInfo = NodeBuilderInfo;

export interface AssemblerCallbacks {
  // Parse edges from format-specific flow structure
  parseFlow: (flowData: any) => Edge[];
  
  // Infer node type from name and context
  inferNodeType: (name: string, context: any) => string;
  
  // Create node data from analysis
  createNodeInfo: (name: string, analysis: NodeAnalysis, context: any) => any;
  
  // Create arrow data from edge
  createArrowData: (edge: Edge, sourceId: string, targetId: string) => any;
  
  // Extract persons from context
  extractPersons: (nodeAnalysis: Record<string, NodeAnalysis>, context: any) => DomainPerson[];
  
  // Extract API keys from persons
  extractApiKeys: (persons: DomainPerson[]) => DomainApiKey[];
  
  // Link persons to nodes
  linkPersonsToNodes?: (nodes: NodeWithHandles[], nodeAnalysis: Record<string, NodeAnalysis>, context: any) => void;
}

export interface AssemblerOptions {
  source: any;
  callbacks: AssemblerCallbacks;
}

/**
 * Common diagram assembler that unifies conversion logic
 */
export class DiagramAssembler {
  private nodeMap: Map<string, NodeID> = new Map();
  private personMap: Map<string, PersonID> = new Map();
  
  /**
   * Assemble a diagram from source data using provided callbacks
   */
  assemble(options: AssemblerOptions): ConverterDiagram {
    const { source, callbacks } = options;
    
    try {
      // Parse flow to build graph structure
      const edges = callbacks.parseFlow(source);
      
      // Analyze nodes from edges (single pass optimization)
      const nodeAnalysis = this.analyzeNodes(edges, source, callbacks);
      
      // Calculate positions using optimized BFS
      const positions = this.calculatePositions(nodeAnalysis);
      
      // Build diagram components
      const persons = callbacks.extractPersons(nodeAnalysis, source);
      const apiKeys = callbacks.extractApiKeys(persons);
      
      // Build nodes with positions
      const nodes = this.buildNodes(nodeAnalysis, positions, source, callbacks);
      
      // Build arrows
      const arrows = this.buildArrows(edges);
      
      // Link persons to nodes if callback provided
      if (callbacks.linkPersonsToNodes) {
        callbacks.linkPersonsToNodes(nodes, nodeAnalysis, source);
      }
      
      return {
        id: `diagram-${generateShortId().slice(0, 4)}`,
        name: 'Imported Diagram',
        nodes,
        arrows,
        persons,
        apiKeys
      } as ConverterDiagram;
    } catch (error) {
      // Return minimal valid diagram on error
      console.error('Diagram assembly error:', error);
      const errorNodeId = nodeId('error-node');
      const errorNodeConfig = getNodeConfig('start' as NodeKind);
      const errorHandles = errorNodeConfig 
        ? generateNodeHandles(errorNodeId, errorNodeConfig, 'start' as NodeKind) 
        : getDefaultHandles(errorNodeId, 'start' as NodeKind);
      
      return {
        id: `diagram-${generateShortId().slice(0, 4)}`,
        name: 'Import Error',
        nodes: [{
          id: errorNodeId,
          type: 'start' as NodeKind,
          position: { x: 0, y: 0 },
          data: {
            id: errorNodeId,
            label: `Import Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
            type: 'start'
          },
          handles: errorHandles
        }],
        arrows: [],
        persons: [],
        apiKeys: []
      } as ConverterDiagram;
    }
  }
  
  /**
   * Analyze nodes from edges in a single pass
   */
  private analyzeNodes(
    edges: Edge[], 
    source: any, 
    callbacks: AssemblerCallbacks
  ): Record<string, NodeAnalysis> {
    const nodeAnalysis: Record<string, NodeAnalysis> = {};
    
    // Single pass to collect nodes and connections
    edges.forEach(edge => {
      // Process source node
      if (!nodeAnalysis[edge.source]) {
        nodeAnalysis[edge.source] = {
          name: edge.source,
          type: callbacks.inferNodeType(edge.source, source),
          incoming: [],
          outgoing: []
        };
      }
      
      // Process target node
      if (!nodeAnalysis[edge.target]) {
        nodeAnalysis[edge.target] = {
          name: edge.target,
          type: callbacks.inferNodeType(edge.target, source),
          incoming: [],
          outgoing: []
        };
      }
      
      // Track connections
      nodeAnalysis[edge.source]!.outgoing.push(edge);
      nodeAnalysis[edge.target]!.incoming.push(edge);
    });
    
    // Refine node types based on connections (integrated into first pass where possible)
    Object.entries(nodeAnalysis).forEach(([_name, analysis]) => {
      // Nodes with conditions become condition nodes
      if (analysis.outgoing.some(e => e.condition)) {
        analysis.type = 'condition';
      }
    });
    
    return nodeAnalysis;
  }
  
  /**
   * Calculate node positions using optimized BFS with proper queue
   */
  private calculatePositions(nodeAnalysis: Record<string, NodeAnalysis>): Record<string, NodePosition> {
    const positions: Record<string, NodePosition> = {};
    
    // Find start nodes
    const startNodes = Object.entries(nodeAnalysis)
      .filter(([_name, analysis]) => analysis.type === 'start' || analysis.incoming.length === 0)
      .map(([name]) => name);
    
    if (startNodes.length === 0 && Object.keys(nodeAnalysis).length > 0) {
      const firstNode = Object.keys(nodeAnalysis)[0];
      if (firstNode) startNodes.push(firstNode);
    }
    
    // Optimized BFS with array-based queue
    const visited = new Set<string>();
    const queue: Array<{ node: string; level: number; index: number }> = 
      startNodes.map((node, i) => ({ node, level: 0, index: i }));
    const levelCounts: Record<number, number> = {};
    
    // Use index-based queue to avoid array shifting
    let queueStart = 0;
    
    while (queueStart < queue.length) {
      const current = queue[queueStart++];
      if (!current) continue;
      const { node, level, index } = current;
      if (visited.has(node)) continue;
      
      visited.add(node);
      
      // Position calculation
      positions[node] = {
        x: level * 250,
        y: index * 150
      };
      
      // Queue children
      const analysis = nodeAnalysis[node];
      if (analysis) {
        const children = analysis.outgoing.map(e => e.target);
        children.forEach(child => {
          if (!visited.has(child)) {
            const nextLevel = level + 1;
            levelCounts[nextLevel] = (levelCounts[nextLevel] || 0) + 1;
            queue.push({
              node: child,
              level: nextLevel,
              index: levelCounts[nextLevel] - 1
            });
          }
        });
      }
    }
    
    return positions;
  }
  
  /**
   * Build nodes using callback-provided node info
   */
  private buildNodes(
    nodeAnalysis: Record<string, NodeAnalysis>,
    positions: Record<string, NodePosition>,
    source: any,
    callbacks: AssemblerCallbacks
  ): NodeWithHandles[] {
    const nodes: NodeWithHandles[] = [];
    
    Object.entries(nodeAnalysis).forEach(([name, analysis]) => {
      const nodeInfo = callbacks.createNodeInfo(name, analysis, source);
      const nodeIdValue = nodeId(nodeInfo.id);
      
      // Store mapping
      this.nodeMap.set(name, nodeIdValue);
      
      // Generate handles for the node
      const nodeConfig = getNodeConfig(nodeInfo.type);
      const handles = nodeConfig 
        ? generateNodeHandles(nodeIdValue, nodeConfig, nodeInfo.type) 
        : getDefaultHandles(nodeIdValue, nodeInfo.type);
      
      // Create node
      const node: NodeWithHandles = {
        id: nodeIdValue,
        type: nodeInfo.type,
        position: positions[name] || { x: 0, y: 0 },
        data: nodeInfo.data,
        handles,
        // Add ReactFlow required properties
        draggable: true,
        selectable: true,
        connectable: true
      };
      
      nodes.push(node);
    });
    
    return nodes;
  }
  
  /**
   * Build arrows from edges
   */
  private buildArrows(edges: Edge[]): DomainArrow[] {
    const arrows: DomainArrow[] = [];
    
    edges.forEach(edge => {
      const sourceId = this.nodeMap.get(edge.source);
      const targetId = this.nodeMap.get(edge.target);
      
      if (!sourceId || !targetId) return;
      
      const id = arrowId(`arrow-${generateShortId().slice(0, 4)}`);
      
      // Determine handle names based on edge properties
      const sourceHandleName = edge.condition ? 
        (edge.condition.includes('not') || edge.condition.startsWith('!') ? 'false' : 'true')
        : 'output';
      const targetHandleName = 'input';
      
      // Create handle IDs
      const sourceHandleId = createHandleId(sourceId, sourceHandleName);
      const targetHandleId = createHandleId(targetId, targetHandleName);
      
      const arrow: DomainArrow = {
        id,
        source: sourceHandleId,
        target: targetHandleId,
        data: {
          label: edge.variable || 'flow',
          contentType: edge.variable ? 'variable_in_object' : 'raw_text',
          branch: edge.condition ? 
            (edge.condition.includes('not') || edge.condition.startsWith('!') ? 'false' : 'true') 
            : undefined
        }
      };
      
      arrows.push(arrow);
    });
    
    return arrows;
  }
  
  /**
   * Get node map for external use
   */
  getNodeMap(): Map<string, NodeID> {
    return this.nodeMap;
  }
  
  /**
   * Get person map for external use
   */
  getPersonMap(): Map<string, PersonID> {
    return this.personMap;
  }
  
  /**
   * Set person map for external use
   */
  setPersonMap(map: Map<string, PersonID>): void {
    this.personMap = map;
  }
  
  /**
   * Build a node using the unified builder system
   */
  static buildNode(info: NodeInfo): NodeWithHandles {
    // Use the imported buildNode function and ensure it has handles
    const node = buildNodeFromInfo(info) as NodeWithHandles;
    // The node from nodeBuilders already has handles, draggable, selectable, connectable
    return node;
  }
  
  /**
   * Build multiple nodes from a record of node infos
   */
  static buildNodes(nodeInfos: Record<string, NodeInfo>): NodeWithHandles[] {
    return Object.values(nodeInfos).map(info => DiagramAssembler.buildNode(info));
  }
  
}