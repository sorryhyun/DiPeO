import React, { useCallback, useRef, useState, Suspense } from 'react';
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
import { FileText, MessageSquare } from 'lucide-react';
import { useDiagram } from '@/hooks';
import { useExecutionStore } from '@/stores/executionStore';
import { useIsReadOnly } from '@/hooks/useStoreSelectors';
import ContextMenu from '../controls/ContextMenu';
import { CustomArrow as CustomArrowBase } from '../arrows/CustomArrow';
import { roundPosition } from '@/utils/canvas';
import nodeTypes from '../nodes/nodeTypes';
import { DiagramNode, Arrow } from '@/types';

// Lazy load the dashboard components
const PropertiesTab = React.lazy(() => import('@/components/properties/PropertiesTab'));
const ConversationTab = React.lazy(() => import('@/components/conversation/ConversationTab'));

// Use dependency injection instead of wrapper components
const edgeTypes: EdgeTypes = {
  customArrow: CustomArrowBase,
};

interface DiagramCanvasProps {
  executionMode?: boolean;
}

const DiagramCanvas: React.FC<DiagramCanvasProps> = ({ executionMode = false }) => {
  // Use the unified diagram hook
  const diagram = useDiagram({
    enableInteractions: true,
    enableFileOperations: true
  });
  
  // Check execution and monitor mode
  const isExecuting = useExecutionStore(state => state.isExecuting);
  const isMonitorMode = useIsReadOnly();
  
  // Destructure commonly used values for cleaner code
  const {
    nodes,
    arrows,
    onNodesChange,
    onArrowsChange,
    onConnect,
    addNode,
    deleteNode,
    deleteArrow,
    selectedNodeId,
    selectedArrowId,
    selectNode,
    selectArrow,
    addPerson,
    // Canvas interactions
    contextMenu,
    closeContextMenu,
    isContextMenuOpen,
    onDragOver,
    onNodeDrop,
    onPaneContextMenu,
    onNodeContextMenu,
    onEdgeContextMenu
  } = diagram;

  const reactFlowWrapper = useRef<HTMLDivElement | null>(null);
  const [rfInstance, setRfInstance] = useState<ReactFlowInstance<DiagramNode, Arrow> | null>(null);
  
  const handleInit = useCallback((instance: ReactFlowInstance<DiagramNode, Arrow>) => {
    setRfInstance(instance);
  }, []);

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
      onNodeDrop?.(event, projectPosition);
    },
    [onNodeDrop, projectPosition, rfInstance]
  );

  const onNodeClick = (_: React.MouseEvent, node: Node) => {
    selectNode(node.id);
  };
  const onArrowClick = (_: React.MouseEvent, edge: Edge) => {
    selectArrow(edge.id);
  };
  const handlePaneClick = () => {
    diagram.clearSelection();
    if (closeContextMenu) {
      closeContextMenu();
    }
  };

  return (
    <div className="h-full flex flex-col">
      {executionMode ? (
        // In execution mode, show only the canvas without property panel
        <div className="h-full w-full relative outline-none" ref={reactFlowWrapper} tabIndex={0} style={{ minHeight: '100%', height: '100%', position: 'relative' }}>
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
              onPaneClick={handlePaneClick}
              onInit={handleInit}
              onNodeContextMenu={(event, node) => {
                selectNode(node.id);
                onNodeContextMenu?.(event, node.id);
              }}
              onEdgeContextMenu={(event, edge) => {
                selectArrow(edge.id);
                onEdgeContextMenu?.(event, edge.id);
              }}
              onPaneContextMenu={(event) => {
                diagram.clearSelection();
                onPaneContextMenu?.(event as React.MouseEvent);
              }}
              nodeTypes={nodeTypes}
              edgeTypes={edgeTypes}
              connectionLineStyle={{ stroke: '#3b82f6', strokeWidth: 2 }}
              defaultEdgeOptions={{ type: 'customArrow', markerEnd: { type: MarkerType.ArrowClosed } }}
              fitView
              onDragOver={onDragOver || undefined}
              onDrop={onDrop}
              className="bg-gray-900"
              style={{ width: '100%', height: '100%' }}
            >
              <Controls />
              <Background variant={BackgroundVariant.Dots} gap={12} size={1} color={executionMode ? "#374151" : undefined} />
            </ReactFlow>
          </div>
          
          {isContextMenuOpen && contextMenu?.position && (
            <Suspense fallback={null}>
              <ContextMenu
                position={contextMenu.position}
                target={contextMenu?.target || 'pane'}
                selectedNodeId={selectedNodeId}
                selectedArrowId={selectedArrowId}
                containerRef={reactFlowWrapper as React.RefObject<HTMLDivElement>}
                onAddNode={addNode}
                onAddPerson={handleAddPerson}
                onDeleteNode={deleteNode}
                onDeleteArrow={deleteArrow}
                onClose={closeContextMenu || (() => {})}
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
              position: 'relative'
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
                onPaneClick={handlePaneClick}
                onInit={handleInit}
                onNodeContextMenu={(event, node) => {
                  selectNode(node.id);
                  onNodeContextMenu?.(event as React.MouseEvent, node.id);
                }}
                onEdgeContextMenu={(event, edge) => {
                  selectArrow(edge.id);
                  onEdgeContextMenu?.(event as React.MouseEvent, edge.id);
                }}
                onPaneContextMenu={(event) => {
                  diagram.clearSelection();
                  onPaneContextMenu?.(event as React.MouseEvent);
                }}
                nodeTypes={nodeTypes}
                edgeTypes={edgeTypes}
                connectionLineStyle={{ stroke: '#3b82f6', strokeWidth: 2 }}
                defaultEdgeOptions={{ type: 'customArrow', markerEnd: { type: MarkerType.ArrowClosed } }}
                fitView
                onDragOver={onDragOver || undefined}
                onDrop={onDrop}
                className={executionMode ? "bg-gray-900" : "bg-gradient-to-br from-slate-50 to-sky-100"}
                style={{ width: '100%', height: '100%' }}
              >
                <Controls />
                <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
              </ReactFlow>
            </div>
            
            {isContextMenuOpen && contextMenu?.position && (
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
                  onClose={closeContextMenu || (() => {})}
                  projectPosition={projectPosition}
                />
              </Suspense>
            )}
          </div>
        </Panel>

        {/* Resizable Handle */}
        <PanelResizeHandle className="h-1 bg-gray-200 hover:bg-gray-300 cursor-row-resize" />

        {/* Property/Conversation Panel - switches based on execution mode */}
        <Panel defaultSize={35} minSize={20}>
          <div className="h-full bg-white flex flex-col">
            {/* Panel Header */}
            <div className="flex border-b bg-gray-50">
              <div className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-white border-b-2 border-blue-500 text-blue-600">
                {isExecuting || isMonitorMode ? (
                  <>
                    <MessageSquare className="w-4 h-4" />
                    Conversation
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4" />
                    Properties
                  </>
                )}
              </div>
            </div>

            {/* Panel Content */}
            <div className="flex-1 overflow-hidden">
              <Suspense fallback={
                <div className="h-full flex items-center justify-center">
                  <div className="text-gray-500 animate-pulse">Loading...</div>
                </div>
              }>
                {isExecuting || isMonitorMode ? (
                  <ConversationTab />
                ) : (
                  <PropertiesTab />
                )}
              </Suspense>
            </div>
          </div>
        </Panel>
      </PanelGroup>
      )}
    </div>
  );
};

export default DiagramCanvas;