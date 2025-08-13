import type React from 'react';

export type ButtonOwnProps<As extends React.ElementType = 'button'> = {
  as?: As;
  children?: React.ReactNode;
  ariaLabel?: string;
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  variant?: 'solid' | 'outline' | 'ghost' | 'link';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  className?: string;
  // Optional click handler; actual onClick may come from As props, so we forward/compose carefully
  onClick?: React.MouseEventHandler<any>;
};

export type ButtonProps<As extends React.ElementType> = ButtonOwnProps<As> &
  Omit<React.ComponentPropsWithoutRef<As>, keyof ButtonOwnProps<As> | 'as'>;