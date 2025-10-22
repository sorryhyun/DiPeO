/**
 * Diagram Viewer Component
 *
 * Read-only XYFlow diagram visualization for ChatGPT widgets
 */

import { ReactFlow, Background, Controls, MiniMap } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { convertDiagramToFlow, getNodeColor } from '../../utils/diagram-converter';
import { nodeTypes } from './CustomNode';
import type { ListDiagramsQuery } from '../../__generated__/graphql';

interface DiagramViewerProps {
  diagram: NonNullable<ListDiagramsQuery['listDiagrams']>[0];
  height?: string;
}

export function DiagramViewer({ diagram, height = '400px' }: DiagramViewerProps) {
  const { nodes, edges } = convertDiagramToFlow(
    diagram.nodes || [],
    diagram.arrows || []
  );

  return (
    <div style={{ height, width: '100%' }} className="border border-gray-200 rounded-lg overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-right"
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={true}
        panOnDrag={true}
        zoomOnScroll={true}
        zoomOnPinch={true}
        minZoom={0.1}
        maxZoom={2}
        defaultEdgeOptions={{
          type: 'smoothstep',
          animated: false,
        }}
      >
        <Background color="#e5e7eb" gap={16} />
        <Controls showInteractive={false} />
        <MiniMap
          nodeColor={(node) => {
            const type = node.type || 'default';
            return getNodeColor(type);
          }}
          maskColor="rgba(0, 0, 0, 0.1)"
          position="bottom-left"
          style={{ width: 100, height: 80 }}
        />
      </ReactFlow>
    </div>
  );
}
