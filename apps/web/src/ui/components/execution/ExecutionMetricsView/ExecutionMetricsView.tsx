import React, { useEffect, useState } from 'react';
import { BarChart3, Clock, Cpu, TrendingUp, Download } from 'lucide-react';
import { Button } from '@/ui/components/common/forms/buttons';

interface TokenUsage {
  input: number;
  output: number;
  total: number;
}

interface NodeMetrics {
  node_id: string;
  node_type: string;
  duration_ms: number;
  token_usage: TokenUsage;
  error?: string;
}

interface ExecutionMetrics {
  execution_id: string;
  total_duration_ms: number;
  node_count: number;
  total_token_usage: TokenUsage;
  bottlenecks: Array<{
    node_id: string;
    node_type: string;
    duration_ms: number;
  }>;
  critical_path_length: number;
  parallelizable_groups: number;
  node_breakdown?: NodeMetrics[];
}

export interface ExecutionMetricsViewProps {
  executionId: string;
  metrics?: ExecutionMetrics | null;
  isActive?: boolean;
  onExport?: (format: 'json' | 'csv') => void;
}

export const ExecutionMetricsView: React.FC<ExecutionMetricsViewProps> = ({
  executionId,
  metrics: initialMetrics,
  isActive = false,
  onExport,
}) => {
  const [metrics, setMetrics] = useState<ExecutionMetrics | null>(initialMetrics || null);
  const [sortField, setSortField] = useState<'node_id' | 'duration' | 'tokens'>('duration');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    if (initialMetrics) {
      setMetrics(initialMetrics);
    }
  }, [initialMetrics]);

  const handleSort = (field: 'node_id' | 'duration' | 'tokens') => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const getSortedNodeBreakdown = () => {
    if (!metrics?.node_breakdown) return [];

    return [...metrics.node_breakdown].sort((a, b) => {
      let compareValue = 0;

      switch (sortField) {
        case 'node_id':
          compareValue = a.node_id.localeCompare(b.node_id);
          break;
        case 'duration':
          compareValue = a.duration_ms - b.duration_ms;
          break;
        case 'tokens':
          compareValue = a.token_usage.total - b.token_usage.total;
          break;
      }

      return sortOrder === 'asc' ? compareValue : -compareValue;
    });
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const exportToJSON = () => {
    if (!metrics) return;

    const dataStr = JSON.stringify(metrics, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);

    const exportLink = document.createElement('a');
    exportLink.setAttribute('href', dataUri);
    exportLink.setAttribute('download', `metrics_${executionId}.json`);
    document.body.appendChild(exportLink);
    exportLink.click();
    document.body.removeChild(exportLink);
  };

  const exportToCSV = () => {
    if (!metrics?.node_breakdown) return;

    const headers = ['Node ID', 'Node Type', 'Duration (ms)', 'Input Tokens', 'Output Tokens', 'Total Tokens', 'Error'];
    const rows = metrics.node_breakdown.map(node => [
      node.node_id,
      node.node_type,
      node.duration_ms.toString(),
      node.token_usage.input.toString(),
      node.token_usage.output.toString(),
      node.token_usage.total.toString(),
      node.error || '',
    ]);

    const csvContent = [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');

    const dataUri = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csvContent);

    const exportLink = document.createElement('a');
    exportLink.setAttribute('href', dataUri);
    exportLink.setAttribute('download', `metrics_${executionId}.csv`);
    document.body.appendChild(exportLink);
    exportLink.click();
    document.body.removeChild(exportLink);
  };

  if (!metrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No metrics available yet</p>
          {isActive && (
            <p className="text-sm text-gray-400 mt-2">Metrics will appear as the execution progresses</p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="pb-2">
            <h3 className="text-sm font-medium text-gray-500">Total Duration</h3>
          </div>
          <div>
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-bold">{formatDuration(metrics.total_duration_ms)}</span>
              <Clock className="h-4 w-4 text-gray-400" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="pb-2">
            <h3 className="text-sm font-medium text-gray-500">Total Tokens</h3>
          </div>
          <div>
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-bold">{metrics.total_token_usage.total.toLocaleString()}</span>
              <Cpu className="h-4 w-4 text-gray-400" />
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {metrics.total_token_usage.input.toLocaleString()} in / {metrics.total_token_usage.output.toLocaleString()} out
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="pb-2">
            <h3 className="text-sm font-medium text-gray-500">Nodes Executed</h3>
          </div>
          <div>
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-bold">{metrics.node_count}</span>
              {metrics.critical_path_length > 0 && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                  {metrics.critical_path_length} critical
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="pb-2">
            <h3 className="text-sm font-medium text-gray-500">Optimization Potential</h3>
          </div>
          <div>
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-bold">{metrics.parallelizable_groups}</span>
              <TrendingUp className="h-4 w-4 text-green-500" />
            </div>
            <div className="text-xs text-gray-500 mt-1">parallelizable groups</div>
          </div>
        </div>
      </div>

      {/* Bottlenecks */}
      {metrics.bottlenecks && metrics.bottlenecks.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="mb-4">
            <h3 className="text-lg font-semibold">Performance Bottlenecks</h3>
          </div>
          <div>
            <div className="space-y-2">
              {metrics.bottlenecks.slice(0, 3).map((bottleneck, idx) => (
                <div key={bottleneck.node_id} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                      idx === 0 ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      #{idx + 1}
                    </span>
                    <span className="font-medium">{bottleneck.node_id}</span>
                    <span className="text-sm text-gray-500">({bottleneck.node_type})</span>
                  </div>
                  <span className="font-mono text-sm">{formatDuration(bottleneck.duration_ms)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Node Breakdown Table */}
      {metrics.node_breakdown && metrics.node_breakdown.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="mb-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Node Breakdown</h3>
              <div className="flex space-x-2">
                <Button variant="ghost" size="sm" onClick={exportToJSON}>
                  <Download className="h-4 w-4 mr-1" />
                  JSON
                </Button>
                <Button variant="ghost" size="sm" onClick={exportToCSV}>
                  <Download className="h-4 w-4 mr-1" />
                  CSV
                </Button>
              </div>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th
                    className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('node_id')}
                  >
                    Node ID {sortField === 'node_id' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th
                    className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('duration')}
                  >
                    Duration {sortField === 'duration' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('tokens')}
                  >
                    Tokens {sortField === 'tokens' && (sortOrder === 'asc' ? '↑' : '↓')}
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {getSortedNodeBreakdown().map(node => (
                  <tr key={node.node_id} className="hover:bg-gray-50">
                    <td className="px-4 py-2 whitespace-nowrap font-medium">{node.node_id}</td>
                    <td className="px-4 py-2 whitespace-nowrap">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        {node.node_type}
                      </span>
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap text-right font-mono text-sm">
                      {formatDuration(node.duration_ms)}
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap text-right">
                      <div className="space-y-1">
                        <div className="font-mono text-sm">{node.token_usage.total.toLocaleString()}</div>
                        <div className="text-xs text-gray-500">
                          {node.token_usage.input}↓ {node.token_usage.output}↑
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap">
                      {node.error ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          Error
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Success
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Live indicator */}
      {isActive && (
        <div className="flex items-center justify-center space-x-2 text-sm text-gray-500">
          <div className="animate-pulse h-2 w-2 bg-green-500 rounded-full" />
          <span>Metrics updating in real-time</span>
        </div>
      )}
    </div>
  );
};
