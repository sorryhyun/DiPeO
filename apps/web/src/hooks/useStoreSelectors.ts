/**
 * useStoreSelectors - UI state selector functions
 * 
 * This file contains UI state management functions for the unified store.
 * For diagram export/import operations, use the useExport hook.
 */

import { useShallow } from 'zustand/react/shallow';
import { useUnifiedStore } from '@/hooks/useUnifiedStore';
import { useCallback } from 'react';


export const useUIState = () => {
  // Use shallow equality check for object selection
  const state = useUnifiedStore(
    useShallow((state) => ({
      dashboardTab: state.dashboardTab,
      setDashboardTab: state.setDashboardTab,
      activeCanvas: state.activeCanvas,
      setActiveCanvas: state.setActiveCanvas,
      activeView: state.activeView,
      showApiKeysModal: state.showApiKeysModal,
      showExecutionModal: state.showExecutionModal,
      openApiKeysModal: state.openApiKeysModal,
      closeApiKeysModal: state.closeApiKeysModal,
      openExecutionModal: state.openExecutionModal,
      closeExecutionModal: state.closeExecutionModal,
      selectedId: state.selectedId,
    }))
  );

  // Memoize the toggle function
  const toggleCanvas = useCallback(() => {
    const canvases: ('main' | 'execution' | 'memory')[] = ['main', 'execution', 'memory'];
    const currentCanvas = state.activeCanvas || 'main';
    const currentIndex = canvases.indexOf(currentCanvas as 'main' | 'execution' | 'memory');
    const nextIndex = (currentIndex + 1) % canvases.length;
    state.setActiveCanvas(canvases[nextIndex] as 'main' | 'execution' | 'memory');
  }, [state.activeCanvas, state.setActiveCanvas]);

  return {
    ...state,
    activeCanvas: state.activeCanvas as 'main' | 'execution' | 'memory',
    toggleCanvas,
    hasSelection: state.selectedId !== null,
  };
};


