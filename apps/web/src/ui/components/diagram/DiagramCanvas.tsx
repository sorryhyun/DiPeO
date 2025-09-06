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
import { useCanvasState, useCanvasOperations } from "@/domain/diagram/contexts";
import { useUnifiedStore } from "@/infrastructure/store/unifiedStore";
import { CustomArrow as CustomArrowBase } from "./CustomArrow";
import nodeTypes from "./nodes/nodeTypes";
import { DomainArrow, arrowId, nodeId, PersonID, NodeType } from '@/infrastructure/types';
import { DiagramAdapter } from '@/domain/diagram/adapters/DiagramAdapter';

const PropertiesTab = React.lazy(
  () => import("@/ui/components/diagram/properties/PropertiesTab")
);
const ConversationTab = React.lazy(
  () => import("@/ui/components/conversation/ConversationTab")
);

const edgeTypes: EdgeTypes = {
  customArrow: CustomArrowBase,
};

interface DiagramCanvasProps {
  executionMode?: boolean;
}

const roundPosition = (position: { x: number; y: number }) => {
  return {
    x: Math.round(position.x / 10) * 10,
    y: Math.round(position.y / 10) * 10,
  };
};

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
    const edges = arrows.map(arrow => DiagramAdapter.arrowToReactFlow(arrow)) as Edge[];

    const baseProps = {
      fitView: false,
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
      nodesDraggable: !readOnly && !isExecuting,
      nodesConnectable: !readOnly && !isExecuting,
      nodesFocusable: true,
      elementsSelectable: true,
      panOnDrag: true,
      panOnScroll: false,
      zoomOnScroll: true,
      zoomOnPinch: true,
      zoomOnDoubleClick: true,
      nodeDragThreshold: 0,
      selectNodesOnDrag: false,
    } as const;

    return {
      ...baseProps,
      onNodeClick: (event: React.MouseEvent, n: ReactFlowNode) => {
        selectNode(n.id);
        highlightPerson(null);
      },
      onEdgeClick: (event: React.MouseEvent, e: Edge) => {
        selectArrow(e.id);
      },
      onNodeDragStart,
      onNodeDragStop,
      onNodeContextMenu: (
        event: React.MouseEvent,
        node: ReactFlowNode
      ) => {
        event.preventDefault();
        selectNode(node.id);
        setDashboardTab('properties');

        if (node.type === NodeType.PERSON_JOB && node.data.person) {
          highlightPerson(node.data.person as PersonID);
        } else {
          highlightPerson(null);
        }
      },
      onEdgeContextMenu: (
        event: React.MouseEvent,
        edge: Edge
      ) => {
        event.preventDefault();
        selectArrow(edge.id);
        setDashboardTab('properties');
      },
      onPaneContextMenu: (evt: React.MouseEvent | MouseEvent) => {
        if (evt && 'preventDefault' in evt) {
          evt.preventDefault();
        }
        clearSelection();
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
  const state = useCanvasState();
  const operations = useCanvasOperations();

  const { nodes, arrows, onNodesChange, onArrowsChange, onConnect } = operations.canvasHandlers;

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

  const highlightPerson = useUnifiedStore(state => state.highlightPerson);
  const setDashboardTab = useUnifiedStore(state => state.setDashboardTab);

  const flowWrapperRef = useRef<HTMLDivElement>(null);
  const [rfInstance, setRfInstance] = useState<ReactFlowInstance | null>(null);

  const setViewport = useUnifiedStore(state => state.setViewport);

  const handleInit = (inst: ReactFlowInstance) => {
    setRfInstance(inst);
    const viewport = inst.getViewport();
    setViewport(viewport.zoom, { x: viewport.x, y: viewport.y });
  };

  const hasFitView = useRef(false);
  const prevNodeCount = useRef(0);

  useEffect(() => {
    if (rfInstance && nodes.length > 0 && prevNodeCount.current === 0 && !hasFitView.current) {
      hasFitView.current = true;
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          rfInstance.fitView({ padding: 0.3, duration: 0, maxZoom: 0.8 });
        });
      });
    }
    prevNodeCount.current = nodes.length;
  }, [nodes.length, rfInstance]);

  // TODO: Implement proper viewport synchronization without causing re-render loops
  const handleViewportChange = useCallback((_viewport: { x: number; y: number; zoom: number }) => {
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

  const handleAddPerson = () => addPerson(
    "New Person",
    "openai",
    "gpt-4.1-nano"
  );
  const showContextMenu = isContextMenuOpen && contextMenu?.position;

  return (
    <div className="h-full flex flex-col">
      {executionMode ? (
        <PanelGroup direction="vertical">
          <Panel defaultSize={70} minSize={20}>
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
