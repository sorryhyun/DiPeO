import React from 'react';
import { FieldConfig } from './nodeConfig';

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

export interface GenericPropertiesPanelProps {
  nodeId: string;
  nodeType: string;
  fields: FieldConfig[];
  title: string;
  icon?: React.ReactNode;
  data?: Record<string, any>;
  onChange?: (nodeId: string, data: Record<string, any>) => void;
}