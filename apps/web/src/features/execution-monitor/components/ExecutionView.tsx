import React from 'react';
import DiagramCanvas from '@/features/diagram-editor/components/DiagramCanvas';
import { ExecutionControls } from './ExecutionControls';

const ExecutionView = React.memo(() => {
  return (
    <div className="h-full flex flex-col bg-gray-900">
      <ExecutionControls />
      
      <div className="flex-1">
        <DiagramCanvas executionMode />
      </div>
    </div>
  );
});

ExecutionView.displayName = 'ExecutionView';

export { ExecutionView };
export default ExecutionView;