// apps/web/src/stores/typed-actions-simple.ts
/**
 * Simplified typed actions for the diagram store
 * This provides a cleaner API without complex type gymnastics
 */
import { NodeID, ArrowID, PersonID, nodeId, arrowId, personId } from '@/types/branded';
import { NodeType } from '@/types/enums';
import { Vec2 } from '@/types/primitives';
import { 
  createStartNode,
  createConditionNode,
  createPersonJobNode,
  createEndpointNode,
  createDBNode,
  createJobNode,
  createUserResponseNode,
  createNotionNode,
  createPersonBatchJobNode
} from '@/utils/factories/node-factory';
import { connect } from '@/utils/connection-helpers';
import type { DomainPerson } from '@/types/domain/person';

/**
 * Create typed actions for any store-like object
 */
export function createTypedActions(store: any) {
  const nodeFactories = {
    [NodeType.Start]: createStartNode,
    [NodeType.Condition]: createConditionNode,
    [NodeType.PersonJob]: createPersonJobNode,
    [NodeType.Endpoint]: createEndpointNode,
    [NodeType.DB]: createDBNode,
    [NodeType.Job]: createJobNode,
    [NodeType.UserResponse]: createUserResponseNode,
    [NodeType.Notion]: createNotionNode,
    [NodeType.PersonBatchJob]: createPersonBatchJobNode
  };

  return {
    /**
     * Add a start node
     */
    addStartNode(output: string, position?: Vec2, label?: string): NodeID {
      const node = createStartNode(output, position, label);
      store.addNode(node as any);
      return node.id;
    },

    /**
     * Add a condition node
     */
    addConditionNode(
      condition: string,
      type: 'simple' | 'complex' | 'detect_max_iterations' = 'simple',
      position?: Vec2,
      label?: string
    ): NodeID {
      const node = createConditionNode(condition, type, position, label);
      store.addNode(node as any);
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
        maxIteration?: number;
        contextCleaningRule?: 'no_forget' | 'on_every_turn' | 'upon_request';
        position?: Vec2;
        label?: string;
      }
    ): NodeID {
      const node = createPersonJobNode(
        personId as string,
        { firstOnlyPrompt, defaultPrompt },
        options
      );
      store.addNode(node as any);
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
      const node = createEndpointNode(action, filename, position, label);
      store.addNode(node as any);
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
      // Get nodes from store
      const nodes = store.nodes || store.getState?.()?.nodes || [];
      const fromNode = nodes.find((n: any) => n.id === fromNodeId);
      const toNode = nodes.find((n: any) => n.id === toNodeId);
      
      if (!fromNode || !toNode) {
        throw new Error(`Nodes not found: ${!fromNode ? fromNodeId : toNodeId}`);
      }

      // Add arrow to store
      const arrowId = arrowId(`ar-${Date.now()}`);
      store.addArrow({
        id: arrowId,
        source: fromNodeId as string,
        sourceHandle: fromHandle,
        target: toNodeId as string,
        targetHandle: toHandle,
        type: 'smoothstep',
        animated: options?.animated,
        label: options?.label
      });
      
      return arrowId;
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
      const arrows = store.arrows || store.getState?.()?.arrows || [];
      const connectedArrows = arrows.filter(
        (a: any) => a.source === nodeId || a.target === nodeId
      );
      
      connectedArrows.forEach((arrow: any) => {
        store.removeArrow(arrow.id);
      });
      
      // Remove node
      store.removeNode(nodeId);
    },

    /**
     * Validate diagram
     */
    validateDiagram(): { valid: boolean; errors: string[] } {
      const nodes = store.nodes || store.getState?.()?.nodes || [];
      const arrows = store.arrows || store.getState?.()?.arrows || [];
      const persons = store.persons || store.getState?.()?.persons || [];
      const errors: string[] = [];
      
      // Check for start nodes
      const startNodes = nodes.filter((n: any) => n.type === NodeType.Start);
      if (startNodes.length === 0) {
        errors.push('Diagram must have at least one start node');
      }
      
      // Check for endpoint nodes
      const endpointNodes = nodes.filter((n: any) => n.type === NodeType.Endpoint);
      if (endpointNodes.length === 0) {
        errors.push('Diagram must have at least one endpoint node');
      }
      
      // Check for orphaned nodes
      nodes.forEach((node: any) => {
        if (node.type !== NodeType.Start) {
          const hasIncoming = arrows.some((a: any) => a.target === node.id);
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