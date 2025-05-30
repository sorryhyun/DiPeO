import React from 'react';
import clsx from 'clsx';

interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {}

export const Label = React.forwardRef<HTMLLabelElement, LabelProps>(
  ({ className, ...props }, ref) => {
    return (
      <label
        ref={ref}
        className={clsx("block text-sm font-medium text-slate-700 mb-1", className)}
        {...props}
      />
    );
  }
);
Label.displayName = "Label";