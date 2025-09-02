// src/core/contracts.ts

// Domain roles
export type Role = 'patient' | 'doctor' | 'nurse' | 'admin'

// Basic user contracts
export interface UserBase {
  id: string
  email: string
  name: string
  avatarUrl?: string
  roles: Role[]
  createdAt: string
  updatedAt?: string
}

// Patient-specific user
export interface Patient extends UserBase {
  dob?: string
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

// Unified User type
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

// API response types
export type ApiResult<T> = { success: true; data: T; meta?: Record<string, any> }
export type ApiResponse<T> = ApiResult<T>

export type ApiError = {
  success: false
  error: { code: string; message: string; details?: any }
}

// Paginated API response
export type PaginatedResponse<T> = ApiResult<{ items: T[]; page: number; pageSize: number; total: number }>

export interface Pagination {
  page: number
  pageSize: number
  total?: number
}

// Authentication payloads
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

// WebSocket real-time events
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

// UI state helpers
export type LoadingState = 'idle' | 'loading' | 'succeeded' | 'failed'

export interface FormState<T = any> {
  values: T
  touched: Partial<Record<string, boolean>>
  errors: Partial<Record<string, string>>
  isValid: boolean
  isSubmitting: boolean
}