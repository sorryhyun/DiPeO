// apps/web/src/stores/typed-actions.ts
/**
 * Simplified typed actions for the diagram store
 * This provides a cleaner API without complex type gymnastics
 */
import { useMemo } from 'react';
import { NodeID, ArrowID, PersonID, HandleID, personId, arrowId, handleId } from '@/types/branded';
import { Vec2 } from '@/types';
import { generateArrowId } from '@/types/primitives/id-generation';
import { buildNode, type NodeInfo } from '@/utils/converters/nodeBuilders';
import type { DomainPerson } from '@/types/domain/person';
import type { DomainArrow } from '@/types/domain/arrow';
import type { DomainNode } from '@/types/domain/node';
import type { DomainHandle } from '@/types/domain/handle';

/**
 * Interface for a diagram store with required operations
 */
export interface DiagramStore {
  // Collections
  nodes: Map<NodeID, DomainNode>;
  arrows: Map<ArrowID, DomainArrow>;
  handles: Map<HandleID, DomainHandle>;
  persons: Map<PersonID, DomainPerson>;
  
  // Node operations
  addNode: (node: DomainNode) => void;
  updateNode: (id: NodeID, updates: Partial<DomainNode>) => void;
  removeNode: (id: NodeID) => void;
  
  // Arrow operations
  addArrow: (arrow: DomainArrow) => void;
  removeArrow: (id: ArrowID) => void;
  
  // Person operations
  createPerson?: (config: Omit<DomainPerson, 'id'>) => DomainPerson;
  
  // Helper methods
  getAllNodes?: () => DomainNode[];
  getAllArrows?: () => DomainArrow[];
  getNodeHandles?: (nodeId: NodeID) => DomainHandle[];
  
  // Transaction support
  transaction?: <T>(fn: () => T) => T;
}

/**
 * Configuration for workflow creation
 */
export interface WorkflowConfig {
  input: string;
  personId: PersonID;
  firstPrompt: string;
  defaultPrompt: string;
  position?: Vec2;
}

/**
 * Result of workflow creation
 */
export interface WorkflowResult {
  startId: NodeID;
  processId: NodeID;
  endId: NodeID;
}

/**
 * Node definition for bulk operations
 */
export interface NodeDefinition {
  type: 'start' | 'condition' | 'person_job' | 'endpoint' | 'db' | 'job' | 'user_response' | 'notion' | 'person_batch_job';
  position?: Vec2;
  label?: string;
  // Type-specific properties
  output?: string; // for start
  condition?: string; // for condition
  conditionType?: 'expression' | 'detect_max_iterations'; // for condition
  personId?: PersonID; // for person_job, person_batch_job
  firstPrompt?: string; // for person_job, person_batch_job
  defaultPrompt?: string; // for person_job, person_batch_job
  action?: 'save' | 'output'; // for endpoint
  filename?: string; // for endpoint
  subType?: 'fixed_prompt' | 'file'; // for db
  sourceDetails?: string; // for db
  code?: string; // for job
  language?: 'python' | 'javascript' | 'bash'; // for job
  promptMessage?: string; // for user_response
  timeoutSeconds?: number; // for user_response
  operation?: 'read' | 'write'; // for notion
  pageId?: string; // for notion
}

/**
 * Create typed actions for any store-like object
 */
