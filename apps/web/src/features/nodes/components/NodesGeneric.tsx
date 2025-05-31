// apps/web/src/components/nodes/NodesGeneric.tsx

import React, { Suspense } from 'react';
import { NodeProps } from '@xyflow/react';
import { GenericNode } from './BaseNode';
import { UNIFIED_NODE_CONFIGS } from '@/shared/types';
import { StartNode, ConditionNode, JobNode, DBNode, EndpointNode, PersonJobNode } from './nodes';

// Loading component for lazy-loaded nodes
const NodeLoadingFallback: React.FC<NodeProps> = ({ id, data, selected }) => (
  <GenericNode id={id} data={data} selected={selected} nodeType="defaultNode">
    <span className="text-gray-400">Loading...</span>
  </GenericNode>
);

// Map of node types to their lazy-loaded components
const nodeComponents: Record<string, React.LazyExoticComponent<React.FC<NodeProps>>> = {
  start: StartNode,
  condition: ConditionNode,
  job: JobNode,
  db: DBNode,
  endpoint: EndpointNode,
  person_job: PersonJobNode,
};

// Universal Node Component - routes to appropriate lazy-loaded component
const UniversalNode: React.FC<NodeProps> = (props) => {
  const nodeType = (props.data as any).type;
  const NodeComponent = nodeComponents[nodeType];
  
  if (!NodeComponent) {
    const config = UNIFIED_NODE_CONFIGS[nodeType];
    return (
      <GenericNode {...props} nodeType={config?.reactFlowType || "defaultNode"}>
        <span className="text-red-500">Unknown node type: {nodeType}</span>
      </GenericNode>
    );
  }

  return (
    <Suspense fallback={<NodeLoadingFallback {...props} />}>
      <NodeComponent {...props} />
    </Suspense>
  );
};

// Export named component for backward compatibility
export { PersonJobNode as PersonJobNodeGeneric };

// Default export mapping for React Flow using UNIFIED_NODE_CONFIGS
export default Object.fromEntries(
  Object.entries(UNIFIED_NODE_CONFIGS).map(([_, config]) => [
    config.reactFlowType,
    UniversalNode
  ])
);