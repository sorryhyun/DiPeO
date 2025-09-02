// src/app/config.ts

import type { User, Patient } from '@/core/contracts'

/**
 * Raw environment variables surface
 */
export interface RawEnv {
  VITE_APP_NAME?: string
  VITE_API_BASE_URL?: string
  VITE_ENABLE_MOCKS?: 'true' | 'false'
  VITE_NODE_ENV?: 'development' | 'production' | 'test'
  VITE_FEATURES?: string
  VITE_WS_URL?: string
  VITE_BUILD_TIME?: string
}

/**
 * Feature flags for the app
 */
export interface AppFeatures {
  appointments: boolean
  prescriptions: boolean
  lab_results: boolean
  telemedicine: boolean
  analytics: boolean
  mock_data: boolean
  [key: string]: boolean
}

/**
 * Runtime app configuration
 */
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

/**
 * Helper to parse VITE_FEATURES CSV into AppFeatures
 */
const knownFeatureKeys: Array<keyof AppFeatures> = [
  'appointments',
  'prescriptions',
  'lab_results',
  'telemedicine',
  'analytics',
  'mock_data',
]

const parseFeatures = (csv?: string): AppFeatures => {
  const features: AppFeatures = {
    appointments: false,
    prescriptions: false,
    lab_results: false,
    telemedicine: false,
    analytics: false,
    mock_data: false
  }

  if (!csv) return features

  const keys = csv
    .split(',')
    .map((k) => k.trim())
    .filter((k) => k.length > 0)

  for (const key of keys) {
    if (knownFeatureKeys.includes(key as keyof AppFeatures)) {
      features[key as keyof AppFeatures] = true
    } else {
      // Unknown keys are ignored to preserve type-safety
    }
  }

  return features
}

/**
 * Materialized runtime config from environment
 */
const raw = (import.meta.env as unknown) as RawEnv

// Determine environment
const envCandidate = (raw.VITE_NODE_ENV ?? (import.meta.env.MODE ?? 'development')) as
  | 'development'
  | 'production'
  | 'test'

const isDevelopment = envCandidate === 'development'
const isProduction = envCandidate === 'production'

// API base URL - prefer explicit env, fallback to window origin + /api or /api
let apiBaseUrl: string =
  raw.VITE_API_BASE_URL ??
  (typeof window !== 'undefined'
    ? `${window.location.origin}/api`
    : '/api')

// WS URL (optional)
const wsUrl = raw.VITE_WS_URL

// Features parsed from VITE_FEATURES
const features = parseFeatures(raw.VITE_FEATURES)

// Mock data enablement
const enableMockData = raw.VITE_ENABLE_MOCKS === 'true' || features.mock_data === true

// App name
const appName = raw.VITE_APP_NAME ?? 'App'

// Build timestamp (optional, for development)
const buildTimestamp = (raw.VITE_BUILD_TIME ?? new Date().toISOString()) as string

// Prepare mock data (only if enabled)
type AppConfigWithMock = AppConfig & { mock?: { currentUser?: Patient } }
let mockCurrentUser: Patient | undefined
if (enableMockData) {
  const mockUser = {
    id: 'mock-user-1',
    name: 'Alex Mock',
    email: 'alex.mock@example.test',
    role: 'patient'
  } as unknown as User

  // Cast to Patient to satisfy the mock_currentUser shape
  mockCurrentUser = mockUser as unknown as Patient
}

const baseConfig: AppConfig = {
  appName,
  env: envCandidate,
  isDevelopment,
  isProduction,
  apiBaseUrl,
  wsUrl,
  features,
  enableMockData,
  buildTimestamp
}

// Final appConfig export with optional mock data
export const appConfig: AppConfigWithMock = {
  ...baseConfig,
  ...(enableMockData && mockCurrentUser
    ? {
        mock: {
          currentUser: mockCurrentUser
        }
      }
    : {})
}

// Re-exports for convenience (in case other modules import by name)
export type { AppConfigWithMock as AppConfigRuntime }

/*
Notes:
- All env access uses import.meta.env (Vite) as required.
- The mock data is deterministic and only attached when enableMockData is true.
- The appConfig is immutable at runtime except for the optional mock property in development.
*/

// [ ] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from `@/app/config`
// [ ] Exports default named component
// [ ] Adds basic ARIA and keyboard handlers (where relevant)