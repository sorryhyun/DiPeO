import React from 'react';
import { DiagramCanvas } from '@/components/diagram/canvas';
import ExecutionControls from './ExecutionControls';

const ExecutionView = React.memo(() => {
  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Execution Controls */}
      <ExecutionControls />
      
      {/* Main content area - DiagramCanvas with executionMode will show ConversationDashboard */}
      <div className="flex-1">
        <DiagramCanvas executionMode />
      </div>
    </div>
  );
});

ExecutionView.displayName = 'ExecutionView';

export default ExecutionView;