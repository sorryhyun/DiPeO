/**
 * Execution List Widget
 *
 * Displays a list of diagram executions with status and timing information
 */

import { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Status } from '@dipeo/models';
import { useGraphQLQuery } from '../hooks/use-graphql-query';
import { WidgetLayout } from '../components/WidgetLayout';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { StatusBadge } from '../components/StatusBadge';
import { LIST_EXECUTIONS_QUERY } from '../__generated__/queries/all-queries';
import type { ListExecutionsQuery } from '../__generated__/graphql';
import '../shared/index.css';

function ExecutionList() {
  const [statusFilter, setStatusFilter] = useState<Status | 'all'>('all');
  const { data, loading, error, refetch } = useGraphQLQuery<ListExecutionsQuery>(
    LIST_EXECUTIONS_QUERY,
    { limit: 50 },
    { refetchInterval: 10000 } // Refetch every 10 seconds
  );

  const filteredExecutions = data?.listExecutions?.filter((execution) => {
    if (statusFilter === 'all') return true;
    return execution.status === statusFilter;
  }) || [];

  const formatDuration = (started_at: string | null | undefined, ended_at: string | null | undefined) => {
    if (!started_at) return 'N/A';
    if (!ended_at) return 'In progress';
    const duration = new Date(ended_at).getTime() - new Date(started_at).getTime();
    const seconds = Math.floor(duration / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    return `${minutes}m ${seconds % 60}s`;
  };

  return (
    <WidgetLayout
      title="Execution History"
      error={error}
      loading={loading && !data}
    >
      {/* Status Filter */}
      <div className="mb-4 flex gap-2 flex-wrap">
        {['all', Status.RUNNING, Status.COMPLETED, Status.FAILED, Status.PENDING].map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status as Status | 'all')}
            className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
              statusFilter === status
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {status === 'all' ? 'All' : status.charAt(0).toUpperCase() + status.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      {/* Execution Count */}
      <div className="text-sm text-gray-600 mb-3">
        {filteredExecutions.length} execution{filteredExecutions.length !== 1 ? 's' : ''}
      </div>

      {/* Execution Cards */}
      <div className="space-y-3">
        {filteredExecutions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No executions found
          </div>
        ) : (
          filteredExecutions.map((execution) => (
            <div
              key={execution.id}
              className="border border-gray-200 rounded-lg p-4 hover:border-blue-400 hover:shadow-sm transition-all"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <StatusBadge status={execution.status} />
                    <span className="font-semibold text-gray-900">
                      {execution.diagram_id || 'Unknown Diagram'}
                    </span>
                  </div>
                  <div className="text-xs font-mono text-gray-500">
                    {execution.id}
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs text-gray-600">
                <span>
                  Started: {execution.started_at ? new Date(execution.started_at).toLocaleString() : 'N/A'}
                </span>
                <span className="font-medium">
                  {formatDuration(execution.started_at, execution.ended_at)}
                </span>
              </div>

              {execution.error && (
                <div className="mt-2 text-xs text-red-600 bg-red-50 rounded px-2 py-1">
                  Error: {execution.error}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Refresh Button */}
      {data && (
        <button
          onClick={() => refetch()}
          className="mt-4 w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Refresh
        </button>
      )}
    </WidgetLayout>
  );
}

// Mount the widget
const rootElement = document.getElementById('execution-list-root');
if (rootElement) {
  const root = createRoot(rootElement);
  root.render(
    <ErrorBoundary>
      <ExecutionList />
    </ErrorBoundary>
  );
}
