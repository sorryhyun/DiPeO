/**
 * useNodeOperations - Focused hook for node CRUD operations
 */

import { useCallback } from 'react';
import { useUnifiedStore } from '@/shared/hooks/useUnifiedStore';
import { NodeID, Vec2, DomainNode } from '@/core/types';
import { NodeKind } from '@/features/diagram-editor/types/node-kinds';
import { graphQLTypeToNodeKind } from '@/graphql/types';

export interface UseNodeOperationsReturn {
  // CRUD Operations
  addNode: (type: NodeKind, position: Vec2, data?: Record<string, unknown>) => NodeID;
  updateNode: (id: NodeID, updates: Partial<DomainNode>) => void;
  deleteNode: (id: NodeID) => void;
  duplicateNode: (id: NodeID) => NodeID | null;
  
  // Queries
  getNode: (id: NodeID) => DomainNode | null;
  getNodesByType: (type: string) => DomainNode[];
  getAllNodes: () => DomainNode[];
  hasNode: (id: NodeID) => boolean;
  
  // Batch operations
  deleteNodes: (ids: NodeID[]) => void;
  updateNodes: (updates: Map<NodeID, Partial<DomainNode>>) => void;
}

export function useNodeOperations(): UseNodeOperationsReturn {
  const store = useUnifiedStore;
  
  const addNode = useCallback((
    type: NodeKind, 
    position: Vec2, 
    data?: Record<string, unknown>
  ): NodeID => {
    return store.getState().addNode(type, position, data);
  }, []);
  
  const updateNode = useCallback((
    id: NodeID, 
    updates: Partial<DomainNode>
  ): void => {
    store.getState().updateNode(id, updates);
  }, []);
  
  const deleteNode = useCallback((id: NodeID): void => {
    store.getState().deleteNode(id);
  }, []);
  
  const duplicateNode = useCallback((id: NodeID): NodeID | null => {
    const state = store.getState();
    const node = state.nodes.get(id);
    if (!node) return null;
    
    const newPosition = {
      x: (node.position?.x || 0) + 50,
      y: (node.position?.y || 0) + 50
    };
    
    return state.addNode(
      graphQLTypeToNodeKind(node.type) as NodeKind,
      newPosition,
      { ...node.data }
    );
  }, []);
  
  const getNode = useCallback((id: NodeID): DomainNode | null => {
    return store.getState().nodes.get(id) || null;
  }, []);
  
  const getNodesByType = useCallback((type: string): DomainNode[] => {
    const nodes: DomainNode[] = [];
    store.getState().nodes.forEach(node => {
      if (node.type === type) {
        nodes.push(node);
      }
    });
    return nodes;
  }, []);
  
  const getAllNodes = useCallback((): DomainNode[] => {
    return Array.from(store.getState().nodes.values());
  }, []);
  
  const hasNode = useCallback((id: NodeID): boolean => {
    return store.getState().nodes.has(id);
  }, []);
  
  const deleteNodes = useCallback((ids: NodeID[]): void => {
    const state = store.getState();
    state.transaction(() => {
      ids.forEach(id => state.deleteNode(id));
    });
  }, []);
  
  const updateNodes = useCallback((updates: Map<NodeID, Partial<DomainNode>>): void => {
    const state = store.getState();
    state.transaction(() => {
      updates.forEach((update, id) => {
        state.updateNode(id, update);
      });
    });
  }, []);
  
  return {
    // CRUD Operations
    addNode,
    updateNode,
    deleteNode,
    duplicateNode,
    
    // Queries
    getNode,
    getNodesByType,
    getAllNodes,
    hasNode,
    
    // Batch operations
    deleteNodes,
    updateNodes,
  };
}