/**
 * useStoreSelectors - UI state selector functions
 * 
 * This file contains UI state management functions for the unified store.
 * For diagram export/import operations, use the useExport hook.
 */

import { useUnifiedStore } from '@/hooks/useUnifiedStore';


export const useUIState = () => {
  const store = useUnifiedStore();
  
  return {
    dashboardTab: store.dashboardTab,
    setDashboardTab: store.setDashboardTab,
    activeCanvas: store.activeCanvas as 'main' | 'execution' | 'memory',
    setActiveCanvas: store.setActiveCanvas,
    toggleCanvas: () => {
      const canvases: ('main' | 'execution' | 'memory')[] = ['main', 'execution', 'memory'];
      const currentCanvas = store.activeCanvas || 'main';
      const currentIndex = canvases.indexOf(currentCanvas);
      const nextIndex = (currentIndex + 1) % canvases.length;
      store.setActiveCanvas(canvases[nextIndex] as 'main' | 'execution' | 'memory');
    },
    activeView: store.activeView,
    showApiKeysModal: store.showApiKeysModal,
    showExecutionModal: store.showExecutionModal,
    openApiKeysModal: store.openApiKeysModal,
    closeApiKeysModal: store.closeApiKeysModal,
    openExecutionModal: store.openExecutionModal,
    closeExecutionModal: store.closeExecutionModal,
    hasSelection: store.selectedId !== null,
  };
};


