import { useState } from 'react';
import { Button } from '@/shared/components/ui';
import { FileText } from 'lucide-react';
import { PromptFilePicker } from './PromptFilePicker';

interface PromptFileButtonProps {
  onSelectContent: (content: string) => void;
  className?: string;
  tooltip?: string;
}

export function PromptFileButton({ 
  onSelectContent, 
  className = '',
  tooltip = 'Load prompt from file'
}: PromptFileButtonProps) {
  const [showPicker, setShowPicker] = useState(false);
  
  const handleSelect = (content: string) => {
    onSelectContent(content);
    setShowPicker(false);
  };
  
  return (
    <>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className={`h-8 w-8 ${className}`}
        onClick={() => setShowPicker(true)}
        title={tooltip}
      >
        <FileText className="h-4 w-4" />
      </Button>
      
      <PromptFilePicker
        open={showPicker}
        onClose={() => setShowPicker(false)}
        onSelect={handleSelect}
      />
    </>
  );
}