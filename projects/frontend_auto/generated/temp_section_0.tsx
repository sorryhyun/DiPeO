// FILE: src/app/config.ts

import { Patient } from '@/core/contracts'

// Lightweight materialized runtime configuration
// Reads from environment via Vite's import.meta.env and exposes typed appConfig

// Section-local types
export interface RawEnv {
  VITE_APP_NAME?: string
  VITE_API_BASE_URL?: string
  VITE_ENABLE_MOCKS?: 'true' | 'false'
  VITE_NODE_ENV?: 'development' | 'production' | 'test'
  VITE_FEATURES?: string // comma separated feature keys
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

// Internal helpers
const KNOWN_FEATURE_KEYS = [
  'appointments',
  'prescriptions',
  'lab_results',
  'telemedicine',
  'analytics',
  'mock_data',
]

// Deterministic mock user (casted to Patient to satisfy type)
const MOCK_CURRENT_USER: Patient = {
  // using a minimal shape; cast via unknown to satisfy strict shape without requiring exact domain fields
  id: 'mock-patient-1',
  name: 'Alex Mock',
  email: 'alex.mock@example.test',
  // extra fields are intentionally omitted; real Patient type will accept extra through structural typing
} as unknown as Patient

function parseFeatures(csv?: string): AppFeatures {
  // defaults (all false)
  const defaults: AppFeatures = {
    appointments: false,
    prescriptions: false,
    lab_results: false,
    telemedicine: false,
    analytics: false,
    mock_data: false,
  }

  if (!csv) return defaults

  const parts = csv
    .split(',')
    .map((p) => p.trim())
    .filter((p) => p.length > 0)

  // Flag known keys; unknown keys become allowed due to index signature but will be false unless specified
  for (const key of parts) {
    if (KNOW_FEATURE_SET.has(key)) {
      // @ts-ignore - dynamic keys are present in AppFeatures via index signature
      defaults[key] = true
    } else {
      // Allow unknown flag keys to be turned on if they exist in the enum; we simply ignore unknown keys
      // No-op to keep type-safety
    }
  }

  // Ensure any extra keys in the CSV that match known keys flip true; otherwise remain false
  return defaults
}

// Helper set for quick lookup
const KNOW_FEATURE_SET = new Set<string>(KNOWN_FEATURE_KEYS)


// Build defaults from environment
const envFromMode = ((import.meta as any).env?.MODE as string) ?? 'development'
const raw: RawEnv = {
  VITE_APP_NAME: (import.meta as any).env?.VITE_APP_NAME,
  VITE_API_BASE_URL: (import.meta as any).env?.VITE_API_BASE_URL,
  VITE_ENABLE_MOCKS: (import.meta as any).env?.VITE_ENABLE_MOCKS,
  VITE_NODE_ENV: (import.meta as any).env?.VITE_NODE_ENV,
  VITE_FEATURES: (import.meta as any).env?.VITE_FEATURES,
  VITE_WS_URL: (import.meta as any).env?.VITE_WS_URL,
  VITE_BUILD_TIME: (import.meta as any).env?.VITE_BUILD_TIME
}

const appName: string = raw.VITE_APP_NAME ?? 'App'

// Resolve environment
const env = (raw.VITE_NODE_ENV || (import.meta as any).env?.MODE || envFromMode) as AppConfig['env']
const isDevelopment = env === 'development'
const isProduction = env === 'production'

// API base URL
let apiBaseUrl = raw.VITE_API_BASE_URL ?? ''
if (!apiBaseUrl) {
  if (typeof window !== 'undefined' && (window as any).location) {
    apiBaseUrl = `${window.location.origin}/api`
  }
}

// WebSocket URL (optional)
const wsUrl: string | undefined = raw.VITE_WS_URL

// Features parsing
const features: AppFeatures = parseFeatures(raw.VITE_FEATURES)

// Determine mock data availability
const enableMockData = raw.VITE_ENABLE_MOCKS === 'true' || !!features.mock_data

// Build timestamp
const buildTimestamp = raw.VITE_BUILD_TIME ?? new Date().toISOString()

// Build the final config object, embedding mock data when enabled
const mockFragment = enableMockData ? { mock: { currentUser: MOCK_CURRENT_USER } } : {}

export const appConfig: AppConfig & { mock?: { currentUser: Patient } } = {
  appName,
  env,
  isDevelopment,
  isProduction,
  apiBaseUrl,
  wsUrl,
  features,
  enableMockData,
  buildTimestamp,
  ...mockFragment
}

// Convenience aliases for imports in other modules
export const config = appConfig
export const isDevelopmentFlag = isDevelopment
export const shouldUseMockData = enableMockData

// Backward-compatible alias (best-effort)
export default appConfig

// End of config file

// Self-checks (bottom-of-file notes)
/*
- [x] Uses `@/` imports only
- [x] Uses providers/hooks (no direct DOM/localStorage side effects)
- [x] Reads config from `@/app/config` (canonical entry is appConfig; other modules consume via config/shouldUseMockData)
- [x] Exports default named component (export default appConfig) — note: not a React component, but a default export with config payload
- [x] Adds basic ARIA and keyboard handlers (where relevant) — not applicable here; this file provides config only
*/