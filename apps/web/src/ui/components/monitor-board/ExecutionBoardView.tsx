import React, { useRef, useEffect, useCallback } from 'react';
import { Plus, X, Grid3X3, List, Maximize2, Minimize2, Activity } from 'lucide-react';
import { RunColumn } from './RunColumn';
import { RunPicker } from './RunPicker';
import { useUrlSyncedIds } from './useUrlSyncedIds';
import { useAutoFetchExecutions } from './useAutoFetchExecutions';

export default function ExecutionBoardView() {
  const {
    executionIds,
    addExecutionId,
    removeExecutionId,
    reorderExecutionIds,
    clearAll,
    setAutoFetchedIds,
    hasExplicitIds,
  } = useUrlSyncedIds();

  const [showRunPicker, setShowRunPicker] = React.useState(false);
  const [compactMode, setCompactMode] = React.useState(false);
  const [includeCompleted, setIncludeCompleted] = React.useState(false);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Auto-fetch executions when no explicit IDs are provided
  const handleAutoFetchedExecutions = useCallback((fetchedIds: string[]) => {
    setAutoFetchedIds(fetchedIds);
  }, [setAutoFetchedIds]);

  const { loading: autoFetchLoading, executionCount } = useAutoFetchExecutions({
    enabled: !hasExplicitIds, // Only auto-fetch if no explicit IDs in URL
    onExecutionsFetched: handleAutoFetchedExecutions,
    includeCompleted,
  });

  // Handle horizontal scrolling with shift+wheel
  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    const handleWheel = (e: WheelEvent) => {
      // Only handle horizontal scrolling if shift is pressed or it's a horizontal scroll
      if (e.shiftKey || Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
        e.preventDefault();
        container.scrollLeft += e.shiftKey ? e.deltaY : e.deltaX;
      }
    };

    container.addEventListener('wheel', handleWheel, { passive: false });
    return () => container.removeEventListener('wheel', handleWheel);
  }, []);

  const handleAddExecution = (id: string) => {
    addExecutionId(id);
    setShowRunPicker(false);

    // Scroll to the newly added column after a brief delay
    setTimeout(() => {
      if (scrollContainerRef.current) {
        scrollContainerRef.current.scrollTo({
          left: scrollContainerRef.current.scrollWidth,
          behavior: 'smooth',
        });
      }
    }, 100);
  };

  return (
    <div className="h-full flex flex-col bg-gray-950">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-900 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold text-gray-200">
            Execution Monitor Board
          </h1>
          <div className="flex items-center gap-1 px-2 py-1 bg-gray-800 rounded-lg">
            {!hasExplicitIds && (
              <Activity className="w-3 h-3 text-blue-400 animate-pulse mr-1" />
            )}
            <span className="text-xs text-gray-400">
              {executionIds.length} run{executionIds.length !== 1 ? 's' : ''}
              {!hasExplicitIds && ' (auto)'}
            </span>
          </div>
          {!hasExplicitIds && (
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-1.5 text-xs text-gray-400">
                <input
                  type="checkbox"
                  checked={includeCompleted}
                  onChange={(e) => setIncludeCompleted(e.target.checked)}
                  className="rounded border-gray-600 bg-gray-800 text-blue-600 focus:ring-blue-500 focus:ring-offset-0"
                />
                Include completed
              </label>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Compact mode toggle */}
          <button
            onClick={() => setCompactMode(!compactMode)}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
            title={compactMode ? 'Expand view' : 'Compact view'}
          >
            {compactMode ? (
              <Maximize2 className="w-4 h-4 text-gray-400" />
            ) : (
              <Minimize2 className="w-4 h-4 text-gray-400" />
            )}
          </button>

          {/* Add run button */}
          <button
            onClick={() => setShowRunPicker(true)}
            className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm"
          >
            <Plus className="w-4 h-4" />
            Add Run
          </button>

          {/* Clear all button */}
          {executionIds.length > 0 && (
            <button
              onClick={clearAll}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              title="Clear all"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>
          )}
        </div>
      </div>

      {/* Main content area */}
      {executionIds.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            {!hasExplicitIds && autoFetchLoading ? (
              <>
                <Activity className="w-12 h-12 text-blue-500 animate-pulse mx-auto mb-4" />
                <h2 className="text-lg font-medium text-gray-400 mb-2">
                  Searching for active executions...
                </h2>
                <p className="text-sm text-gray-600">
                  Monitoring for running and recent executions
                </p>
              </>
            ) : !hasExplicitIds ? (
              <>
                <Grid3X3 className="w-12 h-12 text-gray-700 mx-auto mb-4" />
                <h2 className="text-lg font-medium text-gray-400 mb-2">
                  No active executions found
                </h2>
                <p className="text-sm text-gray-600 mb-4">
                  Executions will appear here automatically when they start
                </p>
                <div className="flex items-center gap-3 justify-center">
                  <span className="text-xs text-gray-500">
                    Auto-refreshing every 3 seconds
                  </span>
                  <button
                    onClick={() => setShowRunPicker(true)}
                    className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors text-sm"
                  >
                    <Plus className="w-3 h-3" />
                    Add Manually
                  </button>
                </div>
              </>
            ) : (
              <>
                <Grid3X3 className="w-12 h-12 text-gray-700 mx-auto mb-4" />
                <h2 className="text-lg font-medium text-gray-400 mb-2">
                  No executions on the board
                </h2>
                <p className="text-sm text-gray-600 mb-4">
                  Add execution runs to monitor them side by side
                </p>
                <button
                  onClick={() => setShowRunPicker(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors mx-auto"
                >
                  <Plus className="w-4 h-4" />
                  Add First Run
                </button>
              </>
            )}
          </div>
        </div>
      ) : (
        <div
          ref={scrollContainerRef}
          className="flex-1 overflow-x-auto overflow-y-hidden"
          style={{
            scrollSnapType: 'x mandatory',
            scrollBehavior: 'smooth',
          }}
        >
          <div
            className="h-full grid gap-4 px-4 py-4"
            style={{
              gridAutoFlow: 'column',
              gridAutoColumns: compactMode ? 'minmax(400px, 1fr)' : 'minmax(600px, 1fr)',
            }}
          >
            {executionIds.map((id, index) => (
              <RunColumn
                key={id}
                executionId={id}
                onRemove={() => removeExecutionId(id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Run Picker Modal */}
      {showRunPicker && (
        <RunPicker
          onSelect={handleAddExecution}
          onClose={() => setShowRunPicker(false)}
          existingIds={executionIds}
        />
      )}
    </div>
  );
}

// Add custom scrollbar styles
const styles = `
  .custom-scrollbar::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }

  .custom-scrollbar::-webkit-scrollbar-track {
    background: rgb(31 41 55 / 0.5);
    border-radius: 3px;
  }

  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgb(75 85 99);
    border-radius: 3px;
  }

  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgb(107 114 128);
  }
`;

// Inject styles
if (typeof document !== 'undefined') {
  const styleElement = document.createElement('style');
  styleElement.textContent = styles;
  document.head.appendChild(styleElement);
}
