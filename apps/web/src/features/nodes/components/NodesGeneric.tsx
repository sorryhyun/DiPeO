// apps/web/src/components/nodes/NodesGeneric.tsx

import React from 'react';
import { NodeProps } from '@xyflow/react';
import { GenericNode } from './BaseNode';
import { useConsolidatedDiagramStore } from '@/shared/stores';
import { Code, Zap, Link as LinkIcon, Save } from 'lucide-react';
import {
  UNIFIED_NODE_CONFIGS,
  type StartBlockData,
  type PersonJobBlockData,
  type ConditionBlockData,
  type DBBlockData,
  type JobBlockData,
  type EndpointBlockData
} from '../../../shared/types';

// Universal Node Component - replaces all individual node components
const UniversalNode: React.FC<NodeProps> = ({ id, data, selected }) => {
  const nodeType = (data as any).type;
  const config = UNIFIED_NODE_CONFIGS[nodeType];
  
  if (!config) {
    return (
      <GenericNode id={id} data={data} selected={selected} nodeType="defaultNode">
        <span className="text-red-500">Unknown node type: {nodeType}</span>
      </GenericNode>
    );
  }

  // Special handling for person_job nodes that need store access
  if (nodeType === 'person_job') {
    return <PersonJobNodeGeneric {...{ id, data, selected } as any} />;
  }

  // Handle condition node special rendering
  if (nodeType === 'condition') {
    const conditionData = data as ConditionBlockData;
    const isFlipped = conditionData.flipped === true;
    const isMaxIterationMode = conditionData.detectMaxIteration || conditionData.conditionType === 'max_iterations';
    
    return (
      <GenericNode id={id} data={data} selected={selected} nodeType={config.reactFlowType}>
        <div className={`absolute ${isFlipped ? '-left-3' : '-right-3'} top-[30%] -translate-y-[140%] text-[10px] text-red-600 font-semibold pointer-events-none`}>
          False
        </div>
        <div className={`absolute ${isFlipped ? '-left-3' : '-right-3'} top-[70%] translate-y-[40%] text-[10px] text-green-600 font-semibold pointer-events-none`}>
          True
        </div>
        <div className="flex items-center justify-center mb-1">
          <span className="text-lg mr-2">{config.emoji}</span>
          <strong className="text-base">Condition</strong>
        </div>
        <div className="text-xs text-gray-600 mb-1 text-center">
          {isMaxIterationMode ? (
            <span className="font-medium">🔄 Max Iterations</span>
          ) : (
            <span className="font-medium">📐 Expression</span>
          )}
        </div>
        {!isMaxIterationMode && conditionData.expression && (
          <div className="text-xs text-gray-500 px-2 truncate text-center" title={conditionData.expression}>
            {conditionData.expression}
          </div>
        )}
      </GenericNode>
    );
  }

  // Handle job node special rendering
  if (nodeType === 'job') {
    const jobData = data as JobBlockData;
    const subType = jobData.subType || 'code';
    const icon = subType === 'code' ? (
      <Code className="h-5 w-5 text-purple-600 flex-shrink-0" />
    ) : subType === 'api_tool' ? (
      <Zap className="h-5 w-5 text-blue-600 flex-shrink-0" />
    ) : (
      <LinkIcon className="h-5 w-5 text-green-600 flex-shrink-0" />
    );
    const subTypeLabel = subType === 'code' ? 'Code' : subType === 'api_tool' ? 'API Tool' : 'Diagram Link';
    const details = jobData.sourceDetails || '<configure job details>';

    return (
      <GenericNode id={id} data={data} selected={selected} nodeType={config.reactFlowType}>
        <div className="flex items-center space-x-2 mb-1">
          {icon}
          <strong className="text-base truncate">{jobData.label}</strong>
        </div>
        <div className="text-sm text-gray-400 mb-0.5">{subTypeLabel}</div>
        <p className="text-sm text-gray-500 truncate">{details}</p>
      </GenericNode>
    );
  }

  // Handle db node special rendering
  if (nodeType === 'db') {
    const dbData = data as DBBlockData;
    
    return (
      <GenericNode id={id} data={data} selected={selected} nodeType={config.reactFlowType} showFlipButton={false}>
        <div className="flex items-center space-x-2 mb-1">
          <span className="text-xl mr-2">{config.emoji}</span>
          <strong className="text-base truncate">{dbData.label || 'DB Source'}</strong>
        </div>
        <p className="text-sm text-gray-500 truncate">Type: {dbData.subType || 'N/A'}</p>
        <p className="text-sm text-gray-500 truncate">Source: {dbData.sourceDetails || 'N/A'}</p>
      </GenericNode>
    );
  }

  // Handle endpoint node special rendering
  if (nodeType === 'endpoint') {
    const endpointData = data as EndpointBlockData;
    
    return (
      <GenericNode id={id} data={data} selected={selected} nodeType={config.reactFlowType}>
        <span className="text-2xl mb-0.5">{config.emoji}</span>
        <strong className="text-sm truncate">{endpointData.label || 'End'}</strong>
        {endpointData.saveToFile && (
          <div className="flex items-center gap-1 mt-1">
            <Save className="h-3 w-3 text-gray-600" />
            <span className="text-xs text-gray-600">Save</span>
          </div>
        )}
      </GenericNode>
    );
  }

  // Default rendering for start and other simple nodes
  return (
    <GenericNode id={id} data={data} selected={selected} nodeType={config.reactFlowType}>
      <span className="text-2xl mb-0.5">{config.emoji}</span>
      <strong className="text-sm">{(data as any).label || config.label}</strong>
    </GenericNode>
  );
};




