/**
 * Centralized file operations utilities
 * All file download, upload, and save operations should go through this module
 */

import type { ApiResponse, Diagram } from '../../types';
import { getApiUrl, API_ENDPOINTS } from './apiConfig';

/**
 * Basic file download function
 * Downloads a file to the user's device using traditional download approach
 */
export const downloadFile = (content: string, filename: string): void => {
  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/**
 * Enhanced download with File System Access API support
 * Falls back to basic download if API not available
 */
export const downloadEnhanced = async (
  content: string,
  filename: string,
  mimeType: string = 'text/plain'
): Promise<void> => {
  // Check if File System Access API is available
  if ('showSaveFilePicker' in window && typeof window.showSaveFilePicker === 'function') {
    try {
      const handle = await window.showSaveFilePicker({
        suggestedName: filename,
        types: [{
          description: 'Text files',
          accept: { [mimeType]: [`.${filename.split('.').pop()}`] }
        }]
      });
      const writable = await handle.createWritable();
      await writable.write(content);
      await writable.close();
      return;
    } catch (err) {
      // User cancelled or API failed, fall back to basic download
      if (err instanceof Error && err.name !== 'AbortError') {
        console.warn('File System Access API failed:', err);
      }
    }
  }
  
  // Fallback to basic download
  downloadFile(content, filename);
};

/**
 * Download blob data
 */
export const downloadBlob = (blob: Blob, filename: string): void => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/**
 * Read file as text
 */
export const readFileAsText = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result;
      if (typeof content === 'string') {
        resolve(content);
      } else {
        reject(new Error('Failed to read file as text'));
      }
    };
    reader.onerror = reject;
    reader.readAsText(file);
  });
};

/**
 * Open file selection dialog
 */
export const selectFile = (accept?: string): Promise<File | null> => {
  return new Promise((resolve) => {
    const input = document.createElement('input');
    input.type = 'file';
    if (accept) input.accept = accept;
    
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      resolve(file || null);
    };
    
    input.click();
  });
};

/**
 * Save diagram to backend
 */
export const saveDiagramToBackend = async (
  diagram: Diagram,
  filename: string
): Promise<ApiResponse<{ path: string }>> => {
  const response = await fetch(getApiUrl(API_ENDPOINTS.SAVE_DIAGRAM), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      diagram,
      filename,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || 'Failed to save diagram');
  }

  return response.json();
};

/**
 * Get MIME type for file format
 */
export const getMimeType = (format: 'json' | 'yaml' | 'llm-yaml'): string => {
  switch (format) {
    case 'json':
      return 'application/json';
    case 'yaml':
    case 'llm-yaml':
      return 'text/yaml';
    default:
      return 'text/plain';
  }
};

/**
 * Get file extension for format
 */
export const getFileExtension = (format: 'json' | 'yaml' | 'llm-yaml'): string => {
  switch (format) {
    case 'json':
      return '.json';
    case 'yaml':
      return '.yaml';
    case 'llm-yaml':
      return '.llm-yaml';
    default:
      return '.txt';
  }
};

/**
 * Detect file format from filename
 */
export const detectFileFormat = (filename: string): 'json' | 'yaml' | 'llm-yaml' | null => {
  const lower = filename.toLowerCase();
  if (lower.endsWith('.json')) return 'json';
  if (lower.endsWith('.llm-yaml')) return 'llm-yaml';
  if (lower.endsWith('.yaml') || lower.endsWith('.yml')) return 'yaml';
  return null;
};

/**
 * Error handling wrapper for file operations
 */
export const withFileErrorHandling = async <T>(
  operation: () => Promise<T>,
  errorMessage: string
): Promise<T | null> => {
  try {
    return await operation();
  } catch (error) {
    console.error(errorMessage, error);
    return null;
  }
};