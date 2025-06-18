/**
 * useCanvas - Focused hook for canvas state and React Flow integration
 * 
 * This hook provides canvas data and React Flow handlers without mixing in
 * interaction concerns like drag/drop or context menus.
 */

import React, { useRef, useCallback } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { type NodeChange, type EdgeChange, type Connection } from '@xyflow/react';
import { isWithinTolerance } from '@/shared/utils/math';
import { createHandlerTable } from '@/shared/utils/dispatchTable';
import { useUnifiedStore } from '@/shared/hooks/useUnifiedStore';
import { DomainArrow, DomainHandle, DomainNode, DomainPerson,  createHandleId, nodeId } from '@/core/types';
import { nodeToReact } from '@/features/diagram-editor/adapters/DiagramAdapter';
import { createCommonStoreSelector } from '@/core/store/selectorFactory';
import type { NodeID, ArrowID, PersonID, HandleID  } from '@dipeo/domain-models';


// Helper hook for efficient Map to Array conversion
function useCachedMapArray<K, V>(
  map: Map<K, V>,
  mapVersion?: number
): V[] {
  const cacheRef = useRef<{ array: V[]; size: number; version?: number }>({
    array: [],
    size: -1,
    version: -1
  });
  
  return React.useMemo(() => {
    if (cacheRef.current.size !== map.size || 
        (mapVersion !== undefined && cacheRef.current.version !== mapVersion)) {
      cacheRef.current = {
        array: Array.from(map.values()),
        size: map.size,
        version: mapVersion
      };
    }
    return cacheRef.current.array;
  }, [map.size, mapVersion]);
}

export interface UseCanvasOptions {
  readOnly?: boolean;
}

export interface UseCanvasReturn {
  // Canvas Data (optimized with caching)
  nodes: ReturnType<typeof nodeToReact>[];
  arrows: DomainArrow[];
  persons: DomainPerson[];
  handles: Map<HandleID, DomainHandle>;
  
  // Canvas State
  isMonitorMode: boolean;
  isExecutionMode: boolean;
  isConnectable: boolean;
  
  // React Flow Handlers
  onNodesChange: (changes: NodeChange[]) => void;
  onArrowsChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;
  
  // Direct access to arrays (for performance)
  nodesArray: DomainNode[];
  arrowsArray: DomainArrow[];
  personsArray: DomainPerson[];
}