// Person Job Node - Special handling for store access
const PersonJobNodeGenericComponent: React.FC<NodeProps> = ({ id, data, selected }) => {
  const cfg = UNIFIED_NODE_CONFIGS.person_job;
  const jobData = data as PersonJobBlockData;
  // Use shallow selectors to minimize re-renders
  const persons = useConsolidatedDiagramStore(state => state.persons);
  const updateNodeData = useConsolidatedDiagramStore(state => state.updateNodeData);
  const isFlipped = jobData.flipped === true;

  // Memoize event handlers
  const handleDragOver = React.useCallback((e: React.DragEvent) => e.preventDefault(), []);
  const handleDrop = React.useCallback((e: React.DragEvent) => {
    const personId = e.dataTransfer.getData('application/person');
    if (personId) updateNodeData(id, { personId });
  }, [id, updateNodeData]);

  // Find person label only when personId changes
  const personLabel = React.useMemo(() => {
    if (!jobData.personId) return null;
    return persons.find(p => p.id === jobData.personId)?.label || 'Unknown';
  }, [jobData.personId, persons]);

  return (
    <GenericNode
      id={id}
      data={data}
      selected={selected}
      nodeType="personjobNode"
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      <div
        className={`absolute ${isFlipped ? '-right-3' : '-left-3'} top-[30%] -translate-y-[150%] text-[10px] text-purple-600 font-semibold pointer-events-none`}
      >
        first
      </div>
      <div
        className={`absolute ${isFlipped ? '-right-3' : '-left-3'} top-[70%] translate-y-[50%] text-[10px] text-teal-600 font-semibold pointer-events-none`}
      >
        default
      </div>
      <div className="flex items-center justify-center mb-1">
        <span className="text-xl mr-2">{cfg.emoji}</span>
        <strong className="text-base truncate" title={jobData.label || 'Person Job'}>
          {jobData.label || 'Person Job'}
        </strong>
      </div>
      {personLabel && (
        <p className="text-sm text-gray-500 truncate text-center">
          Person: {personLabel}
        </p>
      )}
      <div className="mt-2 space-y-0.5 text-center">
        {jobData.mode && (
          <p className="text-sm text-gray-600">
            Mode: <span className="font-medium">{jobData.mode}</span>
          </p>
        )}
        {jobData.contextCleaningRule && (
          <p className="text-sm text-gray-600">
            Forget: <span className="font-medium">
              {jobData.contextCleaningRule === 'no_forget'
                ? 'Never'
                : jobData.contextCleaningRule === 'on_every_turn'
                ? 'Every turn'
                : 'Upon request'}
            </span>
          </p>
        )}
        {jobData.iterationCount !== undefined && (
          <p className="text-sm text-gray-600">
            Max iterations: <span className="font-medium">{jobData.iterationCount}</span>
          </p>
        )}
      </div>
    </GenericNode>
  );
};

const PersonJobNodeGeneric = React.memo(PersonJobNodeGenericComponent, (prevProps, nextProps) => {
  const prevData = prevProps.data as PersonJobBlockData;
  const nextData = nextProps.data as PersonJobBlockData;
  return (
    prevProps.id === nextProps.id &&
    prevProps.selected === nextProps.selected &&
    prevData.label === nextData.label &&
    prevData.personId === nextData.personId &&
    prevData.flipped === nextData.flipped &&
    prevData.mode === nextData.mode &&
    prevData.contextCleaningRule === nextData.contextCleaningRule &&
    prevData.iterationCount === nextData.iterationCount
  );
});

PersonJobNodeGeneric.displayName = 'PersonJobNodeGeneric';

// Export named components for backward compatibility
export {  PersonJobNodeGeneric };

// Default export mapping for React Flow using UNIFIED_NODE_CONFIGS
export default Object.fromEntries(
  Object.entries(UNIFIED_NODE_CONFIGS).map(([_, config]) => [
    config.reactFlowType,
    UniversalNode
  ])
);