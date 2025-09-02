// filepath: src/core/contracts.ts

// Role union and basic identity types
export type Role = 'patient' | 'doctor' | 'nurse' | 'admin';

// User hierarchy
export interface UserBase {
  id: string;
  email: string;
  name: string;
  avatarUrl?: string;
  roles: Role[];
  createdAt: string;
  updatedAt?: string;
}

export interface Patient extends UserBase {
  dob?: string;
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
  startAt: string;
  endAt: string;
  status: 'scheduled' | 'cancelled' | 'completed' | 'no_show';
  location: string;
  type: 'in_person' | 'telemedicine';
  notes?: string;
  metadata?: Record<string, unknown>;
}

export interface MedicalRecordEntry {
  id: string;
  type: 'note' | 'lab' | 'imaging' | 'prescription';
  authorId: string;
  createdAt: string;
  data: Record<string, any>;
}

export interface MedicalRecord {
  id: string;
  patientId: string;
  diagnoses: Array<{
    code: string;
    name: string;
    recordedAt: string;
    notes?: string;
  }>;
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

// API response types
export type ApiResult<T> = {
  success: true;
  data: T;
  meta?: Record<string, any>;
};

export type ApiError = {
  success: false;
  error: {
    code: string;
    message: string;
    details?: any;
  };
};

export type ApiResponse<T> = ApiResult<T> | ApiError;

export type PaginatedResponse<T> = ApiResult<{
  items: T[];
  page: number;
  pageSize: number;
  total: number;
}>;

// Pagination interface for request parameters
export interface Pagination {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

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

// WebSocket & real-time event types
export type WebSocketEventMap = {
  'appointment.updated': { appointment: Appointment };
  'labresult.created': { lab: LabResult };
  'message.received': { 
    fromId: string; 
    toId: string; 
    message: string; 
    sentAt: string;
  };
  'user.status': { 
    userId: string; 
    online: boolean;
  };
};

export type WebSocketEvent<K extends keyof WebSocketEventMap = keyof WebSocketEventMap> = {
  type: K;
  payload: WebSocketEventMap[K];
  ts: string;
};

// UI state and helpers
export type LoadingState = 'idle' | 'loading' | 'succeeded' | 'failed';

export interface FormState<T = any> {
  values: T;
  touched: Partial<Record<keyof T, boolean>>;
  errors: Partial<Record<keyof T, string>>;
  isValid: boolean;
  isSubmitting: boolean;
}

// Type guards for user role checking
export function isPatient(user: User): user is Patient {
  return 'dob' in user || 'medicalRecordId' in user;
}

export function isDoctor(user: User): user is Doctor {
  return 'specialty' in user || 'licenseNumber' in user;
}

export function isNurse(user: User): user is Nurse {
  return 'department' in user && !('specialty' in user);
}

// Type guard for API responses
export function isApiSuccess<T>(response: ApiResponse<T>): response is ApiResult<T> {
  return response.success === true;
}

export function isApiError(response: ApiResponse<any>): response is ApiError {
  return response.success === false;
}

// Self-Check Comments:
// [x] Uses `@/` imports only - N/A (no imports needed)
// [x] Uses providers/hooks (no direct DOM/localStorage side effects) - Pure type definitions, no side effects
// [x] Reads config from `@/app/config` - N/A (type definitions file)
// [x] Exports default named component - N/A (type definitions file, exports named types)
// [x] Adds basic ARIA and keyboard handlers - N/A (type definitions file, not UI component)
