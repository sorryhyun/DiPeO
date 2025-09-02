// src/app/config.ts
import { Patient } from '@/core/contracts'

// Raw environment interface
export interface RawEnv {
  VITE_APP_NAME?: string
  VITE_API_BASE_URL?: string
  VITE_ENABLE_MOCKS?: 'true' | 'false'
  VITE_NODE_ENV?: 'development' | 'production' | 'test'
  VITE_FEATURES?: string
  VITE_WS_URL?: string
  VITE_BUILD_TIME?: string
}

// Feature flags contract
export interface AppFeatures {
  appointments: boolean
  prescriptions: boolean
  lab_results: boolean
  telemedicine: boolean
  analytics: boolean
  mock_data: boolean
  [key: string]: boolean
}

// Runtime app config
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

// Deterministic mock user (cast to Patient to satisfy type)
const mockPatientFromDev: unknown = {
  id: 'mock-patient-1',
  name: 'Alex Mock',
  email: 'alex.mock@example.test',
  createdAt: new Date().toISOString(),
}
const mockPatient: Patient = mockPatientFromDev as Patient

// Materialized raw env using import.meta.env
const raw = (import.meta.env as unknown) as RawEnv

// Determine environment
// Prefer VITE_NODE_ENV if provided, otherwise rely on Vite's MODE
const mode = ((import.meta.env as any).MODE ?? 'production') as string
const envFromMode = mode === 'development' ? 'development' : mode === 'test' ? 'test' : 'production'
const env: AppConfig['env'] = (raw.VITE_NODE_ENV ?? envFromMode) as AppConfig['env']

const isDevelopment = env === 'development'
const isProduction = env === 'production'

// API base URL determination
const rawApiBase = raw.VITE_API_BASE_URL
const defaultBase = (typeof window !== 'undefined' && window.location?.origin) ? window.location.origin : ''
const apiBaseUrl = (rawApiBase && rawApiBase.length > 0)
  ? rawApiBase
  : (defaultBase ? `${defaultBase}/api` : 'http://localhost:3000/api')

// WebSocket URL (optional)
const wsUrl = raw.VITE_WS_URL || undefined

// Parse features from CSV
const featuresFromEnv = ((raw.VITE_FEATURES ?? '') as string)
  .split(',')
  .map((s) => s.trim())
  .filter((s) => s.length > 0)

const features: AppFeatures = {
  appointments: featuresFromEnv.includes('appointments'),
  prescriptions: featuresFromEnv.includes('prescriptions'),
  lab_results: featuresFromEnv.includes('lab_results'),
  telemedicine: featuresFromEnv.includes('telemedicine'),
  analytics: featuresFromEnv.includes('analytics'),
  mock_data: featuresFromEnv.includes('mock_data'),
}

// Enable mock data if explicitly enabled or if the mock_data feature flag is on
const enableMockData = (raw.VITE_ENABLE_MOCKS === 'true') || features.mock_data

// Build timestamp for traceability
const buildTimestamp = (raw.VITE_BUILD_TIME && raw.VITE_BUILD_TIME.length > 0)
  ? raw.VITE_BUILD_TIME
  : new Date().toISOString()

// App name
const appName = raw.VITE_APP_NAME?.trim() || 'App'

// Base app config object (immutable at runtime)
export const appConfig: AppConfig & { mock?: { currentUser: Patient; patients?: Patient[] } } = {
  appName,
  env,
  isDevelopment,
  isProduction,
  apiBaseUrl,
  wsUrl,
  features,
  enableMockData,
  buildTimestamp,
  ...(enableMockData
    ? {
        mock: {
          currentUser: mockPatient,
          patients: [mockPatient],
        },
      }
    : {})
}

// Self-check comments (appending for tooling visibility)
//
/*
[ ] Uses `@/` imports only
[ ] Uses providers/hooks (no direct DOM/localStorage side effects)
[ ] Reads config from `@/app/config`
[ ] Exports default named component
[ ] Adds basic ARIA and keyboard handlers (where relevant)
*/