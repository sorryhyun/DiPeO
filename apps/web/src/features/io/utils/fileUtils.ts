import { toast } from 'react-hot-toast';
import { getApiUrl, API_ENDPOINTS } from '@/common/utils/apiConfig';
import { createErrorHandlerFactory } from '@/common/types/errorHandling';

/**
 * File format types supported by the system
 */
export type FileFormat = 'json' | 'yaml' | 'llm-yaml';

/**
 * Options for reading files
 */
export interface ReadFileOptions {
  acceptedTypes?: string;
  maxSize?: number;
}

/**
 * Options for saving files
 */
export interface SaveFileOptions {
  filename?: string;
  format: FileFormat;
  defaultFilename?: string;
}

/**
 * Result of file format detection
 */
export interface FileFormatInfo {
  format: FileFormat;
  isLLMFormat: boolean;
}

/**
 * Unified file reader utility
 * @param file - The file to read
 * @param options - Options for reading
 * @returns Promise with file content as string
 */
export const readFileAsText = (file: File, options?: ReadFileOptions): Promise<string> => {
  return new Promise((resolve, reject) => {
    // Validate file size if specified
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
    
    reader.onerror = () => {
      reject(new Error(`Failed to read file: ${file.name}`));
    };
    
    reader.readAsText(file);
  });
};

/**
 * Detect file format from content
 * @param content - File content as string
 * @param filename - Optional filename for extension-based detection
 * @returns Detected file format information
 */
export const detectFileFormat = (content: string, filename?: string): FileFormatInfo => {
  // Check filename extension first
  if (filename) {
    const ext = filename.split('.').pop()?.toLowerCase();
    if (ext === 'json') {
      return { format: 'json', isLLMFormat: false };
    }
    if (ext === 'yaml' || ext === 'yml') {
      // Check if it's LLM-friendly YAML
      if (content.includes('flow:') && (content.includes('prompts:') || content.includes('agents:'))) {
        return { format: 'llm-yaml', isLLMFormat: true };
      }
      return { format: 'yaml', isLLMFormat: false };
    }
  }
  
  // Content-based detection
  try {
    JSON.parse(content);
    return { format: 'json', isLLMFormat: false };
  } catch {
    // Not JSON, check for YAML patterns
    if (content.includes('flow:') && (content.includes('prompts:') || content.includes('agents:'))) {
      return { format: 'llm-yaml', isLLMFormat: true };
    }
    if (content.includes(':') && (content.includes('-') || content.includes('  '))) {
      return { format: 'yaml', isLLMFormat: false };
    }
  }
  
  // Default to JSON if unclear
  return { format: 'json', isLLMFormat: false };
};

/**
 * Save diagram to backend directory
 * @param diagram - Diagram data to save
 * @param options - Save options
 * @returns Promise with save result
 */
export const saveDiagramToBackend = async (
  diagram: any,
  options: SaveFileOptions
): Promise<{ success: boolean; filename: string }> => {
  const errorHandler = createErrorHandlerFactory({ error: toast.error })('Save diagram');
  
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
    errorHandler(error as Error);
    throw error;
  }
};

/**
 * Download content as a file
 * @param content - Content to download
 * @param filename - Name of the file
 * @param mimeType - MIME type of the file
 */
export const downloadFile = (content: string, filename: string, mimeType: string = 'text/plain') => {
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
 * Create a file input element and handle file selection
 * @param options - Options for file selection
 * @returns Promise with selected file
 */
export const selectFile = (options?: ReadFileOptions): Promise<File> => {
  return new Promise((resolve, reject) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = options?.acceptedTypes || '.json,.yaml,.yml';
    
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
 * Higher-order function for file operations with consistent error handling
 * @param operation - The file operation to perform
 * @param operationName - Name of the operation for error messages
 * @returns Wrapped function with error handling
 */
export function withFileErrorHandling<TArgs extends any[], TReturn>(
  operation: (...args: TArgs) => Promise<TReturn>,
  operationName: string
): (...args: TArgs) => Promise<TReturn> {
  return async (...args: TArgs) => {
    try {
      const result = await operation(...args);
      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      toast.error(`${operationName} failed: ${errorMessage}`);
      throw error;
    }
  };
}

/**
 * Get MIME type for file format
 * @param format - File format
 * @returns MIME type string
 */
export const getMimeType = (format: FileFormat): string => {
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
 * @param format - File format
 * @returns File extension
 */
export const getFileExtension = (format: FileFormat): string => {
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