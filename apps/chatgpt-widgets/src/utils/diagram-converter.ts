/**
 * Diagram Converter for ChatGPT Widgets
 *
 * Simplified converter from DiPeO diagram format to XYFlow format
 * Read-only viewer - no editing or validation needed
 */

import type { Node, Edge } from '@xyflow/react';
import type { ListDiagramsQuery } from '../__generated__/graphql';

type DiagramNode = NonNullable<ListDiagramsQuery['listDiagrams']>[0]['nodes'][0];
type DiagramArrow = NonNullable<ListDiagramsQuery['listDiagrams']>[0]['arrows'][0];

/**
 * Convert DiPeO diagram to XYFlow format
 */
export function convertDiagramToFlow(
  nodes: DiagramNode[],
  arrows: DiagramArrow[]
): { nodes: Node[]; edges: Edge[] } {
  const flowNodes: Node[] = nodes.map((node) => ({
    id: node.id,
    type: node.type || 'default',
    position: node.position || { x: 0, y: 0 },
    data: {
      label: node.data?.label || node.id,
      ...node.data,
    },
  }));

  const flowEdges: Edge[] = arrows.map((arrow) => {
    // Parse handle IDs to extract source/target node IDs
    // Format: nodeId_label_direction (e.g., "node_1_output_OUTPUT")
    const sourceNode = arrow.source.split('_')[0] + '_' + arrow.source.split('_')[1];
    const targetNode = arrow.target.split('_')[0] + '_' + arrow.target.split('_')[1];

    return {
      id: arrow.id,
      source: sourceNode,
      target: targetNode,
      sourceHandle: arrow.source,
      targetHandle: arrow.target,
      type: 'smoothstep',
      animated: false,
      data: {
        label: arrow.label,
        content_type: arrow.content_type,
        ...arrow.data,
      },
    };
  });

  return { nodes: flowNodes, edges: flowEdges };
}

/**
 * Get node color based on type
 */
export function getNodeColor(nodeType: string): string {
  const colorMap: Record<string, string> = {
    start: '#10b981', // green
    end: '#ef4444', // red
    person_job: '#3b82f6', // blue
    llm_call: '#8b5cf6', // purple
    code_execution: '#f59e0b', // amber
    conditional: '#ec4899', // pink
    loop: '#06b6d4', // cyan
    data_transform: '#14b8a6', // teal
    webhook: '#f97316', // orange
  };

  return colorMap[nodeType] || '#6b7280'; // default gray
}

/**
 * Get node display name
 */
export function getNodeDisplayName(nodeType: string): string {
  const nameMap: Record<string, string> = {
    start: 'Start',
    end: 'End',
    person_job: 'Person Job',
    llm_call: 'LLM Call',
    code_execution: 'Code Execution',
    conditional: 'Conditional',
    loop: 'Loop',
    data_transform: 'Data Transform',
    webhook: 'Webhook',
  };

  return nameMap[nodeType] || nodeType;
}
