// src/components/VirtualizedList/VirtualizedList.types.ts
export type BaseItem = { id: string; [key: string]: any };

export interface FetchResult<T extends BaseItem> {
  items: T[];
  total: number;
}

export interface VirtualizedListProps<T extends BaseItem> {
  fetcher: (offset: number, limit: number) => Promise<FetchResult<T>>;
  renderItem: (item: T, index: number) => React.ReactNode;
  itemHeight?: number; // px
  initialPageSize?: number;
  ariaLabel?: string;
  className?: string;
}

export interface VirtualizedListContextValue<T extends BaseItem> {
  selectedId: string | null;
  select: (id: string) => void;
}