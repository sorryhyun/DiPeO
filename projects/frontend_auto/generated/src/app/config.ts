// FILE: src/app/config.ts

import type { User, Patient, Appointment, ApiResult } from '@/core/contracts'

// Core Kernel types are imported for consistency with the project architecture.
// This module materializes runtime configuration from environment variables.

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

// Optional mock surface for development/demo flows
export type AppConfigWithMock = AppConfig & { mock?: { currentUser: Patient } }

// Helper: safe-ish parse of features CSV into AppFeatures
function buildFeaturesFromCsv(csv?: string): AppFeatures {
  const keys: (keyof AppFeatures)[] = [
    'appointments',
    'prescriptions',
    'lab_results',
    'telemedicine',
    'analytics',
    'mock_data',
  ]
  // Initialize with defaults (false)
  const features = {
    appointments: false,
    prescriptions: false,
    lab_results: false,
    telemedicine: false,
    analytics: false,
    mock_data: false,
  } as AppFeatures

  if (!csv) return features

  csv
    .split(',')
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
    .forEach((k) => {
      // Only toggle known keys
      if ((features as any).hasOwnProperty(k)) {
        ;(features as any)[k] = true
      }
    })

  // Ensure any extra keys present in CSV end up as false by default
  // (Already handled by initialization)

  // Type safety guard: mark only recognized keys
  keys.forEach((k) => {
    // no-op, ensures key exists in type
    void k
  })

  return features
}

// Materialize env into a cohesive appConfig

// Read environment variables using import.meta.env (Vite)
const raw: RawEnv = {
  VITE_APP_NAME: (import.meta as any).VITE_APP_NAME ?? undefined,
  VITE_API_BASE_URL: (import.meta as any).VITE_API_BASE_URL ?? undefined,
  VITE_ENABLE_MOCKS: (import.meta as any).VITE_ENABLE_MOCKS ?? undefined,
  VITE_NODE_ENV: (import.meta as any).VITE_NODE_ENV ?? undefined,
  VITE_FEATURES: (import.meta as any).VITE_FEATURES ?? undefined,
  VITE_WS_URL: (import.meta as any).VITE_WS_URL ?? undefined,
  VITE_BUILD_TIME: (import.meta as any).VITE_BUILD_TIME ?? undefined
} as RawEnv

// Resolve mode
const mode =
  (import.meta.env?.MODE as 'development' | 'production' | 'test') ??
  raw.VITE_NODE_ENV ??
  'development'

const isDevelopment = mode === 'development'
const isProduction = mode === 'production'
const isTest = mode === 'test'

// Features
const features: AppFeatures = buildFeaturesFromCsv(raw.VITE_FEATURES)

// API base URL (fallback to origin/api for browser contexts)
const apiBaseUrl =
  raw.VITE_API_BASE_URL && raw.VITE_API_BASE_URL.length > 0
    ? raw.VITE_API_BASE_URL
    : (typeof window !== 'undefined' ? `${window.location.origin}/api` : '')

// WebSocket URL
const wsUrl = raw.VITE_WS_URL

// Build timestamp
const buildTimestamp = raw.VITE_BUILD_TIME ?? new Date().toISOString()

// App name
const appName = raw.VITE_APP_NAME ?? 'App'

// Mock data surface (only meaningful if enabled)
const enableMockData = raw.VITE_ENABLE_MOCKS === 'true' || !!features.mock_data

// Small deterministic mock user for development flows
const mockCurrentUser = {
  id: 'mock-patient-1',
  name: 'Alex Mock',
  email: 'alex@example.test',
  roles: ['patient'],
  createdAt: new Date().toISOString(),
} as unknown as Patient

// Base config object
const baseConfig: AppConfig = {
  appName,
  env: mode,
  isDevelopment,
  isProduction,
  apiBaseUrl,
  wsUrl,
  features,
  enableMockData,
  buildTimestamp,
}

// Exported config (with optional live mock surface for dev)
export const appConfig: AppConfigWithMock = {
  ...baseConfig,
  ...(enableMockData ? { mock: { currentUser: mockCurrentUser } } : {}),
}

// Self-check footer comments (for tooling verification)
//
// [ ] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from `@/app/config`
// [ ] Exports default named component
// [ ] Adds basic ARIA and keyboard handlers (where relevant)