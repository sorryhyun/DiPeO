import React, { useCallback, useRef, useState, useEffect, Suspense } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  MarkerType,
  BackgroundVariant,
  Node,
  Edge,
  ReactFlowInstance,
  EdgeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import '@xyflow/react/dist/base.css';
import { PanelGroup, Panel, PanelResizeHandle } from 'react-resizable-panels';
import {
  useContextMenu,
  useKeyboardShortcuts,
  CustomArrow as CustomArrowBase,
  ContextMenu
} from '..';
import { roundPosition } from '../utils/canvasUtils';
import { nodeTypes, useNodeDrag } from '@/features/nodes';
import { DiagramNode, Arrow } from '@/common/types';
import PropertyDashboard from './PropertyDashboard';

import { 
  useCanvasState, 
  useSelectedElement, 
  useExecutionStatus,
  usePersons
} from '@/state/hooks/useStoreSelectors';
import { useUndo, useRedo } from '@/common/utils/storeSelectors';

// Use dependency injection instead of wrapper components
const edgeTypes: EdgeTypes = {
  customArrow: CustomArrowBase,
};

interface DiagramCanvasProps {
  executionMode?: boolean;
}

const DiagramCanvas: React.FC<DiagramCanvasProps> = ({ executionMode = false }) => {
  // Use optimized selectors
  const {
    nodes,
    arrows,
    onNodesChange,
    onArrowsChange,
    onConnect,
    addNode,
    deleteNode,
    deleteArrow,
  } = useCanvasState();
  
  const undo = useUndo();
  const redo = useRedo();
  
  const {
    selectedNodeId,
    selectedArrowId,
    selectedPersonId,
    setSelectedNodeId,
    setSelectedArrowId,
  } = useSelectedElement();
  
  // Execution state from optimized selector
  const { runningNodes, currentRunningNode } = useExecutionStatus();
  
  // Person actions from optimized selector
  const { addPerson, deletePerson } = usePersons();  

  const reactFlowWrapper = useRef<HTMLDivElement | null>(null);
  const [rfInstance, setRfInstance] = useState<ReactFlowInstance<DiagramNode, Arrow> | null>(null);
  
  const handleInit = useCallback((instance: ReactFlowInstance<DiagramNode, Arrow>) => {
    setRfInstance(instance);
  }, []);
  
  const { contextMenu, openContextMenu, closeContextMenu, isOpen } = useContextMenu();

  // Simple nodes array - let BaseNode handle running state via execution store
  const nodesWithExecutionState = nodes;

  // Update ReactFlow instance when running nodes change
  useEffect(() => {
    if (import.meta.env.DEV) {
      // Removed console.log for production build
    }
    // Removed viewport manipulation - let React Flow handle updates naturally
  }, [runningNodes, currentRunningNode]);

  // Handle keyboard shortcuts
  useKeyboardShortcuts({
    onDelete: () => {
      if (selectedNodeId) deleteNode(selectedNodeId);
      else if (selectedArrowId) deleteArrow(selectedArrowId);
      else if (selectedPersonId) deletePerson(selectedPersonId);
    },
    onEscape: closeContextMenu,
    onUndo: undo,
    onRedo: redo,
  });

  // Helper to project screen coords to RF coords
  const projectPosition = useCallback((x: number, y: number) => {
    if (!reactFlowWrapper.current || !rfInstance) return { x: 0, y: 0 };
    
    // screenToFlowPosition expects screen coordinates (absolute), not relative
    // So we pass x, y directly without subtracting the container bounds
    const position = rfInstance.screenToFlowPosition({ 
      x, 
      y 
    });
    
    return roundPosition(position);
  }, [rfInstance]);

  // Context menu actions
  // Use extracted node drag hook
  const { onDragOver, onDrop: onNodeDrop } = useNodeDrag();

  const handleAddPerson = () => {
    addPerson({ label: 'New Person' });
  };

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      // Ensure we have a ReactFlow instance before dropping
      if (!rfInstance) {
        console.warn('ReactFlow instance not ready');
        return;
      }
      onNodeDrop(event, addNode, projectPosition);
    },
    [onNodeDrop, addNode, projectPosition, rfInstance]
  );

  const onNodeClick = (_: React.MouseEvent, node: Node) => {
    setSelectedNodeId(node.id);
  };
  const onArrowClick = (_: React.MouseEvent, edge: Edge) => {
    setSelectedArrowId(edge.id);
  };
  const onPaneClick = () => {
    setSelectedNodeId(null);
    setSelectedArrowId(null);
    closeContextMenu();
  };

  return (
    <div className="h-full flex flex-col">
      {executionMode ? (
        // In execution mode, show only the canvas without property panel
        <div className="h-full w-full relative outline-none" ref={reactFlowWrapper} tabIndex={0} style={{ minHeight: '400px' }}>
          {/* Main diagram layer */}
          <div className="absolute inset-0">
            <ReactFlow
              nodes={nodesWithExecutionState}
              edges={arrows}
              onNodesChange={onNodesChange}
              onEdgesChange={onArrowsChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              onEdgeClick={onArrowClick}
              onPaneClick={onPaneClick}
              onInit={handleInit}
              onNodeContextMenu={(event, node) => {
                event.preventDefault();
                setSelectedNodeId(node.id);
                setSelectedArrowId(null);
                openContextMenu(event.clientX, event.clientY, 'node');
              }}
              onEdgeContextMenu={(event, edge) => {
                event.preventDefault();
                setSelectedArrowId(edge.id);
                setSelectedNodeId(null);
                openContextMenu(event.clientX, event.clientY, 'edge');
              }}
              onPaneContextMenu={(event) => {
                event.preventDefault();
                setSelectedNodeId(null);
                setSelectedArrowId(null);
                openContextMenu(event.clientX, event.clientY, 'pane');
              }}
              nodeTypes={nodeTypes}
              edgeTypes={edgeTypes}
              connectionLineStyle={{ stroke: '#3b82f6', strokeWidth: 2 }}
              defaultEdgeOptions={{ type: 'customArrow', markerEnd: { type: MarkerType.ArrowClosed } }}
              fitView
              onDragOver={onDragOver}
              onDrop={onDrop}
              className="bg-gray-900"
              style={{ width: '100%', height: '100%' }}
            >
              <Controls />
              <Background variant={BackgroundVariant.Dots} gap={12} size={1} color={executionMode ? "#374151" : undefined} />
            </ReactFlow>
          </div>
          
          {isOpen && contextMenu.position && (
            <Suspense fallback={null}>
              <ContextMenu
                position={contextMenu.position}
                target={contextMenu.target}
                selectedNodeId={selectedNodeId}
                selectedArrowId={selectedArrowId}
                containerRef={reactFlowWrapper as React.RefObject<HTMLDivElement>}
                onAddNode={addNode}
                onAddPerson={handleAddPerson}
                onDeleteNode={deleteNode}
                onDeleteArrow={deleteArrow}
                onClose={closeContextMenu}
                projectPosition={projectPosition}
              />
            </Suspense>
          )}
        </div>
      ) : (
        <PanelGroup direction="vertical">
          {/* Canvas Panel */}
          <Panel defaultSize={65} minSize={30}>
          <div
            className="h-full w-full relative outline-none"
            ref={reactFlowWrapper}
            tabIndex={0}
            style={{
              minHeight: '400px',
            }}

          >
            {/* Main diagram layer */}
            <div className="absolute inset-0">
              <ReactFlow
                nodes={nodesWithExecutionState}
                edges={arrows}
                onNodesChange={onNodesChange}
                onEdgesChange={onArrowsChange}
                onConnect={onConnect}
                onNodeClick={onNodeClick}
                onEdgeClick={onArrowClick}
                onPaneClick={onPaneClick}
                onInit={handleInit}
                onNodeContextMenu={(event, node) => {
                  event.preventDefault();
                  setSelectedNodeId(node.id);
                  setSelectedArrowId(null);
                  openContextMenu(event.clientX, event.clientY, 'node');
                }}
                onEdgeContextMenu={(event, edge) => {
                  event.preventDefault();
                  setSelectedArrowId(edge.id);
                  setSelectedNodeId(null);
                  openContextMenu(event.clientX, event.clientY, 'edge');
                }}
                onPaneContextMenu={(event) => {
                  event.preventDefault();
                  setSelectedNodeId(null);
                  setSelectedArrowId(null);
                  openContextMenu(event.clientX, event.clientY, 'pane');
                }}
                nodeTypes={nodeTypes}
                edgeTypes={edgeTypes}
                connectionLineStyle={{ stroke: '#3b82f6', strokeWidth: 2 }}
                defaultEdgeOptions={{ type: 'customArrow', markerEnd: { type: MarkerType.ArrowClosed } }}
                fitView
                onDragOver={onDragOver}
                onDrop={onDrop}
                className={executionMode ? "bg-gray-900" : "bg-gradient-to-br from-slate-50 to-sky-100"}
                style={{ width: '100%', height: '100%' }}
              >
                <Controls />
                <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
              </ReactFlow>
            </div>
            
            {isOpen && contextMenu.position && (
              <Suspense fallback={null}>
                <ContextMenu
                  position={contextMenu.position}
                  target={contextMenu.target}
                  selectedNodeId={selectedNodeId}
                  selectedArrowId={selectedArrowId}
                  containerRef={reactFlowWrapper as React.RefObject<HTMLDivElement>}
                  onAddNode={addNode}
                  onAddPerson={handleAddPerson}
                  onDeleteNode={deleteNode}
                  onDeleteArrow={deleteArrow}
                  onClose={closeContextMenu}
                  projectPosition={projectPosition}
                />
              </Suspense>
            )}
          </div>
        </Panel>

        {/* Resizable Handle */}
        <PanelResizeHandle className="h-1 bg-gray-200 hover:bg-gray-300 cursor-row-resize" />

        {/* Property Dashboard Panel */}
        <Panel defaultSize={35} minSize={20}>
          <PropertyDashboard />
        </Panel>
      </PanelGroup>
      )}
    </div>
  );
};

export default DiagramCanvas;