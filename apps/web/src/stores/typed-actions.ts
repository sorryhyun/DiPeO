// apps/web/src/stores/typed-actions.ts
/**
 * Simplified typed actions for the diagram store
 * This provides a cleaner API without complex type gymnastics
 */
import { NodeID, ArrowID, PersonID, personId, arrowId, handleId } from '@/types/branded';
import { Vec2 } from '@/types';
import { NodeKind } from '@/types/primitives/enums';
import { generateArrowId } from '@/types/primitives/id-generation';
import { buildNode, type NodeInfo } from '@/utils/converters/nodeBuilders';
import type { DomainPerson } from '@/types/domain/person';
import type { DomainArrow } from '@/types/domain/arrow';

/**
 * Create typed actions for any store-like object
 */
export function createTypedActions(store: any) {
  return {
    /**
     * Add a start node
     */
    addStartNode(output: string, position?: Vec2, label?: string): NodeID {
      const nodeInfo: NodeInfo = {
        name: label || 'Start',
        type: 'start',
        position: position || { x: 100, y: 100 }
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
     * Add a person (AI agent)
     */
    addPerson(
      name: string,
      config: Omit<DomainPerson, 'id' | 'name'>
    ): PersonID {
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
    updateNodeData(nodeId: NodeID, data: Record<string, any>): void {
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
      const connectedArrows = arrows.filter((arrow: DomainArrow) => {
        return nodeHandles.some((handle: any) => 
          arrow.source === handle.id || arrow.target === handle.id
        );
      });
      
      connectedArrows.forEach((arrow: DomainArrow) => {
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
      const startNodes = nodes.filter((n: any) => n.type === 'start');
      if (startNodes.length === 0) {
        errors.push('Diagram must have at least one start node');
      }
      
      // Check for endpoint nodes
      const endpointNodes = nodes.filter((n: any) => n.type === 'endpoint');
      if (endpointNodes.length === 0) {
        errors.push('Diagram must have at least one endpoint node');
      }
      
      // Check for orphaned nodes
      nodes.forEach((node: any) => {
        if (node.type !== 'start') {
          const nodeHandles = store.getNodeHandles ? store.getNodeHandles(node.id) : [];
          const inputHandles = nodeHandles.filter((h: any) => h.direction === 'input');
          
          const hasIncoming = inputHandles.some((handle: any) =>
            arrows.some((a: DomainArrow) => a.target === handle.id)
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
    }
  };
}

/**
 * Type for the created actions
 */
export type TypedDiagramActions = ReturnType<typeof createTypedActions>;