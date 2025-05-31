import React from 'react';

export interface FormFieldProps {
  label: string;
  id?: string;
  children: React.ReactNode;
  className?: string;
}

export interface PanelProps {
  icon?: React.ReactNode;
  title: string;
  children: React.ReactNode;
}

