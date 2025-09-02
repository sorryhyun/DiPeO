// FILE: src/app/config.ts
import type { Patient } from '@/core/contracts'

/**
 * App runtime configuration materialized from environment.
 * The file reads environment via import.meta.env (Vite) and exposes:
 *  - appConfig: the primary configuration object
 *  - config: alias to appConfig (for downstream imports)
 *  - isDevelopment: simple flag
 *  - shouldUseMockData: flag to enable/disable mock data usage
 */

// Raw environment shape (from Vite)
export interface RawEnv {
  VITE_APP_NAME?: string
  VITE_API_BASE_URL?: string
  VITE_ENABLE_MOCKS?: 'true' | 'false'
  VITE_NODE_ENV?: 'development' | 'production' | 'test'
  VITE_FEATURES?: string
  VITE_WS_URL?: string
  VITE_BUILD_TIME?: string
}

// Feature flags (typed)
export interface AppFeatures {
  appointments: boolean
  prescriptions: boolean
  lab_results: boolean
  telemedicine: boolean
  analytics: boolean
  mock_data: boolean
  [key: string]: boolean
}

// Core app config
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
}

// Internal helper to parse CSV features into AppFeatures
function parseFeatures(csv?: string): AppFeatures {
  const base: AppFeatures = {
    appointments: false,
    prescriptions: false,
    lab_results: false,
    telemedicine: false,
    analytics: false,
    mock_data: false
  }

  if (!csv) return base

  csv
    .split(',')
    .map((s) => s.trim())
    .forEach((key) => {
      if (!key) return
      // Allow dynamic keys; if a key matches, enable it; otherwise, still enable for forward-compat
      ;(base as any)[key] = true
    })

  return base
}

// Runtime materialization
const raw: RawEnv = {
  VITE_APP_NAME: import.meta.env.VITE_APP_NAME,
  VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
  VITE_ENABLE_MOCKS: (import.meta.env.VITE_ENABLE_MOCKS as 'true' | 'false') ?? undefined,
  VITE_NODE_ENV: (import.meta.env.VITE_NODE_ENV as 'development' | 'production' | 'test') ?? undefined,
  VITE_FEATURES: import.meta.env.VITE_FEATURES,
  VITE_WS_URL: import.meta.env.VITE_WS_URL,
  VITE_BUILD_TIME: import.meta.env.VITE_BUILD_TIME
}

// Resolve environment and features
const appName = raw.VITE_APP_NAME ?? 'HealthcareApp'

// Determine environment
const modeFromEnv = (import.meta.env.MODE as string) ?? ''
const resolvedEnv = (raw.VITE_NODE_ENV || (modeFromEnv as any) || 'development') as AppConfig['env']
const isDevelopment = resolvedEnv === 'development'
const isProduction = resolvedEnv === 'production'

// API base URL (fallback to origin/api if not provided)
const apiBaseUrl =
  (raw.VITE_API_BASE_URL && raw.VITE_API_BASE_URL.trim()) ||
  (typeof window !== 'undefined' ? window.location.origin + '/api' : '')

// WebSocket URL (optional)
const wsUrl = raw.VITE_WS_URL ?? undefined

// Features (CSV -> AppFeatures)
const features = parseFeatures(raw.VITE_FEATURES)

// Whether to enable mock data (explicit flag OR feature flag)
const enableMockData = (raw.VITE_ENABLE_MOCKS === 'true') || features.mock_data

// Build timestamp
const buildTimestamp = raw.VITE_BUILD_TIME ?? new Date().toISOString()

// Section-local mock data (only available in development when mocks are enabled)
let mockData: { currentUser: Patient; patients?: Patient[] } | undefined = undefined
if (isDevelopment && enableMockData) {
  const MOCK_USER: Patient = {
    id: 'mock-user-1',
    email: 'alex.mock@example.test',
    name: 'Alex Mock',
    roles: ['patient'],
    avatarUrl: '',
    createdAt: new Date().toISOString(),
    dob: '1985-05-15',
    gender: 'other'
  }

  const MOCK_PATIENT_2: Patient = {
    id: 'mock-user-2',
    email: 'jane.mock@example.test',
    name: 'Jane Mock',
    roles: ['patient'],
    avatarUrl: '',
    createdAt: new Date().toISOString(),
    dob: '1990-01-01',
    gender: 'female'
  }

  mockData = {
    currentUser: MOCK_USER,
    patients: [MOCK_USER, MOCK_PATIENT_2]
  }
}

// Final appConfig export (typed with optional mock)
export const appConfig: AppConfig & { mock?: { currentUser?: Patient; patients?: Patient[] } } = {
  appName,
  env: resolvedEnv,
  isDevelopment,
  isProduction,
  apiBaseUrl,
  wsUrl,
  features,
  enableMockData,
  buildTimestamp,
  ...(mockData ? { mock: mockData } : {})
}

// Convenience aliases for imports in other parts of the app
export const config = appConfig
export const isDevelopmentFlag = isDevelopment // deprecated alias (kept for safety if any consumer uses old name)
export const shouldUseMockData = enableMockData

// Backwards compatibility exports (named as in Core Kernel spec)
export type AppRuntimeConfig = AppConfig

// Self-check: basic usage examples (commented for developers)
// import { appConfig } from '@/app/config'
// const api = new URL('/appointments', appConfig.apiBaseUrl).toString()

/* Notes:
- appConfig is immutable by convention (const); consumers should not mutate.
- All env reads use import.meta.env.
- Mock data is provided only in development with either VITE_ENABLE_MOCKS or VITE_FEATURES containing mock_data.
*/

// Self-Check Comments
// [ ] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from `@/app/config`
// [ ] Exports default named component
// [ ] Adds basic ARIA and keyboard handlers (where relevant)

