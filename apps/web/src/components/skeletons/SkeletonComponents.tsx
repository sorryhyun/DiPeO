// Skeleton loading components for improved perceived performance
import React from 'react';

export const ConversationSkeleton: React.FC = () => (
  <div className="h-full flex flex-col animate-pulse">
    {/* Person bar skeleton */}
    <div className="flex items-center justify-between px-4 py-2 bg-gray-100 border-b">
      <div className="flex items-center space-x-4">
        <div className="h-8 w-32 bg-gray-200 rounded"></div>
        <div className="h-6 w-24 bg-gray-200 rounded"></div>
      </div>
      <div className="flex items-center space-x-2">
        <div className="h-8 w-8 bg-gray-200 rounded"></div>
        <div className="h-8 w-8 bg-gray-200 rounded"></div>
      </div>
    </div>
    
    {/* Messages skeleton */}
    <div className="flex-1 overflow-hidden p-4 space-y-4">
      {[...Array(5)].map((_, i) => (
        <div key={i} className={`flex ${i % 2 === 0 ? 'justify-start' : 'justify-end'}`}>
          <div className={`max-w-2xl p-3 rounded-lg ${i % 2 === 0 ? 'bg-gray-200' : 'bg-blue-200'}`}>
            <div className="h-3 bg-gray-300 rounded mb-2 w-20"></div>
            <div className="space-y-2">
              <div className="h-4 bg-gray-300 rounded"></div>
              <div className="h-4 bg-gray-300 rounded w-3/4"></div>
            </div>
            <div className="h-3 bg-gray-300 rounded mt-2 w-16"></div>
          </div>
        </div>
      ))}
    </div>
  </div>
);

export const PropertiesSkeleton: React.FC = () => (
  <div className="h-full flex flex-col animate-pulse">
    <div className="p-4 border-b">
      <div className="h-6 bg-gray-200 rounded w-32"></div>
    </div>
    <div className="flex-1 p-4 space-y-4">
      {[...Array(6)].map((_, i) => (
        <div key={i} className="space-y-2">
          <div className="h-4 bg-gray-200 rounded w-24"></div>
          <div className="h-8 bg-gray-200 rounded"></div>
        </div>
      ))}
    </div>
  </div>
);

export const ModalSkeleton: React.FC = () => (
  <div className="animate-pulse">
    <div className="space-y-6">
      <div className="h-6 bg-gray-200 rounded w-48"></div>
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="space-y-2">
            <div className="h-4 bg-gray-200 rounded w-20"></div>
            <div className="h-8 bg-gray-200 rounded"></div>
          </div>
        ))}
      </div>
      <div className="h-10 bg-gray-200 rounded"></div>
    </div>
  </div>
);

export const DiagramCanvasSkeleton: React.FC = () => (
  <div className="h-full bg-gray-50 animate-pulse flex items-center justify-center">
    <div className="text-center">
      <div className="h-12 w-12 bg-gray-200 rounded-full mx-auto mb-4"></div>
      <div className="h-4 bg-gray-200 rounded w-32 mx-auto mb-2"></div>
      <div className="h-3 bg-gray-200 rounded w-48 mx-auto"></div>
    </div>
  </div>
);

export const MemoryLayerSkeleton: React.FC = () => (
  <div className="absolute inset-0 bg-white/80 flex items-center justify-center animate-pulse">
    <div className="text-center">
      <div className="h-8 w-8 bg-gray-200 rounded-full mx-auto mb-3"></div>
      <div className="h-3 bg-gray-200 rounded w-24 mx-auto"></div>
    </div>
  </div>
);