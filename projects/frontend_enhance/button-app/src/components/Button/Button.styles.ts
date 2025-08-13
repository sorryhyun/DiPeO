import clsx from 'clsx';

type Variants = 'solid' | 'outline' | 'ghost' | 'link';
type Sizes = 'xs' | 'sm' | 'md' | 'lg';

export const variantClasses: Record<Variants, string> = {
  solid:
    'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 disabled:bg-blue-500',
  outline:
    'border border-blue-600 text-blue-600 bg-transparent hover:bg-blue-50 focus:ring-blue-500 disabled:bg-blue-50',
  ghost:
    'bg-transparent text-blue-600 hover:bg-blue-50 focus:ring-blue-500 disabled:bg-blue-50',
  link:
    'bg-transparent text-blue-600 underline-offset-2 hover:underline focus:ring-0',
};

export const sizeClasses: Record<Sizes, string> = {
  xs: 'px-2 py-1 text-xs',
  sm: 'px-3 py-2 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-4 py-3 text-base',
};

// base button styling
export const baseClasses =
  'inline-flex items-center justify-center rounded-md font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-2';

export const fullWidthClass = 'w-full';

// utility for combining classes
export function cx(...classes: (string | false | null | undefined)[]) {
  return clsx(classes);
}