import React from 'react';
import { Modal } from '@/ui/components/common/feedback';
import { DiagramFileManager } from '@/domain/diagram';

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
      <DiagramFileManager />
    </Modal>
  );
};