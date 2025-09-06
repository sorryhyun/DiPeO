import React, { useMemo, useEffect } from 'react';
import { createExecutionLocalStore } from './executionLocalStore';
import { useRunSubscription } from './useRunSubscription';
import { RunHeader } from './RunHeader';
import { EventStrip } from './EventStrip';
import { DiagramViewer } from './DiagramViewer';
import { useQuery } from '@apollo/client';
import { GetDiagramDocument, GetExecutionDocument } from '@/__generated__/graphql';
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

  // Fetch execution to get diagram_id
  const { data: executionData } = useQuery(GetExecutionDocument, {
    variables: { id: executionId },
    skip: !executionId,
  });

  const diagramId = executionData?.execution?.diagram_id;

  // Fetch diagram using the diagram_id from execution
  const { data: diagramData, loading: diagramLoading } = useQuery(GetDiagramDocument, {
    variables: { id: diagramId },
    skip: !diagramId,
  });

  // Store diagram data in the local store when it's fetched
  useEffect(() => {
    if (diagramData?.diagram) {
      const { nodes, arrows, handles } = diagramData.diagram;
      store.getState().setDiagramData(
        executionData?.execution?.diagram_id || 'Unknown Diagram',
        nodes || [],
        arrows || [],
        handles || []
      );
    }
  }, [diagramData, executionData, store]);

  return (
    <div
      className="rounded-2xl bg-gray-800/60 border border-gray-700 shadow p-3 min-w-[480px] flex flex-col h-full overflow-hidden"
      style={{ scrollSnapAlign: 'start' }}
    >
      {/* Column Header with run info and controls - Fixed at top */}
      <div className="flex-shrink-0">
        <RunHeader
          executionId={executionId}
          store={store}
          onRemove={onRemove}
        />
      </div>

      {/* Scrollable content area */}
      <div className="flex-1 flex flex-col min-h-0">
        {/* Diagram Canvas - Read only view with execution highlights */}
        <div className="flex-1 rounded-xl overflow-hidden mb-3 bg-gray-900/50 border border-gray-700 min-h-[400px]">
          {diagramLoading ? (
            <div className="h-full w-full flex items-center justify-center text-gray-500">
              <div className="text-center">
                <div className="text-sm opacity-75">Loading diagram...</div>
              </div>
            </div>
          ) : (
            <DiagramViewer store={store} readOnly />
          )}
        </div>

        {/* Event strip showing execution timeline - Fixed height with internal scroll */}
        <div className="flex-shrink-0">
          <EventStrip
            executionId={executionId}
            store={store}
          />
        </div>
      </div>
    </div>
  );
}
