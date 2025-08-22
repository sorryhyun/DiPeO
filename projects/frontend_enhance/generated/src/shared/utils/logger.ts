import { getLogLevel, isDevelopment, isProduction } from '../../app/config/config';

// Log levels in order of severity
const LOG_LEVELS = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
} as const;

type LogLevel = keyof typeof LOG_LEVELS;

interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: string;
  data?: any;
  context?: string;
}

interface LoggerConfig {
  level: LogLevel;
  enableConsole: boolean;
  enableStorage: boolean;
  maxStorageEntries: number;
  enableRemoteLogging: boolean;
}

class Logger {
  private config: LoggerConfig;
  private logStorage: LogEntry[] = [];

  constructor() {
    this.config = {
      level: getLogLevel(),
      enableConsole: isDevelopment(),
      enableStorage: true,
      maxStorageEntries: 1000,
      enableRemoteLogging: isProduction(),
    };

    // Load existing logs from localStorage if available
    this.loadStoredLogs();
  }

  private loadStoredLogs(): void {
    if (!this.config.enableStorage) return;

    try {
      const stored = localStorage.getItem('app_logs');
      if (stored) {
        const logs = JSON.parse(stored) as LogEntry[];
        this.logStorage = logs.slice(-this.config.maxStorageEntries);
      }
    } catch (error) {
      console.warn('Failed to load stored logs:', error);
    }
  }

  private saveLogsToStorage(): void {
    if (!this.config.enableStorage) return;

    try {
      // Keep only the most recent entries
      const logsToStore = this.logStorage.slice(-this.config.maxStorageEntries);
      localStorage.setItem('app_logs', JSON.stringify(logsToStore));
    } catch (error) {
      console.warn('Failed to save logs to storage:', error);
      // Clear old logs if storage is full
      this.logStorage = this.logStorage.slice(-Math.floor(this.config.maxStorageEntries / 2));
    }
  }

  private shouldLog(level: LogLevel): boolean {
    return LOG_LEVELS[level] >= LOG_LEVELS[this.config.level];
  }

  private formatMessage(level: LogLevel, message: string, data?: any): string {
    const timestamp = new Date().toISOString();
    let formattedMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}`;
    
    if (data && typeof data === 'object') {
      formattedMessage += ` | Data: ${JSON.stringify(data)}`;
    } else if (data !== undefined) {
      formattedMessage += ` | Data: ${data}`;
    }
    
    return formattedMessage;
  }

  private createLogEntry(level: LogLevel, message: string, data?: any, context?: string): LogEntry {
    return {
      level,
      message,
      timestamp: new Date().toISOString(),
      data,
      context,
    };
  }

  private logToConsole(level: LogLevel, message: string, data?: any): void {
    if (!this.config.enableConsole) return;

    const formattedMessage = this.formatMessage(level, message, data);
    
    switch (level) {
      case 'debug':
        console.debug(formattedMessage);
        break;
      case 'info':
        console.info(formattedMessage);
        break;
      case 'warn':
        console.warn(formattedMessage);
        break;
      case 'error':
        console.error(formattedMessage);
        break;
    }
  }

  private async sendToRemoteLogger(entry: LogEntry): Promise<void> {
    if (!this.config.enableRemoteLogging) return;

    try {
      // In a real implementation, you would send to your logging service
      // For now, we'll just store it for potential batch sending
      await fetch('/api/logs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(entry),
      });
    } catch (error) {
      // Silently fail remote logging to avoid infinite loops
      if (isDevelopment()) {
        console.warn('Failed to send log to remote service:', error);
      }
    }
  }

  private log(level: LogLevel, message: string, data?: any, context?: string): void {
    if (!this.shouldLog(level)) return;

    const entry = this.createLogEntry(level, message, data, context);

    // Console logging
    this.logToConsole(level, message, data);

    // Store in memory/localStorage
    if (this.config.enableStorage) {
      this.logStorage.push(entry);
      this.saveLogsToStorage();
    }

    // Remote logging (async, non-blocking)
    if (this.config.enableRemoteLogging) {
      this.sendToRemoteLogger(entry).catch(() => {
        // Silently handle remote logging failures
      });
    }
  }

  // Public logging methods
  debug(message: string, data?: any, context?: string): void {
    this.log('debug', message, data, context);
  }

  info(message: string, data?: any, context?: string): void {
    this.log('info', message, data, context);
  }

  warn(message: string, data?: any, context?: string): void {
    this.log('warn', message, data, context);
  }

  error(message: string, data?: any, context?: string): void {
    this.log('error', message, data, context);
  }

  // Utility methods
  setLevel(level: LogLevel): void {
    this.config.level = level;
  }

  getLevel(): LogLevel {
    return this.config.level;
  }

  getLogs(level?: LogLevel): LogEntry[] {
    if (!level) return [...this.logStorage];
    return this.logStorage.filter(log => log.level === level);
  }

  clearLogs(): void {
    this.logStorage = [];
    if (this.config.enableStorage) {
      localStorage.removeItem('app_logs');
    }
  }

  exportLogs(): string {
    return JSON.stringify(this.logStorage, null, 2);
  }

  // Configuration methods
  enableConsoleLogging(enable: boolean): void {
    this.config.enableConsole = enable;
  }

  enableStorageLogging(enable: boolean): void {
    this.config.enableStorage = enable;
  }

  enableRemoteLogging(enable: boolean): void {
    this.config.enableRemoteLogging = enable;
  }

  // Performance logging helpers
  time(label: string): void {
    if (this.shouldLog('debug')) {
      console.time(label);
    }
  }

  timeEnd(label: string): void {
    if (this.shouldLog('debug')) {
      console.timeEnd(label);
    }
  }

  // Group logging for related operations
  group(title: string, collapsed = false): void {
    if (this.config.enableConsole && this.shouldLog('debug')) {
      if (collapsed) {
        console.groupCollapsed(title);
      } else {
        console.group(title);
      }
    }
  }

  groupEnd(): void {
    if (this.config.enableConsole && this.shouldLog('debug')) {
      console.groupEnd();
    }
  }

  // Error boundary integration
  logError(error: Error, errorInfo?: any, context?: string): void {
    const errorData = {
      name: error.name,
      message: error.message,
      stack: error.stack,
      errorInfo,
    };

    this.error(`Unhandled error: ${error.message}`, errorData, context);
  }

  // React Query integration
  logQueryError(queryKey: string, error: any): void {
    this.error(`Query failed: ${queryKey}`, {
      queryKey,
      error: error instanceof Error ? {
        name: error.name,
        message: error.message,
        stack: error.stack,
      } : error,
    }, 'react-query');
  }

  // API request logging
  logApiRequest(method: string, url: string, data?: any): void {
    this.debug(`API ${method.toUpperCase()} ${url}`, data, 'api');
  }

  logApiResponse(method: string, url: string, status: number, data?: any): void {
    const level = status >= 400 ? 'error' : status >= 300 ? 'warn' : 'debug';
    this.log(level, `API ${method.toUpperCase()} ${url} -> ${status}`, data, 'api');
  }
}

// Create singleton instance
const logger = new Logger();

// Export both the instance and the class for testing
export { Logger, LogLevel, LogEntry };
export default logger;

// Named export for convenience
export { logger };