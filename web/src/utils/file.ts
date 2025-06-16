/**
 * Unified file operations utilities
 * All file download, upload, save operations, and format detection
 */

import { toast } from 'react-hot-toast';
import { createLookupTable } from './dispatchTable';
import { apolloClient } from '@/graphql/client';
import { 
  SaveDiagramDocument,
  type SaveDiagramMutation,
  type SaveDiagramMutationVariables,
  UploadFileDocument,
  type UploadFileMutation,
  type UploadFileMutationVariables,
  UploadDiagramDocument,
  type UploadDiagramMutation,
  type UploadDiagramMutationVariables,
  DiagramFormat
} from '@/__generated__/graphql';
import type { DiagramID } from '../types/branded';

export type FileFormat = DiagramFormat;

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
  format: DiagramFormat;
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
 * Save diagram to backend using GraphQL
 * This function now properly handles both new and existing diagrams
 * @param diagramId - The diagram ID (file path) - optional for new diagrams
 * @param options - Save options including format
 */
export const saveDiagramToBackend = async (
  diagramId: DiagramID | null,
  options: SaveFileOptions & { diagramContent?: any }
): Promise<{ success: boolean; filename: string; diagramId?: string }> => {
  try {
    // If we have diagram content, we need to upload it as a new diagram
    if (options.diagramContent) {
      // Create a file from the diagram content
      const filename = options.filename || options.defaultFilename || 'diagram.json';
      const content = typeof options.diagramContent === 'string' 
        ? options.diagramContent 
        : JSON.stringify(options.diagramContent, null, 2);
      
      const file = new File([content], filename, { 
        type: filename.endsWith('.json') ? 'application/json' : 'text/yaml' 
      });
      
      // Upload the diagram
      const uploadResult = await uploadDiagram(file, options.format);
      
      if (!uploadResult.success) {
        throw new Error(uploadResult.message || 'Failed to upload diagram');
      }
      
      return {
        success: true,
        filename: uploadResult.diagramName || filename,
        diagramId: uploadResult.diagramId
      };
    }
    
    // If no content provided but we have a diagramId, use the existing save mutation
    if (diagramId) {
      const { data } = await apolloClient.mutate<SaveDiagramMutation, SaveDiagramMutationVariables>({
        mutation: SaveDiagramDocument,
        variables: {
          diagramId,
          format: options.format || undefined
        }
      });
      
      if (!data?.saveDiagram.success) {
        throw new Error(data?.saveDiagram.error || 'Failed to save diagram');
      }
      
      // Extract filename from the message or use the diagram name
      const filename = data.saveDiagram.diagram?.metadata?.name || 
                      options.filename || 
                      options.defaultFilename || 
                      'diagram';
      
      return {
        success: true,
        filename: filename.endsWith('.yaml') || filename.endsWith('.yml') || filename.endsWith('.json') 
          ? filename 
          : `${filename}.yaml`,
        diagramId
      };
    }
    
    // No diagram ID and no content - error
    throw new Error('Either diagramId or diagramContent must be provided');
    
  } catch (error) {
    console.error('[Save diagram GraphQL]', error);
    toast.error(`Save diagram: ${(error as Error).message}`);
    throw error;
  }
};

/**
 * Detect file format from filename only
 * No content-based detection to avoid confusion
 */
export const detectFileFormat = (content: string, filename?: string): FileFormatInfo => {
  if (!filename) {
    // Default to native format if no filename provided
    return { format: DiagramFormat.Native, isLLMFormat: false };
  }
  
  // Check for specific format extensions in filename
  if (filename.includes('.native.yaml') || filename.includes('.native.yml')) {
    return { format: DiagramFormat.Native, isLLMFormat: false };
  }
  
  if (filename.includes('.readable.yaml') || filename.includes('.readable.yml')) {
    return { format: DiagramFormat.Readable, isLLMFormat: false };
  }
  
  if (filename.includes('.llm.yaml') || filename.includes('.llm.yml') || filename.includes('.llm-readable')) {
    return { format: DiagramFormat.Llm, isLLMFormat: true };
  }
  
  // For plain .yaml or .yml files, default to light format
  const ext = filename.split('.').pop()?.toLowerCase();
  if (ext === 'yaml' || ext === 'yml') {
    return { format: DiagramFormat.Light, isLLMFormat: false };
  }
  
  // Default to native format for unrecognized extensions
  return { format: DiagramFormat.Native, isLLMFormat: false };
};

