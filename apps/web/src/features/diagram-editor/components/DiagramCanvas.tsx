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
import { useCanvasState, useCanvasOperations } from "@/shared/contexts/CanvasContext";
import { useUnifiedStore } from "@/core/store/unifiedStore";
import { CustomArrow as CustomArrowBase } from "./CustomArrow";
import nodeTypes from "./nodes/nodeTypes";
import { DomainArrow, arrowId, nodeId, PersonID } from '@/core/types';
import { DiagramAdapter } from '@/features/diagram-editor/adapters/DiagramAdapter';

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
  highlightPerson: (personId: PersonID | null) => void;
  setDashboardTab: (tab: 'properties' | 'persons' | 'settings' | 'history') => void;
  readOnly: boolean;
  isExecuting: boolean;
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
  highlightPerson,
  setDashboardTab,
  readOnly,
  isExecuting,
}: CommonFlowPropsParams) {
  return useMemo(() => {
    // Convert handle-based arrows to ReactFlow edges
    const edges = arrows.map(arrow => DiagramAdapter.arrowToReactFlow(arrow)) as Edge[];
    
    const baseProps = {
      fitView: false, // We'll handle fitView manually
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
      // Control interactivity based on read-only state
      nodesDraggable: !readOnly && !isExecuting,
      nodesConnectable: !readOnly && !isExecuting,
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
    } as const;

    return {
      ...baseProps,
      onNodeClick: (event: React.MouseEvent, n: ReactFlowNode) => {
        // Enable left-click selection for all nodes
        selectNode(n.id);
        // Clear highlight on any left-click
        highlightPerson(null);
      },
      onEdgeClick: (event: React.MouseEvent, e: Edge) => {
        // Enable left-click selection for edges/arrows
        selectArrow(e.id);
      },
      onNodeDragStart,
      onNodeDragStop,
      onNodeContextMenu: (
        event: React.MouseEvent,
        node: ReactFlowNode
      ) => {
        event.preventDefault();
        // Select node and show properties on right-click
        selectNode(node.id);
        // Ensure properties tab is shown
        setDashboardTab('properties');
        
        // If it's a person_job node, highlight which person it's assigned to
        if (node.type === 'person_job' && node.data.person) {
          highlightPerson(node.data.person as PersonID);
        } else {
          // Clear highlight for other node types
          highlightPerson(null);
        }
      },
      onEdgeContextMenu: (
        event: React.MouseEvent,
        edge: Edge
      ) => {
        event.preventDefault();
        // Select arrow and show properties on right-click
        selectArrow(edge.id);
        // Ensure properties tab is shown
        setDashboardTab('properties');
      },
      onPaneContextMenu: (evt: React.MouseEvent | MouseEvent) => {
        if (evt && 'preventDefault' in evt) {
          evt.preventDefault();
        }
        clearSelection();
        // Clear person highlight when clicking on empty canvas
        highlightPerson(null);
      },
      className: executionMode ? "bg-neutral-900" : "diagram-canvas",
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
    highlightPerson,
    setDashboardTab,
    readOnly,
    isExecuting,
  ]);
}

const DiagramCanvas: React.FC<DiagramCanvasProps> = ({ executionMode = false }) => {
   // Stores & Hooks
  const state = useCanvasState();
  const operations = useCanvasOperations();
  
  // Extract from canvas hook
  const { nodes, arrows, onNodesChange, onArrowsChange, onConnect } = operations.canvasHandlers;
  
  // Extract from interactions hook
  const {
    onDragOver,
    onNodeDrop,
    onNodeContextMenu,
    onEdgeContextMenu,
    onPaneContextMenu,
    contextMenu,
    isContextMenuOpen,
    closeContextMenu: _closeContextMenu,
    onNodeDragStartCanvas,
    onNodeDragStopCanvas,
  } = operations.interactions;
  
  // Extract from operation hooks
  const { addNode: _addNode, deleteNode: _deleteNode } = operations.nodeOps;
  const { deleteArrow: _deleteArrow } = operations.arrowOps;
  const { addPerson } = operations.personOps;
  
  const {
    selectedNodeId,
    selectedArrowId,
    selectedPersonId,
    readOnly,
    isExecuting,
  } = state;
  const {
    selectNode,
    selectArrow,
    clearSelection,
  } = operations;
  
  // Get store methods directly (not inside useMemo) to avoid cross-slice issues
  const highlightPerson = useUnifiedStore(state => state.highlightPerson);
  const setDashboardTab = useUnifiedStore(state => state.setDashboardTab);

   // React Flow instance helpers
  const flowWrapperRef = useRef<HTMLDivElement>(null);
  const [rfInstance, setRfInstance] = useState<ReactFlowInstance | null>(null);
  
  // Get viewport operations from store
  const setViewport = useUnifiedStore(state => state.setViewport);
  
  const handleInit = (inst: ReactFlowInstance) => {
    setRfInstance(inst);
    // Sync initial viewport
    const viewport = inst.getViewport();
    setViewport(viewport.zoom, { x: viewport.x, y: viewport.y });
  };
  
  // Track if we've fit the view and the previous node count
  const hasFitView = useRef(false);
  const prevNodeCount = useRef(0);
  
  // Fit view when nodes are loaded from URL
  useEffect(() => {
    if (rfInstance && nodes.length > 0 && prevNodeCount.current === 0 && !hasFitView.current) {
      const urlParams = new URLSearchParams(window.location.search);
      if (urlParams.has('diagram')) {
        hasFitView.current = true;
        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            rfInstance.fitView({ padding: 0.3, duration: 0, maxZoom: 0.8 });
          });
        });
      }
    }
    prevNodeCount.current = nodes.length;
  }, [nodes.length, rfInstance]);
  
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
    highlightPerson,
    setDashboardTab,
    readOnly,
    isExecuting,
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

  //* JSX
  return (
    <div className="h-full flex flex-col">
      {executionMode ? (
        // Execution mode: Split view with diagram and conversation
        <PanelGroup direction="vertical">
          <Panel defaultSize={70} minSize={20}>
            {/* Diagram view in execution mode */}
            <div ref={flowWrapperRef} tabIndex={0} className="relative h-full w-full outline-none" style={{ minHeight: "200px" }}>
              <ReactFlow {...flowProps} defaultViewport={{ x: 0, y: 0, zoom: 0.85 }} onInit={handleInit} onViewportChange={handleViewportChange} />
              <Controls />
              <Background 
                variant={BackgroundVariant.Dots} 
                gap={16} 
                size={1.5}
                className="opacity-[0.03]"
                color="currentColor"
              />
            </div>
          </Panel>
          <PanelResizeHandle className="h-1 bg-gray-200 hover:bg-gray-300 cursor-row-resize" />
          <Panel defaultSize={30} minSize={25}>
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
              <ReactFlow {...flowProps} defaultViewport={{ x: 0, y: 0, zoom: 0.85 }} onInit={handleInit} onViewportChange={handleViewportChange} />
              <Controls />
              <Background 
                variant={BackgroundVariant.Dots} 
                gap={16} 
                size={1.5}
                className="opacity-[0.03]"
                color="currentColor"
              />
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