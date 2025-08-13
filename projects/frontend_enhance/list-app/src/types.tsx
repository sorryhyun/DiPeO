// src/types.ts
"use client";

export interface DataItemShape {
  id: string;
  // Optional emoji/label-friendly fields for UI, but totally optional
  label?: string;
  title?: string;
  // Additional arbitrary fields are allowed by index signature for generic item shapes
  [key: string]: any;
}

export interface DataListFetchParams {
  page: number;
  pageSize: number;
  query?: string;
  [key: string]: any;
}

export interface DataListProps<T extends DataItemShape> {
  // Optional initial data (uncontrolled usage if fetcher is absent)
  items?: T[];

  // Optional paginated data loader
  fetcher?: (params: DataListFetchParams) => Promise<T[]>;

  // Required render callback for each item
  renderItem: (item: T, index: number) => React.ReactNode;

  // Optional, but strongly preferred for stable keys
  itemKey?: (item: T) => string;

  // Pagination and initial page sizing
  initialPage?: number;
  pageSize?: number;

  // Error callback
  onError?: (err: Error) => void;

  // Accessibility and i18n
  ariaLabel?: string;
  localeAware?: boolean;

  // Virtualization
  virtualized?: boolean;
  height?: number | string; // for virtualization viewport
  itemHeight?: number; // fixed item height (default 48)
  itemHeightFn?: (index: number) => number; // optional dynamic height
  overscan?: number;

  // Keyboard navigation
  enableKeyboardNavigation?: boolean;

  // UI/UX toggles
  showLoadingIndicator?: boolean;
  showEmptyState?: boolean;

  // SSR readiness marker for React Server Components
  enableServerComponentsReadiness?: boolean;
}