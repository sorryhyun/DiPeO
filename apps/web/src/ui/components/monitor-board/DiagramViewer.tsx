import React, { useMemo, useEffect, useState } from 'react';
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  Controls,
  MarkerType,
  Node as ReactFlowNode,
  Edge,
  ReactFlowInstance,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import nodeTypes from '@/ui/components/diagram/nodes/nodeTypes';
import { CustomArrow } from '@/ui/components/diagram/CustomArrow';
import type { StoreApi } from 'zustand';
import type { ExecutionLocalStore } from './executionLocalStore';

const edgeTypes = {
  customArrow: CustomArrow,
};

interface DiagramViewerProps {
  store: StoreApi<ExecutionLocalStore>;
  readOnly?: boolean;
}

export function DiagramViewer({ store, readOnly = true }: DiagramViewerProps) {
  const [rfInstance, setRfInstance] = useState<ReactFlowInstance | null>(null);
  const [nodes, setNodes] = useState<ReactFlowNode[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  // Subscribe to store changes
  useEffect(() => {
    const updateDiagram = (state: ExecutionLocalStore) => {
      // Convert store nodes to ReactFlow nodes
      const rfNodes: ReactFlowNode[] = (state.nodes || []).map((node: any) => {
        const nodeState = state.nodeStates.get(node.id);
        const isRunning = state.runningNodes.has(node.id);
        
        // Add execution state styling
        const nodeStyle: React.CSSProperties = {};
        let className = '';
        
        if (isRunning) {
          className = 'node-running';
          nodeStyle.animation = 'pulse-blue 2s infinite';
        } else if (nodeState) {
          switch (nodeState.status) {
            case 'completed':
              className = 'node-completed';
              nodeStyle.borderColor = '#10b981';
              nodeStyle.borderWidth = 2;
              break;
            case 'failed':
              className = 'node-failed';
              nodeStyle.borderColor = '#ef4444';
              nodeStyle.borderWidth = 2;
              break;
            case 'skipped':
              className = 'node-skipped';
              nodeStyle.opacity = 0.5;
              break;
          }
        }

        return {
          id: node.id,
          type: node.type,
          position: node.position || { x: 0, y: 0 },
          data: {
            ...node.data,
            readOnly: true,
            executionState: nodeState,
            isRunning,
          },
          style: nodeStyle,
          className,
          draggable: false,
        };
      });

      // Convert store edges to ReactFlow edges
      const rfEdges: Edge[] = (state.edges || []).map((edge: any) => ({
        id: edge.id || `${edge.source}-${edge.target}`,
        source: edge.source,
        target: edge.target,
        type: 'customArrow',
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 20,
          height: 20,
        },
        data: edge.data,
      }));

      setNodes(rfNodes);
      setEdges(rfEdges);
    };

    // Subscribe to future changes
    const unsubscribe = store.subscribe(updateDiagram);
    
    // Apply initial state immediately
    updateDiagram(store.getState());

    return unsubscribe;
  }, [store]);

  // Fit view when diagram is loaded
  useEffect(() => {
    if (rfInstance && nodes.length > 0) {
      requestAnimationFrame(() => {
        void rfInstance.fitView({ padding: 0.2, duration: 200 });
      });
    }
  }, [rfInstance, nodes.length]);

  return (
    <div className="h-full w-full relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onInit={setRfInstance}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        panOnDrag={true}
        zoomOnScroll={true}
        fitView
        fitViewOptions={{ padding: 0.2 }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={16}
          size={1}
          color="#374151"
        />
        <Controls
          position="bottom-right"
          showInteractive={false}
        />
      </ReactFlow>
      
      {/* Add pulse animation styles */}
      <style>{`
        @keyframes pulse-blue {
          0%, 100% {
            box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7);
          }
          50% {
            box-shadow: 0 0 0 10px rgba(59, 130, 246, 0);
          }
        }
        
        .node-running {
          border-color: #3b82f6 !important;
          border-width: 2px !important;
          box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
        }
        
        .node-completed {
          background-color: rgba(16, 185, 129, 0.1) !important;
        }
        
        .node-failed {
          background-color: rgba(239, 68, 68, 0.1) !important;
        }
      `}</style>
    </div>
  );
}