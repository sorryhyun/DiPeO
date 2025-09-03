// FILE: src/core/contracts.ts

// Core domain contracts and shared DTOs for the healthcare application.
// This file is the canonical type library used across services, components and providers.
// Exposed exports: User, AuthTokens, ApiResponse<T>, Pagination, LoginPayload, RegisterPayload

// Domain Roles
export type Role = 'patient' | 'doctor' | 'nurse' | 'admin'

// Base user with common identity fields
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

// Unified User union type
export type User = Patient | Doctor | Nurse

// Healthcare domain models

// Appointment between patient and provider
export interface Appointment {
  id: string
  patientId: string
  providerId: string
  startAt: string // ISO string
  endAt?: string
  status: 'scheduled' | 'cancelled' | 'completed' | 'no_show'
  location?: string
  type: 'in_person' | 'telemedicine'
  notes?: string
  metadata?: Record<string, any>
}

// Medical record for a patient
export interface MedicalRecord {
  id: string
  patientId: string
  diagnoses: { code: string; name: string; recordedAt: string; notes?: string }[]
  allergies: string[]
  medicationsSummary?: string
  entries: MedicalRecordEntry[]
}

// Entry within a medical record
export interface MedicalRecordEntry {
  id: string
  type: 'note' | 'lab' | 'imaging' | 'prescription'
  authorId?: string
  createdAt: string
  data: Record<string, any>
}

// Prescription details
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

// Lab result for a patient
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

// API response shapes

// ApiResponse<T> is a discriminated union for success/data or error
export type ApiResponse<T> =
  | { success: true; data: T; meta?: Record<string, any> }
  | { success: false; error: { code: string; message: string; details?: any } }

// Pagination wrapper for generic lists
export interface Pagination<T = any> {
  items: T[]
  page: number
  pageSize: number
  total: number
}

// Auth payloads

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

// WebSocket & real-time event typings could be added here in kernel if needed

// Self-check annotations (for CI/documentation)
/*
// [ ] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from `@/app/config`
// [ ] Exports default named component
// [ ] Adds basic ARIA and keyboard handlers (where relevant)
*/