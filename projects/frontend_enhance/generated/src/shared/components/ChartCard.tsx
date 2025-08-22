import React from 'react';

interface ChartCardProps {
  title: string;
  subtitle?: string;
  loading?: boolean;
  children?: React.ReactNode;
  className?: string;
  'aria-label'?: string;
  [key: string]: any;
}

const ChartCard = React.memo<ChartCardProps>(({
  title,
  subtitle,
  loading = false,
  children,
  className = '',
  'aria-label': ariaLabel,
  ...props
}) => {
  const containerClassName = `
    bg-white dark:bg-gray-800 
    rounded-lg shadow-sm border border-gray-200 dark:border-gray-700
    p-6 transition-colors duration-200
    ${className}
  `.trim();

  return (
    <div
      className={containerClassName}
      role="region"
      aria-label={ariaLabel || `${title} chart`}
      {...props}
    >
      {/* Header */}
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {title}
        </h3>
        {subtitle && (
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {subtitle}
          </p>
        )}
      </div>

      {/* Content Area */}
      <div className="relative min-h-[200px]">
        {loading ? (
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
            <div className="space-y-3">
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
            </div>
            <div className="mt-6 grid grid-cols-4 gap-4">
              <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
              <div className="h-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
              <div className="h-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
              <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded"></div>
            </div>
          </div>
        ) : (
          <div className="w-full h-full">
            {children}
          </div>
        )}
      </div>
    </div>
  );
});

ChartCard.displayName = 'ChartCard';

export default ChartCard;
export type { ChartCardProps };

// Named export for convenience
export { ChartCard };