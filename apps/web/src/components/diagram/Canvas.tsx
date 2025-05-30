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
import { useHistoryStore } from '@/stores';
import {
  useContextMenu,
  useKeyboardShortcuts,
  CustomArrow as CustomArrowBase,
  ContextMenu as ContextMenuBase } from '@repo/diagram-ui';
import { roundPosition } from '@/utils/diagramSanitizer';
import { nodeTypes } from '@/components/nodes';
import { UNIFIED_NODE_CONFIGS, DiagramNode, Arrow } from '@repo/core-model';
import { MemoryLayerSkeleton } from '../skeletons/SkeletonComponents';

// Lazy load memory layer  
const MemoryLayer = React.lazy(() => import('./MemoryLayer'));
import { 
  useCanvasState, 
  useSelectedElement, 
  useExecutionStatus,
  useUIState,
  usePersons
} from '@/hooks/useStoreSelectors';
import { useDiagramContext } from '@/contexts/DiagramContext';

// Use dependency injection instead of wrapper components
const edgeTypes: EdgeTypes = {
  customArrow: CustomArrowBase,
};

// ContextMenu component that uses dependency injection
const ContextMenu = (props: any) => {
  const { nodeTypes, nodeLabels } = useDiagramContext();
  return <ContextMenuBase {...props} nodeTypes={nodeTypes} nodeLabels={nodeLabels} />;
};


const DiagramCanvas: React.FC = () => {
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
  
  const { undo, redo } = useHistoryStore();
  
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
  const { isMemoryLayerTilted } = useUIState();

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
  const projectPosition = (x: number, y: number) => {
    if (!reactFlowWrapper.current || !rfInstance) return { x: 0, y: 0 };
    const bounds = reactFlowWrapper.current.getBoundingClientRect();
    const position = rfInstance.screenToFlowPosition({ x: x - bounds.left, y: y - bounds.top });
    return roundPosition(position);
  };

  // Context menu actions
  const handleAddPerson = () => {
    addPerson({ label: 'New Person' });
  };

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      if (!reactFlowWrapper.current || !rfInstance) return;
      const type = event.dataTransfer.getData('application/reactflow');
      if (!type) return;
      const position = rfInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });
      addNode(type, roundPosition(position));
    },
    [rfInstance, addNode]
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
    <div
      className="h-full w-full relative outline-none"
      ref={reactFlowWrapper}
      tabIndex={0}
      style={{
        minHeight: '400px',
        perspective: '2000px',
        perspectiveOrigin: '50% 50%',
      }}
    >
      <div
        className={`relative h-full w-full transition-all duration-700 ease-out`}
        style={{
          transformStyle: 'preserve-3d',
          transform: isMemoryLayerTilted
            ? 'rotateX(30deg) translateZ(0) scale(0.95)'
            : 'rotateX(0deg) translateZ(0) scale(1)',
        }}
      >
      {/* Main diagram layer */}
      <div className="absolute inset-0" style={{ transform: 'translateZ(0px)' }}>
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
          className={`bg-gradient-to-br from-slate-50 to-sky-100 transition-opacity duration-700 ${
            isMemoryLayerTilted ? 'opacity-90' : 'opacity-100'
          }`}
          style={{ width: '100%', height: '100%' }}
        >
          <Controls />
          <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
        </ReactFlow>
      </div>
      <div
        className={`absolute inset-0 transition-all duration-700 ${
          isMemoryLayerTilted ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        style={{
          transform: 'translateZ(-200px)',
        }}
      >
        <Suspense fallback={<MemoryLayerSkeleton />}>
          <MemoryLayer />
        </Suspense>
      </div>
      {isOpen && contextMenu.position && (
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
      )}
    </div>
  </div>
  );
}

export default DiagramCanvas;
