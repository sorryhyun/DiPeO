import React, { useMemo } from 'react';
import { createExecutionLocalStore } from './executionLocalStore';
import { useRunSubscription } from './useRunSubscription';
import { RunHeader } from './RunHeader';
import { EventStrip } from './EventStrip';
import DiagramCanvas from '@/ui/components/diagram/DiagramCanvas';
import type { StoreApi } from 'zustand';
import type { ExecutionLocalStore } from './executionLocalStore';

interface RunColumnProps {
  executionId: string;
  onRemove?: () => void;
}

export function RunColumn({ executionId, onRemove }: RunColumnProps) {
  // Create a local store instance for this column
  const store = useMemo(() => createExecutionLocalStore(), []);
  
  // Subscribe to execution updates
  useRunSubscription({ executionId, store });

  return (
    <div 
      className="rounded-2xl bg-gray-800/60 border border-gray-700 shadow p-3 min-w-[480px] flex flex-col"
      style={{ scrollSnapAlign: 'start' }}
    >
      {/* Column Header with run info and controls */}
      <RunHeader 
        executionId={executionId} 
        store={store}
        onRemove={onRemove}
      />
      
      {/* Diagram Canvas - Read only view with execution highlights */}
      <div className="h-[56vh] rounded-xl overflow-hidden mb-3 bg-gray-900/50 border border-gray-700">
        <DiagramCanvasWithStore 
          executionMode 
          store={store} 
          readOnly 
        />
      </div>
      
      {/* Event strip showing execution timeline */}
      <EventStrip 
        executionId={executionId} 
        store={store} 
      />
    </div>
  );
}

// Wrapper component to provide the store to DiagramCanvas
// This will be updated once we modify DiagramCanvas to accept a store prop
function DiagramCanvasWithStore({ 
  executionMode, 
  store, 
  readOnly 
}: { 
  executionMode: boolean;
  store: StoreApi<ExecutionLocalStore>;
  readOnly: boolean;
}) {
  // For now, we'll just render the standard DiagramCanvas
  // This will be updated when we modify DiagramCanvas to accept the store prop
  return (
    <div className="h-full w-full flex items-center justify-center text-gray-500">
      <div className="text-center">
        <div className="text-sm opacity-75">Diagram visualization</div>
        <div className="text-xs opacity-50 mt-1">Execution ID: {store.getState().id}</div>
      </div>
    </div>
  );
  
  // TODO: Once DiagramCanvas is modified to accept store prop:
  // return <DiagramCanvas executionMode={executionMode} store={store} readOnly={readOnly} />;
}