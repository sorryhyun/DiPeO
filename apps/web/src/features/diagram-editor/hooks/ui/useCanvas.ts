/**
 * useCanvas - Focused hook for canvas state and React Flow integration
 * 
 * This hook provides canvas data and React Flow handlers without mixing in
 * interaction concerns like drag/drop or context menus.
 */

import React, { useRef, useCallback } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { type NodeChange, type EdgeChange, type Connection } from '@xyflow/react';
import { isWithinTolerance } from '@/lib/utils/math';
import { useUnifiedStore } from '@/core/store/unifiedStore';
import { useUIState } from '@/shared/hooks/selectors';
import { DomainArrow, DomainHandle, DomainNode, DomainPerson, nodeId } from '@/core/types';
import { DiagramAdapter } from '@/features/diagram-editor/adapters/DiagramAdapter';
import { NodeType, type NodeID, type ArrowID, type HandleID } from '@dipeo/domain-models';


// Simple memoized array conversion
function useMapToArray<K, V>(map: Map<K, V>, version: number): V[] {
  return React.useMemo(() => Array.from(map.values()), [map, version]);
}

export interface UseCanvasOptions {
  readOnly?: boolean;
}

export interface UseCanvasReturn {
  // Canvas Data
  nodes: ReturnType<typeof DiagramAdapter.nodeToReactFlow>[];
  arrows: DomainArrow[];
  persons: DomainPerson[];
  handles: Map<HandleID, DomainHandle>;
  
  // Array versions for React components
  nodesArray: DomainNode[];
  arrowsArray: DomainArrow[];
  personsArray: DomainPerson[];
  
  // Canvas State
  isMonitorMode: boolean;
  isConnectable: boolean;
  
  // React Flow Handlers
  onNodesChange: (changes: NodeChange[]) => void;
  onArrowsChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;
}

