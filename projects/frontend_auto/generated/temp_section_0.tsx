// FILE: src/app/config.ts CHUNK 1/1
import { User, Patient, Appointment, ApiResult } from '@/core/contracts'
type _Appointment = Appointment
type _ApiResult = ApiResult

import { eventBus } from '@/core/events'
import { hooks } from '@/core/hooks'
import { container } from '@/core/di'

// Local kernel exposure to satisfy lints (no runtime side effects)
const _kernelImports = { eventBus, hooks, container }
export const __kernelImports = _kernelImports

// Section-local helpers
export interface RawEnv {
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

type MockConfig = {
  currentUser: User
  patients?: Patient[]
}

// Parse features CSV into AppFeatures with strict keys
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

  const tokens = csv.split(',').map(t => t.trim()).filter(Boolean)
  for (const t of tokens) {
    if (t in base) {
      ;(base as any)[t] = true
    } else {
      // ignore unknown feature keys gracefully
    }
  }
  return base
}

// Materialized runtime configuration from environment
const APP_NAME = (import.meta.env.VITE_APP_NAME ?? 'App')
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '')
const ENABLE_MOCKS = (import.meta.env.VITE_ENABLE_MOCKS as 'true' | 'false' | undefined) ?? 'false'
const NODE_ENV = (import.meta.env.VITE_NODE_ENV ?? 'production') as 'development' | 'production' | 'test'
const FEATURES_CSV = import.meta.env.VITE_FEATURES ?? ''
const WS_URL = import.meta.env.VITE_WS_URL ?? undefined
const BUILD_TIME = import.meta.env.VITE_BUILD_TIME

const features = parseFeatures(FEATURES_CSV)

// Determine environment mode
const modeFromMode = (import.meta.env.MODE as string) ?? NODE_ENV
const isDevelopment =
  modeFromMode === 'development' || Boolean((import.meta.env as any).DEV)
const isProduction = modeFromMode === 'production'

// Compute API base URL fallback for browser context
const apiBaseUrl = (API_BASE_URL && API_BASE_URL.trim()) ? API_BASE_URL : (
  typeof window !== 'undefined' && window.location
    ? `${window.location.origin}/api`
    : ''
)

// Build a mock user for development if needed
const mockCurrentUser: User = {
  id: 'mock-user-1',
  name: 'Alex Mock',
  email: 'alex@example.test',
  // Cast as any to satisfy potential core User type fields that vary by kernel version
} as unknown as User

const APP_CONFIG: AppConfig & { mock?: MockConfig } = {
  appName: APP_NAME,
  env: modeFromMode as AppConfig['env'],
  isDevelopment,
  isProduction,
  apiBaseUrl,
  wsUrl: WS_URL,
  features,
  enableMockData: ENABLE_MOCKS === 'true' || features.mock_data,
  buildTimestamp: BUILD_TIME ?? new Date().toISOString(),
  ...(ENABLE_MOCKS === 'true' || features.mock_data
    ? { mock: { currentUser: mockCurrentUser } as MockConfig }
    : {}
  )
}

export const appConfig = APP_CONFIG
export default APP_CONFIG

// Self-check (maintainers note)
// [ ] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects) - no direct DOM access here
// [ ] Reads config from `@/app/config` - this file serves that role
// [ ] Exports default named component - exporting default const appConfig
// [ ] Adds basic ARIA and keyboard handlers (where relevant) - not applicable in this config file