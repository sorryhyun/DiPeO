import React, { useCallback, useMemo } from 'react';
import { NodeProps } from '@xyflow/react';
import { GenericNode } from './base/GenericNode';
import { Code, Zap, Link as LinkIcon, Save } from 'lucide-react';
import { useDiagramStore } from '@/state/stores';
import { NodeType } from '@/common/types/node';
import { getNodeConfig, COMPLETE_NODE_CONFIGS } from '@/common/types/unifiedNodeConfig';

// Type guard to safely get node type
const getNodeType = (data: any): NodeType => {
  return data?.type || 'start';
};

// Separate component for PersonJob content to use hooks
const PersonJobContent: React.FC<{ config: any; data: any }> = ({ config, data }) => {
  const persons = useDiagramStore(state => state.persons);
  const personLabel = useMemo(() => {
    if (!data.personId) return null;
    return persons.find(p => p.id === data.personId)?.label || 'Unknown';
  }, [data.personId, persons]);

  return (
    <>
      <div className="flex items-center justify-center mb-1">
        <span className="text-xl mr-2">{config.emoji}</span>
        <strong className="text-base truncate" title={data.label || config.label}>
          {data.label || config.label}
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

// Node-specific content renderers
const nodeRenderers: Record<NodeType, (props: { config: any; data: any; id: string }) => React.ReactNode> = {
  'start': ({ config, data }) => (
    <>
      <span className="text-2xl mb-0.5">{config.emoji}</span>
      <strong className="text-sm">{data.label || config.label}</strong>
    </>
  ),

  'condition': ({ config, data }) => {
    const isFlipped = data.flipped === true;
    const isMaxIterationMode = data.detectMaxIteration || data.conditionType === 'detect_max_iterations';
    
    // Get handle labels from config
    const trueHandle = config.handles.sources.find((h: any) => h.id === 'true');
    const falseHandle = config.handles.sources.find((h: any) => h.id === 'false');

    return (
      <>
        <div className={`absolute ${isFlipped ? '-left-3' : '-right-3'} top-[30%] -translate-y-[140%] text-[10px] ${falseHandle?.color || 'text-red-600'} font-semibold pointer-events-none`}>
          {falseHandle?.label || 'False'}
        </div>
        <div className={`absolute ${isFlipped ? '-left-3' : '-right-3'} top-[70%] translate-y-[40%] text-[10px] ${trueHandle?.color || 'text-green-600'} font-semibold pointer-events-none`}>
          {trueHandle?.label || 'True'}
        </div>
        <div className="flex items-center justify-center mb-1">
          <span className="text-lg mr-2">{config.emoji}</span>
          <strong className="text-base">{config.label}</strong>
        </div>
        <div className="text-xs text-gray-600 mb-1 text-center">
          {isMaxIterationMode ? (
            <span className="font-medium">🔄 Detect Max Iterations</span>
          ) : (
            <span className="font-medium">📐 Expression</span>
          )}
        </div>
        {!isMaxIterationMode && data.expression && (
          <div className="text-xs text-gray-500 px-2 truncate text-center" title={data.expression}>
            {data.expression}
          </div>
        )}
      </>
    );
  },

  'job': ({ config, data }) => {
    const subType = data.subType || 'python';
    const icon = subType === 'python' || subType === 'javascript' || subType === 'bash' ? (
      <Code className="h-5 w-5 text-purple-600 flex-shrink-0" />
    ) : subType === 'api_tool' ? (
      <Zap className="h-5 w-5 text-blue-600 flex-shrink-0" />
    ) : (
      <LinkIcon className="h-5 w-5 text-green-600 flex-shrink-0" />
    );
    const subTypeLabel = subType.charAt(0).toUpperCase() + subType.slice(1);

    return (
      <>
        <div className="flex items-center space-x-2 mb-1">
          {icon}
          <strong className="text-base truncate">{data.label || config.label}</strong>
        </div>
        <div className="text-sm text-gray-400 mb-0.5">{subTypeLabel}</div>
        {data.code && (
          <p className="text-sm text-gray-500 truncate">Code configured</p>
        )}
      </>
    );
  },

  'db': ({ config, data }) => {
    return (
      <>
        <div className="flex items-center space-x-2 mb-1">
          <span className="text-xl mr-2">{config.emoji}</span>
          <strong className="text-base truncate">{data.label || config.label}</strong>
        </div>
        <p className="text-sm text-gray-500 truncate">Operation: {data.operation || 'N/A'}</p>
        <p className="text-sm text-gray-500 truncate">Path: {data.path || 'N/A'}</p>
      </>
    );
  },

  'endpoint': ({ config, data }) => {
    return (
      <>
        <span className="text-2xl mb-0.5">{config.emoji}</span>
        <strong className="text-sm truncate">{data.label || config.label}</strong>
        {data.action === 'save' && (
          <div className="flex items-center gap-1 mt-1">
            <Save className="h-3 w-3 text-gray-600" />
            <span className="text-xs text-gray-600">Save</span>
          </div>
        )}
      </>
    );
  },

  'person_job': ({ config, data, id }) => {
    const isFlipped = data.flipped === true;
    
    // Get handle labels from config
    const firstHandle = config.handles.targets.find((h: any) => h.id === 'first');
    const defaultHandle = config.handles.targets.find((h: any) => h.id === 'default');

    return (
      <>
        <div
          className={`absolute ${isFlipped ? '-right-3' : '-left-3'} top-[30%] -translate-y-[150%] text-[10px] ${firstHandle?.color || 'text-purple-600'} font-semibold pointer-events-none`}
        >
          {firstHandle?.label || 'first'}
        </div>
        <div
          className={`absolute ${isFlipped ? '-right-3' : '-left-3'} top-[70%] translate-y-[50%] text-[10px] ${defaultHandle?.color || 'text-teal-600'} font-semibold pointer-events-none`}
        >
          {defaultHandle?.label || 'default'}
        </div>
        <PersonJobContent config={config} data={data} />
      </>
    );
  },

  'person_batch_job': ({ config, data }) => {
    // Note: This is called from within a component, so the hook usage is valid
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const persons = useDiagramStore(state => state.persons);
    const personLabel = data.personId 
      ? persons.find(p => p.id === data.personId)?.label || 'Unknown'
      : null;

    return (
      <>
        <div className="flex items-center justify-center mb-1">
          <span className="text-xl mr-2">{config.emoji}</span>
          <strong className="text-base truncate" title={data.label || config.label}>
            {data.label || config.label}
          </strong>
        </div>
        {personLabel && (
          <p className="text-sm text-gray-500 truncate text-center">
            Person: {personLabel}
          </p>
        )}
        <div className="mt-2 space-y-0.5 text-center">
          {data.batchSize !== undefined && (
            <p className="text-sm text-gray-600">
              Batch size: <span className="font-medium">{data.batchSize}</span>
            </p>
          )}
        </div>
      </>
    );
  },
  
  'user_response': ({ config, data }) => (
    <>
      <span className="text-2xl mb-0.5">{config?.emoji || '❓'}</span>
      <strong className="text-sm">{data.label || 'User Response'}</strong>
      {data.promptMessage && (
        <p className="text-xs text-gray-500 mt-1 truncate">{data.promptMessage}</p>
      )}
    </>
  ),
  
  'notion': ({ config, data }) => (
    <>
      <span className="text-2xl mb-0.5">{config?.emoji || '📄'}</span>
      <strong className="text-sm">{data.label || 'Notion'}</strong>
      {data.operation && (
        <p className="text-xs text-gray-500 mt-1">{data.operation}</p>
      )}
    </>
  ),
};

// Main configurable node component
const ConfigurableNode: React.FC<NodeProps> = ({ id, data, selected }) => {
  const nodeType = getNodeType(data);
  const config = getNodeConfig(nodeType);
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
      const personData = e.dataTransfer.getData('application/person');
      if (personData) {
        const person = JSON.parse(personData);
        updateNodeData(id, { personId: person.id });
      }
      setIsDragOver(false);
    }
  }, [nodeType, id, updateNodeData]);

  if (!config) {
    console.warn(`No configuration found for node type: ${nodeType}`);
    return null;
  }

  const renderer = nodeRenderers[nodeType];
  const content = renderer ? renderer({ config, data, id }) : (
    <>
      <span className="text-2xl mb-0.5">{config.emoji}</span>
      <strong className="text-sm">{data.label || config.label}</strong>
    </>
  );

  // Get drag and drop props for person_job nodes
  const dragProps = nodeType === 'person_job' ? {
    onDragOver: handleDragOver,
    onDragEnter: handleDragEnter,
    onDragLeave: handleDragLeave,
    onDrop: handleDrop,
  } : {};

  return (
    <GenericNode
      id={id}
      data={data}
      selected={selected}
      nodeType={nodeType}
      borderColor={config.borderColor}
      width={config.width}
      height={'auto'}
      className={`${config.className} ${isDragOver ? 'ring-2 ring-purple-400' : ''}`}
      {...dragProps}
    >
      {content}
    </GenericNode>
  );
};

export default ConfigurableNode;