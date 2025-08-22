import React, { useEffect, useState, useRef } from 'react';
import { useWebSocket } from '../../../shared/hooks/useWebSocket';

interface LiveUpdate {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  message: string;
  timestamp: number;
  source?: string;
}

interface LiveUpdatesProps {
  className?: string;
  maxItems?: number;
  height?: number;
}

const LiveUpdates: React.FC<LiveUpdatesProps> = ({
  className = '',
  maxItems = 100,
  height = 400
}) => {
  const [updates, setUpdates] = useState<LiveUpdate[]>([]);
  const announcementRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Don't connect to WebSocket in development (no backend available)
  const isDev = import.meta.env.DEV || window.location.hostname === 'localhost';
  const wsUrl = isDev 
    ? '' // Empty URL to prevent connection in development
    : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/updates`;

  const { status } = useWebSocket(isDev ? '' : wsUrl, {
    onMessage: (receivedData: any) => {
      const update: LiveUpdate = {
        id: receivedData.id || Date.now().toString(),
        type: receivedData.type || 'info',
        message: receivedData.message || 'Update received',
        timestamp: receivedData.timestamp || Date.now(),
        source: receivedData.source
      };

      setUpdates(prev => {
        const newUpdates = [update, ...prev];
        if (newUpdates.length > maxItems) {
          return newUpdates.slice(0, maxItems);
        }
        return newUpdates;
      });

      // Announce new update to screen readers
      if (announcementRef.current) {
        announcementRef.current.textContent = `New ${update.type} update: ${update.message}`;
      }

      // Auto-scroll to top when new items arrive
      if (listRef.current) {
        listRef.current.scrollTop = 0;
      }
    },
    shouldReconnect: () => !isDev // Don't try to reconnect in development
  });

  // Generate mock updates in development mode
  useEffect(() => {
    if (import.meta.env.DEV && status === 'disconnected') {
      // Create some mock updates for development
      const mockUpdates: LiveUpdate[] = [
        {
          id: '1',
          type: 'info',
          message: 'Dashboard initialized successfully',
          timestamp: Date.now() - 60000,
          source: 'System'
        },
        {
          id: '2',
          type: 'success',
          message: 'Data synchronization completed',
          timestamp: Date.now() - 120000,
          source: 'Sync Service'
        },
        {
          id: '3',
          type: 'warning',
          message: 'API rate limit approaching threshold',
          timestamp: Date.now() - 180000,
          source: 'API Monitor'
        }
      ];
      setUpdates(mockUpdates);

      // Simulate periodic updates
      const interval = setInterval(() => {
        const types: Array<'info' | 'warning' | 'error' | 'success'> = ['info', 'warning', 'error', 'success'];
        const messages = [
          'New user registered',
          'Background job completed',
          'Cache refreshed',
          'Report generated',
          'Configuration updated'
        ];
        const sources = ['System', 'API', 'Worker', 'Monitor', 'Scheduler'];

        const newUpdate: LiveUpdate = {
          id: Date.now().toString(),
          type: types[Math.floor(Math.random() * types.length)],
          message: messages[Math.floor(Math.random() * messages.length)],
          timestamp: Date.now(),
          source: sources[Math.floor(Math.random() * sources.length)]
        };

        setUpdates(prev => {
          const updated = [newUpdate, ...prev];
          return updated.slice(0, maxItems);
        });
      }, 10000); // Add a new update every 10 seconds

      return () => clearInterval(interval);
    }
  }, [status, maxItems]);

  const getTypeIcon = (type: LiveUpdate['type']) => {
    switch (type) {
      case 'error':
        return '🔴';
      case 'warning':
        return '🟡';
      case 'success':
        return '🟢';
      default:
        return '🔵';
    }
  };

  const getTypeStyles = (type: LiveUpdate['type']) => {
    switch (type) {
      case 'error':
        return 'border-l-red-500 bg-red-50 dark:bg-red-950';
      case 'warning':
        return 'border-l-yellow-500 bg-yellow-50 dark:bg-yellow-950';
      case 'success':
        return 'border-l-green-500 bg-green-50 dark:bg-green-950';
      default:
        return 'border-l-blue-500 bg-blue-50 dark:bg-blue-950';
    }
  };

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);

    if (diffSecs < 60) return `${diffSecs}s ago`;
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };

  const isConnected = status === 'connected';

  return (
    <div className={`bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 rounded-t-lg">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
            Live Updates
          </h3>
          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                isConnected
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
              }`}
              role="status"
              aria-live="polite"
            >
              <span
                className={`w-2 h-2 rounded-full mr-1 ${
                  isConnected ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {updates.length} updates
            </span>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="relative">
        {updates.length === 0 ? (
          <div className="flex items-center justify-center py-12 text-gray-500 dark:text-gray-400">
            <div className="text-center">
              <div className="text-2xl mb-2">📡</div>
              <p className="text-sm">
                {isConnected ? 'Waiting for updates...' : 'Connecting to live feed...'}
              </p>
            </div>
          </div>
        ) : (
          <div
            ref={listRef}
            role="log"
            aria-label="Live updates feed"
            aria-live="polite"
            className="overflow-y-auto focus-within:outline-none"
            style={{ height: `${height}px` }}
            tabIndex={-1}
          >
            {updates.map((update) => (
              <div
                key={update.id}
                className={`mx-2 mb-2 border-l-4 p-3 rounded-r-md shadow-sm transition-colors ${getTypeStyles(update.type)}`}
                role="listitem"
                aria-label={`${update.type} update from ${update.source || 'system'}`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start gap-2 min-w-0 flex-1">
                    <span className="text-sm flex-shrink-0" role="img" aria-label={update.type}>
                      {getTypeIcon(update.type)}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm text-gray-900 dark:text-gray-100 break-words">
                        {update.message}
                      </p>
                      {update.source && (
                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                          Source: {update.source}
                        </p>
                      )}
                    </div>
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">
                    {formatTimestamp(update.timestamp)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Screen reader announcements */}
      <div
        ref={announcementRef}
        className="sr-only"
        aria-live="assertive"
        aria-atomic="true"
      />
    </div>
  );
};

export default LiveUpdates;