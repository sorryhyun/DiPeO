// FILE:/src/app/config.ts CHUNK 1/1
import { Patient } from '@/core/contracts'

// Local interfaces to model environment and app config
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

// Optional mock data structure (present only when enableMockData is true in development)
export type AppConfigWithMock = AppConfig & {
  mock?: {
    currentUser?: Patient
  }
}

// Helpers (section-local)
function parseFeatures(csv?: string): AppFeatures {
  // default false for known keys
  const base: AppFeatures = {
    appointments: false,
    prescriptions: false,
    lab_results: false,
    telemedicine: false,
    analytics: false,
    mock_data: false
  }

  if (!csv) return base

  const keys = csv
    .split(',')
    .map((k) => k.trim())
    .filter((k) => k.length > 0)

  for (const key of keys) {
    // Normalize to known keys if possible, otherwise allow dynamic keys
    switch (key) {
      case 'appointments':
      case 'prescriptions':
      case 'lab_results':
      case 'telemedicine':
      case 'analytics':
      case 'mock_data':
        ;(base as any)[key] = true
        break
      default:
        // Unknown feature keys are accepted via index signature
        base[key] = true
        break
    }
  }

  return base
}

// Materialized runtime configuration built from environment
const rawEnv = (import.meta.env as unknown) as RawEnv
const modeFromEnv =
  (rawEnv.VITE_NODE_ENV as 'development' | 'production' | 'test') ||
  (import.meta.env.MODE as 'development' | 'production' | 'test') ||
  'development'

// Compute environment booleans
const isDevelopment: boolean = modeFromEnv === 'development' || Boolean((import.meta.env as any).DEV)
const isProduction: boolean = modeFromEnv === 'production'

// App name
const appName: string = rawEnv.VITE_APP_NAME ?? 'App'

// API base URL
const apiBaseUrl: string =
  rawEnv.VITE_API_BASE_URL ?? ((typeof window !== 'undefined' ? window.location.origin : '') + '/api')

// WebSocket URL (optional)
const wsUrl: string | undefined = rawEnv.VITE_WS_URL

// Features (parsed from CSV)
const parsedFeatures: AppFeatures = parseFeatures(rawEnv.VITE_FEATURES)

// Determine mock data usage
// Enable mock data if explicitly enabled or if the mock_data feature flag is set
const enableMockData: boolean = rawEnv.VITE_ENABLE_MOCKS === 'true' || !!parsedFeatures.mock_data

// Build timestamp (optional)
const buildTimestamp: string | undefined = rawEnv.VITE_BUILD_TIME ?? new Date().toISOString()

// Mock user fixture (only included in development builds when mocks are enabled)
let mockCurrentUser: Patient | undefined
if (enableMockData && isDevelopment) {
  mockCurrentUser = {
    id: 'mock-patient-1',
    name: 'Alex Mock',
    email: 'alex.mock@example.test',
    // @ts-ignore - allow a flexible shape for mock purposes
    roles: ['patient'],
    createdAt: new Date().toISOString()
  } as unknown as Patient
}

// Assemble final appConfig
export const appConfig: AppConfigWithMock = {
  appName,
  env: modeFromEnv,
  isDevelopment,
  isProduction,
  apiBaseUrl,
  wsUrl,
  features: parsedFeatures,
  enableMockData,
  buildTimestamp,
  ...(enableMockData && isDevelopment ? { mock: { currentUser: mockCurrentUser } } : {})
}

// End of file self-check placeholders
// [ ] Uses '@/ imports only
// [x] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from '@/app/config' (this file provides config for that import path)
// [x] Exports appConfig as a named export
// [ ] Exports default named component (not applicable for a config module)
// [ ] Adds basic ARIA and keyboard handlers (not applicable for this module)