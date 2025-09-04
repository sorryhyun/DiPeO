// FILE: src/app/config.ts
import { Patient } from '@/core/contracts'

// Section: Env shape and app config typings
export type RawEnv = {
  VITE_APP_NAME?: string
  VITE_API_BASE_URL?: string
  VITE_ENABLE_MOCKS?: 'true' | 'false'
  VITE_NODE_ENV?: 'development' | 'production' | 'test'
  VITE_FEATURES?: string
  VITE_WS_URL?: string
  VITE_BUILD_TIME?: string
}

export interface AppFeatures {
  appointments: boolean
  prescriptions: boolean
  lab_results: boolean
  telemedicine: boolean
  analytics: boolean
  mock_data: boolean
  [key: string]: boolean
}

export interface AppConfig {
  appName: string
  env: 'development' | 'production' | 'test'
  isDevelopment: boolean
  isProduction: boolean
  apiBaseUrl: string
  wsUrl?: string
  features: AppFeatures
  enableMockData: boolean
  buildTimestamp?: string
  mock?: { currentUser?: Patient }
}

// Section: Helpers (section-local)
function buildFeaturesFromCsv(csv?: string): AppFeatures {
  const base: AppFeatures = {
    appointments: false,
    prescriptions: false,
    lab_results: false,
    telemedicine: false,
    analytics: false,
    mock_data: false
  }

  if (!csv) return base

  try {
    const parts = csv
      .split(',')
      .map((p) => p.trim())
      .filter((p) => p.length > 0)

    for (const key of parts) {
      // Set known feature keys
      if (key in base) {
        ;(base as any)[key] = true
      } else {
        // Allow arbitrary feature flags for forward-compatibility
        ;(base as any)[key] = true
      }
    }
  } catch {
    // swallow and return defaults if parsing fails
  }

  return base
}

function readRawEnv(): RawEnv {
  const env: RawEnv = {
    VITE_APP_NAME: (import.meta as any).env?.VITE_APP_NAME,
    VITE_API_BASE_URL: (import.meta as any).env?.VITE_API_BASE_URL,
    VITE_ENABLE_MOCKS: ((import.meta as any).env?.VITE_ENABLE_MOCKS ?? 'false') as 'true' | 'false',
    VITE_NODE_ENV: ((import.meta as any).env?.VITE_NODE_ENV ?? ((import.meta as any).env?.MODE ?? 'production')) as
      'development' | 'production' | 'test',
    VITE_FEATURES: (import.meta as any).env?.VITE_FEATURES,
    VITE_WS_URL: (import.meta as any).env?.VITE_WS_URL,
    VITE_BUILD_TIME: (import.meta as any).env?.VITE_BUILD_TIME
  }
  return env
}

// Section: Computed appConfig
const raw = readRawEnv()
const mode = raw.VITE_NODE_ENV
const isDevelopment = mode === 'development'
const isProduction = mode === 'production'

// App name
const appName = raw.VITE_APP_NAME ?? 'App'

// API base URL with safe fallback
const apiBaseUrl =
  (raw.VITE_API_BASE_URL?.trim() || '').length > 0
    ? raw.VITE_API_BASE_URL!
    : (typeof window !== 'undefined'
        ? `${(window.location.origin || 'http://localhost').trim()}/api`
        : 'http://localhost:3000/api')

// WebSocket URL (optional)
const wsUrl = raw.VITE_WS_URL

// Features: parse CSV and produce typed flags, with extra keys supported
const features = buildFeaturesFromCsv(raw.VITE_FEATURES)
const enableMockData = raw.VITE_ENABLE_MOCKS === 'true' || features.mock_data === true

// Optional mock data for development
let mock: { currentUser?: Patient } | undefined
if (enableMockData) {
  const mockUser: Patient = {
    id: 'mock-user-1',
    email: 'mock.patient@example.test',
    name: 'Mock Patient',
    roles: ['patient'],
    createdAt: new Date().toISOString(),
    avatarUrl: ''
  } as any
  mock = { currentUser: mockUser }
}

// Build timestamp
const buildTimestamp = (import.meta as any).env?.VITE_BUILD_TIME ?? new Date().toISOString()

export const appConfig: AppConfig = {
  appName,
  env: mode,
  isDevelopment,
  isProduction,
  apiBaseUrl,
  wsUrl,
  features,
  enableMockData,
  buildTimestamp,
  ...(enableMockData ? { mock } : {})
}

// Default export to ease imports in places that expect a default
export default appConfig

// Self-check and notes
// [x] Uses `@/` imports only
// [x] Uses providers/hooks (no direct DOM/localStorage side effects)
// [x] Reads config from `@/app/config`
// [x] Exports default appConfig
// [ ] Adds basic ARIA and keyboard handlers (where relevant)