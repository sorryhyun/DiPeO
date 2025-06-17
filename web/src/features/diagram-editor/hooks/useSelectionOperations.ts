/**
 * useSelectionOperations - Focused hook for selection management
 */

import { useCallback } from 'react';
import { useUnifiedStore } from '@/shared/hooks/useUnifiedStore';
import { NodeID, ArrowID, PersonID } from '@/core/types';
import type { SelectableType, SelectableID } from '@/core/store/slices/uiSlice';

export interface UseSelectionOperationsReturn {
  // Current selection state
  selectedId: string | null;
  selectedType: SelectableType | null;
  selectedNodeId: NodeID | null;
  selectedArrowId: ArrowID | null;
  selectedPersonId: PersonID | null;
  hasSelection: boolean;
  
  // Selection operations
  selectNode: (id: NodeID) => void;
  selectArrow: (id: ArrowID) => void;
  selectPerson: (id: PersonID) => void;
  clearSelection: () => void;
  
  // Multi-selection (future enhancement)
  isSelected: (id: string) => boolean;
  toggleSelection: (id: string, type: SelectableType) => void;
  
  // Selection queries
  getSelectedNode: () => DomainNode | null;
  getSelectedArrow: () => DomainArrow | null;
  getSelectedPerson: () => DomainPerson | null;
}

import type { DomainNode, DomainArrow, DomainPerson } from '@/core/types';

export function useSelectionOperations(): UseSelectionOperationsReturn {
  const store = useUnifiedStore;
  const selectedId = useUnifiedStore(state => state.selectedId);
  const selectedType = useUnifiedStore(state => state.selectedType);
  
  // Derive specific selected IDs
  const selectedNodeId = selectedType === 'node' ? selectedId as NodeID : null;
  const selectedArrowId = selectedType === 'arrow' ? selectedId as ArrowID : null;
  const selectedPersonId = selectedType === 'person' ? selectedId as PersonID : null;
  const hasSelection = selectedId !== null;
  
  const selectNode = useCallback((id: NodeID): void => {
    store.getState().select(id, 'node');
  }, []);
  
  const selectArrow = useCallback((id: ArrowID): void => {
    store.getState().select(id, 'arrow');
  }, []);
  
  const selectPerson = useCallback((id: PersonID): void => {
    store.getState().select(id, 'person');
  }, []);
  
  const clearSelection = useCallback((): void => {
    store.getState().clearSelection();
  }, []);
  
  const isSelected = useCallback((id: string): boolean => {
    return store.getState().selectedId === id;
  }, []);
  
  const toggleSelection = useCallback((id: string, type: SelectableType): void => {
    const state = store.getState();
    if (state.selectedId === id) {
      state.clearSelection();
    } else {
      state.select(id as SelectableID, type);
    }
  }, []);
  
  const getSelectedNode = useCallback((): DomainNode | null => {
    if (selectedType !== 'node' || !selectedId) return null;
    return store.getState().nodes.get(selectedId as NodeID) || null;
  }, [selectedId, selectedType]);
  
  const getSelectedArrow = useCallback((): DomainArrow | null => {
    if (selectedType !== 'arrow' || !selectedId) return null;
    return store.getState().arrows.get(selectedId as ArrowID) || null;
  }, [selectedId, selectedType]);
  
  const getSelectedPerson = useCallback((): DomainPerson | null => {
    if (selectedType !== 'person' || !selectedId) return null;
    return store.getState().persons.get(selectedId as PersonID) || null;
  }, [selectedId, selectedType]);
  
  return {
    // Current selection state
    selectedId,
    selectedType,
    selectedNodeId,
    selectedArrowId,
    selectedPersonId,
    hasSelection,
    
    // Selection operations
    selectNode,
    selectArrow,
    selectPerson,
    clearSelection,
    
    // Multi-selection
    isSelected,
    toggleSelection,
    
    // Selection queries
    getSelectedNode,
    getSelectedArrow,
    getSelectedPerson,
  };
}