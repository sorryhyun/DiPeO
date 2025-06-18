/**
 * useArrowOperations - Focused hook for arrow CRUD operations
 */

import { useCallback } from 'react';
import { useUnifiedStore } from '@/shared/hooks/useUnifiedStore';
import { ArrowID, HandleID, DomainArrow } from '@/core/types';

export interface UseArrowOperationsReturn {
  // CRUD Operations
  addArrow: (sourceHandle: HandleID, targetHandle: HandleID) => ArrowID | null;
  updateArrow: (id: ArrowID, updates: Partial<DomainArrow>) => void;
  deleteArrow: (id: ArrowID) => void;
  
  // Queries
  getArrow: (id: ArrowID) => DomainArrow | null;
  getArrowsByNode: (nodeId: string) => DomainArrow[];
  getAllArrows: () => DomainArrow[];
  hasArrow: (id: ArrowID) => boolean;
  
  // Batch operations
  deleteArrows: (ids: ArrowID[]) => void;
  deleteArrowsByNode: (nodeId: string) => void;
}

export function useArrowOperations(): UseArrowOperationsReturn {
  const store = useUnifiedStore;
  
  const addArrow = useCallback((
    sourceHandle: HandleID, 
    targetHandle: HandleID
  ): ArrowID | null => {
    return store.getState().addArrow(sourceHandle, targetHandle);
  }, []);
  
  const updateArrow = useCallback((
    id: ArrowID, 
    updates: Partial<DomainArrow>
  ): void => {
    store.getState().updateArrow(id, updates);
  }, []);
  
  const deleteArrow = useCallback((id: ArrowID): void => {
    store.getState().deleteArrow(id);
  }, []);
  
  const getArrow = useCallback((id: ArrowID): DomainArrow | null => {
    return store.getState().arrows.get(id) || null;
  }, []);
  
  const getArrowsByNode = useCallback((nodeId: string): DomainArrow[] => {
    const arrows: DomainArrow[] = [];
    store.getState().arrows.forEach(arrow => {
      // Check if arrow is connected to the node
      const sourceNodeId = arrow.source.split(':')[0];
      const targetNodeId = arrow.target.split(':')[0];
      if (sourceNodeId === nodeId || targetNodeId === nodeId) {
        arrows.push(arrow);
      }
    });
    return arrows;
  }, []);
  
  const getAllArrows = useCallback((): DomainArrow[] => {
    return Array.from(store.getState().arrows.values());
  }, []);
  
  const hasArrow = useCallback((id: ArrowID): boolean => {
    return store.getState().arrows.has(id);
  }, []);
  
  const deleteArrows = useCallback((ids: ArrowID[]): void => {
    const state = store.getState();
    state.transaction(() => {
      ids.forEach(id => state.deleteArrow(id));
    });
  }, []);
  
  const deleteArrowsByNode = useCallback((nodeId: string): void => {
    const state = store.getState();
    const arrowsToDelete: ArrowID[] = [];
    
    state.arrows.forEach((arrow, id) => {
      const sourceNodeId = arrow.source.split(':')[0];
      const targetNodeId = arrow.target.split(':')[0];
      if (sourceNodeId === nodeId || targetNodeId === nodeId) {
        arrowsToDelete.push(id);
      }
    });
    
    if (arrowsToDelete.length > 0) {
      state.transaction(() => {
        arrowsToDelete.forEach(id => state.deleteArrow(id));
      });
    }
  }, []);
  
  return {
    // CRUD Operations
    addArrow,
    updateArrow,
    deleteArrow,
    
    // Queries
    getArrow,
    getArrowsByNode,
    getAllArrows,
    hasArrow,
    
    // Batch operations
    deleteArrows,
    deleteArrowsByNode,
  };
}