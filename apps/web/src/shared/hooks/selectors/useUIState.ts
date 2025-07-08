import { useShallow } from 'zustand/react/shallow';
import { useUnifiedStore } from '@/shared/hooks/useUnifiedStore';
import type { SelectableID, SelectableType, ActiveView, DashboardTab } from '@/core/store/slices/uiSlice';

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
  
  // NOTE: isDragging, isConnecting, and modal states have been moved
  // to local component state to reduce global store complexity
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
      // NOTE: Modal state now managed locally in components
      
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
 * @deprecated Modal states have been moved to local component state
 */
export const useModalStates = () => {
  console.warn('useModalStates is deprecated. Modal states should be managed locally in components.');
  return {
    showApiKeysModal: false,
    showExecutionModal: false,
    showSettingsModal: false,
    showPersonModal: false,
    hasOpenModal: false
  };
};