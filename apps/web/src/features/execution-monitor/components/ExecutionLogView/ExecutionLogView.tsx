import React, { useState, useEffect, useRef } from 'react';
import { FileText, Info, AlertCircle, AlertTriangle, Download, Trash2 } from 'lucide-react';
import { Button } from '@/shared/components/forms/buttons';
import { useExecutionLogStream } from '../../hooks/useExecutionLogStream';
import { useExecution } from '../../hooks';
import { formatTimestamp } from '@/lib/utils/date';
import { executionId } from '@/core/types';

interface LogEntry {
  level: string;
  message: string;
  timestamp: string;
  logger: string;
  node_id?: string;
}

const LogLevelIcon: React.FC<{ level: string }> = ({ level }) => {
  switch (level.toUpperCase()) {
    case 'ERROR':
      return <AlertCircle className="h-4 w-4 text-red-500" />;
    case 'WARNING':
    case 'WARN':
      return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    case 'INFO':
      return <Info className="h-4 w-4 text-blue-500" />;
    default:
      return <FileText className="h-4 w-4 text-gray-400" />;
  }
};

const getLogLevelColor = (level: string): string => {
  switch (level.toUpperCase()) {
    case 'ERROR':
      return 'text-red-600 bg-red-50';
    case 'WARNING':
    case 'WARN':
      return 'text-yellow-600 bg-yellow-50';
    case 'INFO':
      return 'text-blue-600 bg-blue-50';
    case 'DEBUG':
      return 'text-gray-600 bg-gray-50';
    default:
      return 'text-gray-500 bg-gray-50';
  }
};

export const ExecutionLogView: React.FC = () => {
  const { execution } = useExecution();
  const { logs, clearLogs } = useExecutionLogStream(execution.executionId ? executionId(execution.executionId) : null);
  const [filter, setFilter] = useState<string>('');
  const [levelFilter, setLevelFilter] = useState<string>('ALL');
  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const filteredLogs = logs.filter(log => {
    const matchesText = !filter || 
      log.message.toLowerCase().includes(filter.toLowerCase()) ||
      log.logger.toLowerCase().includes(filter.toLowerCase()) ||
      (log.node_id && log.node_id.toLowerCase().includes(filter.toLowerCase()));
    
    const matchesLevel = levelFilter === 'ALL' || log.level.toUpperCase() === levelFilter;
    
    return matchesText && matchesLevel;
  });

  const exportLogs = () => {
    const logText = filteredLogs.map(log => 
      `[${log.timestamp}] [${log.level}] ${log.logger}${log.node_id ? ` (${log.node_id})` : ''}: ${log.message}`
    ).join('\n');
    
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `execution-log-${execution.executionId}-${new Date().toISOString()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (!execution.isRunning && logs.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400">
        <div className="text-center">
          <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
          <p>No execution logs available</p>
          <p className="text-sm mt-1">Logs will appear here when an execution starts</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col">
      {/* Controls */}
      <div className="px-4 py-2 bg-gray-50 border-b flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <input
            type="text"
            placeholder="Filter logs..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-1 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="px-3 py-1 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="ALL">All Levels</option>
            <option value="DEBUG">Debug</option>
            <option value="INFO">Info</option>
            <option value="WARNING">Warning</option>
            <option value="ERROR">Error</option>
          </select>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={exportLogs}
            disabled={filteredLogs.length === 0}
          >
            <Download className="h-4 w-4 mr-1" />
            Export
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={clearLogs}
            disabled={logs.length === 0}
          >
            <Trash2 className="h-4 w-4 mr-1" />
            Clear
          </Button>
        </div>
      </div>

      {/* Logs */}
      <div className="flex-1 overflow-auto p-4 font-mono text-xs">
        {filteredLogs.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            No logs match your filter criteria
          </div>
        ) : (
          <div className="space-y-1">
            {filteredLogs.map((log, index) => (
              <div
                key={index}
                className={`flex items-start space-x-2 py-1 px-2 rounded ${
                  log.level.toUpperCase() === 'ERROR' ? 'bg-red-50' : ''
                }`}
              >
                <LogLevelIcon level={log.level} />
                <div className="flex-1 break-all">
                  <span className="text-gray-500">{formatTimestamp(log.timestamp)}</span>
                  <span className={`ml-2 px-1 py-0.5 text-xs rounded ${getLogLevelColor(log.level)}`}>
                    {log.level}
                  </span>
                  <span className="ml-2 text-gray-600">{log.logger}</span>
                  {log.node_id && (
                    <span className="ml-2 text-purple-600">({log.node_id.slice(0, 8)}...)</span>
                  )}
                  <div className="mt-1 text-gray-800">{log.message}</div>
                </div>
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        )}
      </div>

      {/* Status */}
      {execution.isRunning && (
        <div className="px-4 py-2 bg-green-50 border-t text-sm text-green-700 flex items-center">
          <div className="animate-pulse w-2 h-2 bg-green-500 rounded-full mr-2" />
          Streaming logs...
        </div>
      )}
    </div>
  );
};

export default ExecutionLogView;