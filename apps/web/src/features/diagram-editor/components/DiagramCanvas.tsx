import React, {
  Suspense,
  useCallback,
  useMemo,
  useRef,
  useState,
  useEffect,
} from "react";
import {
  Background,
  BackgroundVariant,
  Controls,
  Edge,
  EdgeTypes,
  MarkerType,
  Node as ReactFlowNode,
  ReactFlow,
  NodeChange,
  EdgeChange,
  Connection,
  ReactFlowInstance,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import "@xyflow/react/dist/base.css";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { FileText } from "lucide-react";
import { useCanvasContext } from "../contexts/CanvasContext";
import { useUnifiedStore } from "@/core/store/unifiedStore";
import ContextMenu from "./controls/ContextMenu";
import { CustomArrow as CustomArrowBase } from "./CustomArrow";
import nodeTypes from "./nodes/nodeTypes";
import { DomainArrow, arrowId, nodeId } from '@/core/types';
import { NodeType } from '@dipeo/domain-models';
import { arrowToReact } from '@/features/diagram-editor/adapters/DiagramAdapter';

// Lazy‑loaded tabs
const PropertiesTab = React.lazy(
  () => import("@/features/properties-editor/components/PropertiesTab")
);
const ConversationTab = React.lazy(
  () => import("@/features/conversation/components/ConversationTab")
);

// Edge type map
const edgeTypes: EdgeTypes = {
  customArrow: CustomArrowBase,
};

interface DiagramCanvasProps {
  /** When true, the property panel is hidden & execution‑mode colours are used */
  executionMode?: boolean;
}

const roundPosition = (position: { x: number; y: number }) => {
  return {
    x: Math.round(position.x / 10) * 10,
    y: Math.round(position.y / 10) * 10,
  };
};

/**
 * Single source of truth for *all* ReactFlow props we pass around.
 * Keeping them in one object avoids prop‑list drift between the two
 * ReactFlow instances that used to live in this file.
 */
interface CommonFlowPropsParams {
  nodes: ReactFlowNode[];
  arrows: DomainArrow[];
  onNodesChange: (changes: NodeChange[]) => void;
  onArrowsChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;
  onNodeContextMenu?: (event: React.MouseEvent, nodeId: string) => void;
  onEdgeContextMenu?: (event: React.MouseEvent, edgeId: string) => void;
  onPaneContextMenu?: (event: React.MouseEvent) => void;
  onDragOver?: React.DragEventHandler;
  onDrop: React.DragEventHandler<HTMLElement>;
  onNodeDragStart?: (event: React.MouseEvent, node: ReactFlowNode) => void;
  onNodeDragStop?: (event: React.MouseEvent, node: ReactFlowNode) => void;
  selectNode: (id: string) => void;
  selectArrow: (id: string) => void;
  executionMode: boolean;
  clearSelection: () => void;
}

function useCommonFlowProps({
  nodes,
  arrows,
  onNodesChange,
  onArrowsChange,
  onConnect,
  onNodeContextMenu,
  onEdgeContextMenu,
  onPaneContextMenu,
  onDragOver,
  onDrop,
  onNodeDragStart,
  onNodeDragStop,
  selectNode,
  selectArrow,
  executionMode,
  clearSelection,
}: CommonFlowPropsParams) {
  return useMemo(() => {
    // Convert handle-based arrows to ReactFlow edges
    const edges = arrows.map(arrow => arrowToReact(arrow)) as Edge[];
    
    const baseProps = {
      fitView: true,
      nodes,
      edges,
      connectionLineStyle: { stroke: "#3b82f6", strokeWidth: 2 },
      defaultEdgeOptions: {
        type: "customArrow" as const,
        markerEnd: { type: MarkerType.ArrowClosed },
      },
      nodeTypes,
      edgeTypes,
      onNodesChange,
      onEdgesChange: onArrowsChange,
      onConnect,
      onPaneClick: () => {
        clearSelection();
      },
      onDragOver: onDragOver ?? undefined,
      onDrop,
      // Enable node dragging (we'll control which button in the node component)
      nodesDraggable: true,
      nodesConnectable: true,
      nodesFocusable: true,
      elementsSelectable: true,
      panOnDrag: true, // Use left mouse button with space/cmd key for panning
      panOnScroll: false,
      zoomOnScroll: true,
      zoomOnPinch: true,
      zoomOnDoubleClick: true,
      // Remove drag threshold for immediate interaction
      nodeDragThreshold: 0,
      selectNodesOnDrag: false,
      // Prevent delay on selection
      // connectionMode: 'loose', // Removed due to type incompatibility
    } as const;

    return {
      ...baseProps,
      onNodeClick: (_: React.MouseEvent, n: ReactFlowNode) => selectNode(n.id),
      onEdgeClick: (_: React.MouseEvent, e: Edge) => selectArrow(e.id),
      onNodeDragStart,
      onNodeDragStop,
      onNodeContextMenu: (
        event: React.MouseEvent,
        node: ReactFlowNode
      ) => {
        event.preventDefault();
        selectNode(node.id);
        // Disable context menu
        // onNodeContextMenu?.(event, node.id);
      },
      onEdgeContextMenu: (
        event: React.MouseEvent,
        edge: Edge
      ) => {
        event.preventDefault();
        selectArrow(edge.id);
        // Disable context menu
        // onEdgeContextMenu?.(event, edge.id);
      },
      onPaneContextMenu: (evt: React.MouseEvent | MouseEvent) => {
        if (evt && 'preventDefault' in evt) {
          evt.preventDefault();
        }
        clearSelection();
        // Disable context menu
        // if (evt && 'preventDefault' in evt) {
        //   onPaneContextMenu?.(evt as React.MouseEvent);
        // }
      },
      className: executionMode ? "bg-gray-900" : "bg-gradient-to-br from-slate-50 to-sky-100",
    } satisfies Parameters<typeof ReactFlow>[0];
  }, [
    arrows,
    clearSelection,
    executionMode,
    nodes,
    onArrowsChange,
    onConnect,
    onDragOver,
    onDrop,
    onNodeContextMenu,
    onEdgeContextMenu,
    onNodesChange,
    onPaneContextMenu,
    selectArrow,
    selectNode,
    onNodeDragStart,
    onNodeDragStop,
  ]);
}

const DiagramCanvas: React.FC<DiagramCanvasProps> = ({ executionMode = false }) => {
  /** --------------------------------------------------
   * Stores & Hooks
   * --------------------------------------------------*/
  const context = useCanvasContext();
  
  // Extract from canvas hook
  const { nodes, arrows, onNodesChange, onArrowsChange, onConnect } = context.canvas;
  
  // Extract from interactions hook
  const {
    onDragOver,
    onNodeDrop,
    onNodeContextMenu,
    onEdgeContextMenu,
    onPaneContextMenu,
    contextMenu,
    isContextMenuOpen,
    closeContextMenu,
    onNodeDragStartCanvas,
    onNodeDragStopCanvas,
  } = context.interactions;
  
  // Extract from operation hooks
  const { addNode, deleteNode } = context.nodeOps;
  const { deleteArrow } = context.arrowOps;
  const { addPerson } = context.personOps;
  
  const {
    selectedNodeId,
    selectedArrowId,
    selectNode,
    selectArrow,
    clearSelection,
  } = context;

  /** --------------------------------------------------
   * React Flow instance helpers
   * --------------------------------------------------*/
  const flowWrapperRef = useRef<HTMLDivElement>(null);
  const [rfInstance, setRfInstance] = useState<ReactFlowInstance | null>(null);
  
  // Get viewport operations from store
  const setViewport = useUnifiedStore(state => state.setViewport);
  const setZoom = useUnifiedStore(state => state.setZoom);
  const setPosition = useUnifiedStore(state => state.setPosition);
  
  const handleInit = (inst: ReactFlowInstance) => {
    setRfInstance(inst);
    // Sync initial viewport
    const viewport = inst.getViewport();
    setViewport(viewport.zoom, { x: viewport.x, y: viewport.y });
  };
  
  // Handle viewport changes - commented out to prevent infinite loops
  // TODO: Implement proper viewport synchronization without causing re-render loops
  const handleViewportChange = useCallback((_viewport: { x: number; y: number; zoom: number }) => {
    // Temporarily disabled to prevent infinite loops
    // The viewport state is not critical for functionality
  }, []);

  const projectPosition = useCallback(
    (x: number, y: number) => {
      if (!flowWrapperRef.current || !rfInstance) return { x: 0, y: 0 };
      return roundPosition(rfInstance.screenToFlowPosition({ x, y }));
    },
    [rfInstance]
  );

  const onDrop = useCallback(
    (evt: React.DragEvent) => {
      if (!rfInstance) return;
      onNodeDrop?.(evt, projectPosition);
    },
    [onNodeDrop, projectPosition, rfInstance]
  );

  /** --------------------------------------------------
   * Memoised ReactFlow props shared by both modes
   * --------------------------------------------------*/
  const flowProps = useCommonFlowProps({
    nodes,
    arrows,
    onNodesChange,
    onArrowsChange,
    onConnect,
    onNodeContextMenu,
    onEdgeContextMenu,
    onPaneContextMenu,
    onDragOver,
    onDrop,
    onNodeDragStart: onNodeDragStartCanvas,
    onNodeDragStop: onNodeDragStopCanvas,
    selectNode: (id: string) => selectNode(nodeId(id)),
    selectArrow: (id: string) => selectArrow(arrowId(id)),
    executionMode,
    clearSelection,
  });

  /** --------------------------------------------------
   * Context‑menu helpers
   * --------------------------------------------------*/
  const handleAddPerson = () => addPerson(
    "New Person",
    "openai",
    "gpt-4.1-nano"
  );
  const showContextMenu = isContextMenuOpen && contextMenu?.position;

  /** --------------------------------------------------
   * Render helpers
   * --------------------------------------------------*/
  const renderContextMenu = () =>
    showContextMenu && (
      <Suspense fallback={null}>
        <ContextMenu
          position={contextMenu!.position!}
          target={contextMenu!.target || "pane"}
          selectedNodeId={selectedNodeId ? nodeId(selectedNodeId) : null}
          selectedArrowId={selectedArrowId ? arrowId(selectedArrowId) : null}
          containerRef={flowWrapperRef as React.RefObject<HTMLDivElement>}
          onAddNode={(type, position) => addNode(type, position)}
          onAddPerson={handleAddPerson}
          onDeleteNode={deleteNode}
          onDeleteArrow={deleteArrow}
          onClose={closeContextMenu!}
          projectPosition={projectPosition}
        />
      </Suspense>
    );

  /** --------------------------------------------------
   * JSX
   * --------------------------------------------------*/
  return (
    <div className="h-full flex flex-col">
      {executionMode ? (
        // Execution mode: Split view with diagram and conversation
        <PanelGroup direction="vertical">
          <Panel defaultSize={40} minSize={20}>
            {/* Diagram view in execution mode */}
            <div ref={flowWrapperRef} tabIndex={0} className="relative h-full w-full outline-none" style={{ minHeight: "200px" }}>
              <ReactFlow {...flowProps} onInit={handleInit} onViewportChange={handleViewportChange} />
              <Controls />
              <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
              {/* Context menu disabled */}
              {/* {renderContextMenu()} */}
            </div>
          </Panel>
          <PanelResizeHandle className="h-1 bg-gray-200 hover:bg-gray-300 cursor-row-resize" />
          <Panel defaultSize={60} minSize={30}>
            {/* Conversation view */}
            <div className="h-full bg-white">
              <Suspense
                fallback={
                  <div className="h-full flex items-center justify-center text-gray-500 animate-pulse">
                    Loading conversation view...
                  </div>
                }
              >
                <ConversationTab />
              </Suspense>
            </div>
          </Panel>
        </PanelGroup>
      ) : (
        // Non-execution mode: Show diagram canvas with properties panel
        <PanelGroup direction="vertical">
          <Panel defaultSize={65} minSize={30}>
            <div ref={flowWrapperRef} tabIndex={0} className="relative h-full w-full outline-none" style={{ minHeight: "400px" }}>
              <ReactFlow {...flowProps} onInit={handleInit} onViewportChange={handleViewportChange} />
              <Controls />
              <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
              {/* Context menu disabled */}
              {/* {renderContextMenu()} */}
            </div>
          </Panel>
          <PanelResizeHandle className="h-1 bg-gray-200 hover:bg-gray-300 cursor-row-resize" />
          <Panel defaultSize={35} minSize={20}>
            {/* Properties panel only shown in non-execution mode */}
            <div className="h-full bg-white flex flex-col">
              <div className="flex border-b bg-gray-50">
                <div className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-white border-b-2 border-blue-500 text-blue-600">
                  <FileText className="w-4 h-4" /> Properties
                </div>
              </div>
              <div className="flex-1 overflow-hidden">
                <Suspense
                  fallback={
                    <div className="h-full flex items-center justify-center text-gray-500 animate-pulse">
                      Loading…
                    </div>
                  }
                >
                  <PropertiesTab />
                </Suspense>
              </div>
            </div>
          </Panel>
        </PanelGroup>
      )}
    </div>
  );
};

export default React.memo(DiagramCanvas);