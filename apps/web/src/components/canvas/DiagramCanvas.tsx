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
import { useCanvasInteractions } from '@/hooks';
import { ContextMenu } from './ContextMenu';
import { CustomArrow as CustomArrowBase } from './CustomArrow';
import { roundPosition } from '@/utils/canvas';
import nodeTypes from './nodeTypes';
import { DiagramNode, Arrow } from '@/types';
import { 
  useCanvasState, 
  useSelectedElement, 
  usePersons 
} from '@/hooks/useStoreSelectors';
import { useHistoryActions } from '@/hooks/useHistoryActions';

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
  
  const { handleUndo, handleRedo } = useHistoryActions();
  
  const {
    selectedNodeId,
    selectedArrowId,
    selectedPersonId,
    setSelectedNodeId,
    setSelectedArrowId,
  } = useSelectedElement();
  
  // Person actions from optimized selector
  const { addPerson, deletePerson } = usePersons();  

  const reactFlowWrapper = useRef<HTMLDivElement | null>(null);
  const [rfInstance, setRfInstance] = useState<ReactFlowInstance<DiagramNode, Arrow> | null>(null);
  
  const handleInit = useCallback((instance: ReactFlowInstance<DiagramNode, Arrow>) => {
    setRfInstance(instance);
  }, []);
  
  // Canvas interactions - provides context menu, keyboard shortcuts, and drag/drop
  const {
    contextMenu,
    openContextMenu,
    closeContextMenu,
    isContextMenuOpen,
    onNodeDragStart,
    onDragOver,
    onNodeDrop,
    onPaneClick,
    onPaneContextMenu,
    onNodeContextMenu,
    onEdgeContextMenu
  } = useCanvasInteractions({
    onSave: () => console.log('Save triggered'),
    onUndo: handleUndo,
    onRedo: handleRedo,
  });

  // Simple nodes array - let BaseNode handle running state via execution store
  const nodesWithExecutionState = nodes;

  // Note: Keyboard shortcuts are now handled by useCanvasInteractions

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
      onNodeDrop(event, projectPosition);
    },
    [onNodeDrop, projectPosition, rfInstance]
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
                setSelectedNodeId(node.id);
                setSelectedArrowId(null);
                onNodeContextMenu(event, node.id);
              }}
              onEdgeContextMenu={(event, edge) => {
                setSelectedArrowId(edge.id);
                setSelectedNodeId(null);
                onEdgeContextMenu(event, edge.id);
              }}
              onPaneContextMenu={(event) => {
                setSelectedNodeId(null);
                setSelectedArrowId(null);
                onPaneContextMenu(event);
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
          
          {isContextMenuOpen && contextMenu.position && (
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
                  setSelectedNodeId(node.id);
                  setSelectedArrowId(null);
                  onNodeContextMenu(event, node.id);
                }}
                onEdgeContextMenu={(event, edge) => {
                  setSelectedArrowId(edge.id);
                  setSelectedNodeId(null);
                  onEdgeContextMenu(event, edge.id);
                }}
                onPaneContextMenu={(event) => {
                  setSelectedNodeId(null);
                  setSelectedArrowId(null);
                  onPaneContextMenu(event);
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
            
            {isContextMenuOpen && contextMenu.position && (
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

        {/* Property Dashboard Panel - now handled by Sidebar */}
        <Panel defaultSize={35} minSize={20}>
          <div className="h-full bg-gray-50 flex items-center justify-center text-gray-500">
            Properties panel moved to right sidebar
          </div>
        </Panel>
      </PanelGroup>
      )}
    </div>
  );
};

export default DiagramCanvas;