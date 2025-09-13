/**
 * File domain models
 * These interfaces define file-related types for diagram operations and storage
 */

export type FileID = string & { readonly __brand: 'FileID' };

export interface File {
  id: FileID;
  name: string;
  path: string;
  content?: string;
  size?: number;
  mime_type?: string;
  created_at?: string;
  modified_at?: string;
  metadata?: Record<string, any>;
}

export interface FileOperationResult {
  success: boolean;
  file?: File;
  message?: string;
  error?: string;
}
