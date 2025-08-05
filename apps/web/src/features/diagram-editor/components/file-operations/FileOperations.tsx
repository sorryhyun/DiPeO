import React, { useState, useCallback, useEffect } from 'react';
import { Upload, Download } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/shared/components/forms/buttons/Button';
import { Select } from '@/shared/components/forms/Select';
import { 
  useConvertDiagramFormatMutation,
  useUploadFileMutation,
  useGetDiagramLazyQuery
} from '@/__generated__/graphql';
import { DiagramFormat } from '@dipeo/models';
import { useFileOperations } from '@/features/diagram-editor/hooks';
import { serializeDiagram } from '@/features/diagram-editor/utils/diagramSerializer';
import { useDiagramLoader } from '@/features/diagram-editor/hooks/useDiagramLoader';

export const FileOperations: React.FC = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<DiagramFormat>(DiagramFormat.NATIVE);
  const [diagramName, setDiagramName] = useState<string>('diagram');

  const [convertDiagramMutation] = useConvertDiagramFormatMutation();
  const [uploadFileMutation] = useUploadFileMutation();
  const { saveDiagram } = useFileOperations();
  const [getDiagram] = useGetDiagramLazyQuery();
  const { loadDiagramFromData } = useDiagramLoader();

  // Initialize with default format
  useEffect(() => {
    // Set default format based on user preference or keep as NATIVE
    setSelectedFormat(DiagramFormat.NATIVE);
  }, []);

  const handleConvertAndLoad = useCallback(async () => {
    const finalName = diagramName.trim();
    if (!finalName) {
      toast.error('Please enter a diagram name');
      return;
    }
    
    setIsUploading(true);
    
    try {
      // Build the diagram path based on selected format
      let diagramPath = finalName;
      if (selectedFormat === DiagramFormat.LIGHT) {
        diagramPath = `${selectedFormat}/${finalName}`;
      } else if (selectedFormat === DiagramFormat.READABLE) {
        diagramPath = `${selectedFormat}/${finalName}`;
      } else if (selectedFormat === DiagramFormat.NATIVE) {
        diagramPath = `${selectedFormat}/${finalName}`;
      }
      
      // Fetch diagram content from server
      const { data, error } = await getDiagram({
        variables: { id: diagramPath }
      });
      
      if (error) {
        toast.error(`Failed to load diagram: ${error.message}`);
        return;
      }
      
      if (data?.diagram) {
        // Load the diagram data directly without URL changes
        loadDiagramFromData({
          nodes: data.diagram.nodes || [],
          arrows: data.diagram.arrows || [],
          handles: data.diagram.handles || [],
          persons: data.diagram.persons || [],
          metadata: data.diagram.metadata
        });
        
        toast.success(`Loaded ${finalName}`);
      } else {
        toast.error('Diagram not found');
      }
    } catch (err) {
      console.error('Failed to load diagram:', err);
      toast.error('Failed to load diagram');
    } finally {
      setIsUploading(false);
    }
  }, [diagramName, selectedFormat, getDiagram, loadDiagramFromData]);

  const handleExport = useCallback(async () => {
    try {
      // Use the user-provided name or default
      const finalName = diagramName.trim() || 'diagram';
      
      // Check if the user already included the extension
      const hasExtension = finalName.endsWith('.json') || finalName.endsWith('.yaml') || finalName.endsWith('.yml');
      
      // Generate filename based on format
      const extension = selectedFormat === DiagramFormat.NATIVE ? 'json' : 'yaml';
      const filename = hasExtension ? finalName : `${finalName}.${extension}`;
      
      // For native format, use the existing saveDiagram function
      if (selectedFormat === DiagramFormat.NATIVE) {
        await saveDiagram(filename, selectedFormat);
        toast.success(`Saved as ${filename}`);
        return;
      }
      
      // For light and readable formats, use convert + upload approach
      // First, serialize the current diagram state
      const diagramContent = JSON.stringify(serializeDiagram());
      
      // Convert diagram to the desired format
      const convertResult = await convertDiagramMutation({
        variables: {
          content: diagramContent,
          fromFormat: DiagramFormat.NATIVE,
          toFormat: selectedFormat
        }
      });
      
      if (!convertResult.data?.convert_diagram_format?.success) {
        throw new Error(convertResult.data?.convert_diagram_format?.error || 'Conversion failed');
      }
      
      // Get the converted content
      const convertedContent = convertResult.data.convert_diagram_format.content;
      if (!convertedContent) {
        throw new Error('No content returned from conversion');
      }
      
      
      // Simply use the filename as the path
      // The saveDiagram function will prepend 'files/' to it
      const path = filename;
      
      // Create a File object from the converted content
      const file = new File([convertedContent], filename, { 
        type: 'text/yaml' 
      });
      
      // Upload the converted file
      const uploadResult = await uploadFileMutation({
        variables: {
          file,
          path: filename
        }
      });
      
      if (!uploadResult.data?.upload_file?.success) {
        throw new Error(uploadResult.data?.upload_file?.error || 'Upload failed');
      }
      
      toast.success(`Saved as ${filename}`);
    } catch (error) {
      console.error('Export error:', error);
      toast.error(error instanceof Error ? error.message : 'Export failed');
    }
  }, [selectedFormat, diagramName, saveDiagram, convertDiagramMutation, uploadFileMutation]);

  const exportFormats = [
    { value: DiagramFormat.NATIVE, label: 'Native JSON' },
    { value: DiagramFormat.READABLE, label: 'Readable YAML' },
    { value: DiagramFormat.LIGHT, label: 'Light YAML' }
  ];

  return (
    <div className="space-y-3">
      {/* Load diagram by name */}
      <Button
        onClick={handleConvertAndLoad}
        variant="default"
        className="w-full text-sm"
        size="sm"
        disabled={isUploading}
      >
        {isUploading ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
            <span>Loading...</span>
          </>
        ) : (
          <>
            <Upload className="w-4 h-4 mr-2" />
            <span>Convert and Load</span>
          </>
        )}
      </Button>

      {/* Export */}
      <div className="space-y-2">
        <input
          type="text"
          value={diagramName}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDiagramName(e.target.value)}
          placeholder="Diagram name"
          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        
        <Select
          value={selectedFormat}
          onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelectedFormat(e.target.value as DiagramFormat)}
          className="w-full text-sm"
        >
          {exportFormats.map(format => (
            <option key={format.value} value={format.value}>
              {format.label}
            </option>
          ))}
        </Select>
        
        <Button
          onClick={handleExport}
          variant="outline"
          className="w-full text-sm"
          size="sm"
        >
          <Download className="w-4 h-4 mr-2" />
          Convert and Save
        </Button>
      </div>
    </div>
  );
};