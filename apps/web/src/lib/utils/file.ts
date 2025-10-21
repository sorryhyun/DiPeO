/**
 * Unified file operations utilities
 * All file download, upload, save operations, and format detection
 */

import { toast } from 'react-hot-toast';
import { apolloClient } from '@/lib/graphql/client';
import {
  UploadFileDocument,
  type UploadFileMutation,
  type UploadFileMutationVariables,
} from '@/__generated__/graphql';
import { DiagramFormat } from '@dipeo/models';

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
    input.accept = options?.acceptedTypes || '.json,.yaml,.yml,.react.json,.native.yaml,.readable.yaml';

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
 * Save diagram file to server using GraphQL
 */
export const saveDiagram = async (file: File, format?: DiagramFormat): Promise<{
  success: boolean;
  diagramId?: string;
  diagramName?: string;
  nodeCount?: number;
  message: string;
}> => {
  try {
    // Just send the path without 'files/' prefix
    // Backend will handle putting it in the right directory
    const path = file.name;

    const { data } = await apolloClient.mutate<UploadFileMutation, UploadFileMutationVariables>({
      mutation: UploadFileDocument,
      variables: {
        file,
        path
      }
    });

    if (!data?.uploadFile.success) {
      const errorMsg = (data?.uploadFile as Record<string, unknown>)?.error;
      throw new Error(typeof errorMsg === 'string' ? errorMsg : 'Failed to save diagram');
    }

    // Extract diagram ID from filename
    const filename = file.name;
    const diagramId = filename.replace('.yaml', '').replace('.yml', '').replace('.json', '');

    const uploadResult = data.uploadFile as Record<string, unknown>;
    return {
      success: true,
      diagramId,
      diagramName: filename,
      nodeCount: undefined, // We don't have this info from uploadFile
      message: typeof uploadResult.message === 'string' ? uploadResult.message : 'Diagram saved successfully'
    };
  } catch (error) {
    console.error('[Save diagram GraphQL]', error);
    const message = (error as Error).message;
    toast.error(`Save diagram: ${message}`);
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
        file: {
          filename,
          contentBase64,
          contentType
        },
        path: `uploads/${filename}`
      }
    });

    if (!data?.uploadFile.success) {
      const errorMsg = (data?.uploadFile as Record<string, unknown>)?.error;
      throw new Error(typeof errorMsg === 'string' ? errorMsg : 'Failed to upload file');
    }

    const uploadResult = data.uploadFile as Record<string, unknown>;
    return {
      success: true,
      path: typeof uploadResult.path === 'string' ? uploadResult.path : undefined,
      sizeBytes: typeof uploadResult.sizeBytes === 'number' ? uploadResult.sizeBytes : undefined,
      message: typeof uploadResult.message === 'string' ? uploadResult.message : undefined
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
export function withFileErrorHandling<TArgs extends unknown[], TReturn>(
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
