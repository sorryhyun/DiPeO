import React, { useState, useMemo } from 'react';
import { Search, X, Clock, CheckCircle2, XCircle, AlertCircle, Activity } from 'lucide-react';
import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';

// GraphQL query to fetch recent executions
const LIST_EXECUTIONS = gql`
  query ListRecentExecutions($limit: Int) {
    executions(limit: $limit) {
      id
      diagram_id
      status
      started_at
      ended_at
      error
    }
  }
`;

interface Execution {
  id: string;
  diagramName: string;
  status: string;
  startedAt: string;
  finishedAt?: string | null;
  errorMessage?: string | null;
}

interface RunPickerProps {
  onSelect: (executionId: string) => void;
  onClose: () => void;
  existingIds: string[];
}

export function RunPicker({ onSelect, onClose, existingIds }: RunPickerProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [manualId, setManualId] = useState('');

  // Fetch recent executions
  const { data, loading, error } = useQuery(LIST_EXECUTIONS, {
    variables: { limit: 50 },
    pollInterval: 5000, // Poll every 5 seconds for updates
  });

  // Filter executions based on search term and exclude already added ones
  const filteredExecutions = useMemo(() => {
    if (!data?.executions) return [];
    
    return data.executions.filter((exec: Execution) => {
      // Exclude already added executions
      if (existingIds.includes(exec.id)) return false;
      
      // Apply search filter
      if (!searchTerm) return true;
      
      const searchLower = searchTerm.toLowerCase();
      return (
        exec.id.toLowerCase().includes(searchLower) ||
        exec.diagramName.toLowerCase().includes(searchLower) ||
        exec.status.toLowerCase().includes(searchLower)
      );
    });
  }, [data, searchTerm, existingIds]);

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running':
        return <Activity className="w-4 h-4 text-blue-400 animate-pulse" />;
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-400" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-400" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleManualAdd = () => {
    if (manualId.trim() && !existingIds.includes(manualId.trim())) {
      onSelect(manualId.trim());
      setManualId('');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-gray-900 rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
          <h2 className="text-lg font-semibold text-gray-200">
            Add Execution to Board
          </h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Search bar */}
        <div className="px-6 py-4 border-b border-gray-800">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search executions by ID or diagram name..."
              className="w-full pl-10 pr-4 py-2 bg-gray-800 text-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
          </div>
        </div>

        {/* Manual ID input */}
        <div className="px-6 py-3 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={manualId}
              onChange={(e) => setManualId(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleManualAdd()}
              placeholder="Or enter execution ID manually..."
              className="flex-1 px-3 py-1.5 bg-gray-800 text-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleManualAdd}
              disabled={!manualId.trim() || existingIds.includes(manualId.trim())}
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg text-sm transition-colors"
            >
              Add
            </button>
          </div>
        </div>

        {/* Executions list */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {loading && (
            <div className="flex items-center justify-center py-8">
              <div className="text-gray-500">Loading executions...</div>
            </div>
          )}
          
          {error && (
            <div className="flex items-center justify-center py-8">
              <div className="text-red-400">Failed to load executions</div>
            </div>
          )}
          
          {!loading && !error && filteredExecutions.length === 0 && (
            <div className="flex items-center justify-center py-8">
              <div className="text-gray-500">
                {searchTerm ? 'No matching executions found' : 'No recent executions available'}
              </div>
            </div>
          )}
          
          {!loading && !error && filteredExecutions.length > 0 && (
            <div className="space-y-2">
              {filteredExecutions.map((execution: Execution) => (
                <button
                  key={execution.id}
                  onClick={() => onSelect(execution.id)}
                  className="w-full p-3 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors text-left group"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5">
                        {getStatusIcon(execution.status)}
                      </div>
                      <div>
                        <div className="font-medium text-gray-200">
                          {execution.diagram_id || 'Unknown Diagram'}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          ID: {execution.id}
                        </div>
                        <div className="text-xs text-gray-500 mt-0.5">
                          Started: {formatTime(execution.startedAt)}
                          {execution.finishedAt && (
                            <span className="ml-2">
                              • Ended: {formatTime(execution.finishedAt)}
                            </span>
                          )}
                        </div>
                        {execution.errorMessage && (
                          <div className="text-xs text-red-400 mt-1 truncate">
                            {execution.errorMessage}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                      <span className="text-xs text-blue-400">
                        Click to add →
                      </span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}