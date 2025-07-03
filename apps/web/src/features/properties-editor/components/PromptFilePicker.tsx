import { useState, useEffect } from 'react';
import { Modal, Button } from '@/shared/components/ui';
import { Loader2, FileText, FileCode, File } from 'lucide-react';
import { useQuery, useLazyQuery } from '@apollo/client';
import { GetPromptFilesDocument, GetPromptFileDocument } from '@/__generated__/graphql';
import { format } from 'date-fns';

interface PromptFile {
  name: string;
  path: string;
  size: number;
  modified: number;
  extension: string;
}

interface PromptFilePickerProps {
  open: boolean;
  onClose: () => void;
  onSelect: (content: string) => void;
}

export function PromptFilePicker({ open, onClose, onSelect }: PromptFilePickerProps) {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [previewContent, setPreviewContent] = useState<string>('');
  
  // Query to get list of prompt files
  const { data, loading, error } = useQuery(GetPromptFilesDocument, {
    skip: !open,
  });
  
  // Lazy query to get file content
  const [getFileContent, { loading: loadingContent }] = useLazyQuery(GetPromptFileDocument);
  
  const promptFiles = (data?.prompt_files || []) as PromptFile[];
  
  // Load preview when file is selected
  useEffect(() => {
    if (selectedFile) {
      getFileContent({
        variables: { filename: selectedFile },
        onCompleted: (data) => {
          const fileData = data.prompt_file as { content: string };
          setPreviewContent(fileData.content);
        },
      });
    }
  }, [selectedFile, getFileContent]);
  
  const handleSelect = () => {
    if (selectedFile && previewContent) {
      onSelect(previewContent);
      onClose();
    }
  };
  
  const getFileIcon = (extension: string) => {
    switch (extension) {
      case '.txt':
        return <FileText className="w-4 h-4" />;
      case '.json':
      case '.yaml':
      case '.yml':
        return <FileCode className="w-4 h-4" />;
      default:
        return <File className="w-4 h-4" />;
    }
  };
  
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };
  
  return (
    <Modal 
      isOpen={open} 
      onClose={onClose}
      title="Select Prompt File"
      className="max-w-4xl"
    >
      <div className="flex flex-col h-[500px]">
        <div className="flex gap-4 flex-1">
          {/* File List */}
          <div className="w-1/3 border rounded-lg">
            <div className="h-full overflow-y-auto">
              {loading && (
                <div className="flex items-center justify-center h-full">
                  <Loader2 className="w-6 h-6 animate-spin" />
                </div>
              )}
              
              {error && (
                <div className="p-4 text-sm text-destructive">
                  Error loading prompt files
                </div>
              )}
              
              {!loading && !error && promptFiles.length === 0 && (
                <div className="p-4 text-sm text-muted-foreground">
                  No prompt files found in /files/prompts/
                </div>
              )}
              
              {promptFiles.map((file) => (
                <button
                  key={file.name}
                  onClick={() => setSelectedFile(file.name)}
                  className={`w-full p-3 text-left hover:bg-accent transition-colors ${
                    selectedFile === file.name ? 'bg-accent' : ''
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {getFileIcon(file.extension)}
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">{file.name}</div>
                      <div className="text-xs text-muted-foreground">
                        {formatFileSize(file.size)} • {format(new Date(file.modified * 1000), 'MMM dd, yyyy')}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
          
          {/* Preview */}
          <div className="flex-1 border rounded-lg">
            <div className="h-full overflow-y-auto">
              {!selectedFile && (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  Select a file to preview
                </div>
              )}
              
              {selectedFile && loadingContent && (
                <div className="flex items-center justify-center h-full">
                  <Loader2 className="w-6 h-6 animate-spin" />
                </div>
              )}
              
              {selectedFile && !loadingContent && previewContent && (
                <pre className="p-4 text-sm font-mono whitespace-pre-wrap">
                  {previewContent}
                </pre>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex justify-end gap-2 mt-4">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button 
            onClick={handleSelect} 
            disabled={!selectedFile || !previewContent || loadingContent}
          >
            Use This Prompt
          </Button>
        </div>
      </div>
    </Modal>
  );
}