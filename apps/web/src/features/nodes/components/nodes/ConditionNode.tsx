import React from 'react';
import { NodeProps } from '@xyflow/react';
import { GenericNode } from '../base/GenericNode';
import { UNIFIED_NODE_CONFIGS, type ConditionBlockData } from '@/shared/types';

const ConditionNode: React.FC<NodeProps> = ({ id, data, selected }) => {
  const config = UNIFIED_NODE_CONFIGS.condition!;
  const conditionData = data as ConditionBlockData;
  const isFlipped = conditionData.flipped === true;
  const isMaxIterationMode = conditionData.detectMaxIteration || conditionData.conditionType === 'detect_max_iterations';
  
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
    </GenericNode>
  );
};

export default ConditionNode;