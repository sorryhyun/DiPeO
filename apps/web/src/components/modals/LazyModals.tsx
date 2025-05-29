// Lazy loaded modal components with fallbacks
import React, { Suspense } from 'react';
import { ModalSkeleton } from '../skeletons/SkeletonComponents';

const ApiKeysModal = React.lazy(() => import('./ApiKeysModal'));

interface LazyApiKeysModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const LazyApiKeysModal: React.FC<LazyApiKeysModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;
  
  return (
    <Suspense fallback={<ModalSkeleton />}>
      <ApiKeysModal isOpen={isOpen} onClose={onClose} />
    </Suspense>
  );
};