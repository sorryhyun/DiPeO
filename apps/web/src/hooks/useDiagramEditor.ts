// hooks/useDiagramEditor.ts
import {useExecutionSelectors, useCanvasSelectors, useUISelectors} from "@/hooks/useStoreSelectors";
import {useCallback} from "react";

export const useDiagramEditor = () => {
  const canvas = useCanvasSelectors();
  const execution = useExecutionSelectors();
  const ui = useUISelectors();

  return {
    // Canvas
    nodes: canvas.nodes,
    arrows: canvas.arrows,
    addNode: canvas.addNode,

    // Execution
    isRunning: execution.currentRunningNode !== null,
    runningNodes: execution.runningNodes,

    // UI
    selectedId: ui.selectedNodeId || ui.selectedArrowId,

    // Combined actions
    deleteSelected: useCallback(() => {
      if (ui.selectedNodeId) {
        canvas.deleteNode(ui.selectedNodeId);
      } else if (ui.selectedArrowId) {
        canvas.deleteArrow(ui.selectedArrowId);
      }
    }, [ui.selectedNodeId, ui.selectedArrowId, canvas.deleteNode, canvas.deleteArrow]),
  };
};