export function useCanvas(options: UseCanvasOptions = {}): UseCanvasReturn {
  const { readOnly = false } = options;
  
  // Create stable selector
  const storeSelector = React.useMemo(() => createCommonStoreSelector(), []);
  const storeState = useUnifiedStore(useShallow(storeSelector));
  
  // Convert Maps to arrays with efficient caching
  const nodesArray = useCachedMapArray(storeState.nodesMap, storeState.dataVersion) as DomainNode[];
  const arrowsArray = useCachedMapArray(storeState.arrows, storeState.dataVersion) as DomainArrow[];
  const personsArray = useCachedMapArray(storeState.persons, storeState.dataVersion) as DomainPerson[];
  const handlesArray = useCachedMapArray(storeState.handlesMap, storeState.dataVersion) as DomainHandle[];
  
  // Position update batching
  const positionUpdateQueueRef = useRef<Map<NodeID, { x: number; y: number }>>(new Map());
  const rafIdRef = useRef<number | undefined>(undefined);
  
  const processBatchedPositionUpdates = useCallback(() => {
    if (positionUpdateQueueRef.current.size === 0) return;
    
    storeState.transaction(() => {
      positionUpdateQueueRef.current.forEach((position, nodeId) => {
        storeState.updateNode(nodeId, { position });
      });
      positionUpdateQueueRef.current.clear();
    });
    
    rafIdRef.current = undefined;
  }, [storeState]);
  
  const batchPositionUpdate = useCallback((nodeId: NodeID, position: { x: number; y: number }) => {
    positionUpdateQueueRef.current.set(nodeId, position);
    
    if (!rafIdRef.current) {
      rafIdRef.current = requestAnimationFrame(processBatchedPositionUpdates);
    }
  }, [processBatchedPositionUpdates]);
  
  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
      }
    };
  }, []);
  
  // Create node change handler table
  const nodeChangeHandlers = React.useMemo(() => 
    createHandlerTable<NodeChange['type'], [NodeChange, typeof storeState], void>({
      position: () => {
        // Position changes are handled inline
      },
      dimensions: () => {
        // Dimensions are handled by React Flow internally
      },
      replace: () => {
        // Handle node replacement if needed
      },
      remove: (change, state) => {
        if ('id' in change) {
          state.deleteNode(change.id as NodeID);
        }
      },
      select: (change, state) => {
        if ('selected' in change && 'id' in change) {
          if (change.selected) {
            state.select(change.id as NodeID, 'node');
          } else if (state.selectedId === change.id) {
            state.clearSelection();
          }
        }
      },
      add: () => {
        // React Flow is initializing the node
      },
    }), []
  );

  const onNodesChange = useCallback((changes: NodeChange[]) => {
    if (readOnly || storeState.isMonitorMode || storeState.isExecutionMode) return;
    
    changes.forEach((change) => {
      if (change.type === 'position' && change.position) {
        const node = storeState.nodesMap.get(change.id as NodeID);
        if (node) {
          const tolerance = change.dragging ? 5 : 0.01;
          const positionChanged = 
            !isWithinTolerance(node.position?.x || 0, change.position.x, tolerance) ||
            !isWithinTolerance(node.position?.y || 0, change.position.y, tolerance);
          
          if (positionChanged && !change.dragging) {
            batchPositionUpdate(change.id as NodeID, change.position);
          }
        }
      } else {
        nodeChangeHandlers.execute(change.type, change, storeState);
      }
    });
  }, [readOnly, storeState, batchPositionUpdate, nodeChangeHandlers]);
  
  const onArrowsChange = useCallback((changes: EdgeChange[]) => {
    if (readOnly || storeState.isMonitorMode || storeState.isExecutionMode) return;
    
    storeState.transaction(() => {
      changes.forEach((change) => {
        if (change.type === 'remove') {
          storeState.deleteArrow(change.id as ArrowID);
        }
      });
    });
  }, [readOnly, storeState]);
  
  const onConnect = useCallback((connection: Connection) => {
    if (readOnly || storeState.isMonitorMode || storeState.isExecutionMode) return;
    
    if (connection.source && connection.target && 
        connection.sourceHandle && connection.targetHandle) {
      // Strip any numeric suffixes that React Flow might have added
      const stripSuffix = (handleName: string): string => {
        const match = handleName.match(/^(.+)_\d+$/);
        return match && match[1] ? match[1] : handleName;
      };
      
      const sourceHandleId = createHandleId(
        nodeId(connection.source),
        stripSuffix(connection.sourceHandle)
      );
      const targetHandleId = createHandleId(
        nodeId(connection.target),
        stripSuffix(connection.targetHandle)
      );
      
      storeState.addArrow(sourceHandleId, targetHandleId);
    }
  }, [readOnly, storeState]);
  
  // Create handle lookup for efficient access
  const handlesByNode = React.useMemo(() => {
    const lookup = new Map<NodeID, DomainHandle[]>();
    handlesArray.forEach(handle => {
      const handles = lookup.get(nodeId(handle.nodeId)) || [];
      handles.push(handle);
      lookup.set(nodeId(handle.nodeId), handles);
    });
    return lookup;
  }, [handlesArray]);
  
  // Convert nodes to React Flow format
  const nodes = React.useMemo(() => {
    return nodesArray.map(node => {
      const nodeHandles = handlesByNode.get(node.id as NodeID) || [];
      return nodeToReact(node, nodeHandles);
    });
  }, [nodesArray, handlesByNode]);
  
  const isConnectable = !readOnly && !storeState.isMonitorMode && !storeState.isExecutionMode;
  
  return {
    // Canvas Data
    nodes,
    arrows: arrowsArray,
    persons: personsArray,
    handles: storeState.handlesMap,
    
    // Canvas State
    isMonitorMode: storeState.isMonitorMode,
    isExecutionMode: storeState.isExecutionMode,
    isConnectable,
    
    // React Flow Handlers
    onNodesChange,
    onArrowsChange,
    onConnect,
    
    // Direct arrays for performance
    nodesArray,
    arrowsArray,
    personsArray,
  };
}