import React from 'react';
import { Button } from './Button';

interface FileUploadButtonProps {
  accept?: string;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  children: React.ReactNode;
  variant?: 'outline' | 'default' | 'secondary' | 'destructive' | 'ghost' | 'link';
  className?: string;
  size?: 'default' | 'sm' | 'lg' | 'icon';
  multiple?: boolean;
  disabled?: boolean;
  title?: string;
}

export const FileUploadButton: React.FC<FileUploadButtonProps> = ({
  accept,
  onChange,
  children,
  variant = 'outline',
  className,
  size = 'default',
  multiple = false,
  disabled = false,
  title
}) => {
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  
  const handleClick = () => {
    // Safe ref access
    fileInputRef.current?.click();
  };
  
  const handleChange = React.useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    
    // Process file upload
    const files = event.target.files;
    if (files && files.length > 0) {
      onChange(event);
    }
    
    // Reset input to allow same file selection
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [onChange]);
  
  return (
    <>
      <Button 
        variant={variant} 
        className={className}
        size={size}
        onClick={handleClick}
        disabled={disabled}
        title={title}
      >
        {children}
      </Button>
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        onChange={handleChange}
        style={{ display: 'none' }}
        multiple={multiple}
        disabled={disabled}
        // Add aria-label for accessibility
        aria-label="File upload input"
      />
    </>
  );
};