export function createTypedActions(store: DiagramStore) {
  return {
    /**
     * Add a start node
     */
    addStartNode(output: string, position?: Vec2, label?: string): NodeID {
      // Validate inputs
      if (!output || output.trim() === '') {
        throw new Error('Start node output cannot be empty');
      }
      
      const nodeInfo: NodeInfo = {
        name: label || 'Start',
        type: 'start',
        position: position || { x: 100, y: 100 },
        data: output
      };
      const node = buildNode(nodeInfo);
      store.addNode(node);
      return node.id;
    },

    /**
     * Add a condition node
     */
    addConditionNode(
      condition: string,
      conditionType: 'expression' | 'detect_max_iterations' = 'expression',
      position?: Vec2,
      label?: string
    ): NodeID {
      const nodeInfo: NodeInfo = {
        name: label || 'Condition',
        type: 'condition',
        position: position || { x: 100, y: 100 },
        condition,
        conditionType
      };
      const node = buildNode(nodeInfo);
      store.addNode(node);
      return node.id;
    },

    /**
     * Add a person job node
     */
    addPersonJobNode(
      personId: PersonID,
      firstOnlyPrompt: string,
      defaultPrompt: string,
      options?: {
        maxIterations?: number;
        contextCleaningRule?: 'no_forget' | 'on_every_turn' | 'upon_request';
        position?: Vec2;
        label?: string;
      }
    ): NodeID {
      // Validate inputs
      if (!personId) {
        throw new Error('Person ID is required for person job node');
      }
      if (!firstOnlyPrompt?.trim()) {
        throw new Error('First prompt is required for person job node');
      }
      if (!defaultPrompt?.trim()) {
        throw new Error('Default prompt is required for person job node');
      }
      
      // Check if person exists
      if (store.persons && !store.persons.has(personId)) {
        throw new Error(`Person with ID ${personId} not found`);
      }
      
      const nodeInfo: NodeInfo = {
        name: options?.label || 'Person Job',
        type: 'person_job',
        position: options?.position || { x: 100, y: 100 },
        personId: personId as string,
        firstPrompt: firstOnlyPrompt,
        prompt: defaultPrompt,
        maxIterations: options?.maxIterations,
        contextCleaningRule: options?.contextCleaningRule
      };
      const node = buildNode(nodeInfo);
      store.addNode(node);
      return node.id;
    },

    /**
     * Add an endpoint node
     */
    addEndpointNode(
      action: 'save' | 'output',
      filename?: string,
      position?: Vec2,
      label?: string
    ): NodeID {
      const nodeInfo: NodeInfo = {
        name: label || 'Endpoint',
        type: 'endpoint',
        position: position || { x: 100, y: 100 },
        filePath: action === 'save' ? filename : undefined,
        saveToFile: action === 'save'
      };
      const node = buildNode(nodeInfo);
      store.addNode(node);
      return node.id;
    },

    /**
     * Add a DB node
     */
    addDBNode(
      subType: 'fixed_prompt' | 'file',
      sourceDetails: string,
      position?: Vec2,
      label?: string
    ): NodeID {
      const nodeInfo: NodeInfo = {
        name: label || 'Database',
        type: 'db',
        position: position || { x: 100, y: 100 },
        subType,
        sourceDetails
      };
      const node = buildNode(nodeInfo);
      store.addNode(node);
      return node.id;
    },

    /**
     * Add a job node
     */
    addJobNode(
      code: string,
      language: 'python' | 'javascript' | 'bash' = 'python',
      position?: Vec2,
      label?: string
    ): NodeID {
      const nodeInfo: NodeInfo = {
        name: label || 'Job',
        type: 'job',
        position: position || { x: 100, y: 100 },
        code,
        subType: 'code',
        language
      };
      const node = buildNode(nodeInfo);
      store.addNode(node);
      return node.id;
    },

    /**
     * Add a user response node
     */
    addUserResponseNode(
      promptMessage: string,
      timeoutSeconds: number = 30,
      position?: Vec2,
      label?: string
    ): NodeID {
      const nodeInfo: NodeInfo = {
        name: label || 'User Response',
        type: 'user_response',
        position: position || { x: 100, y: 100 },
        promptMessage,
        timeoutSeconds
      };
      const node = buildNode(nodeInfo);
      store.addNode(node);
      return node.id;
    },

    /**
     * Add a notion node
     */
    addNotionNode(
      operation: 'read' | 'write',
      pageId: string,
      position?: Vec2,
      label?: string
    ): NodeID {
      const nodeInfo: NodeInfo = {
        name: label || 'Notion',
        type: 'notion',
        position: position || { x: 100, y: 100 },
        subType: operation,
        pageId
      };
      const node = buildNode(nodeInfo);
      store.addNode(node);
      return node.id;
    },

    /**
     * Add a person batch job node
     */
    addPersonBatchJobNode(
      personId: PersonID,
      firstOnlyPrompt: string,
      defaultPrompt: string,
      options?: {
        position?: Vec2;
        label?: string;
        contextCleaningRule?: 'no_forget' | 'on_every_turn' | 'upon_request';
      }
    ): NodeID {
      const nodeInfo: NodeInfo = {
        name: options?.label || 'Person Batch Job',
        type: 'person_batch_job',
        position: options?.position || { x: 100, y: 100 },
        personId: personId as string,
        firstPrompt: firstOnlyPrompt,
        prompt: defaultPrompt,
        contextCleaningRule: options?.contextCleaningRule
      };
      const node = buildNode(nodeInfo);
      store.addNode(node);
      return node.id;
    },

    /**
     * Add a person (configured LLM instance)
     */
    addPerson(
      name: string,
      config: Omit<DomainPerson, 'id' | 'name'>
    ): PersonID {
      if (!store.createPerson) {
        throw new Error('Store does not support creating persons');
      }
      
      const person = store.createPerson({
        name,
        ...config
      });
      return personId(person.id);
    },

    /**
     * Connect two nodes
     */
    connectNodes(
      fromNodeId: NodeID,
      fromHandle: string,
      toNodeId: NodeID,
      toHandle: string,
      options?: {
        animated?: boolean;
        label?: string;
      }
    ): ArrowID {
      // Create handle IDs
      const sourceHandleId = handleId(fromNodeId, fromHandle);
      const targetHandleId = handleId(toNodeId, toHandle);

      // Create arrow
      const newArrowId = arrowId(generateArrowId());
      const arrow: DomainArrow = {
        id: newArrowId,
        source: sourceHandleId,
        target: targetHandleId,
        data: options?.label ? { label: options.label } : {}
      };
      
      store.addArrow(arrow);
      return newArrowId;
    },

    /**
     * Update node data
     */
    updateNodeData(nodeId: NodeID, data: Record<string, unknown>): void {
      store.updateNode(nodeId, { data });
    },

    /**
     * Remove a node
     */
    removeNode(nodeId: NodeID): void {
      // Remove connected arrows
      const arrows = store.getAllArrows ? store.getAllArrows() : [];
      const nodeHandles = store.getNodeHandles ? store.getNodeHandles(nodeId) : [];
      
      // Filter arrows connected to any of this node's handles
      const connectedArrows = arrows.filter((arrow) => {
        return nodeHandles.some((handle) => 
          arrow.source === handle.id || arrow.target === handle.id
        );
      });
      
      connectedArrows.forEach((arrow) => {
        store.removeArrow(arrow.id);
      });
      
      // Remove node
      store.removeNode(nodeId);
    },

    /**
     * Validate diagram
     */
    validateDiagram(): { valid: boolean; errors: string[] } {
      const nodes = store.getAllNodes ? store.getAllNodes() : [];
      const arrows = store.getAllArrows ? store.getAllArrows() : [];
      const errors: string[] = [];
      
      // Check for start nodes
      const startNodes = nodes.filter((n) => n.type === 'start');
      if (startNodes.length === 0) {
        errors.push('Diagram must have at least one start node');
      }
      
      // Check for endpoint nodes
      const endpointNodes = nodes.filter((n) => n.type === 'endpoint');
      if (endpointNodes.length === 0) {
        errors.push('Diagram must have at least one endpoint node');
      }
      
      // Check for orphaned nodes
      nodes.forEach((node) => {
        if (node.type !== 'start') {
          const nodeHandles = store.getNodeHandles ? store.getNodeHandles(node.id) : [];
          const inputHandles = nodeHandles.filter((h) => h.direction === 'input');
          
          const hasIncoming = inputHandles.some((handle) =>
            arrows.some((a) => a.target === handle.id)
          );
          
          if (!hasIncoming) {
            errors.push(`Node "${node.data?.label || node.id}" has no incoming connections`);
          }
        }
      });
      
      return {
        valid: errors.length === 0,
        errors
      };
    },
    
    /**
     * Add a complete workflow in one transaction
     */
    addWorkflow(config: WorkflowConfig): WorkflowResult {
      const doWork = () => {
        const startId = this.addStartNode(config.input, config.position);
        const processId = this.addPersonJobNode(
          config.personId,
          config.firstPrompt,
          config.defaultPrompt,
          { position: config.position ? { x: config.position.x + 200, y: config.position.y } : undefined }
        );
        const endId = this.addEndpointNode(
          'output', 
          undefined,
          config.position ? { x: config.position.x + 400, y: config.position.y } : undefined
        );
        
        this.connectNodes(startId, 'default', processId, 'first');
        this.connectNodes(processId, 'default', endId, 'default');
        
        return { startId, processId, endId };
      };
      
      // Use transaction if available, otherwise execute directly
      if (store.transaction) {
        return store.transaction(doWork);
      } else {
        return doWork();
      }
    },
    
    /**
     * Add multiple nodes in one transaction
     */
    addMultipleNodes(nodes: NodeDefinition[]): NodeID[] {
      const doWork = () => {
        return nodes.map(nodeDef => {
          switch (nodeDef.type) {
            case 'start':
              if (!nodeDef.output) throw new Error('Start node requires output');
              return this.addStartNode(nodeDef.output, nodeDef.position, nodeDef.label);
              
            case 'condition':
              if (!nodeDef.condition) throw new Error('Condition node requires condition');
              return this.addConditionNode(
                nodeDef.condition,
                nodeDef.conditionType || 'expression',
                nodeDef.position,
                nodeDef.label
              );
              
            case 'person_job':
              if (!nodeDef.personId || !nodeDef.firstPrompt || !nodeDef.defaultPrompt) {
                throw new Error('Person job node requires personId, firstPrompt, and defaultPrompt');
              }
              return this.addPersonJobNode(
                nodeDef.personId,
                nodeDef.firstPrompt,
                nodeDef.defaultPrompt,
                { position: nodeDef.position, label: nodeDef.label }
              );
              
            case 'endpoint':
              return this.addEndpointNode(
                nodeDef.action || 'output',
                nodeDef.filename,
                nodeDef.position,
                nodeDef.label
              );
              
            case 'db':
              if (!nodeDef.subType || !nodeDef.sourceDetails) {
                throw new Error('DB node requires subType and sourceDetails');
              }
              return this.addDBNode(
                nodeDef.subType,
                nodeDef.sourceDetails,
                nodeDef.position,
                nodeDef.label
              );
              
            case 'job':
              if (!nodeDef.code) throw new Error('Job node requires code');
              return this.addJobNode(
                nodeDef.code,
                nodeDef.language || 'python',
                nodeDef.position,
                nodeDef.label
              );
              
            case 'user_response':
              if (!nodeDef.promptMessage) throw new Error('User response node requires promptMessage');
              return this.addUserResponseNode(
                nodeDef.promptMessage,
                nodeDef.timeoutSeconds,
                nodeDef.position,
                nodeDef.label
              );
              
            case 'notion':
              if (!nodeDef.operation || !nodeDef.pageId) {
                throw new Error('Notion node requires operation and pageId');
              }
              return this.addNotionNode(
                nodeDef.operation,
                nodeDef.pageId,
                nodeDef.position,
                nodeDef.label
              );
              
            case 'person_batch_job':
              if (!nodeDef.personId || !nodeDef.firstPrompt || !nodeDef.defaultPrompt) {
                throw new Error('Person batch job node requires personId, firstPrompt, and defaultPrompt');
              }
              return this.addPersonBatchJobNode(
                nodeDef.personId,
                nodeDef.firstPrompt,
                nodeDef.defaultPrompt,
                { position: nodeDef.position, label: nodeDef.label }
              );
              
            default:
              throw new Error(`Unknown node type: ${nodeDef.type}`);
          }
        });
      };
      
      // Use transaction if available, otherwise execute directly
      if (store.transaction) {
        return store.transaction(doWork);
      } else {
        return doWork();
      }
    }
  };
}

/**
 * Type for the created actions
 */
export type TypedDiagramActions = ReturnType<typeof createTypedActions>;

/**
 * React hook for typed diagram actions
 * Provides memoized actions and integrates with your store
 */
export function useTypedDiagramActions(store: DiagramStore): TypedDiagramActions {
  return useMemo(() => createTypedActions(store), [store]);
}