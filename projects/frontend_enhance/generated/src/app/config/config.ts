interface Config {
  apiBaseUrl: string;
  wsUrl: string;
  enableOffline: boolean;
  enableAnalytics: boolean;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  defaultTheme: 'light' | 'dark' | 'system';
  features: {
    offlineSupport: boolean;
    realTimeUpdates: boolean;
    dataVisualization: boolean;
    advancedFiltering: boolean;
    exportFeatures: boolean;
  };
  pagination: {
    defaultPageSize: number;
    maxPageSize: number;
  };
  cache: {
    staleTime: number;
    cacheTime: number;
  };
  websocket: {
    reconnectInterval: number;
    maxReconnectAttempts: number;
  };
}

// Helper function to get environment variable with fallback
function getEnvVar(key: string, fallback: string): string {
  // Use Vite's import.meta.env
  const value = import.meta.env[`VITE_${key}`];
  return value || fallback;
}

// Helper function to get boolean environment variable
function getEnvBool(key: string, fallback: boolean): boolean {
  const value = getEnvVar(key, String(fallback));
  return value.toLowerCase() === 'true';
}

// Helper function to get number environment variable
function getEnvNumber(key: string, fallback: number): number {
  const value = getEnvVar(key, String(fallback));
  const parsed = parseInt(value, 10);
  return isNaN(parsed) ? fallback : parsed;
}

// Create configuration object
const config: Config = {
  apiBaseUrl: getEnvVar('API_BASE_URL', 'http://localhost:8000'),
  wsUrl: getEnvVar('WS_URL', 'ws://localhost:8000/ws'),
  enableOffline: getEnvBool('ENABLE_OFFLINE', true),
  enableAnalytics: getEnvBool('ENABLE_ANALYTICS', false),
  logLevel: (getEnvVar('LOG_LEVEL', 'info') as Config['logLevel']),
  defaultTheme: (getEnvVar('DEFAULT_THEME', 'system') as Config['defaultTheme']),
  features: {
    offlineSupport: getEnvBool('ENABLE_OFFLINE', true),
    realTimeUpdates: getEnvBool('FEATURE_REAL_TIME_UPDATES', true),
    dataVisualization: getEnvBool('FEATURE_DATA_VISUALIZATION', true),
    advancedFiltering: getEnvBool('FEATURE_ADVANCED_FILTERING', true),
    exportFeatures: getEnvBool('FEATURE_EXPORT', true),
  },
  pagination: {
    defaultPageSize: getEnvNumber('DEFAULT_PAGE_SIZE', 20),
    maxPageSize: getEnvNumber('MAX_PAGE_SIZE', 100),
  },
  cache: {
    staleTime: getEnvNumber('CACHE_STALE_TIME', 5 * 60 * 1000), // 5 minutes
    cacheTime: getEnvNumber('CACHE_TIME', 10 * 60 * 1000), // 10 minutes
  },
  websocket: {
    reconnectInterval: getEnvNumber('WS_RECONNECT_INTERVAL', 5000), // 5 seconds
    maxReconnectAttempts: getEnvNumber('WS_MAX_RECONNECT_ATTEMPTS', 5),
  },
};

// Validation for required fields in development
if (import.meta.env.DEV) {
  const requiredFields: (keyof Config)[] = ['apiBaseUrl'];
  
  for (const field of requiredFields) {
    if (!config[field]) {
      throw new Error(`Missing required configuration: ${field}`);
    }
  }
  
  // Validate log level
  const validLogLevels = ['debug', 'info', 'warn', 'error'];
  if (!validLogLevels.includes(config.logLevel)) {
    console.warn(`Invalid log level: ${config.logLevel}. Using 'info' as fallback.`);
    config.logLevel = 'info';
  }
  
  // Validate theme
  const validThemes = ['light', 'dark', 'system'];
  if (!validThemes.includes(config.defaultTheme)) {
    console.warn(`Invalid theme: ${config.defaultTheme}. Using 'system' as fallback.`);
    config.defaultTheme = 'system';
  }
}

// Helper functions for runtime decisions
export const isDevelopment = (): boolean => import.meta.env.DEV;

export const isProduction = (): boolean => import.meta.env.PROD;

export const getApiBaseUrl = (): string => config.apiBaseUrl;

export const getWebSocketUrl = (): string => config.wsUrl;

export const isDarkModeDefault = (): boolean => config.defaultTheme === 'dark';

export const isFeatureEnabled = (feature: keyof Config['features']): boolean => {
  return config.features[feature];
};

export const shouldEnableOffline = (): boolean => config.enableOffline;

export const shouldEnableAnalytics = (): boolean => config.enableAnalytics && isProduction();

export const getLogLevel = (): Config['logLevel'] => config.logLevel;

export const getPaginationConfig = () => config.pagination;

export const getCacheConfig = () => config.cache;

export const getWebSocketConfig = () => config.websocket;

// Export the main config object
export default config;

// Export the Config type for use in other files
export type { Config };

// Named export for config object
export { config };