// hooks/useDiagramEditor.ts
import {useExecutionSelectors, useCanvasSelectors, useSelectedElement} from "@/hooks/useStoreSelectors";
import {useCallback} from "react";

export const useDiagramEditor = () => {
  const canvas = useCanvasSelectors();
  const execution = useExecutionSelectors();
  const selection = useSelectedElement();

  return {
    // Canvas
    nodes: canvas.nodes,
    arrows: canvas.arrows,
    addNode: canvas.addNode,

    // Execution
    isRunning: execution.currentRunningNode !== null,
    runningNodes: execution.runningNodes,

    // UI
    selectedId: selection.selectedNodeId || selection.selectedArrowId,

    // Combined actions
    deleteSelected: useCallback(() => {
      if (selection.selectedNodeId) {
        canvas.deleteNode(selection.selectedNodeId);
      } else if (selection.selectedArrowId) {
        canvas.deleteArrow(selection.selectedArrowId);
      }
    }, [selection.selectedNodeId, selection.selectedArrowId, canvas.deleteNode, canvas.deleteArrow]),
  };
};