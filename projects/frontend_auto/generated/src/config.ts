// src/config.ts

/**
 * Runtime configuration for the application.
 * Centralized configuration to be consumed by mocks, providers, and services.
 */

// Public export keys for localStorage usage
export interface LocalStorageKeys {
  AUTH_TOKEN: string;
  USER_PROFILE: string;
  THEME: string;
  [key: string]: string;
}

// Development mode flags
export interface DevelopmentMode {
  enable_mock_data?: boolean;
  disable_websocket_in_dev?: boolean;
  use_localstorage_persistence?: boolean;
}

// Shape of the entire app config
export interface AppConfig {
  apiBaseUrl: string;
  development_mode: DevelopmentMode;
  localStorageKeys: LocalStorageKeys;
}

/**
 * Defaults to sensible production-like values. These will be merged with any
 * global override provided at runtime via window.__APP_CONFIG__ (if present),
 * or environment-specific builds can override through process.env in bundlers.
 */
const DEFAULT_CONFIG: AppConfig = {
  apiBaseUrl: '/api',
  development_mode: {
    enable_mock_data: false,
    disable_websocket_in_dev: false,
    use_localstorage_persistence: true,
  },
  localStorageKeys: {
    AUTH_TOKEN: 'app_auth_token',
    USER_PROFILE: 'app_user_profile',
    THEME: 'app_theme',
  },
};

// Attempt to read a runtime override from a global hook for flexibility in dev.
// This does not require any import and remains backward compatible in prod.
let runtimeConfig: Partial<AppConfig> = {};
try {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const win: any = typeof window !== 'undefined' ? window : undefined;
  if (win && win.__APP_CONFIG__) {
    // shallow merge; nested objects are partially overridden below
    runtimeConfig = win.__APP_CONFIG__ as Partial<AppConfig>;
  }
} catch {
  // No global config available; fall back to defaults
  runtimeConfig = {};
}

// Merge defaults with runtime overrides
const APP_CONFIG: AppConfig = {
  apiBaseUrl: runtimeConfig.apiBaseUrl ?? DEFAULT_CONFIG.apiBaseUrl,
  development_mode: {
    enable_mock_data:
      runtimeConfig.development_mode?.enable_mock_data ??
      DEFAULT_CONFIG.development_mode.enable_mock_data,
    disable_websocket_in_dev:
      runtimeConfig.development_mode?.disable_websocket_in_dev ??
      DEFAULT_CONFIG.development_mode.disable_websocket_in_dev,
    use_localstorage_persistence:
      runtimeConfig.development_mode?.use_localstorage_persistence ??
      DEFAULT_CONFIG.development_mode.use_localstorage_persistence,
  },
  localStorageKeys: {
    AUTH_TOKEN:
      runtimeConfig.localStorageKeys?.AUTH_TOKEN ??
      DEFAULT_CONFIG.localStorageKeys.AUTH_TOKEN,
    USER_PROFILE:
      runtimeConfig.localStorageKeys?.USER_PROFILE ??
      DEFAULT_CONFIG.localStorageKeys.USER_PROFILE,
    THEME:
      runtimeConfig.localStorageKeys?.THEME ??
      DEFAULT_CONFIG.localStorageKeys.THEME,
  },
};

// Public exposed constants consumed across the app
export const API_BASE_URL: string = APP_CONFIG.apiBaseUrl;
export const ENABLE_MOCKS: boolean =
  APP_CONFIG.development_mode.enable_mock_data ?? false;
export const LOCALSTORAGE_KEYS: LocalStorageKeys = APP_CONFIG.localStorageKeys;