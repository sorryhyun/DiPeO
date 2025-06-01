import React from 'react';
import { NodeProps } from '@xyflow/react';
import { GenericNode } from '../base/GenericNode';
import { useConsolidatedDiagramStore } from '@/core/stores';
import { UNIFIED_NODE_CONFIGS, type PersonJobBlockData } from '@/shared/types';

const PersonJobNodeComponent: React.FC<NodeProps> = ({ id, data, selected }) => {
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
      nodeType="personJobNode"
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
        <span className="text-xl mr-2">{cfg?.emoji}</span>
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
        {jobData.contextCleaningRule ? (
          <p className="text-sm text-gray-600">
            Forget: <span className="font-medium">
              {jobData.contextCleaningRule === 'noForget'
                ? 'Never'
                : jobData.contextCleaningRule === 'onEveryTurn'
                ? 'Every turn'
                : 'Upon request'}
            </span>
          </p>
        ) : null}
        {jobData.iterationCount !== undefined ? (
          <p className="text-sm text-gray-600">
            Max iterations: <span className="font-medium">{jobData.iterationCount}</span>
          </p>
        ) : null}
      </div>
    </GenericNode>
  );
};

const PersonJobNode = React.memo(PersonJobNodeComponent, (prevProps, nextProps) => {
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

PersonJobNode.displayName = 'PersonJobNode';

export default PersonJobNode;