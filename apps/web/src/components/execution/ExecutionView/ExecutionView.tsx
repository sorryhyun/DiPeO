import React from 'react';
import { DiagramCanvas } from '@/components/diagram/canvas';
import { ConversationDashboard } from '@/components/conversation';
import ExecutionControls from './ExecutionControls';

const ExecutionView = () => {
  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Execution Controls */}
      <ExecutionControls />
      
      {/* Main content area with diagram and conversation panel */}
      <div className="flex-1 flex flex-col">
        {/* Read-only Diagram Canvas */}
        <div className="flex-1">
          <DiagramCanvas executionMode />
        </div>
        
        {/* Conversation Dashboard Panel at bottom */}
        <div className="h-64 border-t border-gray-700 bg-white overflow-hidden">
          <ConversationDashboard />
        </div>
      </div>
    </div>
  );
};

export default ExecutionView;