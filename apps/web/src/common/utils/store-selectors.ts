/**
 * Centralized store selectors
 * All store access should go through these selectors for consistency
 */

import { useDiagramStore } from '@/state/stores/diagramStore';
import { useApiKeyStore } from '@/state/stores/apiKeyStore';
import { useExecutionStore } from '@/state/stores/executionStore';
import { useConsolidatedUIStore } from '@/state/stores/consolidatedUIStore';
import { useHistoryStore } from '@/state/stores/historyStore';
import { type DiagramNode, type Arrow, type PersonDefinition } from '@/common/types';

/**
 * Diagram Store Selectors
 */

// Node selectors
export const useNodes = () => useDiagramStore(state => state.nodes);
export const useNode = (nodeId: string): DiagramNode | undefined => 
  useDiagramStore(state => state.nodes.find(n => n.id === nodeId));
export const useAddNode = () => useDiagramStore(state => state.addNode);
export const useDeleteNode = () => useDiagramStore(state => state.deleteNode);
export const useUpdateNodeData = () => useDiagramStore(state => state.updateNodeData);
export const useOnNodesChange = () => useDiagramStore(state => state.onNodesChange);

// Arrow selectors
export const useArrows = () => useDiagramStore(state => state.arrows);
export const useArrow = (arrowId: string): Arrow | undefined => 
  useDiagramStore(state => state.arrows.find(a => a.id === arrowId));
// Note: addArrow is handled through onConnect
export const useDeleteArrow = () => useDiagramStore(state => state.deleteArrow);
export const useUpdateArrowData = () => useDiagramStore(state => state.updateArrowData);
export const useOnArrowsChange = () => useDiagramStore(state => state.onArrowsChange);
export const useOnConnect = () => useDiagramStore(state => state.onConnect);

// Person selectors
export const usePersons = () => useDiagramStore(state => state.persons);
export const usePerson = (personId: string): PersonDefinition | undefined => 
  useDiagramStore(state => state.persons.find(p => p.id === personId));
export const useGetPersonById = () => useDiagramStore(state => state.getPersonById);
export const useAddPerson = () => useDiagramStore(state => state.addPerson);
export const useUpdatePerson = () => useDiagramStore(state => state.updatePerson);
export const useDeletePerson = () => useDiagramStore(state => state.deletePerson);

// Diagram state selectors
export const useIsReadOnly = () => useDiagramStore(state => state.isReadOnly);
export const useSetReadOnly = () => useDiagramStore(state => state.setReadOnly);

// Combined selectors for common patterns
export const useDiagramData = () => {
  const nodes = useNodes();
  const arrows = useArrows();
  const persons = usePersons();
  
  return { nodes, arrows, persons };
};

/**
 * API Key Store Selectors
 */
export const useApiKeys = () => useApiKeyStore(state => state.apiKeys);
export const useApiKey = (apiKeyId: string) => 
  useApiKeyStore(state => state.apiKeys.find(key => key.id === apiKeyId));
export const useSetApiKeys = () => useApiKeyStore(state => state.setApiKeys);
export const useAddApiKey = () => useApiKeyStore(state => state.addApiKey);
export const useUpdateApiKey = () => useApiKeyStore(state => state.updateApiKey);
export const useDeleteApiKey = () => useApiKeyStore(state => state.deleteApiKey);

/**
 * Execution Store Selectors
 */
export const useIsExecuting = () => useExecutionStore(state => state.isExecuting);
export const useRunContext = () => useExecutionStore(state => state.runContext);
export const useRunningNodes = () => useExecutionStore(state => state.runningNodes);
export const useCurrentRunningNode = () => useExecutionStore(state => state.currentRunningNode);
// Note: nodeResults are not stored in ExecutionStore
export const useSkippedNodes = () => useExecutionStore(state => state.skippedNodes);
export const useIsNodeSkipped = (nodeId: string) => useExecutionStore(state => Boolean(state.skippedNodes[nodeId]));

// Node-specific execution state
export const useNodeExecutionState = (nodeId: string) => {
  const runningNodes = useRunningNodes();
  const isCurrentRunning = useExecutionStore(state => state.currentRunningNode === nodeId);
  const nodeRunningState = useExecutionStore(state => state.nodeRunningStates[nodeId] || false);
  const skippedNodeInfo = useExecutionStore(state => state.skippedNodes[nodeId]);
  
  return {
    isRunning: runningNodes.includes(nodeId),
    isCurrentRunning,
    nodeRunningState,
    isSkipped: Boolean(skippedNodeInfo),
    skipReason: skippedNodeInfo?.reason
  };
};

/**
 * UI Store Selectors
 */
export const useSelectedNodeId = () => useConsolidatedUIStore(state => state.selectedNodeId);
export const useSelectedArrowId = () => useConsolidatedUIStore(state => state.selectedArrowId);
export const useSelectedPersonId = () => useConsolidatedUIStore(state => state.selectedPersonId);
export const useSetSelectedNodeId = () => useConsolidatedUIStore(state => state.setSelectedNodeId);
export const useSetSelectedArrowId = () => useConsolidatedUIStore(state => state.setSelectedArrowId);
export const useSetSelectedPersonId = () => useConsolidatedUIStore(state => state.setSelectedPersonId);
export const useClearSelection = () => useConsolidatedUIStore(state => state.clearSelection);

export const useDashboardTab = () => useConsolidatedUIStore(state => state.dashboardTab);
export const useSetDashboardTab = () => useConsolidatedUIStore(state => state.setDashboardTab);

export const useActiveCanvas = () => useConsolidatedUIStore(state => state.activeCanvas);
export const useSetActiveCanvas = () => useConsolidatedUIStore(state => state.setActiveCanvas);
export const useToggleCanvas = () => useConsolidatedUIStore(state => state.toggleCanvas);

// Combined UI selectors
export const useSelectedElement = () => {
  const selectedNodeId = useSelectedNodeId();
  const selectedArrowId = useSelectedArrowId();
  const selectedPersonId = useSelectedPersonId();
  
  return {
    selectedNodeId,
    selectedArrowId,
    selectedPersonId,
    hasSelection: Boolean(selectedNodeId || selectedArrowId || selectedPersonId),
    selectedType: selectedNodeId ? 'node' : selectedArrowId ? 'arrow' : selectedPersonId ? 'person' : null
  };
};

/**
 * History Store Selectors
 */
export const useCanUndo = () => useHistoryStore(state => state.canUndo());
export const useCanRedo = () => useHistoryStore(state => state.canRedo());
export const useUndo = () => useHistoryStore(state => state.undo);
export const useRedo = () => useHistoryStore(state => state.redo);
// Note: use saveToHistory instead of pushHistory

/**
 * Cross-store selectors
 */

// Get selected node/arrow/person data
export const useSelectedNodeData = () => {
  const selectedNodeId = useSelectedNodeId();
  return useNode(selectedNodeId || '');
};

export const useSelectedArrowData = () => {
  const selectedArrowId = useSelectedArrowId();
  return useArrow(selectedArrowId || '');
};

export const useSelectedPersonData = () => {
  const selectedPersonId = useSelectedPersonId();
  return usePerson(selectedPersonId || '');
};