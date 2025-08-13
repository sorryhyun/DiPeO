import React from 'react';

export const Spinner: React.FC<{ ariaLabel?: string }> = ({
  ariaLabel = 'Loading',
}) => {
  // Small circular spinner; aria-label ensures testability
  return (
    <span
      role="status"
      aria-label={ariaLabel}
      className="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"
    />
  );
};

export default Spinner;