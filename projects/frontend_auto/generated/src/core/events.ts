// FILE:/src/core/contracts.ts

// Core domain contracts and API surface for healthcare domain models

// Roles
export type Role = 'patient' | 'doctor' | 'nurse' | 'admin'

// Base user
export interface UserBase {
  id: string
  email: string
  name: string
  avatarUrl?: string
  roles: Role[]
  createdAt: string
  updatedAt?: string
}

// Patient-specific
export interface Patient extends UserBase {
  dob?: string
  gender?: 'male' | 'female' | 'other'
  medicalRecordId?: string
  primaryDoctorId?: string
}

// Doctor-specific
export interface Doctor extends UserBase {
  specialty?: string
  licenseNumber?: string
  clinicIds?: string[]
}

// Nurse-specific
export interface Nurse extends UserBase {
  department?: string
}

// Generic User union
export type User = Patient | Doctor | Nurse | UserBase

// Domain models

export interface Appointment {
  id: string
  patientId: string
  providerId: string
  startAt: string
  endAt?: string
  status: 'scheduled' | 'cancelled' | 'completed' | 'no_show'
  location?: string
  type: 'in_person' | 'telemedicine'
  notes?: string
  metadata?: Record<string, unknown>
}

export interface MedicalRecordEntry {
  id: string
  type: 'note' | 'lab' | 'imaging' | 'prescription'
  authorId?: string
  createdAt: string
  data: Record<string, any>
}

export interface MedicalRecord {
  id: string
  patientId: string
  diagnoses: { code: string; name: string; recordedAt: string; notes?: string }[]
  allergies: string[]
  medicationsSummary?: string
  entries: MedicalRecordEntry[]
}

export interface Prescription {
  id: string
  patientId: string
  prescriberId?: string
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

// Authentication tokens
export interface AuthTokens {
  accessToken: string
  refreshToken?: string
  expiresAt?: string | number
}

// API surface

export type ApiResult<T> = {
  success: true
  data: T
  meta?: Record<string, any>
}

// API error shape
export type ApiError = {
  success: false
  error: { code: string; message: string; details?: any }
}

// Unified API response type
export type ApiResponse<T> = ApiResult<T> | ApiError

// Pagination wrapper
export interface Pagination<T> {
  items: T[]
  page: number
  pageSize: number
  total: number
}

// Auth payloads
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

// WebSocket event map (real-time)
export type WebSocketEventMap = {
  'appointment.updated': { appointment: Appointment }
  'labresult.created': { lab: LabResult }
  'message.received': { fromId: string; toId: string; message: string; sentAt: string }
  'user.status': { userId: string; online: boolean }
}

// Generic WebSocket event type
export type WebSocketEvent<K extends keyof WebSocketEventMap = keyof WebSocketEventMap> = {
  type: K
  payload: WebSocketEventMap[K]
  ts: string
}

// UI state helpers
export type LoadingState = 'idle' | 'loading' | 'succeeded' | 'failed'

export interface FormState<T = any> {
  values: T
  touched: Partial<Record<string, boolean>>
  errors: Partial<Record<string, string>>
  isValid: boolean
  isSubmitting: boolean
}

// Exported alias for external usage (as per spec)
export type { User as UserType }

// Note: LabResult type is defined earlier in this file to satisfy WebSocketEventMap dependency.
// The rest of the codebase should import these types from '@/core/contracts'

// ARIA/keyboard-friendly helpers (types-only placeholders for future integration)
export type AriaLabel = string

// End of contracts file

// Self-check comments
// [ ] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from `@/app/config`
// [ ] Exports default named component
// [ ] Adds basic ARIA and keyboard handlers (where relevant)