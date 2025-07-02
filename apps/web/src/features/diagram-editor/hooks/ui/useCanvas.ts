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
import { DomainArrow, DomainHandle, DomainNode, DomainPerson, nodeId } from '@/core/types';
import { DiagramAdapter } from '@/features/diagram-editor/adapters/DiagramAdapter';
import { createCommonStoreSelector } from '@/core/store/selectorFactory';
import { NodeType, type NodeID, type ArrowID, type HandleID, createHandleId } from '@dipeo/domain-models';


// Helper hook for efficient Map to Array conversion
function useCachedMapArray<K, V>(
  map: Map<K, V>,
  mapVersion?: number
): V[] {
  const cacheRef = useRef<{ array: V[]; size: number; version?: number; mapRef: Map<K, V> | null }>({
    array: [],
    size: -1,
    version: -1,
    mapRef: null
  });
  
  return React.useMemo(() => {
    // Check if map reference changed, size changed, or version changed
    if (cacheRef.current.mapRef !== map ||
        cacheRef.current.size !== map.size || 
        (mapVersion !== undefined && cacheRef.current.version !== mapVersion)) {
      cacheRef.current = {
        array: Array.from(map.values()),
        size: map.size,
        version: mapVersion,
        mapRef: map
      };
    }
    return cacheRef.current.array;
  }, [map, map.size, mapVersion]);
}

export interface UseCanvasOptions {
  readOnly?: boolean;
}

export interface UseCanvasReturn {
  // Canvas Data (optimized with caching)
  nodes: ReturnType<typeof DiagramAdapter.nodeToReactFlow>[];
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
  
  // Use arrays directly from store - no conversion needed
  const nodesArray = storeState.nodesArray || [];
  const arrowsArray = storeState.arrowsArray || [];
  const personsArray = storeState.personsArray || [];
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
      add: (change) => {
        // React Flow is initializing the node - we need to handle this
        // to avoid the "trying to drag a node that is not initialized" error
        if ('item' in change && change.item) {
          // The node is already in our store, but React Flow needs to track it internally
          // We don't need to add it to our store again, just acknowledge the change
        }
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
          const currentX = node.position?.x ?? 0;
          const currentY = node.position?.y ?? 0;
          const positionChanged = 
            !isWithinTolerance(currentX, change.position.x, tolerance) ||
            !isWithinTolerance(currentY, change.position.y, tolerance);
          
          if (positionChanged) {
            // Update position immediately for natural movement
            storeState.updateNode(change.id as NodeID, { 
              position: {
                x: change.position.x,
                y: change.position.y
              }
            });
          }
        }
      } else {
        nodeChangeHandlers.execute(change.type, change, storeState);
      }
    });
  }, [readOnly, storeState, nodeChangeHandlers]);
  
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
      
      const cleanSourceHandle = stripSuffix(connection.sourceHandle);
      const cleanTargetHandle = stripSuffix(connection.targetHandle);
      
      const sourceHandleId = createHandleId(
        nodeId(connection.source),
        cleanSourceHandle
      );
      const targetHandleId = createHandleId(
        nodeId(connection.target),
        cleanTargetHandle
      );
      
      // Check if this is a connection from a condition node's True/False handle
      let arrowData: Record<string, any> | undefined;
      const sourceHandleName = cleanSourceHandle.toLowerCase();
      if (sourceHandleName === 'true' || sourceHandleName === 'false') {
        // Get the source node to verify it's a condition node
        const sourceNode = storeState.nodesMap.get(nodeId(connection.source));
        if (sourceNode && sourceNode.type === NodeType.CONDITION) {
          arrowData = { branch: sourceHandleName };
        }
      }
      
      storeState.addArrow(sourceHandleId, targetHandleId, arrowData);
    }
  }, [readOnly, storeState]);
  
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