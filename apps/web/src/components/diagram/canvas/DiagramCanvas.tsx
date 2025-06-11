import React, {
  Suspense,
  useCallback,
  useMemo,
  useRef,
  useState,
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
import { useDiagram } from "@/hooks";
import ContextMenu from "../controls/ContextMenu";
import { CustomArrow as CustomArrowBase } from "../arrows/CustomArrow";
import nodeTypes from "../nodes/nodeTypes";
import { DomainArrow, arrowToReact, nodeId, arrowId } from "@/types";

// Lazy‑loaded tabs
const PropertiesTab = React.lazy(
  () => import("@/components/properties/PropertiesTab")
);
const ConversationTab = React.lazy(
  () => import("@/components/conversation/ConversationTab")
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
      // Ensure nodes are draggable and selectable
      nodesDraggable: true,
      nodesConnectable: true,
      nodesFocusable: true,
      elementsSelectable: true,
      panOnDrag: true,
      panOnScroll: false,
      zoomOnScroll: true,
      zoomOnPinch: true,
      zoomOnDoubleClick: true,
    } as const;

    return {
      ...baseProps,
      onNodeClick: (_: React.MouseEvent, n: ReactFlowNode) => selectNode(n.id),
      onEdgeClick: (_: React.MouseEvent, e: Edge) => selectArrow(e.id),
      onNodeContextMenu: (
        event: React.MouseEvent,
        node: ReactFlowNode
      ) => {
        selectNode(node.id);
        onNodeContextMenu?.(event, node.id);
      },
      onEdgeContextMenu: (
        event: React.MouseEvent,
        edge: Edge
      ) => {
        selectArrow(edge.id);
        onEdgeContextMenu?.(event, edge.id);
      },
      onPaneContextMenu: (evt: React.MouseEvent | MouseEvent) => {
        clearSelection();
        if (evt && 'preventDefault' in evt) {
          onPaneContextMenu?.(evt as React.MouseEvent);
        }
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
  ]);
}

const DiagramCanvas: React.FC<DiagramCanvasProps> = ({ executionMode = false }) => {
  /** --------------------------------------------------
   * Stores & Hooks
   * --------------------------------------------------*/
  const {
    // diagram state & callbacks
    nodes,
    arrows,
    onNodesChange,
    onArrowsChange,
    onConnect,
    onDragOver,
    onNodeDrop,
    onNodeContextMenu,
    onEdgeContextMenu,
    onPaneContextMenu,
    // node/edge utils
    addNode,
    addPerson,
    deleteNode,
    deleteArrow,
    selectedNodeId,
    selectedArrowId,
    selectNode,
    selectArrow,
    contextMenu,
    isContextMenuOpen,
    closeContextMenu,
    clearSelection,
  } = useDiagram({ enableInteractions: true, enableFileOperations: true });


  /** --------------------------------------------------
   * React Flow instance helpers
   * --------------------------------------------------*/
  const flowWrapperRef = useRef<HTMLDivElement>(null);
  const [rfInstance, setRfInstance] = useState<ReactFlowInstance | null>(null);
  const handleInit = (inst: ReactFlowInstance) => setRfInstance(inst);

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
    selectNode,
    selectArrow,
    executionMode,
    clearSelection,
  });

  /** --------------------------------------------------
   * Context‑menu helpers
   * --------------------------------------------------*/
  const handleAddPerson = () => addPerson({ 
    label: "New Person",
    model: "gpt-4.1-nano",
    service: "openai"
  });
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
          onAddNode={addNode}
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
              <ReactFlow {...flowProps} onInit={handleInit} />
              <Controls />
              <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
              {renderContextMenu()}
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
              <ReactFlow {...flowProps} onInit={handleInit} />
              <Controls />
              <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
              {renderContextMenu()}
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