import React from 'react';
import { downloadFile, getMimeType, FileFormat, withFileErrorHandling } from '../utils/fileUtils';

export const useDownload = () => {
  const [isDownloading, setIsDownloading] = React.useState(false);
  
  // Enhanced download with File System Access API support
  const downloadEnhanced = React.useCallback(async (
    data: string | Blob,
    filename: string,
    mimeType?: string
  ) => {
    setIsDownloading(true);
    
    try {
      const blob = data instanceof Blob 
        ? data 
        : new Blob([data], { type: mimeType || 'text/plain' });
      
      // Try modern File System Access API first if available
      if ('showSaveFilePicker' in window && typeof window.showSaveFilePicker === 'function') {
        try {
          // Determine file extension from filename
          const ext = filename.split('.').pop()?.toLowerCase() || 'txt';
          const mimeToExtMap: Record<string, string[]> = {
            'text/plain': ['.txt'],
            'application/json': ['.json'],
            'text/yaml': ['.yaml', '.yml', '.llm-yaml'],
            'text/csv': ['.csv'],
            'text/markdown': ['.md'],
          };
          
          const handle = await window.showSaveFilePicker({
            suggestedName: filename,
            types: [{
              description: 'Files',
              accept: Object.entries(mimeToExtMap).reduce((acc, [mime, exts]) => {
                acc[mime] = exts;
                return acc;
              }, {} as Record<string, string[]>),
            }],
          });
          
          const writable = await handle.createWritable();
          await writable.write(blob);
          await writable.close();
          return;
        } catch (err) {
          // User cancelled or API not supported, fall back to traditional method
          if (err instanceof Error && err.name !== 'AbortError') {
            console.warn('File System Access API failed, falling back to traditional download:', err);
          }
        }
      }
      
      // Fall back to unified downloadFile utility
      if (typeof data === 'string') {
        downloadFile(data, filename, mimeType);
      } else {
        // For blob data, convert to string or use URL
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.style.display = 'none';
        
        document.body.appendChild(a);
        a.click();
        
        setTimeout(() => {
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        }, 100);
      }
      
    } catch (error) {
      console.error('Download failed:', error);
      throw error;
    } finally {
      setIsDownloading(false);
    }
  }, []);
  
  // Type-safe download functions
  const downloadAs = React.useCallback(async (
    content: string,
    filename: string,
    format: FileFormat
  ) => {
    const mimeType = getMimeType(format);
    return downloadEnhanced(content, filename, mimeType);
  }, [downloadEnhanced]);
  
  const downloadJson = React.useCallback((data: object, filename: string) => {
    const content = JSON.stringify(data, null, 2);
    return downloadAs(content, filename, 'json');
  }, [downloadAs]);
  
  const downloadYaml = React.useCallback((data: string, filename: string) => {
    return downloadAs(data, filename, 'yaml');
  }, [downloadAs]);
  
  const downloadLLMYaml = React.useCallback((data: string, filename: string) => {
    return downloadAs(data, filename, 'llm-yaml');
  }, [downloadAs]);
  
  const downloadBlob = React.useCallback((blob: Blob, filename: string) => {
    return downloadEnhanced(blob, filename);
  }, [downloadEnhanced]);
  
  // Wrapped versions with error handling
  const safeDownload = withFileErrorHandling(downloadEnhanced, 'Download file');
  const safeDownloadJson = withFileErrorHandling(downloadJson, 'Download JSON');
  const safeDownloadYaml = withFileErrorHandling(downloadYaml, 'Download YAML');
  
  return { 
    // Core functions
    download: downloadEnhanced,
    downloadAs,
    downloadJson, 
    downloadYaml,
    downloadLLMYaml,
    downloadBlob,
    
    // Safe versions with error handling
    safeDownload,
    safeDownloadJson,
    safeDownloadYaml,
    
    // State
    isDownloading 
  };
};