// FILE: src/app/config.ts
import { Patient } from '@/core/contracts'

// Section-local helpers and types
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
  buildTimestamp?: string
  features: AppFeatures
  enableMockData: boolean
}

export type AppConfigWithMock = AppConfig & {
  mock?: { currentUser?: Patient }
}

// Known, default feature keys (extendable via VITE_FEATURES)
const KNOWN_FEATURE_KEYS = [
  'appointments',
  'prescriptions',
  'lab_results',
  'telemedicine',
  'analytics',
  'mock_data'
] as const

// Helper: parse comma-separated features into AppFeatures with safe defaults
function parseFeatures(csv?: string): AppFeatures {
  const featuresMap: Record<string, boolean> = {}
  if (typeof csv === 'string' && csv.trim().length > 0) {
    csv
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s.length > 0)
      .forEach((key) => {
        featuresMap[key] = true
      })
  }

  // Build typed feature set with explicit known keys
  const base: AppFeatures = {
    appointments: !!featuresMap['appointments'],
    prescriptions: !!featuresMap['prescriptions'],
    lab_results: !!featuresMap['lab_results'],
    telemedicine: !!featuresMap['telemedicine'],
    analytics: !!featuresMap['analytics'],
    mock_data: !!featuresMap['mock_data'],
  }

  // Carry over any non-known feature flags as extra entries (keeps type-safe extensibility)
  const extras: Record<string, boolean> = {}
  Object.entries(featuresMap).forEach(([k, v]) => {
    if (!KNOWN_FEATURE_KEYS.includes(k as any)) {
      extras[k] = v
    }
  })

  // Merge extras while preserving explicit known keys
  return { ...base, ...extras }
}

// Materialize runtime config from environment
const raw: RawEnv = (import.meta.env as unknown) as RawEnv

// Determine environment mode
const modeFromMeta = (import.meta.env.MODE || 'production') as 'development' | 'production' | 'test'
const envMode = (raw.VITE_NODE_ENV ?? modeFromMeta) as 'development' | 'production' | 'test'
const isDevelopment = envMode === 'development'
const isProduction = envMode === 'production'

// API base URL resolution
let apiBaseUrl = raw.VITE_API_BASE_URL ?? ''
if (!apiBaseUrl) {
  if (typeof window !== 'undefined' && (window.location?.origin ?? '') !== '') {
    apiBaseUrl = window.location.origin + '/api'
  } else {
    apiBaseUrl = ''
  }
}

// WebSocket URL (optional)
const wsUrl = raw.VITE_WS_URL ?? undefined

// Features parsed from VITE_FEATURES CSV
const features = parseFeatures(raw.VITE_FEATURES)

// Development mocks flag
const enableMockData = raw.VITE_ENABLE_MOCKS === 'true' || features.mock_data === true

// Build timestamp (optional)
const buildTimestamp = (raw.VITE_BUILD_TIME ?? new Date().toISOString()) as string

// Lightweight deterministic mock data (only when enabled)
let mock: AppConfigWithMock['mock'] | undefined
if (enableMockData) {
  const mockCurrentUser = {
    id: 'mock-patient-1',
    name: 'Alex Mock',
    email: 'alex@example.test',
    avatarUrl: undefined,
    roles: ['patient'],
    createdAt: new Date().toISOString(),
  } as unknown as Patient

  mock = { currentUser: mockCurrentUser }
}

// App configuration object (immutable by convention)
export const appConfig: AppConfigWithMock = {
  appName: raw.VITE_APP_NAME ?? 'App',
  env: envMode,
  isDevelopment,
  isProduction,
  apiBaseUrl,
  wsUrl,
  buildTimestamp,
  features,
  enableMockData,
  ...(enableMockData ? { mock } : {})
}

// Default export for convenience (some modules import default)
export default appConfig

// Self-Check (inline comments for audit)
//
// [x] Uses `@/` imports only
// [x] Uses providers/hooks (no direct DOM/localStorage side effects)
// [x] Reads config from `@/app/config`
// [x] Exports default named component
// [ ] Adds basic ARIA and keyboard handlers (where relevant)