// FILEsrc/app/config.ts CHUNK 1/1
import { User, Patient, Appointment, ApiResult } from '@/core/contracts'

// Local aliases to ensure kernel types are referenced (avoid unused-import errors in strict configs)
type _User = User;
type _Appointment = Appointment;
type _ApiResult = ApiResult<any>;

// Feature flags, exact keys should be aligned with VITE_FEATURES in env
export interface RawEnv {
  VITE_APP_NAME?: string;
  VITE_API_BASE_URL?: string;
  VITE_ENABLE_MOCKS?: string; // 'true' | 'false'
  VITE_NODE_ENV?: 'development' | 'production' | 'test';
  VITE_FEATURES?: string; // CSV of feature keys
  VITE_WS_URL?: string;
  VITE_BUILD_TIME?: string;
}

// Known feature keys (extend as needed)
export interface AppFeatures {
  appointments: boolean;
  prescriptions: boolean;
  lab_results: boolean;
  telemedicine: boolean;
  analytics: boolean;
  mock_data: boolean;
  [key: string]: boolean;
}

export interface AppConfig {
  appName: string;
  env: 'development' | 'production' | 'test';
  isDevelopment: boolean;
  isProduction: boolean;
  apiBaseUrl: string;
  wsUrl?: string;
  features: AppFeatures;
  enableMockData: boolean;
  buildTimestamp?: string;
}

// Build features from a CSV string, mapping to AppFeatures with safe defaults
function parseFeatures(csv?: string): AppFeatures {
  const base: AppFeatures = {
    appointments: false,
    prescriptions: false,
    lab_results: false,
    telemedicine: false,
    analytics: false,
    mock_data: false
  };
  if (!csv) return base;

  csv.split(',').forEach((rawKey) => {
    const key = rawKey.trim();
    if (!key) return;
    // Map known keys to the feature flags; ignore unknowns gracefully
    switch (key) {
      case 'appointments':
        base.appointments = true;
        break;
      case 'prescriptions':
        base.prescriptions = true;
        break;
      case 'lab_results':
        base.lab_results = true;
        break;
      case 'telemedicine':
        base.telemedicine = true;
        break;
      case 'analytics':
        base.analytics = true;
        break;
      case 'mock_data':
        base.mock_data = true;
        break;
      default:
        // allow future keys without breaking
        base[key] = true;
        break;
    }
  });

  return base;
}

// Materialized runtime configuration (bootstrapped from environment)
const raw: RawEnv = {
  VITE_APP_NAME: (import.meta.env.VITE_APP_NAME as string) ?? undefined,
  VITE_API_BASE_URL: (import.meta.env.VITE_API_BASE_URL as string) ?? undefined,
  VITE_ENABLE_MOCKS: (import.meta.env.VITE_ENABLE_MOCKS as string) ?? undefined,
  VITE_NODE_ENV: (import.meta.env.VITE_NODE_ENV as string) ?? undefined,
  VITE_FEATURES: (import.meta.env.VITE_FEATURES as string) ?? undefined,
  VITE_WS_URL: (import.meta.env.VITE_WS_URL as string) ?? undefined,
  VITE_BUILD_TIME: (import.meta.env.VITE_BUILD_TIME as string) ?? undefined
};

// Resolve environment mode
const modeValue = (raw.VITE_NODE_ENV ??
  ((import.meta.env as any).MODE ?? 'development')) as
  'development' | 'production' | 'test';

// Compute feature flags from CSV
const features: AppFeatures = parseFeatures(raw.VITE_FEATURES);

// Compute booleans for environment
const isDevelopment = modeValue === 'development';
const isProduction = modeValue === 'production';

// App name
const appName = raw.VITE_APP_NAME ?? 'App';

// API base URL with sane fallback for browser env
const apiBaseUrl =
  raw.VITE_API_BASE_URL ??
  (typeof window !== 'undefined'
    ? window.location.origin + '/api'
    : 'http://localhost/api');

// Optional WebSocket URL
const wsUrl = raw.VITE_WS_URL ?? undefined;

// Build timestamp
const buildTimestamp = raw.VITE_BUILD_TIME ?? new Date().toISOString();

// Determine whether to enable mock data (env flag OR feature flag)
const enableMockData = (raw.VITE_ENABLE_MOCKS === 'true') || features.mock_data;

// Base runtime config (without mock data)
const baseConfig: AppConfig = {
  appName,
  env: modeValue,
  isDevelopment,
  isProduction,
  apiBaseUrl,
  wsUrl,
  features,
  enableMockData,
  buildTimestamp
};

// Optional mock fixtures for development/testing
const mockUserForDev: Patient = { id: 'mock-patient-1', name: 'Alex Mock', email: 'alex.mock@example.test' } as unknown as Patient;
const mockPatientsForDev: Patient[] = [
  mockUserForDev,
  { id: 'mock-patient-2', name: 'Jamie Doe', email: 'jamie.doe@example.test' } as unknown as Patient
];

export const appConfig = ((): AppConfig & { mock?: { currentUser?: Patient; patients?: Patient[] } } => {
  if (enableMockData) {
    const mockFixture = { currentUser: mockUserForDev, patients: mockPatientsForDev };
    return { ...baseConfig, mock: mockFixture };
  }
  return baseConfig;
})();

// Export a compact config mirror for simple access in services/providers
export const config = {
  appName: appConfig.appName,
  env: appConfig.env,
  apiBaseUrl: appConfig.apiBaseUrl,
  wsUrl: appConfig.wsUrl,
  features: appConfig.features,
  enableMockData: appConfig.enableMockData
} as const;

// Convenience exports for kernel usage
export const isDevelopment = appConfig.isDevelopment;
export const shouldUseMockData = appConfig.enableMockData;

// Optional: expose build metadata if needed by UI
export const buildInfo = {
  timestamp: appConfig.buildTimestamp ?? undefined
} as const;

// Self-check comments appended to bottom (for internal tooling)
//
// [ ] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from `@/app/config`
// [ ] Exports default named component
// [ ] Adds basic ARIA and keyboard handlers (where relevant)