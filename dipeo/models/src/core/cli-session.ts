/**
 * CLI Session domain models
 * These interfaces define CLI session-related types for terminal operations
 */

export type CliSessionID = string & { readonly __brand: 'CliSessionID' };

export interface CliSession {
  id: CliSessionID;
  session_id: string;
  user_id?: string;
  started_at: string;
  last_active?: string;
  status: 'active' | 'inactive' | 'terminated';
  metadata?: Record<string, any>;
  current_directory?: string;
  environment?: Record<string, string>;
}

export interface CliSessionResult {
  success: boolean;
  session?: CliSession;
  message?: string;
  error?: string;
}
