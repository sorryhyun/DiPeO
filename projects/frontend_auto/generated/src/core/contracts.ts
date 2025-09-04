// src/app/config.ts

import type { Patient } from '@/core/contracts'

// Raw environment shape as a reference for consumers
export interface RawEnv {
  VITE_APP_NAME?: string
  VITE_API_BASE_URL?: string
  VITE_ENABLE_MOCKS?: 'true' | 'false'
  VITE_NODE_ENV?: string
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

// Runtime app configuration
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

// Optional mock payload for development
type AppConfigWithMock = AppConfig & { mock?: { currentUser: Patient } }

// Helper: parse feature CSV into AppFeatures
function parseFeatures(csv?: string): AppFeatures {
  // Known feature keys
  const knownKeys: (keyof AppFeatures)[] = [
    'appointments',
    'prescriptions',
    'lab_results',
    'telemedicine',
    'analytics',
    'mock_data',
  ]

  const result: AppFeatures = {
    appointments: false,
    prescriptions: false,
    lab_results: false,
    telemedicine: false,
    analytics: false,
    mock_data: false,
  }

  if (!csv) return result

  const items = csv
    .split(',')
    .map((s) => s.trim())
    .filter((s) => s.length > 0)

  for (const key of items) {
    if (knownKeys.includes(key as keyof AppFeatures)) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (result as any)[key] = true
    }
  }

  return result
}

// Materialized env values
const raw: RawEnv = {
  VITE_APP_NAME: (import.meta as any).env?.VITE_APP_NAME,
  VITE_API_BASE_URL: (import.meta as any).env?.VITE_API_BASE_URL,
  VITE_ENABLE_MOCKS: (import.meta as any).env?.VITE_ENABLE_MOCKS,
  VITE_NODE_ENV: (import.meta as any).env?.VITE_NODE_ENV,
  VITE_FEATURES: (import.meta as any).env?.VITE_FEATURES,
  VITE_WS_URL: (import.meta as any).env?.VITE_WS_URL,
  VITE_BUILD_TIME: (import.meta as any).env?.VITE_BUILD_TIME
}

// Determine mode
const env = (import.meta as any).env
const modeFromVite = (env?.MODE as string) ?? raw.VITE_NODE_ENV ?? 'development'
let envValue: AppConfig['env'] = (modeFromVite as AppConfig['env'])
if (!['development', 'production', 'test'].includes(envValue)) {
  envValue = 'development'
}
const isDevelopment = envValue === 'development'
const isProduction = envValue === 'production'

// App name
const appName = raw.VITE_APP_NAME ?? 'App'

// API base URL (fallback to current origin/api)
const apiBaseUrl =
  raw.VITE_API_BASE_URL ||
  (typeof window !== 'undefined' ? window.location.origin + '/api' : '')

// WebSocket URL
const wsUrl = raw.VITE_WS_URL

// Features
const features = parseFeatures(raw.VITE_FEATURES)

// Mock enabling flag
const enableMockData = raw.VITE_ENABLE_MOCKS === 'true' || features.mock_data === true

// Build timestamp
const buildTimestamp = raw.VITE_BUILD_TIME ?? new Date().toISOString()

// Base config object
const baseConfig: AppConfig = {
  appName,
  env: envValue,
  isDevelopment,
  isProduction,
  apiBaseUrl,
  wsUrl,
  features,
  enableMockData,
  buildTimestamp
}

// Optional mock payload for development
const mockUser: Patient = {
  id: 'mock-patient-1',
  name: 'Alex Mock',
  email: 'alex@example.test',
  roles: ['patient'],
  createdAt: new Date().toISOString()
} as Patient

const finalConfig: AppConfigWithMock =
  enableMockData
    ? { ...baseConfig, mock: { currentUser: mockUser } }
    : (baseConfig as AppConfigWithMock)

// Export the materialized config
export const appConfig: AppConfigWithMock = finalConfig

// Self-check comments
// [ ] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from `@/app/config`
// [ ] Exports default named component
// [ ] Adds basic ARIA and keyboard handlers (where relevant)