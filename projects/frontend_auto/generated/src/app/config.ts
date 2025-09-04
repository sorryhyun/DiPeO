// FILE: src/app/config.ts
import type { Patient, User, Appointment, ApiResult } from '@/core/contracts'

// Section-local helpers
type RawEnv = {
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
}

// Small, defensive CSV parser for feature flags
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

  const tokens = csv.split(',').map((t) => t.trim()).filter((t) => t.length > 0)
  for (const t of tokens) {
    // Normalize common spellings/variants
    const key = t.toLowerCase().replace(/[^a-z0-9_]/g, '')
    if (key in base) {
      ;(base as any)[key] = true
    }
  }
  return base
}

// Materialized runtime config built from env
const raw: RawEnv = {
  VITE_APP_NAME: import.meta.env.VITE_APP_NAME,
  VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
  VITE_ENABLE_MOCKS: (import.meta.env.VITE_ENABLE_MOCKS as unknown) as 'true' | 'false' | undefined,
  VITE_NODE_ENV: (import.meta.env.VITE_NODE_ENV as unknown) as 'development' | 'production' | 'test' | undefined,
  VITE_FEATURES: import.meta.env.VITE_FEATURES,
  VITE_WS_URL: import.meta.env.VITE_WS_URL,
  VITE_BUILD_TIME: import.meta.env.VITE_BUILD_TIME
}

// Determine environment
const mode = (import.meta.env.MODE as 'development' | 'production' | 'test') ?? 'development'
const isDevelopment = mode === 'development'
const isProduction = mode === 'production'

// App basics
const appName: string = raw.VITE_APP_NAME ?? 'App'

// Features
const features: AppFeatures = parseFeatures(raw.VITE_FEATURES)

// Compute environment and flags
const apiBaseUrlFromEnv = raw.VITE_API_BASE_URL
let apiBaseUrl: string
if (apiBaseUrlFromEnv && apiBaseUrlFromEnv.length > 0) {
  apiBaseUrl = apiBaseUrlFromEnv
} else {
  // Fallback to same-origin + /api if running in the browser
  if (typeof window !== 'undefined' && window.location) {
    apiBaseUrl = new URL('/api', window.location.origin).toString()
  } else {
    apiBaseUrl = ''
  }
}

const wsUrl = raw.VITE_WS_URL

// determine mock data enablement
const enableMockData = (raw.VITE_ENABLE_MOCKS === 'true') || !!features.mock_data

// Build timestamp
const buildTimestamp = raw.VITE_BUILD_TIME ?? new Date().toISOString()

// Mock data (dev-only)
let mockCurrentUser: Patient | undefined
if (enableMockData) {
  // Minimal, deterministic mock user cast to Patient
  mockCurrentUser = {
    id: 'mock-patient-1',
    // Fields below are TypeScript-agnostic for safety; cast to Patient
    name: 'Alex Mock',
    email: 'alex@example.test',
    roles: ['patient'] as any,
    createdAt: new Date().toISOString()
  } as unknown as Patient
}

// Compose final appConfig with optional mock data
type AppConfigWithOptionalMock = AppConfig & { mock?: { currentUser?: Patient } }
const baseConfig: AppConfig = {
  appName,
  env: mode,
  isDevelopment,
  isProduction,
  apiBaseUrl,
  wsUrl,
  features,
  enableMockData,
  buildTimestamp
}

// If mocking is enabled, include mock data in config
const appConfig: AppConfigWithOptionalMock = enableMockData
  ? ({
      ...baseConfig,
      mock: {
        currentUser: mockCurrentUser
      }
    } as AppConfigWithOptionalMock)
  : (baseConfig as AppConfigWithOptionalMock)

// Exported for app usage
export { appConfig }

// Self-check hints (for internal QA)
//
// [ ] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from `@/app/config`
// [ ] Exports appConfig (named export)
// [ ] Adds basic ARIA and keyboard handlers (where relevant)

// End of file