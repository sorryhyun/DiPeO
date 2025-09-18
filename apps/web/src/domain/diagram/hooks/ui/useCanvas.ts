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
import { useUnifiedStore } from '@/infrastructure/store/unifiedStore';
import { useUIState } from '@/infrastructure/store/hooks/state';
import { DomainArrow, DomainHandle, DomainNode, DomainPerson, nodeId } from '@/infrastructure/types';
import { DiagramAdapter } from '@/domain/diagram/adapters/DiagramAdapter';
import { NodeType, type NodeID, type ArrowID, type HandleID } from '@dipeo/models';


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
    dataVersion,
    isMonitorMode,
    executionNodeStates,
    executionRunningNodes,
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
    dataVersion: state.dataVersion,
    isMonitorMode: state.isMonitorMode,
    executionNodeStates: state.execution.nodeStates,
    executionRunningNodes: state.execution.runningNodes,
    addArrow: state.addArrow,
    deleteArrow: state.deleteArrow,
    updateNode: state.updateNode,
    deleteNode: state.deleteNode,
    transaction: state.transaction,
    select: state.select,
    clearSelection: state.clearSelection,
    selectedId: state.selectedId
  })));

  // Get arrays using memoization based on dataVersion
  const nodesArray = React.useMemo(() => {
    return nodesMap ? Array.from(nodesMap.values()) : [];
  }, [nodesMap, dataVersion]);

  const arrowsArray = React.useMemo(() => {
    return arrowsMap ? Array.from(arrowsMap.values()) : [];
  }, [arrowsMap, dataVersion]);

  const personsArray = React.useMemo(() => {
    return personsMap ? Array.from(personsMap.values()) : [];
  }, [personsMap, dataVersion]);

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
      if (change.type === 'position') {
        if ('position' in change && change.position) {
          const node = nodesMap.get(change.id as NodeID);
          if (node) {
            const tolerance = 'dragging' in change && change.dragging ? 5 : 0.01;
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
        }
      } else if (change.type === 'remove') {
        if ('id' in change) {
          deleteNode(change.id as NodeID);
        }
      } else if (change.type === 'select') {
        if ('selected' in change && 'id' in change) {
          if (change.selected) {
            select(change.id as NodeID, 'node');
          } else if (selectedId === change.id) {
            clearSelection();
          }
        }
      }
      // For all other change types (add, reset, dimensions, replace, etc.)
      // We don't need to do anything - React Flow handles them internally
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

  // Convert nodes to React Flow format with execution state
  const nodes = React.useMemo(() => {
    return nodesArray.map(node => {
      const nodeHandles = handlesByNode.get(node.id as NodeID) || [];
      const baseNode = DiagramAdapter.nodeToReactFlow(node, nodeHandles);

      // Apply execution state styling if in execution mode or monitor mode
      if ((isExecutionMode || isMonitorMode) && executionNodeStates) {
        const nodeState = executionNodeStates.get(node.id);
        const isRunning = executionRunningNodes?.has(node.id);

        // Add execution state to node data
        baseNode.data = {
          ...baseNode.data,
          executionState: nodeState,
          isRunning
        };

        // Apply visual styling based on state
        const nodeStyle: React.CSSProperties = {};
        let className = '';

        if (isRunning) {
          className = 'node-running';
          nodeStyle.animation = 'pulse-blue 2s infinite';
          nodeStyle.borderColor = '#3b82f6';
          nodeStyle.borderWidth = 2;
        } else if (nodeState) {
          switch (nodeState.status) {
            case 'completed':
              className = 'node-completed';
              nodeStyle.borderColor = '#10b981';
              nodeStyle.borderWidth = 2;
              nodeStyle.backgroundColor = 'rgba(16, 185, 129, 0.1)';
              break;
            case 'failed':
              className = 'node-failed';
              nodeStyle.borderColor = '#ef4444';
              nodeStyle.borderWidth = 2;
              nodeStyle.backgroundColor = 'rgba(239, 68, 68, 0.1)';
              break;
            case 'skipped':
              className = 'node-skipped';
              nodeStyle.opacity = 0.5;
              break;
          }
        }

        // Apply the styling to the node
        baseNode.style = { ...baseNode.style, ...nodeStyle };
        if (className) {
          baseNode.className = className;
        }
      }

      return baseNode;
    });
  }, [nodesArray, handlesByNode, isExecutionMode, isMonitorMode, executionNodeStates, executionRunningNodes]);

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
