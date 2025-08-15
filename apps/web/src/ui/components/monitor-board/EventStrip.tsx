import React, { useMemo, useState } from 'react';
import { useStore } from 'zustand';
import { ChevronRight, AlertCircle, CheckCircle, XCircle, Clock, Activity } from 'lucide-react';
import type { StoreApi } from 'zustand';
import type { ExecutionLocalStore, NodeEvent } from './executionLocalStore';

interface EventStripProps {
  executionId: string;
  store: StoreApi<ExecutionLocalStore>;
}

interface Event {
  id: string;
  type: 'start' | 'complete' | 'fail' | 'node_start' | 'node_complete' | 'node_fail';
  timestamp: number;
  nodeId?: string;
  message: string;
  error?: string;
}

export function EventStrip({ executionId, store }: EventStripProps) {
  const { startedAt, finishedAt, nodeEvents, nodeStates, isRunning } = useStore(store);
  const [expandedEvents, setExpandedEvents] = useState<Set<string>>(new Set());

  // Generate events from execution and node events
  const events = useMemo(() => {
    const eventList: Event[] = [];
    
    // Add execution start event
    if (startedAt) {
      eventList.push({
        id: 'exec-start',
        type: 'start',
        timestamp: startedAt,
        message: 'Execution started',
      });
    }
    
    // Add node events from the chronological events array
    nodeEvents.forEach((event, index) => {
      // Use index and timestamp to ensure unique IDs for nodes that run multiple times
      const baseId = `node-${event.nodeId}-${event.timestamp}-${index}`;
      
      if (event.status === 'running') {
        eventList.push({
          id: baseId,
          type: 'node_start',
          timestamp: event.timestamp,
          nodeId: event.nodeId,
          message: `Node ${event.nodeId} started`,
        });
      } else if (event.status === 'completed') {
        eventList.push({
          id: baseId,
          type: 'node_complete',
          timestamp: event.timestamp,
          nodeId: event.nodeId,
          message: `Node ${event.nodeId} completed`,
        });
      } else if (event.status === 'failed') {
        eventList.push({
          id: baseId,
          type: 'node_fail',
          timestamp: event.timestamp,
          nodeId: event.nodeId,
          message: `Node ${event.nodeId} failed`,
          error: event.error || undefined,
        });
      }
    });
    
    // Add execution end event
    if (finishedAt) {
      const hasFailed = Array.from(nodeStates.values()).some(s => s.status === 'failed');
      eventList.push({
        id: 'exec-end',
        type: hasFailed ? 'fail' : 'complete',
        timestamp: finishedAt,
        message: hasFailed ? 'Execution failed' : 'Execution completed',
      });
    }
    
    // Sort by timestamp (should already be sorted, but ensure it)
    return eventList.sort((a, b) => a.timestamp - b.timestamp);
  }, [startedAt, finishedAt, nodeEvents, nodeStates]);

  const toggleEvent = (eventId: string) => {
    setExpandedEvents(prev => {
      const next = new Set(prev);
      if (next.has(eventId)) {
        next.delete(eventId);
      } else {
        next.add(eventId);
      }
      return next;
    });
  };

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 1,
    });
  };

  const formatRelativeTime = (timestamp: number) => {
    if (!startedAt) return '';
    const seconds = (timestamp - startedAt) / 1000;
    return `+${seconds.toFixed(1)}s`;
  };

  const getEventIcon = (type: Event['type']) => {
    switch (type) {
      case 'start':
      case 'node_start':
        return <Activity className="w-3 h-3 text-blue-400" />;
      case 'complete':
      case 'node_complete':
        return <CheckCircle className="w-3 h-3 text-green-400" />;
      case 'fail':
      case 'node_fail':
        return <XCircle className="w-3 h-3 text-red-400" />;
      default:
        return <Clock className="w-3 h-3 text-gray-400" />;
    }
  };

  if (events.length === 0) {
    return (
      <div className="h-24 rounded-lg bg-gray-900/30 border border-gray-700 flex items-center justify-center">
        <div className="text-xs text-gray-500">
          {isRunning ? 'Waiting for events...' : 'No events'}
        </div>
      </div>
    );
  }

  return (
    <div className="h-24 rounded-lg bg-gray-900/30 border border-gray-700 overflow-hidden">
      <div className="h-full overflow-y-auto custom-scrollbar p-2 space-y-1">
        {events.map((event) => {
          const isExpanded = expandedEvents.has(event.id);
          const hasError = !!event.error;
          
          return (
            <div
              key={event.id}
              className={`
                rounded px-2 py-1 text-xs transition-colors cursor-pointer
                ${hasError ? 'bg-red-900/20 hover:bg-red-900/30' : 'bg-gray-800/50 hover:bg-gray-800/70'}
              `}
              onClick={() => hasError && toggleEvent(event.id)}
            >
              <div className="flex items-center gap-2">
                {/* Event icon */}
                <div className="flex-shrink-0">
                  {getEventIcon(event.type)}
                </div>
                
                {/* Timestamp */}
                <div className="flex-shrink-0 text-gray-500 font-mono text-[10px]">
                  {formatTime(event.timestamp)}
                  <span className="ml-1 text-gray-600">
                    {formatRelativeTime(event.timestamp)}
                  </span>
                </div>
                
                {/* Message */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1">
                    {hasError && (
                      <ChevronRight 
                        className={`w-3 h-3 text-gray-500 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                      />
                    )}
                    <span className={`${hasError ? 'text-red-400' : 'text-gray-300'} truncate`}>
                      {event.message}
                    </span>
                  </div>
                </div>
                
                {/* Node ID badge */}
                {event.nodeId && (
                  <div className="flex-shrink-0">
                    <span className="px-1.5 py-0.5 bg-gray-700/50 rounded text-[10px] text-gray-400 font-mono">
                      {event.nodeId.slice(0, 8)}
                    </span>
                  </div>
                )}
              </div>
              
              {/* Expanded error details */}
              {hasError && isExpanded && event.error && (
                <div className="mt-1 pl-5 pr-2 py-1 bg-red-900/10 rounded text-[10px] text-red-300/80 font-mono break-all">
                  {event.error}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}