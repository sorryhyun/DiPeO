/**
 * GraphQL-based file operations utilities
 * Handles diagram saving using GraphQL mutations
 */

import { toast } from 'react-hot-toast';
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
  type DiagramID 
} from '@/__generated__/graphql';
import type { SaveFileOptions } from './file';

/**
 * Save diagram to backend using GraphQL
 * @param diagramId - The diagram ID (file path)
 * @param options - Save options including format
 */
export const saveDiagramToBackendGraphQL = async (
  diagramId: DiagramID,
  options: SaveFileOptions
): Promise<{ success: boolean; filename: string }> => {
  try {
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
        : `${filename}.yaml`
    };
  } catch (error) {
    console.error('[Save diagram GraphQL]', error);
    toast.error(`Save diagram: ${(error as Error).message}`);
    throw error;
  }
};

/**
 * Upload diagram file using GraphQL
 */
export const uploadDiagramGraphQL = async (file: File, format?: string): Promise<{
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
export const uploadFileGraphQL = async (
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
      resolve(base64Content);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
};