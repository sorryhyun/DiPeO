import {
  UnifiedStore,
  NodeID,
  ArrowID,
  PersonID,
  HandleID,
  NodeExecutionState,
} from '../types';
import {
  type DiagramFormat,
  DomainNode,
  DomainArrow,
  DomainPerson,
  DomainHandle,
  NodeType,
  Status,
} from '@dipeo/models';

export type Selector<T> = (state: UnifiedStore) => T;
export type ParameterizedSelector<P, T> = (params: P) => Selector<T>;

/**
 * Memoized selectors for efficient state access
 */

// ===== Basic Entity Selectors =====

export const selectNodes: Selector<Map<NodeID, DomainNode>> = (state) =>
  state.nodes;

export const selectArrows: Selector<Map<ArrowID, DomainArrow>> = (state) =>
  state.arrows;

export const selectPersons: Selector<Map<PersonID, DomainPerson>> = (state) =>
  state.persons;

export const selectHandles: Selector<Map<HandleID, DomainHandle>> = (state) =>
  state.handles;

// ===== Parameterized Entity Selectors =====

export const selectNodeById: ParameterizedSelector<NodeID | null, DomainNode | null> =
  (nodeId) => (state) => nodeId ? state.nodes.get(nodeId) || null : null;

export const selectArrowById: ParameterizedSelector<ArrowID | null, DomainArrow | null> =
  (arrowId) => (state) => arrowId ? state.arrows.get(arrowId) || null : null;

export const selectPersonById: ParameterizedSelector<PersonID | null, DomainPerson | null> =
  (personId) => (state) => personId ? state.persons.get(personId) || null : null;

// ===== Array Selectors (Computed) =====

export const selectNodesArray: Selector<DomainNode[]> = (state) =>
  state.nodesArray;

export const selectArrowsArray: Selector<DomainArrow[]> = (state) =>
  state.arrowsArray;

export const selectPersonsArray: Selector<DomainPerson[]> = (state) =>
  state.personsArray;

// ===== Filtered Selectors =====

export const selectNodesByType: ParameterizedSelector<NodeType, DomainNode[]> =
  (nodeType) => (state) =>
    Array.from(state.nodes.values()).filter(
      (node) => node.type === nodeType
    );

// Helper to extract node ID from handle ID
// Handle ID format: {nodeId}_{handleLabel}_{direction}
function extractNodeIdFromHandleId(handleId: HandleID): NodeID {
  const parts = handleId.split('_');
  // The last part is direction, second-to-last is handle label
  // Everything before that is the node ID (which might contain underscores)
  return parts.slice(0, -2).join('_') as NodeID;
}

export const selectConnectedArrows: ParameterizedSelector<NodeID, DomainArrow[]> =
  (nodeId) => (state) =>
    Array.from(state.arrows.values()).filter(
      (arrow) => {
        const sourceNodeId = extractNodeIdFromHandleId(arrow.source);
        const targetNodeId = extractNodeIdFromHandleId(arrow.target);
        return sourceNodeId === nodeId || targetNodeId === nodeId;
      }
    );

export const selectIncomingArrows: ParameterizedSelector<NodeID, DomainArrow[]> =
  (nodeId) => (state) =>
    Array.from(state.arrows.values()).filter(
      (arrow) => {
        const targetNodeId = extractNodeIdFromHandleId(arrow.target);
        return targetNodeId === nodeId;
      }
    );

export const selectOutgoingArrows: ParameterizedSelector<NodeID, DomainArrow[]> =
  (nodeId) => (state) =>
    Array.from(state.arrows.values()).filter(
      (arrow) => {
        const sourceNodeId = extractNodeIdFromHandleId(arrow.source);
        return sourceNodeId === nodeId;
      }
    );

// ===== UI Selectors =====

