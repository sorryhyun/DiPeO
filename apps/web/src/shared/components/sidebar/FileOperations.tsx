import React, { useState, useCallback, useEffect } from 'react';
import { Upload, Download } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/shared/components/ui/buttons/Button';
import { Select } from '@/shared/components/ui/inputs/Select';
import { 
  useConvertDiagramMutation,
  useUploadFileMutation
} from '@/__generated__/graphql';
import { DiagramFormat } from '@dipeo/domain-models';
import { useFileOperations } from '@/shared/hooks/useFileOperations';
import { serializeDiagram } from '@/shared/utils/diagramSerializer';

export const FileOperations: React.FC = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<DiagramFormat>(DiagramFormat.NATIVE);
  const [diagramName, setDiagramName] = useState<string>('diagram');

  const [convertDiagramMutation] = useConvertDiagramMutation();
  const [uploadFileMutation] = useUploadFileMutation();
  const { saveDiagram } = useFileOperations();

  // Initialize diagram name from URL
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const currentDiagramId = urlParams.get('diagram');
    if (currentDiagramId) {
      setDiagramName(currentDiagramId);
    }
  }, []);

  const handleConvertAndLoad = useCallback(() => {
    const finalName = diagramName.trim();
    if (!finalName) {
      toast.error('Please enter a diagram name');
      return;
    }
    
    setIsUploading(true);
    
    // Build the diagram path based on selected format
    let diagramPath = finalName;
    if (selectedFormat === DiagramFormat.LIGHT) {
      diagramPath = `light/${finalName}`;
    } else if (selectedFormat === DiagramFormat.READABLE) {
      diagramPath = `readable/${finalName}`;
    } else if (selectedFormat === DiagramFormat.NATIVE) {
      diagramPath = `native/${finalName}`;
    }
    
    // Update URL without page refresh
    const newUrl = `/?diagram=${diagramPath}`;
    window.history.pushState({}, '', newUrl);
    
    // Dispatch a custom event that useDiagramLoader can listen to
    window.dispatchEvent(new PopStateEvent('popstate'));
    
    // Reset loading state after a short delay
    setTimeout(() => setIsUploading(false), 1000);
  }, [diagramName, selectedFormat]);

  const handleExport = useCallback(async () => {
    try {
      // Use the user-provided name or default
      const finalName = diagramName.trim() || 'diagram';
      
      // Generate filename based on format
      const extension = selectedFormat === DiagramFormat.NATIVE ? 'json' : 'yaml';
      const filename = `${finalName}.${extension}`;
      
      // For native format, use the existing saveDiagram function
      if (selectedFormat === DiagramFormat.NATIVE) {
        await saveDiagram(filename, selectedFormat);
        const formatDir = selectedFormat.toLowerCase();
        toast.success(`Saved to ${formatDir}/${filename}`);
        return;
      }
      
      // For light and readable formats, use convert + upload approach
      // First, serialize the current diagram state
      const diagramContent = serializeDiagram();
      
      // Convert diagram to the desired format
      const convertResult = await convertDiagramMutation({
        variables: {
          content: diagramContent,
          targetFormat: selectedFormat,
          includeMetadata: true
        }
      });
      
      if (!convertResult.data?.convertDiagram?.success) {
        throw new Error(convertResult.data?.convertDiagram?.error || 'Conversion failed');
      }
      
      // Get the converted content
      const convertedContent = convertResult.data.convertDiagram.content;
      if (!convertedContent) {
        throw new Error('No content returned from conversion');
      }
      
      // Determine the category based on format
      const category = `diagrams/${selectedFormat}`;
      
      // Create a File object from the converted content
      const file = new File([convertedContent], filename, { 
        type: 'text/yaml' 
      });
      
      // Upload the file directly to diagrams/{format}/ directory
      const uploadResult = await uploadFileMutation({
        variables: {
          file,
          category
        }
      });
      
      if (!uploadResult.data?.uploadFile?.success) {
        throw new Error(uploadResult.data?.uploadFile?.error || 'Upload failed');
      }
      
      // Show success message
      toast.success(`Saved to ${category}/${filename}`);
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
          onChange={(e) => setDiagramName(e.target.value)}
          placeholder="Diagram name"
          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        
        <Select
          value={selectedFormat}
          onChange={(e) => setSelectedFormat(e.target.value as DiagramFormat)}
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