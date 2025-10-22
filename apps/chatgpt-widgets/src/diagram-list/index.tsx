/**
 * Diagram List Widget
 *
 * Displays a searchable, filterable list of available DiPeO diagrams
 */

import { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { useGraphQLQuery } from '../hooks/use-graphql-query';
import { WidgetLayout } from '../components/WidgetLayout';
import { ErrorBoundary } from '../components/ErrorBoundary';
import { LIST_DIAGRAMS_QUERY } from '../__generated__/queries/all-queries';
import type { ListDiagramsQuery } from '../__generated__/graphql';
import '../shared/index.css';

function DiagramList() {
  const [searchQuery, setSearchQuery] = useState('');
  const { data, loading, error, refetch } = useGraphQLQuery<ListDiagramsQuery>(
    LIST_DIAGRAMS_QUERY
  );

  const filteredDiagrams = data?.listDiagrams?.filter((diagram) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      diagram.metadata?.name?.toLowerCase().includes(query) ||
      diagram.metadata?.description?.toLowerCase().includes(query)
    );
  }) || [];

  return (
    <WidgetLayout
      title="DiPeO Diagrams"
      error={error}
      loading={loading && !data}
    >
      {/* Search Box */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search diagrams..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Diagram Count */}
      <div className="text-sm text-gray-600 mb-3">
        {filteredDiagrams.length} diagram{filteredDiagrams.length !== 1 ? 's' : ''} found
      </div>

      {/* Diagram Cards */}
      <div className="space-y-3">
        {filteredDiagrams.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No diagrams found
          </div>
        ) : (
          filteredDiagrams.map((diagram, index) => (
            <div
              key={diagram.metadata?.name || `diagram-${index}`}
              className="border border-gray-200 rounded-lg p-4 hover:border-blue-400 hover:shadow-sm transition-all cursor-pointer"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{diagram.metadata?.name || 'Unnamed Diagram'}</h3>
                  {diagram.metadata?.description && (
                    <p className="text-sm text-gray-600 mt-1">{diagram.metadata.description}</p>
                  )}
                  <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                    {diagram.metadata?.format && (
                      <span className="px-2 py-0.5 bg-gray-100 rounded">
                        {diagram.metadata.format}
                      </span>
                    )}
                    {diagram.nodes && (
                      <span>{diagram.nodes.length} nodes</span>
                    )}
                    {diagram.metadata?.created && (
                      <span>{new Date(diagram.metadata.created).toLocaleDateString()}</span>
                    )}
                  </div>
                </div>
              </div>
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
const rootElement = document.getElementById('diagram-list-root');
if (rootElement) {
  const root = createRoot(rootElement);
  root.render(
    <ErrorBoundary>
      <DiagramList />
    </ErrorBoundary>
  );
}
