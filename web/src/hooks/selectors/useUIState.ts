import { useShallow } from 'zustand/react/shallow';
import { useUnifiedStore } from '@/hooks/useUnifiedStore';
import type { SelectableID, SelectableType, ActiveView, DashboardTab } from '@/stores/slices/uiSlice';

interface UIState {
  // Selection
  selectedId: SelectableID | null;
  selectedType: SelectableType | null;
  multiSelectedIds: Set<SelectableID>;
  hasSelection: boolean;
  selectionCount: number;
  
  // View state
  activeView: ActiveView;
  activeCanvas: string;
  dashboardTab: DashboardTab;
  
  // Mode state
  readOnly: boolean;
  executionReadOnly: boolean;
  isDragging: boolean;
  isConnecting: boolean;
  
  // Modal state
  activeModal: 'apikeys' | 'execution' | 'settings' | 'person' | null;
}

/**
 * Focused selector hook for UI state
 * Provides all UI-related state with computed values
 * 
 * @example
 * ```typescript
 * const { selectedId, hasSelection, readOnly } = useUIState();
 * ```
 */
export const useUIState = (): UIState => {
  return useUnifiedStore(
    useShallow(state => {
      // Determine active modal
      let activeModal: UIState['activeModal'] = null;
      if (state.showApiKeysModal) activeModal = 'apikeys';
      else if (state.showExecutionModal) activeModal = 'execution';
      else if (state.showSettingsModal) activeModal = 'settings';
      else if (state.showPersonModal) activeModal = 'person';
      
      return {
        selectedId: state.selectedId,
        selectedType: state.selectedType,
        multiSelectedIds: state.multiSelectedIds || new Set(),
        hasSelection: !!state.selectedId || (state.multiSelectedIds?.size > 0),
        selectionCount: state.multiSelectedIds?.size || (state.selectedId ? 1 : 0),
        activeView: state.activeView,
        activeCanvas: state.activeCanvas,
        dashboardTab: state.dashboardTab,
        readOnly: state.readOnly,
        executionReadOnly: state.executionReadOnly,
        isDragging: state.isDragging || false,
        isConnecting: state.isConnecting || false,
        activeModal
      };
    })
  );
};

/**
 * Hook to get selection state
 */
export const useSelection = () => {
  return useUnifiedStore(
    useShallow(state => ({
      selectedId: state.selectedId,
      selectedType: state.selectedType,
      multiSelectedIds: state.multiSelectedIds || new Set(),
      isSelected: (id: SelectableID) => state.isSelected?.(id) || 
        state.selectedId === id || 
        state.multiSelectedIds?.has(id)
    }))
  );
};

/**
 * Hook to check if a specific entity is selected
 */
export const useIsSelected = (id: SelectableID): boolean => {
  return useUnifiedStore(state => 
    state.isSelected?.(id) || 
    state.selectedId === id || 
    state.multiSelectedIds?.has(id) || 
    false
  );
};

/**
 * Hook to get read-only state
 */
export const useReadOnlyState = () => {
  return useUnifiedStore(
    useShallow(state => ({
      readOnly: state.readOnly,
      executionReadOnly: state.executionReadOnly,
      isReadOnly: state.readOnly || state.executionReadOnly
    }))
  );
};

/**
 * Hook to get modal states
 */
export const useModalStates = () => {
  return useUnifiedStore(
    useShallow(state => ({
      showApiKeysModal: state.showApiKeysModal,
      showExecutionModal: state.showExecutionModal,
      showSettingsModal: state.showSettingsModal || false,
      showPersonModal: state.showPersonModal || false,
      hasOpenModal: state.showApiKeysModal || 
        state.showExecutionModal || 
        state.showSettingsModal || 
        state.showPersonModal
    }))
  );
};