export const selectSelectedEntity: Selector<DomainNode | DomainArrow | DomainPerson | null> =
  (state) => {
    const id = state.selectedId;
    const type = state.selectedType;
    if (!id || !type) return null;

    switch (type) {
      case 'node':
        return state.nodes.get(id as NodeID) || null;
      case 'arrow':
        return state.arrows.get(id as ArrowID) || null;
      case 'person':
        return state.persons.get(id as PersonID) || null;
      default:
        return null;
    }
  };

export const selectIsSelected: ParameterizedSelector<string, boolean> =
  (id) => (state) => state.selectedId === id;

export const selectSelectionType: Selector<'node' | 'arrow' | 'person' | null> =
  (state) => state.selectedType;

// ===== Execution Selectors =====

export const selectIsExecuting: Selector<boolean> = (state) =>
  state.execution.isRunning;

export const selectExecutionStatus: Selector<Status | null> = (state) =>
  state.execution.isRunning ? Status.RUNNING : null;

export const selectNodeExecutionState: ParameterizedSelector<NodeID, NodeExecutionState | undefined> =
  (nodeId) => (state) => state.execution.nodeStates.get(nodeId);

export const selectExecutionProgress: Selector<number> = (state) => {
  const nodeStates = state.execution.nodeStates;
  if (!nodeStates.size) return 0;
  const completed = Array.from(nodeStates.values())
    .filter(s => s.status === Status.COMPLETED).length;
  return (completed / nodeStates.size) * 100;
};

export const selectExecutionError: Selector<string | null> = (state) => {
  const errors = Array.from(state.execution.nodeStates.values())
    .filter(s => s.error)
    .map(s => s.error);
  return errors.length > 0 ? errors.join(', ') : null;
};

// ===== Diagram Metadata Selectors =====

export const selectDiagramName: Selector<string> = (state) =>
  state.diagramName;

export const selectDiagramDescription: Selector<string> = (state) =>
  state.diagramDescription;

export const selectDiagramId: Selector<string | null> = (state) =>
  state.diagramId;

export const selectDiagramFormat: Selector<DiagramFormat | null> = (state) =>
  state.diagramFormat;

export const selectDataVersion: Selector<number> = (state) =>
  state.dataVersion;

// ===== History Selectors =====

export const selectCanUndo: Selector<boolean> = (state) =>
  state.history.undoStack.length > 0;

export const selectCanRedo: Selector<boolean> = (state) =>
  state.history.redoStack.length > 0;

export const selectHistoryLength: Selector<number> = (state) =>
  state.history.undoStack.length;

// ===== Memoization Helper =====

function createSelector<Args extends any[], R>(
  selectors: Array<Selector<any>>,
  combiner: (...args: Args) => R
): Selector<R> {
  let lastArgs: any[] | null = null;
  let lastResult: R | null = null;

  return (state: UnifiedStore) => {
    const currentArgs = selectors.map(sel => sel(state));

    if (lastArgs && currentArgs.every((arg, i) => arg === lastArgs![i])) {
      return lastResult!;
    }

    lastArgs = currentArgs;
    lastResult = combiner(...(currentArgs as Args));
    return lastResult;
  };
}

// ===== Composite Selectors =====

export const selectDiagramStatistics: Selector<{
  nodeCount: number;
  arrowCount: number;
  personCount: number;
  nodeTypes: Set<NodeType>;
}> = createSelector(
  [selectNodes, selectArrows, selectPersons],
  (nodes: Map<NodeID, DomainNode>, arrows: Map<ArrowID, DomainArrow>, persons: Map<PersonID, DomainPerson>) => ({
    nodeCount: nodes.size,
    arrowCount: arrows.size,
    personCount: persons.size,
    nodeTypes: new Set(Array.from(nodes.values()).map(n => n.type)),
  })
);

