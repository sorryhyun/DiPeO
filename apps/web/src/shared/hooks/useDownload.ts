import React from 'react';

export const useDownload = () => {
  const [isDownloading, setIsDownloading] = React.useState(false);
  
  const download = React.useCallback(async (
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
          const handle = await window.showSaveFilePicker({
            suggestedName: filename,
            types: [{
              description: 'Files',
              accept: {
                'text/plain': ['.txt'],
                'application/json': ['.json'],
                'text/yaml': ['.yaml', '.yml'],
              },
            }],
          });
          
          const writable = await handle.createWritable();
          await writable.write(blob);
          await writable.close();
          return;
        } catch (err: any) {
          // User cancelled or API not supported, fall back to traditional method
          if (err.name !== 'AbortError') {
            console.warn('File System Access API failed, falling back to traditional download:', err);
          }
        }
      }
      
      // Traditional download method using blob URL
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.style.display = 'none';
      
      // Append to body, click, and remove
      document.body.appendChild(a);
      a.click();
      
      // Cleanup after a small delay to ensure download starts
      setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }, 100);
      
    } catch (error) {
      console.error('Download failed:', error);
      throw error;
    } finally {
      setIsDownloading(false);
    }
  }, []);
  
  const downloadJson = React.useCallback((data: object, filename: string) => {
    return download(JSON.stringify(data, null, 2), filename, 'application/json');
  }, [download]);
  
  const downloadYaml = React.useCallback((data: string, filename: string) => {
    return download(data, filename, 'text/yaml');
  }, [download]);
  
  const downloadBlob = React.useCallback((blob: Blob, filename: string) => {
    return download(blob, filename);
  }, [download]);
  
  return { 
    download, 
    downloadJson, 
    downloadYaml,
    downloadBlob,
    isDownloading 
  };
};