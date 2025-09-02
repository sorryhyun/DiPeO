// File: src/core/contracts.ts

// Domain roles
export type Role = 'patient' | 'doctor' | 'nurse' | 'admin'

// User hierarchy
export interface UserBase {
  id: string
  email: string
  name: string
  avatarUrl?: string
  roles: Role[]
  createdAt: string
  updatedAt?: string
}

export interface Patient extends UserBase {
  dob?: string
  gender?: 'male' | 'female' | 'other'
  medicalRecordId?: string
  primaryDoctorId?: string
}

export interface Doctor extends UserBase {
  specialty?: string
  licenseNumber?: string
  clinicIds?: string[]
}

export interface Nurse extends UserBase {
  department?: string
}

export type User = Patient | Doctor | Nurse | UserBase

// Healthcare domain models
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

export interface Diagnosis {
  code: string
  name: string
  recordedAt: string
  notes?: string
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
  diagnoses: Diagnosis[]
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

// API response types
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

export type PaginatedResponse<T> = ApiResult<{ items: T[]; page: number; pageSize: number; total: number }>

// Compatibility alias: some parts of the app may refer to ApiResponse
export type ApiResponse<T> = ApiResult<T>

// Pagination helper type (as a standalone alias for easy usage across UI layers)
export type Pagination<T> = { items: T[]; page: number; pageSize: number; total: number }

// Auth and payload types
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

// WebSocket & real-time event typings (optional per feature flag)
export type WebSocketEventMap = {
  'appointment.updated': { appointment: Appointment }
  'labresult.created': { lab: LabResult }
  'message.received': { fromId: string; toId: string; message: string; sentAt: string }
  'user.status': { userId: string; online: boolean }
}

export type WebSocketEvent<K extends keyof WebSocketEventMap = keyof WebSocketEventMap> = {
  type: K
  payload: WebSocketEventMap[K]
  ts: string
}

// UI state and helpers
export type LoadingState = 'idle' | 'loading' | 'succeeded' | 'failed'

export interface FormState<T = any> {
  values: T
  touched: Partial<Record<string, boolean>>
  errors: Partial<Record<string, string>>
  isValid: boolean
  isSubmitting: boolean
}

// Optional: simple runtime-safe helpers (types only; no runtime logic here)

// Self-Check (inline): 
// [ ] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from `@/app/config`
// [ ] Exports default named component
// [ ] Adds basic ARIA and keyboard handlers (where relevant)