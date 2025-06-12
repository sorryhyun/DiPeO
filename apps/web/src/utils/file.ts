/**
 * Unified file operations utilities
 * All file download, upload, save operations, and format detection
 */

import { toast } from 'react-hot-toast';
import type { ConverterDiagram } from '@/utils/converters/types';
import { getApiUrl, API_ENDPOINTS } from './api/config';
import { createLookupTable } from './dispatchTable';

export type FileFormat = 'light' | 'native' | 'readable' | 'llm-readable';

export interface ReadFileOptions {
  acceptedTypes?: string;
  maxSize?: number;
}

export interface SaveFileOptions {
  filename?: string;
  format: FileFormat;
  defaultFilename?: string;
}

export interface FileFormatInfo {
  format: FileFormat;
  isLLMFormat: boolean;
}

/**
 * Read file as text with options
 */
export const readFileAsText = (file: File, options?: ReadFileOptions): Promise<string> => {
  return new Promise((resolve, reject) => {
    if (options?.maxSize && file.size > options.maxSize) {
      reject(new Error(`File size exceeds maximum allowed size of ${options.maxSize} bytes`));
      return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result;
      if (typeof result === 'string') {
        resolve(result);
      } else {
        reject(new Error('Failed to read file as text'));
      }
    };
    reader.onerror = () => reject(new Error(`Failed to read file: ${file.name}`));
    reader.readAsText(file);
  });
};

/**
 * File selection dialog
 */
export const selectFile = (options?: ReadFileOptions): Promise<File> => {
  return new Promise((resolve, reject) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = options?.acceptedTypes || '.yaml,.yml,.native.yaml,.readable.yaml,.llm-readable.yaml';
    
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        resolve(file);
      } else {
        reject(new Error('No file selected'));
      }
    };
    
    input.click();
  });
};

/**
 * Basic file download
 */
export const downloadFile = (content: string, filename: string, mimeType: string = 'text/plain'): void => {
  const blob = new Blob([content], { type: mimeType });
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
 * Enhanced download with File System Access API
 */
export const downloadEnhanced = async (
  content: string,
  filename: string,
  mimeType: string = 'text/plain'
): Promise<void> => {
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
      if (err instanceof Error && err.name !== 'AbortError') {
        console.warn('File System Access API failed:', err);
      }
    }
  }
  downloadFile(content, filename, mimeType);
};

/**
 * Save diagram to backend
 */
export const saveDiagramToBackend = async (
  diagram: ConverterDiagram,
  options: SaveFileOptions
): Promise<{ success: boolean; filename: string }> => {
  try {
    const response = await fetch(getApiUrl(API_ENDPOINTS.SAVE_DIAGRAM), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        diagram,
        filename: options.filename || options.defaultFilename || 'diagram',
        format: options.format
      }),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to save file: ${response.statusText}`);
    }
    
    const result = await response.json();
    return {
      success: true,
      filename: result.filename
    };
  } catch (error) {
    console.error('[Save diagram]', error);
    toast.error(`Save diagram: ${(error as Error).message}`);
    throw error;
  }
};

/**
 * Detect file format from content and filename
 */
export const detectFileFormat = (content: string, filename?: string): FileFormatInfo => {
  if (filename) {
    const ext = filename.split('.').pop()?.toLowerCase();
    
    // Check for specific YAML types by filename
    if (filename.includes('.native.yaml') || filename.includes('.native.yml')) {
      return { format: 'native', isLLMFormat: false };
    }
    if (filename.includes('.readable.yaml') || filename.includes('.readable.yml')) {
      return { format: 'readable', isLLMFormat: false };
    }
    if (filename.includes('.llm-readable') || filename.includes('.llm.yaml') || filename.includes('.llm.yml')) {
      return { format: 'llm-readable', isLLMFormat: true };
    }
    
    if (ext === 'yaml' || ext === 'yml') {
      // Check content to determine YAML type
      if (content.includes('flow:') && (content.includes('prompts:') || content.includes('persons:'))) {
        return { format: 'llm-readable', isLLMFormat: true };
      }
      if (content.includes('workflow:') && content.includes("version: '1.0'")) {
        return { format: 'readable', isLLMFormat: false };
      }
      // Check if it's native format (DomainDiagram structure)
      if (content.includes('metadata:') && content.includes('nodes:') && content.includes('arrows:')) {
        return { format: 'native', isLLMFormat: false };
      }
      // Default to light format for regular YAML files
      return { format: 'light', isLLMFormat: false };
    }
  }
  
  // Check content structure
  if (content.includes('flow:') && (content.includes('prompts:') || content.includes('persons:'))) {
    return { format: 'llm-readable', isLLMFormat: true };
  }
  if (content.includes('workflow:') && content.includes("version: '1.0'")) {
    return { format: 'readable', isLLMFormat: false };
  }
  // Check if it's native format (DomainDiagram structure)
  if (content.includes('metadata:') && content.includes('nodes:') && content.includes('arrows:')) {
    return { format: 'native', isLLMFormat: false };
  }
  if (content.includes(':') && (content.includes('-') || content.includes('  '))) {
    return { format: 'light', isLLMFormat: false };
  }
  
  // Default to light format
  return { format: 'light', isLLMFormat: false };
};

// Create lookup tables for file format mappings
const mimeTypeLookup = createLookupTable<FileFormat, string>({
  'light': 'text/yaml',
  'native': 'text/yaml',
  'readable': 'text/yaml',
  'llm-readable': 'text/yaml'
});

const fileExtensionLookup = createLookupTable<FileFormat, string>({
  'light': '.yaml',
  'native': '.native.yaml',
  'readable': '.readable.yaml',
  'llm-readable': '.llm-readable.yaml'
});

/**
 * Get MIME type for format
 */
export const getMimeType = (format: FileFormat): string => {
  return mimeTypeLookup(format) || 'text/plain';
};

/**
 * Get file extension for format
 */
export const getFileExtension = (format: FileFormat): string => {
  return fileExtensionLookup(format) || '.txt';
};

/**
 * Error handling wrapper for file operations
 */
export function withFileErrorHandling<TArgs extends any[], TReturn>(
  operation: (...args: TArgs) => Promise<TReturn>,
  operationName: string
): (...args: TArgs) => Promise<TReturn> {
  return async (...args: TArgs) => {
    try {
      return await operation(...args);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      toast.error(`${operationName} failed: ${errorMessage}`);
      throw error;
    }
  };
}