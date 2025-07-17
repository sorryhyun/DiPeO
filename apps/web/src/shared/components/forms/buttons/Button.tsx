import React from 'react';
import clsx from 'clsx';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'secondary' | 'destructive' | 'outline' | 'ghost' | 'link' | 'gradient';
  size?: 'default' | 'sm' | 'lg' | 'xl' | 'icon';
  loading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', loading = false, disabled, children, ...props }, ref) => {
    const baseStyles = `
      inline-flex items-center justify-center gap-2
      font-medium transition-all duration-200
      focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2
      disabled:cursor-not-allowed disabled:opacity-50
      ring-offset-background
      relative overflow-hidden
    `;
    
    const variants = {
      default: `
        bg-neutral-900 text-white 
        hover:bg-neutral-800 hover:shadow-md
        active:scale-[0.98]
      `,
      primary: `
        bg-primary-600 text-white 
        hover:bg-primary-700 hover:shadow-md hover:shadow-primary-500/25
        active:scale-[0.98]
      `,
      secondary: `
        bg-accent-600 text-white 
        hover:bg-accent-700 hover:shadow-md hover:shadow-accent-500/25
        active:scale-[0.98]
      `,
      destructive: `
        bg-danger-600 text-white 
        hover:bg-danger-700 hover:shadow-md hover:shadow-danger-500/25
        active:scale-[0.98]
      `,
      outline: `
        border-2 border-border bg-transparent
        hover:bg-neutral-50 hover:border-neutral-300 hover:shadow-sm
        active:scale-[0.98]
      `,
      ghost: `
        bg-transparent
        hover:bg-neutral-100 hover:text-neutral-900
        active:bg-neutral-200
      `,
      link: `
        bg-transparent underline-offset-4 
        hover:underline hover:text-primary-600
        px-0 h-auto
      `,
      gradient: `
        bg-gradient-to-r from-primary-600 to-accent-600 text-white
        hover:shadow-lg hover:shadow-primary-500/25
        hover:from-primary-700 hover:to-accent-700
        active:scale-[0.98]
        before:absolute before:inset-0
        before:bg-gradient-to-r before:from-white/0 before:via-white/20 before:to-white/0
        before:translate-x-[-200%] hover:before:translate-x-[200%]
        before:transition-transform before:duration-700
      `,
    };
    
    const sizes = {
      default: "h-10 px-4 py-2 text-sm rounded-lg",
      sm: "h-8 px-3 py-1.5 text-xs rounded-md",
      lg: "h-12 px-6 py-3 text-base rounded-lg",
      xl: "h-14 px-8 py-4 text-lg rounded-xl",
      icon: "h-10 w-10 p-0 rounded-lg",
    };
    
    const iconSizes = {
      default: "h-4 w-4",
      sm: "h-3 w-3",
      lg: "h-5 w-5",
      xl: "h-6 w-6",
      icon: "h-5 w-5",
    };
    
    return (
      <button
        className={clsx(
          baseStyles,
          variants[variant],
          sizes[size],
          loading && "cursor-wait",
          className
        )}
        disabled={disabled || loading}
        ref={ref}
        {...props}
      >
        {loading && (
          <svg
            className={clsx("animate-spin", iconSizes[size])}
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";