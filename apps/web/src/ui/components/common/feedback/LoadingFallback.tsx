import React from 'react';
import Spinner from './Spinner';

export const LoadingFallback: React.FC = () => (
  <div className="flex justify-center p-4">
    <Spinner />
  </div>
);

export default LoadingFallback;