export const selectValidationState: Selector<{
  isValid: boolean;
  errors: string[];
  warnings: string[];
}> = createSelector(
  [selectNodes, selectArrows],
  (nodes: Map<NodeID, DomainNode>, arrows: Map<ArrowID, DomainArrow>) => {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Check for disconnected nodes
    const connectedNodes = new Set<NodeID>();
    arrows.forEach((arrow) => {
      const sourceNodeId = extractNodeIdFromHandleId(arrow.source);
      const targetNodeId = extractNodeIdFromHandleId(arrow.target);
      connectedNodes.add(sourceNodeId);
      connectedNodes.add(targetNodeId);
    });

    nodes.forEach((node, id) => {
      if (!connectedNodes.has(id) && node.type !== NodeType.START) {
        warnings.push(`Node ${id} is disconnected`);
      }
    });

    // Check for missing start node
    const hasStartNode = Array.from(nodes.values()).some(
      (n) => n.type === NodeType.START
    );
    if (!hasStartNode) {
      errors.push('Diagram must have a START node');
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
    };
  }
);

export const selectExecutionSummary: Selector<{
  isExecuting: boolean;
  progress: number;
  totalNodes: number;
  completedNodes: number;
  failedNodes: number;
  successRate: number;
}> = (state: UnifiedStore) => {
  const isExecuting = selectIsExecuting(state);
  const progress = selectExecutionProgress(state);
  const nodeStates = state.execution.nodeStates;

  const totalNodes = nodeStates.size;
  const completedNodes = Array.from(nodeStates.values()).filter(
    (state: NodeExecutionState) => state.status === Status.COMPLETED
  ).length;
  const failedNodes = Array.from(nodeStates.values()).filter(
    (state: NodeExecutionState) => state.status === Status.FAILED
  ).length;

  return {
    isExecuting,
    progress,
    totalNodes,
    completedNodes,
    failedNodes,
    successRate: totalNodes > 0 ? completedNodes / totalNodes : 0,
  };
};

// ===== Performance Optimized Selectors =====

// Memoized selector for expensive computations
export const selectGraphStructure: Selector<{
  adjacencyList: Map<NodeID, NodeID[]>;
  nodeCount: number;
  edgeCount: number;
  isDAG: boolean;
}> = createSelector(
  [selectNodes, selectArrows],
  (nodes: Map<NodeID, DomainNode>, arrows: Map<ArrowID, DomainArrow>) => {
    // Build adjacency list for graph traversal
    const adjacencyList = new Map<NodeID, NodeID[]>();

    nodes.forEach((_, nodeId: NodeID) => {
      adjacencyList.set(nodeId, []);
    });

    arrows.forEach((arrow: DomainArrow) => {
      const sourceNodeId = extractNodeIdFromHandleId(arrow.source);
      const targetNodeId = extractNodeIdFromHandleId(arrow.target);

      const neighbors = adjacencyList.get(sourceNodeId) || [];
      neighbors.push(targetNodeId);
      adjacencyList.set(sourceNodeId, neighbors);
    });

    return {
      adjacencyList,
      nodeCount: nodes.size,
      edgeCount: arrows.size,
      isDAG: checkIsDAG(adjacencyList),
    };
  }
);

// Helper function for DAG check
function checkIsDAG(adjacencyList: Map<NodeID, NodeID[]>): boolean {
  const visited = new Set<NodeID>();
  const recursionStack = new Set<NodeID>();

  function hasCycle(node: NodeID): boolean {
    visited.add(node);
    recursionStack.add(node);

    const neighbors = adjacencyList.get(node) || [];
    for (const neighbor of neighbors) {
      if (!visited.has(neighbor)) {
        if (hasCycle(neighbor)) return true;
      } else if (recursionStack.has(neighbor)) {
        return true;
      }
    }

    recursionStack.delete(node);
    return false;
  }

  for (const node of adjacencyList.keys()) {
    if (!visited.has(node)) {
      if (hasCycle(node)) return false;
    }
  }

  return true;
}

// Note: Selector hooks should be created in components that import both selectors and the store
// to avoid circular dependencies. Example usage:
//
// import { useUnifiedStore } from '@/infrastructure/store';
// import { selectNodeById } from '@/infrastructure/store/selectors';
//
// const useNodeById = (id: NodeID) => useUnifiedStore(selectNodeById(id));
