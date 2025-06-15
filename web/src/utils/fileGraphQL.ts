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
  type DiagramID 
} from '@/generated/graphql';
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
 * Upload diagram file using GraphQL (when available)
 * Note: This is a placeholder for when the upload mutations are exposed in the schema
 */
export const uploadDiagramGraphQL = async (file: File): Promise<{
  success: boolean;
  diagramId?: string;
  message: string;
}> => {
  // TODO: Implement when upload mutations are exposed in GraphQL schema
  throw new Error('File upload via GraphQL is not yet available. Use REST API for now.');
};