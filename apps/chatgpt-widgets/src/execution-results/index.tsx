/**
 * Execution Results Widget
 *
 * Displays comprehensive execution results including:
 * - Execution status and metadata
 * - Node execution timeline
 * - Token usage metrics
 * - Output data
 */

import { createRoot } from 'react-dom/client';
import { useWidgetProps } from '../hooks/use-widget-state';
import { useGraphQLQuery } from '../hooks/use-graphql-query';
import { WidgetLayout } from '../components/WidgetLayout';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { StatusBadge } from '../components/StatusBadge';
import { GET_EXECUTION_QUERY } from '../__generated__/queries/all-queries';
import type { GetExecutionQuery } from '../__generated__/graphql';
import '../shared/index.css';

interface ExecutionResultsProps {
  executionId: string;
}

function ExecutionResults() {
  const props = useWidgetProps<ExecutionResultsProps>();

  const { data, loading, error } = useGraphQLQuery<GetExecutionQuery>(
    GET_EXECUTION_QUERY,
    { executionId: props?.executionId },
    { skip: !props?.executionId, refetchInterval: 5000 }
  );

  if (!props) {
    return (
      <WidgetLayout>
        <div className="text-sm text-gray-500">Waiting for execution data...</div>
      </WidgetLayout>
    );
  }

  return (
    <WidgetLayout
      title="Execution Results"
      error={error}
      loading={loading && !data}
    >
      {data?.getExecution && (
        <div className="space-y-4">
          {/* Status Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <StatusBadge status={data.getExecution.status} />
              <span className="text-sm font-medium text-gray-700">
                {data.getExecution.diagram_id || 'Unknown Diagram'}
              </span>
            </div>
            <div className="text-xs text-gray-500">
              {data.getExecution.id}
            </div>
          </div>

          {/* Timing Information */}
          <div className="bg-gray-50 rounded-lg p-3 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Started:</span>
              <span className="font-mono text-gray-900">
                {data.getExecution.started_at ? new Date(data.getExecution.started_at).toLocaleString() : 'N/A'}
              </span>
            </div>
            {data.getExecution.ended_at && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Completed:</span>
                <span className="font-mono text-gray-900">
                  {new Date(data.getExecution.ended_at).toLocaleString()}
                </span>
              </div>
            )}
          </div>

          {/* Error */}
          {data.getExecution.error && (
            <div className="bg-red-50 rounded-lg p-3">
              <h3 className="text-sm font-semibold text-red-700 mb-2">Error</h3>
              <pre className="text-xs text-red-600 overflow-x-auto whitespace-pre-wrap">
                {data.getExecution.error}
              </pre>
            </div>
          )}

          {/* Metrics */}
          {data.getExecution.metrics && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Metrics</h3>
              <pre className="bg-gray-50 rounded-lg p-3 text-xs overflow-x-auto">
                {JSON.stringify(data.getExecution.metrics, null, 2)}
              </pre>
            </div>
          )}

          {/* LLM Usage */}
          {data.getExecution.llm_usage && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">LLM Usage</h3>
              <div className="bg-gray-50 rounded-lg p-3 space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Input Tokens:</span>
                  <span className="font-mono">{data.getExecution.llm_usage.input || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Output Tokens:</span>
                  <span className="font-mono">{data.getExecution.llm_usage.output || 0}</span>
                </div>
                {data.getExecution.llm_usage.cached !== null && data.getExecution.llm_usage.cached !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Cached Tokens:</span>
                    <span className="font-mono">{data.getExecution.llm_usage.cached}</span>
                  </div>
                )}
                {data.getExecution.llm_usage.total !== null && data.getExecution.llm_usage.total !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Cost:</span>
                    <span className="font-mono">${data.getExecution.llm_usage.total.toFixed(4)}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </WidgetLayout>
  );
}

// Mount the widget
const rootElement = document.getElementById('execution-results-root');
if (rootElement) {
  const root = createRoot(rootElement);
  root.render(
    <ErrorBoundary>
      <ExecutionResults />
    </ErrorBoundary>
  );
}
