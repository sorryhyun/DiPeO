import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'outlined' | 'elevated' | 'filled';
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'xl' | 'full';
  shadow?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  clickable?: boolean;
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  onKeyDown?: (event: React.KeyboardEvent) => void;
  role?: string;
  'aria-label'?: string;
  'aria-labelledby'?: string;
  'aria-describedby'?: string;
  tabIndex?: number;
  [key: string]: any;
}

const Card = React.memo<CardProps>(({
  children,
  className = '',
  variant = 'default',
  padding = 'md',
  rounded = 'md',
  shadow = 'sm',
  clickable = false,
  disabled = false,
  loading = false,
  onClick,
  onKeyDown,
  role,
  tabIndex,
  ...props
}) => {
  // Base classes
  const baseClasses = 'transition-colors duration-200';

  // Variant classes
  const variantClasses = {
    default: 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700',
    outlined: 'bg-transparent border-2 border-gray-300 dark:border-gray-600',
    elevated: 'bg-white dark:bg-gray-800',
    filled: 'bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700',
  };

  // Padding classes
  const paddingClasses = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
    xl: 'p-8',
  };

  // Rounded classes
  const roundedClasses = {
    none: '',
    sm: 'rounded-sm',
    md: 'rounded-lg',
    lg: 'rounded-xl',
    xl: 'rounded-2xl',
    full: 'rounded-full',
  };

  // Shadow classes
  const shadowClasses = {
    none: '',
    sm: 'shadow-sm',
    md: 'shadow-md',
    lg: 'shadow-lg',
    xl: 'shadow-xl',
  };

  // Interactive classes
  const interactiveClasses = clickable && !disabled
    ? 'cursor-pointer hover:shadow-md hover:border-gray-300 dark:hover:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800'
    : '';

  // Disabled classes
  const disabledClasses = disabled
    ? 'opacity-50 cursor-not-allowed'
    : '';

  // Loading classes
  const loadingClasses = loading
    ? 'relative overflow-hidden'
    : '';

  // Combine all classes
  const cardClasses = [
    baseClasses,
    variantClasses[variant],
    paddingClasses[padding],
    roundedClasses[rounded],
    shadowClasses[shadow],
    interactiveClasses,
    disabledClasses,
    loadingClasses,
    className,
  ]
    .filter(Boolean)
    .join(' ');

  // Handle keyboard interactions for clickable cards
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (onKeyDown) {
      onKeyDown(event);
      return;
    }

    if (clickable && !disabled && onClick) {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        onClick();
      }
    }
  };

  // Handle click events
  const handleClick = () => {
    if (!disabled && !loading && onClick) {
      onClick();
    }
  };

  // Determine appropriate ARIA attributes
  const ariaAttributes = {
    role: role || (clickable ? 'button' : undefined),
    tabIndex: clickable && !disabled ? (tabIndex ?? 0) : tabIndex,
    'aria-disabled': disabled ? true : undefined,
    'aria-busy': loading ? true : undefined,
    ...props,
  };

  // Filter out undefined values from aria attributes
  const cleanAriaAttributes = Object.fromEntries(
    Object.entries(ariaAttributes).filter(([_, value]) => value !== undefined)
  );

  return (
    <div
      className={cardClasses}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      {...cleanAriaAttributes}
    >
      {loading && (
        <div className="absolute inset-0 bg-white/50 dark:bg-gray-800/50 flex items-center justify-center z-10">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500" />
        </div>
      )}
      {children}
    </div>
  );
});

Card.displayName = 'Card';

export default Card;
export type { CardProps };

// Named export for convenience
export { Card };