// Create lookup tables for file format mappings
const mimeTypeLookup = createLookupTable<DiagramFormat, string>({
  [DiagramFormat.Light]: 'text/yaml',
  [DiagramFormat.Native]: 'text/yaml',
  [DiagramFormat.Readable]: 'text/yaml',
  [DiagramFormat.Llm]: 'text/yaml'
});

const fileExtensionLookup = createLookupTable<DiagramFormat, string>({
  [DiagramFormat.Light]: '.yaml',
  [DiagramFormat.Native]: '.native.yaml',
  [DiagramFormat.Readable]: '.readable.yaml',
  [DiagramFormat.Llm]: '.llm-readable.yaml'
});

/**
 * Get MIME type for format
 */
export const getMimeType = (format: DiagramFormat): string => {
  return mimeTypeLookup(format) || 'text/plain';
};

/**
 * Get file extension for format
 */
export const getFileExtension = (format: DiagramFormat): string => {
  return fileExtensionLookup(format) || '.txt';
};

/**
 * Upload diagram file using GraphQL
 */
export const uploadDiagram = async (file: File, format?: DiagramFormat): Promise<{
  success: boolean;
  diagramId?: string;
  diagramName?: string;
  nodeCount?: number;
  message: string;
}> => {
  try {
    const { data } = await apolloClient.mutate<UploadDiagramMutation, UploadDiagramMutationVariables>({
      mutation: UploadDiagramDocument,
      variables: {
        file,
        format,
        validateOnly: false
      }
    });
    
    if (!data?.uploadDiagram.success) {
      throw new Error(data?.uploadDiagram.message || 'Failed to upload diagram');
    }
    
    return {
      success: true,
      diagramId: data.uploadDiagram.diagramId || undefined,
      diagramName: data.uploadDiagram.diagramName || undefined,
      nodeCount: data.uploadDiagram.nodeCount || undefined,
      message: data.uploadDiagram.message
    };
  } catch (error) {
    console.error('[Upload diagram GraphQL]', error);
    const message = (error as Error).message;
    toast.error(`Upload diagram: ${message}`);
    return {
      success: false,
      message
    };
  }
};

/**
 * Upload a generic file using GraphQL
 */
export const uploadFile = async (
  filename: string,
  contentBase64: string,
  contentType?: string
): Promise<{
  success: boolean;
  path?: string;
  sizeBytes?: number;
  message?: string;
}> => {
  try {
    const { data } = await apolloClient.mutate<UploadFileMutation, UploadFileMutationVariables>({
      mutation: UploadFileDocument,
      variables: {
        input: {
          filename,
          contentBase64,
          contentType
        }
      }
    });
    
    if (!data?.uploadFile.success) {
      throw new Error(data?.uploadFile.error || 'Failed to upload file');
    }
    
    return {
      success: true,
      path: data.uploadFile.path || undefined,
      sizeBytes: data.uploadFile.sizeBytes || undefined,
      message: data.uploadFile.message || undefined
    };
  } catch (error) {
    console.error('[Upload file GraphQL]', error);
    const message = (error as Error).message;
    toast.error(`Upload file: ${message}`);
    return {
      success: false,
      message
    };
  }
};

/**
 * Helper function to convert File to base64
 */
export const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const base64 = reader.result as string;
      // Remove the data URL prefix (e.g., "data:text/plain;base64,")
      const base64Content = base64.split(',')[1];
      if (base64Content) {
        resolve(base64Content);
      } else {
        reject(new Error('Failed to extract base64 content from file'));
      }
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
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