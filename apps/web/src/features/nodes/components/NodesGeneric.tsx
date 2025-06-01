// apps/web/src/components/nodes/NodesGeneric.tsx

import React, { Suspense } from 'react';
import { NodeProps } from '@xyflow/react';
import { GenericNode } from './base/GenericNode';
import { UNIFIED_NODE_TYPES } from '@/shared/types';
import { StartNode, ConditionNode, JobNode, DBNode, EndpointNode, PersonJobNode, PersonBatchJobNode } from './nodes';

// Loading component for lazy-loaded nodes
const NodeLoadingFallback: React.FC<NodeProps> = ({ id, data, selected }) => {
  const nodeType = (data as { type: string }).type;
  const config = UNIFIED_NODE_TYPES[nodeType];
  const reactFlowType = config?.reactFlowType || "startNode";
  
  return (
    <GenericNode id={id} data={data} selected={selected} nodeType={reactFlowType}>
      <span className="text-gray-400">Loading...</span>
    </GenericNode>
  );
};

// Map of node types to their lazy-loaded components
const nodeComponents: Record<string, React.LazyExoticComponent<React.FC<NodeProps>>> = {
  start: StartNode,
  condition: ConditionNode,
  job: JobNode,
  db: DBNode,
  endpoint: EndpointNode,
  person_job: PersonJobNode,
  person_batch_job: PersonBatchJobNode,
};

// Universal Node Component - routes to appropriate lazy-loaded component
const UniversalNode: React.FC<NodeProps> = (props) => {
  const nodeType = (props.data as any).type;
  const NodeComponent = nodeComponents[nodeType];
  
  if (!NodeComponent) {
    const config = UNIFIED_NODE_TYPES[nodeType];
    return (
      <GenericNode {...props} nodeType={config?.reactFlowType || "startNode"}>
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


// Default export mapping for React Flow using UNIFIED_NODE_CONFIGS
export default Object.fromEntries(
  Object.entries(UNIFIED_NODE_TYPES).map(([_, config]) => [
    config.reactFlowType,
    UniversalNode
  ])
);