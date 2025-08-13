import React from 'react';
import { Spinner } from './Button.spinner';
import { ButtonProps, ButtonOwnProps } from './Button.types';
import { baseClasses, sizeClasses, variantClasses, fullWidthClass, cx } from './Button.styles';

type ButtonForwardRef = <As extends React.ElementType = 'button'>(
  props: ButtonProps<As> & { ref?: React.Ref<any> }
) => JSX.Element;

function ButtonInner<As extends React.ElementType = 'button'>(
  props: ButtonProps<As>,
  ref: React.Ref<any>
) {
  const {
    as,
    children,
    ariaLabel,
    loading = false,
    disabled = false,
    fullWidth = false,
    variant = 'solid',
    size = 'md',
    leftIcon,
    rightIcon,
    className,
    onClick: onClickFromProps,
    ...rest
  } = props;

  const Element = (as ?? 'button') as React.ElementType;

  // When rendering non-button (e.g., <a>), emulate button semantics
  const isButtonElement = Element === 'button';

  // Merge classes from design system
  const computed = cx(
    baseClasses,
    sizeClasses[size],
    variantClasses[variant],
    fullWidth && fullWidthClass,
    (loading || disabled) && 'opacity-60 cursor-not-allowed',
    className
  );

  // Guarded click handler: do not propagate when loading/disabled
  const handleClick = (e: React.MouseEvent<any>) => {
    if (loading || disabled) {
      e.preventDefault();
      return;
    }
    onClickFromProps?.(e);
  };

  // Keyboard activation for non-button renderings (Enter/Space)
  const handleKeyDown = (e: React.KeyboardEvent<any>) => {
    if (loading || disabled) return;
    if (!isButtonElement && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      // Trigger user-provided onClick for non-button elements
      onClickFromProps?.(e as any);
    }
  };

  // Roll in aria-disabled for non-button controls
  const ariaDisabled = (disabled || loading) ? true : undefined;

  // Ensure focusability for non-button elements
  const accessibilityProps: any = isButtonElement
    ? {}
    : {
        role: 'button',
        'aria-disabled': ariaDisabled ?? undefined,
        tabIndex: 0,
      };

  // Pass through any intrinsic props from As element while preserving our props
  // We spread rest first to allow our aria-label to win if provided
  // and to avoid prop collisions with ButtonOwnProps
  return (
    <Element
      ref={ref}
      {...rest}
      {...accessibilityProps}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className={computed}
      aria-label={ariaLabel}
    >
      {/* Left icon shown only when not loading to avoid crowding with spinner */}
      {leftIcon && !loading && <span className="mr-2 -ml-0.5">{leftIcon}</span>}

      {/* Inline loading spinner when loading is true */}
      {loading && (
        <span className={leftIcon ? 'mr-2' : 'mr-0'}>
          <Spinner ariaLabel="Loading" />
        </span>
      )}

      {/* Button content/text */}
      {children}

      {/* Right icon shown only when not loading */}
      {rightIcon && !loading && <span className="ml-2">{rightIcon}</span>}
    </Element>
  );
}

// Generic wrapper to provide proper typing in consumer code
const Button = React.forwardRef(ButtonInner) as unknown as ButtonForwardRef;

// Export types for consumers
export type { ButtonProps, ButtonOwnProps };

// Default export
export default React.memo(Button);