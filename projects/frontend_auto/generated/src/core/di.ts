// Core domain contracts and shared DTOs for the healthcare application

// Role and user hierarchy
export type Role = 'patient' | 'doctor' | 'nurse' | 'admin';

export interface UserBase {
  id: string;
  email: string;
  name: string;
  avatarUrl?: string;
  roles: Role[];
  createdAt: string; // ISO date string
  updatedAt?: string; // ISO date string
}

export interface Patient extends UserBase {
  dob?: string; // date of birth ISO
  gender?: 'male' | 'female' | 'other';
  medicalRecordId?: string;
  primaryDoctorId?: string;
}

export interface Doctor extends UserBase {
  specialty?: string;
  licenseNumber?: string;
  clinicIds?: string[];
}

export interface Nurse extends UserBase {
  department?: string;
}

export type User = Patient | Doctor | Nurse | UserBase;

// Healthcare domain models
export interface Appointment {
  id: string;
  patientId: string;
  providerId: string;
  startAt: string; // ISO date-time
  endAt: string;   // ISO date-time
  status: 'scheduled' | 'cancelled' | 'completed' | 'no_show';
  location?: string;
  type?: 'in_person' | 'telemedicine';
  notes?: string;
  metadata?: Record<string, unknown>;
}

export interface MedicalRecordEntry {
  id: string;
  type: 'note' | 'lab' | 'imaging' | 'prescription';
  authorId: string;
  createdAt: string; // ISO date-time
  data: Record<string, any>;
}

export interface Diagnosis {
  code: string;
  name: string;
  recordedAt: string; // ISO date-time
  notes?: string;
}

export interface MedicalRecord {
  id: string;
  patientId: string;
  diagnoses: Diagnosis[];
  allergies: string[];
  medicationsSummary?: string;
  entries: MedicalRecordEntry[];
}

export interface Prescription {
  id: string;
  patientId: string;
  prescriberId: string;
  medication: string;
  dose: string;
  frequency: string;
  startDate?: string;
  endDate?: string;
  instructions?: string;
  refills?: number;
}

export interface LabResult {
  id: string;
  patientId: string;
  testName: string;
  orderedById?: string;
  specimenDate?: string;
  resultDate?: string;
  value?: string | number;
  unit?: string;
  normalRange?: string;
  status: 'pending' | 'completed' | 'cancelled';
  attachments?: string[];
}

// API/Server contract types
export interface ApiResponseErrorDetails {
  code: string;
  message: string;
  details?: any;
}

export type ApiResult<T> = {
  success: true;
  data: T;
  meta?: Record<string, any>;
};

export type ApiError = {
  success: false;
  error: ApiResponseErrorDetails;
};

export type PaginatedResponse<T> = ApiResult<{ items: T[]; page: number; pageSize: number; total: number }>;

// Aliases to support existing and planned symbol names
export type ApiResponse<T> = ApiResult<T>;
export type Pagination<T> = PaginatedResponse<T>;

// Auth and payload types
export interface AuthTokens {
  accessToken: string;
  refreshToken?: string;
  expiresAt?: string | number;
}

export interface LoginPayload {
  email: string;
  password: string;
  otp?: string;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
  role?: Role;
}

// WebSocket & real-time event typings
export interface WebSocketEventMap {
  'appointment.updated': { appointment: Appointment };
  'labresult.created': { lab: LabResult };
  'message.received': { fromId: string; toId: string; message: string; sentAt: string };
  'user.status': { userId: string; online: boolean };
}

export type WebSocketEvent<K extends keyof WebSocketEventMap = keyof WebSocketEventMap> = {
  type: K;
  payload: WebSocketEventMap[K];
  ts: string;
};

// UI state helpers
export type LoadingState = 'idle' | 'loading' | 'succeeded' | 'failed';

export interface FormState<T = any> {
  values: T;
  touched: Partial<Record<string, boolean>>;
  errors: Partial<Record<string, string>>;
  isValid: boolean;
  isSubmitting: boolean;
}

// Small additional exportable types to satisfy shared usage
export type LabEventPayload = { lab: LabResult; };


// Self-check / metadata (no side effects here)
//
// [ ] Uses `@/` imports only
// [ ] Uses providers/hooks (no direct DOM/localStorage side effects)
// [ ] Reads config from `@/app/config`
// [ ] Exports default named component
// [ ] Adds basic ARIA and keyboard handlers (where relevant)