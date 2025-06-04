import React, { useCallback, useMemo } from 'react';
import { NodeProps } from '@xyflow/react';
import { GenericNode } from './base/GenericNode';
import { Code, Zap, Link as LinkIcon, Save } from 'lucide-react';
import { useDiagramStore } from '@/state/stores';
import { UNIFIED_NODE_CONFIGS, type
  StartBlockData,
  ConditionBlockData,
  JobBlockData,
  DBBlockData,
  EndpointBlockData,
  PersonJobBlockData,
  PersonBatchJobBlockData,
} from '@/common/types';

// Type guard to safely get node type
const getNodeType = (data: any): string => {
  return data?.type || 'start';
};

// Node-specific content renderers
const nodeRenderers: Record<string, (props: NodeRenderProps) => React.ReactNode> = {
  start: ({ config, data }) => (
    <>
      <span className="text-2xl mb-0.5">{config.emoji}</span>
      <strong className="text-sm">{(data as StartBlockData).label || config.label}</strong>
    </>
  ),

  condition: ({ config, data }) => {
    const conditionData = data as ConditionBlockData;
    const isFlipped = conditionData.flipped === true;
    const isMaxIterationMode = conditionData.detectMaxIteration || conditionData.conditionType === 'detect_max_iterations';

    return (
      <>
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
            <span className="font-medium">🔄 Detect Max Iterations</span>
          ) : (
            <span className="font-medium">📐 Expression</span>
          )}
        </div>
        {!isMaxIterationMode && conditionData.expression && (
          <div className="text-xs text-gray-500 px-2 truncate text-center" title={conditionData.expression}>
            {conditionData.expression}
          </div>
        )}
      </>
    );
  },

  job: ({ config, data }) => {
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
      <>
        <div className="flex items-center space-x-2 mb-1">
          {icon}
          <strong className="text-base truncate">{jobData.label}</strong>
        </div>
        <div className="text-sm text-gray-400 mb-0.5">{subTypeLabel}</div>
        <p className="text-sm text-gray-500 truncate">{details}</p>
      </>
    );
  },

  db: ({ config, data }) => {
    const dbData = data as DBBlockData;
    return (
      <>
        <div className="flex items-center space-x-2 mb-1">
          <span className="text-xl mr-2">{config.emoji}</span>
          <strong className="text-base truncate">{dbData.label || 'DB Source'}</strong>
        </div>
        <p className="text-sm text-gray-500 truncate">Type: {dbData.subType || 'N/A'}</p>
        <p className="text-sm text-gray-500 truncate">Source: {dbData.sourceDetails || 'N/A'}</p>
      </>
    );
  },

  endpoint: ({ config, data }) => {
    const endpointData = data as EndpointBlockData;
    return (
      <>
        <span className="text-2xl mb-0.5">{config.emoji}</span>
        <strong className="text-sm truncate">{endpointData.label || 'End'}</strong>
        {endpointData.saveToFile && (
          <div className="flex items-center gap-1 mt-1">
            <Save className="h-3 w-3 text-gray-600" />
            <span className="text-xs text-gray-600">Save</span>
          </div>
        )}
      </>
    );
  },

  person_job: ({ config, data, id }) => {
    const jobData = data as PersonJobBlockData;
    const isFlipped = jobData.flipped === true;

    return (
      <>
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
        <PersonJobContent config={config} data={jobData} />
      </>
    );
  },

  person_batch_job: ({ config, data }) => {
    const batchData = data as PersonBatchJobBlockData;
    // Note: This is called from within a component, so the hook usage is valid
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const persons = useDiagramStore(state => state.persons);
    const personLabel = batchData.personId 
      ? persons.find(p => p.id === batchData.personId)?.label || 'Unknown'
      : null;

    return (
      <>
        <div className="flex items-center justify-center mb-1">
          <span className="text-xl mr-2">{config.emoji}</span>
          <strong className="text-base truncate" title={batchData.label || 'Person Batch Job'}>
            {batchData.label || 'Person Batch Job'}
          </strong>
        </div>
        {personLabel && (
          <p className="text-sm text-gray-500 truncate text-center">
            Person: {personLabel}
          </p>
        )}
        <div className="mt-2 space-y-0.5 text-center">
          {batchData.batchSize !== undefined && (
            <p className="text-sm text-gray-600">
              Batch size: <span className="font-medium">{batchData.batchSize}</span>
            </p>
          )}
          {batchData.aggregationMethod && (
            <p className="text-sm text-gray-600">
              Aggregation: <span className="font-medium">{batchData.aggregationMethod}</span>
            </p>
          )}
        </div>
      </>
    );
  },
};

