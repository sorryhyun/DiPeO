// src/config.ts

type DevelopmentModeConfig = {
  enable_mock_data: boolean;
  disable_websocket_in_dev: boolean;
  use_localstorage_persistence: boolean;
};

// LocalStorage keys used across the application
export const LOCALSTORAGE_KEYS = {
  authToken: 'app_auth_token',
  userProfile: 'app_user_profile',
  lastVisitedChannel: 'app_last_channel',
  userSettings: 'app_user_settings',
  themePreference: 'app_theme_preference',
} as const;

// Helper to safely parse boolean-like environment variables
const parseBoolean = (value: string | undefined, defaultValue: boolean): boolean => {
  if (typeof value !== 'string') return defaultValue;
  const v = value.toLowerCase().trim();
  if (v === 'true' || v === '1' || v === 'yes' || v === 'on') return true;
  if (v === 'false' || v === '0' || v === 'no' || v === 'off') return false;
  return defaultValue;
};

// Environment and runtime overrides (when available)
const rawEnv = (typeof process !== 'undefined' ? (process as any).env : {}) as { [key: string]: string | undefined };

const envApiBaseUrl = rawEnv.REACT_APP_API_BASE_URL || '/api';
const envEnableMock = rawEnv.REACT_APP_ENABLE_MOCKS;
const envDisableWS = rawEnv.REACT_APP_DISABLE_WS_DEV;
const envUseLS = rawEnv.REACT_APP_USE_LOCALSTORAGE_PERSISTENCE;

// Defaults
const DEFAULT_DEVELOPMENT_MODE: DevelopmentModeConfig = {
  enable_mock_data: false,
  disable_websocket_in_dev: false,
  use_localstorage_persistence: true,
};

// Computed development mode from environment or defaults
const developmentMode: DevelopmentModeConfig = {
  enable_mock_data: parseBoolean(envEnableMock, DEFAULT_DEVELOPMENT_MODE.enable_mock_data),
  disable_websocket_in_dev: parseBoolean(envDisableWS, DEFAULT_DEVELOPMENT_MODE.disable_websocket_in_dev),
  use_localstorage_persistence: parseBoolean(envUseLS, DEFAULT_DEVELOPMENT_MODE.use_localstorage_persistence),
};

// Final config object
export const config = {
  apiBaseUrl: envApiBaseUrl,
  development_mode: developmentMode,
  localStorageKeys: LOCALSTORAGE_KEYS,
} as const;

// Convenience exports for common usage
export const API_BASE_URL = config.apiBaseUrl;
export const ENABLE_MOCKS = config.development_mode.enable_mock_data;