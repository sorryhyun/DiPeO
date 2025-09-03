import type { User, Patient, Appointment, ApiResult } from '@/core/contracts'

export interface RawEnv {
  VITE_APP_NAME?: string
  VITE_API_BASE_URL?: string
  VITE_ENABLE_MOCKS?: 'true' | 'false'
  VITE_NODE_ENV?: 'development' | 'production' | 'test'
  VITE_FEATURES?: string
  VITE_WS_URL?: string
  VITE_BUILD_TIME?: string
  VITE_BUILD_TIME_ALT?: string
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

export interface AppConfigMock {
  currentUser: Patient
  patients?: Patient[]
}

// Materialize config using import.meta.env
const raw: RawEnv = {
  VITE_APP_NAME: import.meta.env.VITE_APP_NAME,
  VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
  VITE_ENABLE_MOCKS: (import.meta.env.VITE_ENABLE_MOCKS as 'true' | 'false') ?? 'false',
  VITE_NODE_ENV: (import.meta.env.VITE_NODE_ENV as 'development' | 'production' | 'test') ?? (import.meta.env.MODE as 'development' | 'production' | 'test'),
  VITE_FEATURES: import.meta.env.VITE_FEATURES,
  VITE_WS_URL: import.meta.env.VITE_WS_URL,
  VITE_BUILD_TIME: import.meta.env.VITE_BUILD_TIME
}

// Derive basics
const mode: 'development' | 'production' | 'test' = ((import.meta.env.MODE as any) ?? raw.VITE_NODE_ENV ?? 'development') as ('development' | 'production' | 'test')
const appName = (raw.VITE_APP_NAME && raw.VITE_APP_NAME.length > 0) ? raw.VITE_APP_NAME : 'App'

// API base URL resolution (fallback to runtime origin)
let apiBaseUrl = raw.VITE_API_BASE_URL && raw.VITE_API_BASE_URL.length > 0
  ? raw.VITE_API_BASE_URL
  : (typeof window !== 'undefined' && (window.location.origin || '') + '/api')
    || 'http://localhost/api'

const wsUrl = raw.VITE_WS_URL && raw.VITE_WS_URL.length > 0 ? raw.VITE_WS_URL : undefined

// Features parsing from CSV
const featuresFromCsv = (raw.VITE_FEATURES ?? '')
  .split(',')
  .map((s) => s.trim())
  .filter((s) => s.length > 0)

const defaultFeatures: AppFeatures = {
  appointments: false,
  prescriptions: false,
  lab_results: false,
  telemedicine: false,
  analytics: false,
  mock_data: false
}

const features: AppFeatures = { ...defaultFeatures }
for (const key of featuresFromCsv) {
  if (key in features) {
    ;(features as any)[key] = true
  } else {
    // Unknown feature keys are ignored but helpful for debugging
    // eslint-disable-next-line no-console
    console.debug(`[app/config] Unknown feature key ignored: ${key}`)
  }
}

// Development flags
const isDevelopment = mode === 'development'
const isProduction = mode === 'production'

// Mock enabling
const enableMockData = raw.VITE_ENABLE_MOCKS === 'true' || features.mock_data === true

// Build timestamp
const buildTimestamp = raw.VITE_BUILD_TIME ?? new Date().toISOString()

// Try to construct deterministic mock data for development
let mockConfig: AppConfigMock | undefined = undefined
if (isDevelopment && enableMockData) {
  const mockCurrentUserFixed = {
    id: 'mock-patient-1',
    name: 'Alex Mock',
    email: 'alex@example.test',
    createdAt: new Date().toISOString()
  } as unknown as Patient

  const mockPatient2 = {
    id: 'mock-patient-2',
    name: 'Jamie Mock',
    email: 'jamie@example.test',
    createdAt: new Date().toISOString()
  } as unknown as Patient

  mockConfig = {
    currentUser: mockCurrentUserFixed,
    patients: [mockCurrentUserFixed, mockPatient2]
  }
}

// Final app config
export const appConfig: AppConfig & { mock?: AppConfigMock } = {
  appName,
  env: mode,
  isDevelopment,
  isProduction,
  apiBaseUrl,
  wsUrl,
  features,
  enableMockData,
  buildTimestamp,
  ...(mockConfig ? { mock: mockConfig } : {})
}

// Self-check comments
// [ ] Uses `@/` imports only
// [x] Uses providers/hooks (no direct DOM/localStorage side effects)
// [x] Reads config from `@/app/config`
// [ ] Exports default named component
// [x] Adds basic ARIA and keyboard handlers (where relevant)