// Separate component for PersonJob content to use hooks
const PersonJobContent: React.FC<{ config: any; data: PersonJobBlockData }> = ({ config, data }) => {
  const persons = useDiagramStore(state => state.persons);
  const personLabel = useMemo(() => {
    if (!data.personId) return null;
    return persons.find(p => p.id === data.personId)?.label || 'Unknown';
  }, [data.personId, persons]);

  return (
    <>
      <div className="flex items-center justify-center mb-1">
        <span className="text-xl mr-2">{config.emoji}</span>
        <strong className="text-base truncate" title={data.label || 'Person Job'}>
          {data.label || 'Person Job'}
        </strong>
      </div>
      {personLabel && (
        <p className="text-sm text-gray-500 truncate text-center">
          Person: {personLabel}
        </p>
      )}
      <div className="mt-2 space-y-0.5 text-center">
        {data.contextCleaningRule ? (
          <p className="text-sm text-gray-600">
            Forget: <span className="font-medium">
              {data.contextCleaningRule === 'no_forget'
                ? 'Never'
                : data.contextCleaningRule === 'on_every_turn'
                ? 'Every turn'
                : 'Upon request'}
            </span>
          </p>
        ) : null}
        {data.iterationCount !== undefined ? (
          <p className="text-sm text-gray-600">
            Max iterations: <span className="font-medium">{data.iterationCount}</span>
          </p>
        ) : null}
      </div>
    </>
  );
};

interface NodeRenderProps {
  config: any;
  data: any;
  id: string;
  selected?: boolean;
}

// Main configurable node component
const ConfigurableNode: React.FC<NodeProps> = ({ id, data, selected }) => {
  const nodeType = getNodeType(data);
  const config = UNIFIED_NODE_CONFIGS[nodeType];
  const updateNodeData = useDiagramStore(state => state.updateNodeData);
  const [isDragOver, setIsDragOver] = React.useState(false);

  // Event handlers for person_job drag and drop
  const handleDragOver = useCallback((e: React.DragEvent) => {
    if (nodeType === 'person_job') {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'copy';
    }
  }, [nodeType]);

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    if (nodeType === 'person_job' && e.dataTransfer.types.includes('application/person')) {
      setIsDragOver(true);
    }
  }, [nodeType]);

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    if (nodeType === 'person_job') {
      e.preventDefault();
      const personId = e.dataTransfer.getData('application/person');
      if (personId) {
        updateNodeData(id, { personId });
      }
      setIsDragOver(false);
    }
  }, [nodeType, id, updateNodeData]);

  if (!config) {
    return (
      <GenericNode id={id} data={data} selected={selected} nodeType="start">
        <span className="text-red-500">Unknown node type: {nodeType}</span>
      </GenericNode>
    );
  }

  const renderer = nodeRenderers[nodeType];
  const showFlipButton = nodeType !== 'db'; // DB nodes don't have flip button

  const genericNodeProps: any = {
    id,
    data,
    selected,
    nodeType: config.reactFlowType,
    showFlipButton,
  };

  // Add drag handlers for person_job nodes
  if (nodeType === 'person_job') {
    genericNodeProps.onDragOver = handleDragOver;
    genericNodeProps.onDragEnter = handleDragEnter;
    genericNodeProps.onDragLeave = handleDragLeave;
    genericNodeProps.onDrop = handleDrop;
    genericNodeProps.className = isDragOver ? 'ring-2 ring-blue-400 ring-offset-2' : '';
  }

  return (
    <GenericNode {...genericNodeProps}>
      {renderer ? renderer({ config, data, id, selected }) : (
        <>
          <span className="text-2xl mb-0.5">{config.emoji}</span>
          <strong className="text-sm">{(data as any).label || config.label}</strong>
        </>
      )}
    </GenericNode>
  );
};

export default ConfigurableNode;