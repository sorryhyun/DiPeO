import React from 'react';
import { X } from 'lucide-react';
import { Modal } from '@/components/ui/feedback/Modal';
import { DiagramFileManager } from '@/components/diagram/DiagramFileManager';

interface DiagramFileModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DiagramFileModal: React.FC<DiagramFileModalProps> = ({ isOpen, onClose }) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Diagram File Manager"
      className="max-w-2xl w-full max-h-[90vh] overflow-hidden"
    >
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Diagram File Manager
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
          </button>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          <DiagramFileManager />
        </div>
      </div>
    </Modal>
  );
};