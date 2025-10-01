import { useCallback, useState } from 'react';
import { DiagramFormat } from '@dipeo/models';
import { useConvertDiagramFormatMutation, useUploadFileMutation } from '@/__generated__/graphql';
import { serializeDiagram } from '@/domain/diagram/utils/diagramSerializer';
import { toast } from 'sonner';

interface UseDiagramSaveOptions {
  saveToFileSystem: (filename?: string, format?: DiagramFormat) => Promise<any>;
}

interface UseDiagramSaveParams {
  selectedFormat: DiagramFormat;
  diagramName: string;
  diagramId: string | null;
}

/**
 * Custom hook for handling diagram save operations with format conversion
 */
export function useDiagramSave({ saveToFileSystem }: UseDiagramSaveOptions) {
  const [isSaving, setIsSaving] = useState(false);
  const [convertDiagramMutation] = useConvertDiagramFormatMutation();
  const [uploadFileMutation] = useUploadFileMutation();

  /**
   * Extracts base filename by removing format-specific extensions
   */
  const extractBaseName = (filename: string): string => {
    let baseName = filename;

    // Remove format-specific double extensions first (e.g., .light.yaml, .readable.yaml)
    const formatExtensionRemoved = baseName.replace(/\.(native|light|readable)\.(json|yaml|yml)$/i, '');
    if (formatExtensionRemoved !== baseName) {
      baseName = formatExtensionRemoved;
    } else {
      // If no format-specific extension, just remove the file extension
      baseName = baseName.replace(/\.(json|yaml|yml)$/i, '');
    }

    // If nothing was removed (edge case), use everything before the last dot
    if (baseName === filename && filename.includes('.')) {
      baseName = filename.substring(0, filename.lastIndexOf('.'));
    }

    return baseName;
  };

  /**
   * Generates filename with appropriate format extension
   */
  const generateFilename = (baseName: string, format: DiagramFormat): string => {
    switch (format) {
      case DiagramFormat.NATIVE:
        return `${baseName}.native.json`;
      case DiagramFormat.LIGHT:
        return `${baseName}.light.yaml`;
      case DiagramFormat.READABLE:
        return `${baseName}.readable.yaml`;
      default:
        return `${baseName}.yaml`;
    }
  };

  /**
   * Checks if filename already has the correct format extension
   */
  const hasCorrectExtension = (filename: string, format: DiagramFormat): boolean => {
    switch (format) {
      case DiagramFormat.NATIVE:
        return filename.endsWith('.native.json');
      case DiagramFormat.LIGHT:
        return filename.endsWith('.light.yaml');
      case DiagramFormat.READABLE:
        return filename.endsWith('.readable.yaml');
      default:
        return false;
    }
  };

  /**
   * Determines the save path based on existing diagram ID and selected format
   */
  const determineSavePath = (
    diagramId: string | null,
    diagramName: string,
    selectedFormat: DiagramFormat
  ): string => {
    const finalName = diagramName.trim() || 'diagram';
    let savePath: string;
    let filename: string = '';

    if (diagramId) {
      // Parse the diagram ID to extract directory and base filename
      const pathParts = diagramId.split('/');
      const fullFilename = pathParts[pathParts.length - 1] || '';
      const directories = pathParts.slice(0, -1);

      // Extract base name
      let baseName = extractBaseName(fullFilename);

      // Use the user-provided name if it's different from the extracted base name
      if (finalName.trim() && finalName !== 'diagram' && finalName !== baseName) {
        // Extract just the filename part from finalName (in case user entered a path)
        const finalNameParts = finalName.split('/');
        const finalNameOnly = finalNameParts[finalNameParts.length - 1];

        // Check if the final name already has the correct format extension
        if (finalNameOnly && hasCorrectExtension(finalNameOnly, selectedFormat)) {
          filename = finalNameOnly;
        } else if (finalNameOnly) {
          // Clean the final name
          baseName = extractBaseName(finalNameOnly);
        }
      }

      // Generate filename based on selected format (only if not already set)
      if (!filename) {
        filename = generateFilename(baseName, selectedFormat);
      }

      // Reconstruct the path
      if (directories.length > 0) {
        // Check if we're in a format-specific directory that needs to be changed
        const lastDir = directories[directories.length - 1];
        if (lastDir === 'light' || lastDir === 'readable' || lastDir === 'native') {
          // Replace the format directory with the new format
          const newFormatDir = selectedFormat.toLowerCase();
          savePath = [...directories.slice(0, -1), newFormatDir, filename].join('/');
        } else {
          // Keep the existing directory structure
          savePath = [...directories, filename].join('/');
        }
      } else {
        // No directory, save directly in files/
        savePath = filename;
      }
    } else {
      // For new diagrams, check if finalName already has the correct extension
      if (hasCorrectExtension(finalName, selectedFormat)) {
        filename = finalName;
      } else {
        // Clean the filename and add appropriate extension
        const cleanName = extractBaseName(finalName);
        filename = generateFilename(cleanName, selectedFormat);
      }

      savePath = filename;
    }

    return savePath;
  };

  /**
   * Handles the save operation with format conversion if needed
   */
  const handleSave = useCallback(async (params: UseDiagramSaveParams) => {
    const { selectedFormat, diagramName, diagramId } = params;

    try {
      setIsSaving(true);

      // Determine the save path
      const savePath = determineSavePath(diagramId, diagramName, selectedFormat);

      // For native format, use the existing saveDiagram function
      if (selectedFormat === DiagramFormat.NATIVE) {
        await saveToFileSystem(savePath, selectedFormat);
        toast.success(`Saved to ${savePath}`);
        return;
      }

      // For light and readable formats, use convert + upload approach
      // First, serialize the current diagram state
      const diagramContent = JSON.stringify(serializeDiagram());

      // Convert diagram to the desired format
      const convertResult = await convertDiagramMutation({
        variables: {
          content: diagramContent,
          from_format: DiagramFormat.NATIVE,
          to_format: selectedFormat
        }
      });

      if (!convertResult.data?.convertDiagramFormat?.success) {
        throw new Error(convertResult.data?.convertDiagramFormat?.error || 'Conversion failed');
      }

      // Get the converted content
      const convertedContent = convertResult.data.convertDiagramFormat.data;
      if (!convertedContent) {
        throw new Error('No content returned from conversion');
      }

      // Extract filename from savePath
      const savePathParts = savePath.split('/');
      const saveFilename = savePathParts[savePathParts.length - 1];

      // Create a File object from the converted content
      const file = new File([convertedContent], saveFilename || 'diagram.yaml', {
        type: 'text/yaml'
      });

      // Upload the file to the appropriate directory
      const uploadResult = await uploadFileMutation({
        variables: {
          file,
          path: savePath
        }
      });

      if (!uploadResult.data?.uploadFile?.success) {
        throw new Error(uploadResult.data?.uploadFile?.error || 'Upload failed');
      }

      // Show success message
      toast.success(`Saved to ${savePath}`);
    } catch (error) {
      console.error('Save error:', error);
      toast.error(error instanceof Error ? error.message : 'Save failed');
    } finally {
      setIsSaving(false);
    }
  }, [saveToFileSystem, convertDiagramMutation, uploadFileMutation]);

  return {
    isSaving,
    handleSave
  };
}
