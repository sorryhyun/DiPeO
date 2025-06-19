/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_TITLE: string
  readonly VITE_API_PORT?: string
  readonly VITE_API_HOST?: string
  readonly VITE_DEBUG_WEBSOCKET?: string
  // Vite built-in env variables
  readonly DEV: boolean
  readonly PROD: boolean
  readonly MODE: string
  readonly BASE_URL: string
  readonly SSR: boolean
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}