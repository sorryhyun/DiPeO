import React, { useState, useCallback, useRef } from 'react';
import { Upload, Download, FileUp, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/ui/components/common/forms/buttons';
import { Select } from '@/ui/components/common/forms';
import { useFileOperations } from '@/domain/diagram/hooks';
import { 
  useGetSupportedFormatsQuery
} from '@/__generated__/graphql';
import { DiagramFormat } from '@dipeo/models';

interface DiagramFileManagerProps {
  className?: string;
}

export const DiagramFileManager: React.FC<DiagramFileManagerProps> = ({ className }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<DiagramFormat>(DiagramFormat.NATIVE);
  const [includeMetadata, setIncludeMetadata] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Get diagram ID from file operations or state
  const diagramId = useRef<string | null>(null);

  const { saveDiagram, downloadAs } = useFileOperations();
  
  // Fetch supported formats from GraphQL
  const { data: formatsData, loading: formatsLoading } = useGetSupportedFormatsQuery();

  const handleFileSelect = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    
    try {
      // Use file operations hook to handle the file
      const result = await saveDiagram(file.name, selectedFormat);
      
      if (!result || !result.diagramId) {
        throw new Error('Failed to save diagram');
      }

      const { diagramId: newDiagramId, diagramName, nodeCount } = result;
      diagramId.current = newDiagramId || null;
      
      toast.success(
        <div className="flex flex-col gap-1">
          <span className="font-medium">Upload successful!</span>
          <span className="text-sm opacity-80">
            {diagramName} • {nodeCount} nodes
          </span>
        </div>
      );

    } catch (error) {
      console.error('Upload error:', error);
      toast.error(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setIsUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }, [saveDiagram, selectedFormat]);

  const handleExport = useCallback(async () => {
    try {
      // Use file operations hook to download
      await downloadAs(selectedFormat, undefined, includeMetadata);
    } catch (error) {
      console.error('Export error:', error);
    }
  }, [selectedFormat, includeMetadata, downloadAs]);

  return (
    <div className={`flex flex-col gap-6 p-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm ${className}`}>
      {/* Upload Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold flex items-center gap-2 text-gray-900 dark:text-gray-100">
          <Upload className="w-5 h-5" />
          Upload Diagram
        </h3>
        
        <div className="relative">
          <input
            ref={fileInputRef}
            type="file"
            accept=".yaml,.yml,.json"
            onChange={handleFileSelect}
            className="hidden"
            id="diagram-upload"
          />
          
          <label
            htmlFor="diagram-upload"
            className={`
              flex flex-col items-center justify-center w-full h-32 
              border-2 border-dashed rounded-lg cursor-pointer
              transition-all duration-200
              ${isUploading 
                ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20' 
                : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500 hover:bg-gray-50 dark:hover:bg-gray-700/50'
              }
            `}
          >
            {isUploading ? (
              <div className="flex flex-col items-center gap-2">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
                <span className="text-sm text-gray-600 dark:text-gray-400">Processing...</span>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <FileUp className="w-8 h-8 text-gray-400 dark:text-gray-500" />
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Drop YAML/JSON file here or click to browse
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-500">
                  {formatsLoading ? 'Loading formats...' : 
                   formatsData?.supported_formats
                     ?.filter(f => f.supports_import)
                     .map(f => f.format)
                     .join(', ') || 'Multiple formats supported'}
                </span>
              </div>
            )}
          </label>
        </div>

        <div className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <AlertCircle className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
          <p className="text-sm text-blue-800 dark:text-blue-300">
            Upload YAML diagram files to convert them into executable format.
            The system will auto-detect the format.
          </p>
        </div>
      </div>

      {/* Export Section */}
      <div className="space-y-4 pt-4 border-t dark:border-gray-700">
        <h3 className="text-lg font-semibold flex items-center gap-2 text-gray-900 dark:text-gray-100">
          <Download className="w-5 h-5" />
          Export Diagram
        </h3>

        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Export Format
            </label>
            <Select
              value={selectedFormat}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelectedFormat(e.target.value as DiagramFormat)}
              className="w-full"
              disabled={formatsLoading}
            >
              {formatsData?.supported_formats
                ?.filter(format => format.supports_export)
                .map(format => (
                  <option key={format.format} value={format.format.toUpperCase() as DiagramFormat}>
                    {format.name}
                  </option>
                )) || []}
            </Select>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              {formatsData?.supported_formats?.find(f => f.format.toUpperCase() === selectedFormat)?.description}
            </p>
          </div>

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={includeMetadata}
              onChange={(e) => setIncludeMetadata(e.target.checked)}
              className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">Include metadata</span>
          </label>

          <Button
            onClick={handleExport}
            disabled={!diagramId.current}
            variant={diagramId.current ? 'default' : 'secondary'}
            className="w-full"
          >
            {diagramId.current ? 'Export Diagram' : 'No diagram to export'}
          </Button>
        </div>
      </div>

      {/* Format Information */}
      <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
        <p className="font-medium">Supported formats:</p>
        <ul className="ml-4 space-y-0.5">
          <li>• <strong>Native JSON:</strong> Complete diagram with all properties (JSON format)</li>
          <li>• <strong>Light:</strong> Human-readable with label-based references (YAML format)</li>
          <li>• <strong>Readable:</strong> Workflow-oriented format (YAML format)</li>
        </ul>
      </div>
    </div>
  );
};