export function useCanvas(options: UseCanvasOptions = {}): UseCanvasReturn {
  const { readOnly = false } = options;
  
  // Get UI state for execution mode detection
  const { activeCanvas } = useUIState();
  const isExecutionMode = activeCanvas === 'execution';
  
  // Direct store access with simplified selectors
  const { 
    nodes: nodesMap, 
    arrows: arrowsMap, 
    persons: personsMap,
    handles: handlesMap,
    nodesArray,
    arrowsArray,
    personsArray,
    dataVersion,
    isMonitorMode,
    addArrow,
    deleteArrow,
    updateNode,
    deleteNode,
    transaction,
    select,
    clearSelection,
    selectedId
  } = useUnifiedStore(useShallow(state => ({
    nodes: state.nodes,
    arrows: state.arrows,
    persons: state.persons,
    handles: state.handles,
    nodesArray: state.nodesArray,
    arrowsArray: state.arrowsArray,
    personsArray: state.personsArray,
    dataVersion: state.dataVersion,
    isMonitorMode: state.isMonitorMode,
    addArrow: state.addArrow,
    deleteArrow: state.deleteArrow,
    updateNode: state.updateNode,
    deleteNode: state.deleteNode,
    transaction: state.transaction,
    select: state.select,
    clearSelection: state.clearSelection,
    selectedId: state.selectedId
  })));
  
  // We get arrays directly from store now, but keep handlesArray for local use
  const handlesArray = useMapToArray(handlesMap, dataVersion);
  
  // Position update batching
  const positionUpdateQueueRef = useRef<Map<NodeID, { x: number; y: number }>>(new Map());
  const rafIdRef = useRef<number | undefined>(undefined);
  
  const processBatchedPositionUpdates = useCallback(() => {
    if (positionUpdateQueueRef.current.size === 0) return;
    
    transaction(() => {
      positionUpdateQueueRef.current.forEach((position, nodeId) => {
        updateNode(nodeId, { position });
      });
      positionUpdateQueueRef.current.clear();
    });
    
    rafIdRef.current = undefined;
  }, [transaction, updateNode]);
  
  
  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
      }
    };
  }, []);

  const onNodesChange = useCallback((changes: NodeChange[]) => {
    if (readOnly || isMonitorMode) return;
    
    changes.forEach((change) => {
      if (change.type === 'position' && change.position) {
        const node = nodesMap.get(change.id as NodeID);
        if (node) {
          const tolerance = change.dragging ? 5 : 0.01;
          const currentX = node.position?.x ?? 0;
          const currentY = node.position?.y ?? 0;
          const positionChanged = 
            !isWithinTolerance(currentX, change.position.x, tolerance) ||
            !isWithinTolerance(currentY, change.position.y, tolerance);
          
          if (positionChanged) {
            updateNode(change.id as NodeID, { 
              position: {
                x: change.position.x,
                y: change.position.y
              }
            });
          }
        }
      } else if (change.type === 'remove' && 'id' in change) {
        deleteNode(change.id as NodeID);
      } else if (change.type === 'select' && 'selected' in change && 'id' in change) {
        if (change.selected) {
          select(change.id as NodeID, 'node');
        } else if (selectedId === change.id) {
          clearSelection();
        }
      }
    });
  }, [readOnly, isMonitorMode, isExecutionMode, nodesMap, updateNode, deleteNode, select, clearSelection, selectedId]);
  
  const onArrowsChange = useCallback((changes: EdgeChange[]) => {
    if (readOnly || isMonitorMode || isExecutionMode) return;
    
    transaction(() => {
      changes.forEach((change) => {
        if (change.type === 'remove') {
          deleteArrow(change.id as ArrowID);
        }
      });
    });
  }, [readOnly, isMonitorMode, isExecutionMode, transaction, deleteArrow]);
  
  const onConnect = useCallback((connection: Connection) => {
    if (readOnly || isMonitorMode || isExecutionMode) return;
    
    if (connection.source && connection.target && 
        connection.sourceHandle && connection.targetHandle) {
      // The handle IDs from React Flow are already in the correct format
      // Just use them directly as HandleIDs
      const sourceHandleId = connection.sourceHandle as HandleID;
      const targetHandleId = connection.targetHandle as HandleID;
      
      // Extract handle name from the handle ID for condition node check
      // Handle ID format: nodeId_handleName_direction
      const sourceHandleParts = sourceHandleId.split('_');
      const sourceHandleName = sourceHandleParts[sourceHandleParts.length - 2]?.toLowerCase();
      
      // Check if this is a connection from a condition node's True/False handle
      let arrowData: Record<string, any> | undefined;
      if (sourceHandleName === 'condtrue' || sourceHandleName === 'condfalse') {
        // Get the source node to verify it's a condition node
        const sourceNode = nodesMap.get(nodeId(connection.source));
        if (sourceNode && sourceNode.type === NodeType.CONDITION) {
          arrowData = { branch: sourceHandleName === 'condtrue' ? 'true' : 'false' };
        }
      }
      
      addArrow(sourceHandleId, targetHandleId, arrowData);
    }
  }, [readOnly, isMonitorMode, isExecutionMode, nodesMap, addArrow]);
  
  // Create handle lookup for efficient access
  const handlesByNode = React.useMemo(() => {
    const lookup = new Map<NodeID, DomainHandle[]>();
    handlesArray.forEach(handle => {
      const handles = lookup.get(nodeId(handle.node_id)) || [];
      handles.push(handle);
      lookup.set(nodeId(handle.node_id), handles);
    });
    return lookup;
  }, [handlesArray]);
  
  // Convert nodes to React Flow format
  const nodes = React.useMemo(() => {
    return nodesArray.map(node => {
      const nodeHandles = handlesByNode.get(node.id as NodeID) || [];
      return DiagramAdapter.nodeToReactFlow(node, nodeHandles);
    });
  }, [nodesArray, handlesByNode]);
  
  const isConnectable = !readOnly && !isMonitorMode;
  
  return {
    // Canvas Data
    nodes,
    arrows: arrowsArray,
    persons: personsArray,
    handles: handlesMap,
    
    // Array versions for React components
    nodesArray,
    arrowsArray,
    personsArray,
    
    // Canvas State
    isMonitorMode,
    isConnectable,
    
    // React Flow Handlers
    onNodesChange,
    onArrowsChange,
    onConnect,
  };
}