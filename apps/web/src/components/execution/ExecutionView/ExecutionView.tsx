import React from 'react';
import { DiagramCanvas } from '@/components/diagram/canvas';
import { ConversationDashboard } from '@/components/conversation';
import ExecutionControls from './ExecutionControls';

const ExecutionView = () => {
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
};

export default ExecutionView;