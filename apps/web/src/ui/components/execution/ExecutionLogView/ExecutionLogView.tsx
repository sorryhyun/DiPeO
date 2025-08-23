import React, { useState, useEffect, useRef, useCallback } from 'react';
import { FileText, Info, AlertCircle, AlertTriangle, Download, Trash2, ArrowDown } from 'lucide-react';
import { Button } from '@/ui/components/common/forms/buttons';
import { useExecutionLogStream } from '@/domain/execution/hooks/useExecutionLogStream';
import { useCanvas } from '@/domain/diagram/contexts';
import { formatTimestamp } from '@/lib/utils/date';
import { executionId } from '@/infrastructure/types';

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
      return 'text-red-400 bg-red-900/20';
    case 'WARNING':
    case 'WARN':
      return 'text-yellow-400 bg-yellow-900/20';
    case 'INFO':
      return 'text-blue-400 bg-blue-900/20';
    case 'DEBUG':
      return 'text-gray-300 bg-gray-800/20';
    default:
      return 'text-gray-400 bg-gray-800/20';
  }
};

export const ExecutionLogView: React.FC = () => {
  // Get execution from Canvas context to avoid multiple instances
  const { operations } = useCanvas();
  const { execution, isRunning } = operations.executionOps;
  // execution.executionId is already a string, don't need to wrap it
  const { logs, clearLogs } = useExecutionLogStream(execution.executionId as ReturnType<typeof executionId> | null);
  const [filter, setFilter] = useState<string>('');
  const [levelFilter, setLevelFilter] = useState<string>('ALL');
  const logsEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [isAtBottom, setIsAtBottom] = useState(true);
  const [autoScroll, setAutoScroll] = useState(true);

  // Check if user is at bottom of scroll
  const checkIfAtBottom = useCallback(() => {
    if (!scrollContainerRef.current) return true;
    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    return Math.abs(scrollHeight - scrollTop - clientHeight) < 10;
  }, []);

  // Handle scroll events
  const handleScroll = useCallback(() => {
    const atBottom = checkIfAtBottom();
    setIsAtBottom(atBottom);
    // Disable auto-scroll if user scrolls up manually
    if (!atBottom && autoScroll) {
      setAutoScroll(false);
    }
    // Re-enable auto-scroll if user scrolls back to bottom
    if (atBottom && !autoScroll) {
      setAutoScroll(true);
    }
  }, [checkIfAtBottom, autoScroll]);

  // Scroll to bottom function
  const scrollToBottom = useCallback(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    setAutoScroll(true);
  }, []);

  // Auto-scroll to bottom when new logs arrive (only if autoScroll is enabled)
  useEffect(() => {
    if (autoScroll) {
      logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

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

  if (!isRunning && logs.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-900 text-gray-400">
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
      <div className="px-4 py-2 bg-gray-800 border-b border-gray-700 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <input
            type="text"
            placeholder="Filter logs..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-1 text-sm bg-gray-700 text-white border border-gray-600 rounded-md placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="px-3 py-1 text-sm bg-gray-700 text-white border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
      <div className="flex-1 relative">
        <div 
          ref={scrollContainerRef}
          onScroll={handleScroll}
          className="h-full overflow-auto p-4 font-mono text-xs bg-gray-900"
        >
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
                    log.level.toUpperCase() === 'ERROR' ? 'bg-red-900/10' : ''
                  }`}
                >
                  <LogLevelIcon level={log.level} />
                  <div className="flex-1 break-all">
                    <span className="text-gray-400">{formatTimestamp(log.timestamp)}</span>
                    <span className={`ml-2 px-1 py-0.5 text-xs rounded ${getLogLevelColor(log.level)}`}>
                      {log.level}
                    </span>
                    <span className="ml-2 text-gray-300">{log.logger}</span>
                    {log.node_id && (
                      <span className="ml-2 text-purple-400">({log.node_id.slice(0, 8)}...)</span>
                    )}
                    <div className="mt-1 text-white">{log.message}</div>
                  </div>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          )}
        </div>

        {/* Scroll to bottom button */}
        {!isAtBottom && filteredLogs.length > 0 && (
          <button
            onClick={scrollToBottom}
            className="absolute bottom-4 right-4 p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg transition-all duration-200 hover:scale-110"
            title="Scroll to bottom"
          >
            <ArrowDown className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Status */}
      {isRunning && (
        <div className="px-4 py-2 bg-green-900/20 border-t border-gray-700 text-sm text-green-400 flex items-center justify-between">
          <div className="flex items-center">
            <div className="animate-pulse w-2 h-2 bg-green-400 rounded-full mr-2" />
            Streaming logs...
          </div>
          {!autoScroll && (
            <div className="text-yellow-400 text-xs">
              Auto-scroll paused • Scroll down to resume
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ExecutionLogView;