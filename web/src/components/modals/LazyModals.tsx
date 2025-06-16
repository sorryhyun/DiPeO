// Lazy loaded modal components with fallbacks
import React, { Suspense } from 'react';

const ApiKeysModal = React.lazy(() => import('./ApiKeysModal'));
const DiagramFileModal = React.lazy(() => import('./DiagramFileModal'));

interface LazyApiKeysModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface LazyDiagramFileModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const LazyApiKeysModal: React.FC<LazyApiKeysModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;
  
  return (
    <Suspense fallback={
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 shadow-xl">
          <div className="animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-32 mb-4"></div>
            <div className="space-y-3">
              <div className="h-4 bg-gray-100 rounded"></div>
              <div className="h-4 bg-gray-100 rounded"></div>
              <div className="h-4 bg-gray-100 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    }>
      <ApiKeysModal isOpen={isOpen} onClose={onClose} />
    </Suspense>
  );
};

export const LazyDiagramFileModal: React.FC<LazyDiagramFileModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;
  
  return (
    <Suspense fallback={
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 shadow-xl">
          <div className="animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-48 mb-4"></div>
            <div className="space-y-3">
              <div className="h-32 bg-gray-100 rounded"></div>
              <div className="h-4 bg-gray-100 rounded w-3/4"></div>
              <div className="h-4 bg-gray-100 rounded w-1/2"></div>
            </div>
          </div>
        </div>
      </div>
    }>
      <DiagramFileModal isOpen={isOpen} onClose={onClose} />
    </Suspense>
  );
};