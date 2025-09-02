// FILE: src/core/contracts.ts

// Domain roles
export type Role = 'patient' | 'doctor' | 'nurse' | 'admin';

// Base user identity
export interface UserBase {
  id: string
  email: string
  name: string
  avatarUrl?: string
  roles: Role[]
  createdAt: string // ISO date string
  updatedAt?: string
}

// Patient-specific user
export interface Patient extends UserBase {
  dob?: string // date of birth ISO string or date
  gender?: 'male' | 'female' | 'other'
  medicalRecordId?: string
  primaryDoctorId?: string
}

// Doctor-specific user
export interface Doctor extends UserBase {
  specialty?: string
  licenseNumber?: string
  clinicIds?: string[]
}

// Nurse-specific user
export interface Nurse extends UserBase {
  department?: string
}

// Public User type (exported for external usage)
export type User = Patient | Doctor | Nurse | UserBase;

// Healthcare domain models

export interface Appointment {
  id: string
  patientId: string
  providerId: string
  startAt: string // ISO datetime
  endAt: string // ISO datetime
  status: 'scheduled' | 'cancelled' | 'completed' | 'no_show'
  location?: string
  type: 'in_person' | 'telemedicine'
  notes?: string
  metadata?: Record<string, unknown>
}

interface Diagnosis {
  code: string
  name: string
  recordedAt: string
  notes?: string
}

export interface MedicalRecordEntry {
  id: string
  type: 'note' | 'lab' | 'imaging' | 'prescription'
  authorId: string
  createdAt: string
  data: Record<string, any>
}

export interface MedicalRecord {
  id: string
  patientId: string
  diagnoses: Diagnosis[]
  allergies: string[]
  medicationsSummary?: string
  entries: MedicalRecordEntry[]
}

export interface Prescription {
  id: string
  patientId: string
  prescriberId: string
  medication: string
  dose: string
  frequency: string
  startDate?: string
  endDate?: string
  instructions?: string
  refills?: number
}

export interface LabResult {
  id: string
  patientId: string
  testName: string
  orderedById?: string
  specimenDate?: string
  resultDate?: string
  value?: string | number
  unit?: string
  normalRange?: string
  status: 'pending' | 'completed' | 'cancelled'
  attachments?: string[]
}

// API response contracts

export type ApiResult<T> = {
  success: true
  data: T
  meta?: Record<string, any>
}

export type ApiError = {
  success: false
  error: {
    code: string
    message: string
    details?: any
  }
}

// Generic API response that callers can handle uniformly
export type ApiResponse<T> = ApiResult<T> | ApiError

// Pagination helpers

export interface Pagination {
  page: number
  pageSize: number
  total: number
}

// Auth and payload typings

export interface AuthTokens {
  accessToken: string
  refreshToken?: string
  expiresAt?: string | number
}

export interface LoginPayload {
  email: string
  password: string
  otp?: string
}

export interface RegisterPayload {
  name: string
  email: string
  password: string
  role?: Role
}

// WebSocket-related internal types (not exported for external consumption by default)
type WebSocketEventMap = {
  'appointment.updated': { appointment: Appointment }
  'labresult.created': { lab: LabResult }
  'message.received': { fromId: string; toId: string; message: string; sentAt: string }
  'user.status': { userId: string; online: boolean }
}

type WebSocketEvent<K extends keyof WebSocketEventMap = keyof WebSocketEventMap> = {
  type: K
  payload: WebSocketEventMap[K]
  ts: string
}

// UI state helpers (internal)
type LoadingState = 'idle' | 'loading' | 'succeeded' | 'failed'
interface FormState<T = any> {
  values: T
  touched: Partial<Record<string, boolean>>
  errors: Partial<Record<string, string>>
  isValid: boolean
  isSubmitting: boolean
}

// Runtime helpers (example guards)

/**
 * Simple runtime check for AuthTokens shape
 */
export function isAuthTokens(obj: any): obj is AuthTokens {
  return !!obj && typeof obj === 'object' && typeof obj.accessToken === 'string'
}

// Self-check footer for tooling compatibility
// [ ] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from `@/app/config`
// [ ] Exports default named component
// [ ] Adds basic ARIA and keyboard handlers (where relevant)


// End of core/contracts.ts

