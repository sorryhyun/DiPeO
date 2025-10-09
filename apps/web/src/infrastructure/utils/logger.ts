type LogLevel = "debug" | "info" | "warn" | "error";

interface LoggerConfig {
  level: LogLevel;
  enabled: boolean;
  prefix?: string;
}

class Logger {
  private config: LoggerConfig;
  private readonly levels: Record<LogLevel, number> = {
    debug: 0,
    info: 1,
    warn: 2,
    error: 3,
  };

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = {
      level: config.level || this.getDefaultLevel(),
      enabled: config.enabled ?? this.isEnabledByDefault(),
      prefix: config.prefix || "[DiPeO]",
    };
  }

  private getDefaultLevel(): LogLevel {
    if (typeof window !== "undefined") {
      const urlParams = new URLSearchParams(window.location.search);
      const debugParam = urlParams.get("debug");
      if (debugParam === "true") return "debug";
    }
    return import.meta.env.DEV ? "debug" : "warn";
  }

  private isEnabledByDefault(): boolean {
    return import.meta.env.DEV || this.hasDebugParam();
  }

  private hasDebugParam(): boolean {
    if (typeof window !== "undefined") {
      const urlParams = new URLSearchParams(window.location.search);
      return urlParams.get("debug") === "true";
    }
    return false;
  }

  private shouldLog(level: LogLevel): boolean {
    return (
      this.config.enabled && this.levels[level] >= this.levels[this.config.level]
    );
  }

  private formatMessage(level: LogLevel, message: string): string {
    const timestamp = new Date().toISOString();
    return `${this.config.prefix} [${timestamp}] [${level.toUpperCase()}] ${message}`;
  }

  debug(message: string, ...args: unknown[]): void {
    if (this.shouldLog("debug")) {
      console.debug(this.formatMessage("debug", message), ...args);
    }
  }

  info(message: string, ...args: unknown[]): void {
    if (this.shouldLog("info")) {
      console.info(this.formatMessage("info", message), ...args);
    }
  }

  warn(message: string, ...args: unknown[]): void {
    if (this.shouldLog("warn")) {
      console.warn(this.formatMessage("warn", message), ...args);
    }
  }

  error(message: string, ...args: unknown[]): void {
    if (this.shouldLog("error")) {
      console.error(this.formatMessage("error", message), ...args);
    }
  }

  log(message: string, ...args: unknown[]): void {
    this.info(message, ...args);
  }

  setLevel(level: LogLevel): void {
    this.config.level = level;
  }

  setEnabled(enabled: boolean): void {
    this.config.enabled = enabled;
  }

  createChild(prefix: string): Logger {
    return new Logger({
      level: this.config.level,
      enabled: this.config.enabled,
      prefix: `${this.config.prefix}:${prefix}`,
    });
  }
}

export const logger = new Logger();

export const createLogger = (prefix: string): Logger => {
  return logger.createChild(prefix);
};

export default logger;
