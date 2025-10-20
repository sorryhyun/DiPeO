/**
 * Execution Results Widget
 *
 * Displays comprehensive execution results including:
 * - Execution status and metadata
 * - Node execution timeline
 * - Token usage metrics
 * - Output data
 */

import React from 'react';
import { createRoot } from 'react-dom/client';
import { useWidgetProps } from '../hooks/use-widget-state';
import { useGraphQLQuery } from '../hooks/use-graphql-query';
import { WidgetLayout } from '../components/WidgetLayout';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { StatusBadge, Status } from '../components/StatusBadge';
import '../shared/index.css';

interface ExecutionResultsProps {
  executionId: string;
}

interface ExecutionData {
  execution: {
    sessionId: string;
    status: Status;
    diagramName: string;
    startedAt: string;
    completedAt: string | null;
    metadata: Record<string, any>;
  };
}

const GET_EXECUTION_QUERY = `
  query GetExecution($sessionId: String!) {
    execution(sessionId: $sessionId) {
      sessionId
      status
      diagramName
      startedAt
      completedAt
      metadata
    }
  }
`;

function ExecutionResults() {
  const props = useWidgetProps<ExecutionResultsProps>();

  const { data, loading, error } = useGraphQLQuery<ExecutionData>(
    GET_EXECUTION_QUERY,
    { sessionId: props?.executionId },
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
      {data?.execution && (
        <div className="space-y-4">
          {/* Status Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <StatusBadge status={data.execution.status} />
              <span className="text-sm font-medium text-gray-700">
                {data.execution.diagramName}
              </span>
            </div>
            <div className="text-xs text-gray-500">
              {data.execution.sessionId}
            </div>
          </div>

          {/* Timing Information */}
          <div className="bg-gray-50 rounded-lg p-3 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Started:</span>
              <span className="font-mono text-gray-900">
                {new Date(data.execution.startedAt).toLocaleString()}
              </span>
            </div>
            {data.execution.completedAt && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Completed:</span>
                <span className="font-mono text-gray-900">
                  {new Date(data.execution.completedAt).toLocaleString()}
                </span>
              </div>
            )}
          </div>

          {/* Metadata */}
          {data.execution.metadata && Object.keys(data.execution.metadata).length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Metadata</h3>
              <pre className="bg-gray-50 rounded-lg p-3 text-xs overflow-x-auto">
                {JSON.stringify(data.execution.metadata, null, 2)}
              </pre>
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
