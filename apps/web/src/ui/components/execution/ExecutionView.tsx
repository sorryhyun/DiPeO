import React from 'react';
import DiagramCanvas from '@/ui/components/diagram/DiagramCanvas';
import { ExecutionControls } from './ExecutionControls';
import { ErrorBoundary } from '../common/ErrorBoundary';

const ExecutionView = React.memo(() => {
  return (
    <div className="h-full flex flex-col bg-gray-900">
      <ExecutionControls />

      <div className="flex-1">
        <ErrorBoundary>
          <DiagramCanvas executionMode />
        </ErrorBoundary>
      </div>
    </div>
  );
});

ExecutionView.displayName = 'ExecutionView';

export { ExecutionView };
export default ExecutionView;
