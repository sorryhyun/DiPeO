import React from 'react';
import { SPACE_Y_4 } from '../styles.constants';

/**
 * Layout components for property panels
 * Field components have been moved to UnifiedFormField
 */

export const Form: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <form className="space-y-3">{children}</form>
);

// Horizontal form row for inline fields
export const FormRow: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = "flex flex-wrap gap-3" }) => (
  <div className={className}>{children}</div>
);

// Layout Components
interface TwoColumnLayoutProps {
  leftColumn: React.ReactNode;
  rightColumn: React.ReactNode;
}

export const TwoColumnPanelLayout: React.FC<TwoColumnLayoutProps> = ({
  leftColumn,
  rightColumn
}) => (
  <div className="grid grid-cols-2 gap-4">
    <div className={SPACE_Y_4}>{leftColumn}</div>
    <div className={SPACE_Y_4}>{rightColumn}</div>
  </div>
);

export const SingleColumnPanelLayout: React.FC<{ children: React.ReactNode }> = ({
  children
}) => (
  <div className={SPACE_Y_4}>{children}</div>
);
