/**
 * Custom Node Component for Diagram Viewer
 *
 * Simplified read-only node display for ChatGPT widgets
 */

import { Handle, Position, NodeProps } from '@xyflow/react';
import { getNodeColor, getNodeDisplayName } from '../../utils/diagram-converter';

export function CustomNode({ data, type }: NodeProps) {
  const nodeType = type || 'default';
  const color = getNodeColor(nodeType);
  const displayName = getNodeDisplayName(nodeType);
  const label = String(data.label || displayName);

  return (
    <div
      className="px-4 py-2 rounded-lg border-2 shadow-sm bg-white min-w-[120px]"
      style={{ borderColor: color }}
    >
      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3"
        style={{ background: color }}
      />

      {/* Node Content */}
      <div className="flex flex-col gap-1">
        <div
          className="text-xs font-medium uppercase tracking-wide"
          style={{ color }}
        >
          {displayName}
        </div>
        <div className="text-sm font-semibold text-gray-900">{label}</div>
      </div>

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3"
        style={{ background: color }}
      />
    </div>
  );
}

/**
 * Node types registry for XYFlow
 */
export const nodeTypes = {
  default: CustomNode,
  start: CustomNode,
  end: CustomNode,
  person_job: CustomNode,
  llm_call: CustomNode,
  code_execution: CustomNode,
  conditional: CustomNode,
  loop: CustomNode,
  data_transform: CustomNode,
  webhook: CustomNode,
};
