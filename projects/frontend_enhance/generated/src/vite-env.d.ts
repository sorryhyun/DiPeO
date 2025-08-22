/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_WS_URL: string
  readonly VITE_ENABLE_OFFLINE: string
  readonly VITE_ENABLE_ANALYTICS: string
  readonly VITE_LOG_LEVEL: string
  readonly VITE_DEFAULT_THEME: string
  readonly VITE_FEATURE_REAL_TIME_UPDATES: string
  readonly VITE_FEATURE_DATA_VISUALIZATION: string
  readonly VITE_FEATURE_ADVANCED_FILTERING: string
  readonly VITE_FEATURE_EXPORT: string
  readonly VITE_DEFAULT_PAGE_SIZE: string
  readonly VITE_MAX_PAGE_SIZE: string
  readonly VITE_CACHE_STALE_TIME: string
  readonly VITE_CACHE_TIME: string
  readonly VITE_WS_RECONNECT_INTERVAL: string
  readonly VITE_WS_MAX_RECONNECT_ATTEMPTS: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}