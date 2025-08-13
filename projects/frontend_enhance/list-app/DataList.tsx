"use client";

import React, {
  createElement,
  Fragment,
  ReactNode,
  ReactElement,
  useCallback,
  useEffect,
  useMemo,
  useReducer,
  useRef,
  useState,
  Suspense,
  memo,
} from "react";

// Lightweight logger utility (to be extended as needed)
export const logEvent = (event: string, payload?: any) => {
  if (typeof console !== "undefined") {
    console.info(`[DataList] ${event}`, payload ?? "");
  }
};

// Tokens and minimal design-system integration (Tailwind-first)
export type Dir = "ltr" | "rtl";

export interface DataListProps<T> {
  items: T[]; // optional when using a fetcher; ignored if fetcher provided and data comes from fetcher
  renderItem: (item: T, index: number) => ReactNode;
  itemKey?: (item: T) => string;
  pageSize?: number;
  fetcher?: (params: { page: number; pageSize: number }) => Promise<T[]>;
  loadingPolicy?: "eager" | "lazy";
  onLoadMore?: () => void;
  ariaLabel?: string;
  className?: string;
  dir?: Dir;
}

// Internal: reducer for data-loading lifecycle (idle | loading | loaded | empty | error)
type LoadingState = "idle" | "loading" | "loaded" | "empty" | "error";

type Action<T> =
  | { type: "FETCH" }
  | { type: "FETCH_SUCCESS"; payload: T[] }
  | { type: "FETCH_ERROR"; error: string }
  | { type: "RESET" };

type DataState<T> = {
  status: LoadingState;
  data: T[];
  error?: string;
  page: number;
};

function dataListReducer<T extends { id: string }>(
  state: DataState<T>,
  action: Action<T>
): DataState<T> {
  switch (action.type) {
    case "FETCH":
      return { ...state, status: "loading" };
    case "FETCH_SUCCESS": {
      // If loading page 1, replace; else append
      const isFirstPage = state.page <= 1;
      const newData = isFirstPage ? action.payload : [...state.data, ...action.payload];
      const newStatus = action.payload.length === 0 && newData.length === 0 ? "empty" : "loaded";
      return { ...state, status: newStatus, data: newData, error: undefined, page: state.page };
    }
    case "FETCH_ERROR":
      return { ...state, status: "error", error: action.error };
    case "RESET":
      return { status: "idle", data: [], error: undefined, page: 1 };
    default:
      return state;
  }
}

// Small debounced value hook (shared utility)
export function useDebouncedValue<T>(value: T, delay = 250): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return v;
}

// DataList main component (safe TSX generic pattern)
function DataList<T extends { id: string }>(props: DataListProps<T>): JSX.Element {
  const {
    items,
    renderItem,
    itemKey,
    pageSize = 20,
    fetcher,
    loadingPolicy = "eager",
    onLoadMore,
    ariaLabel,
    className,
    dir: dirProp,
  } = props;

  // Direction (RTL/LTR) handling (SSR-safe: only rely on document on client)
  const [direction, setDirection] = useState<Dir>("ltr");
  useEffect(() => {
    if (typeof document !== "undefined") {
      const d = (document.dir === "rtl" ? "rtl" : "ltr") as Dir;
      setDirection(d);
    }
  }, []);

  // Public direction override
  const dir = dirProp ?? direction;

  // Data management: controlled vs uncontrolled
  // Uncontrolled path: use internal data state when fetcher is provided or data is not fully controlled
  const initialState: DataState<T> = useMemo(
    () => ({
      status: fetcher ? "idle" : (items?.length ?? 0) > 0 ? "loaded" : "empty",
      data: [],
      error: undefined,
      page: 1,
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [fetcher]
  );

  const [state, dispatch] = useReducer(dataListReducer as any, initialState);

  // Load data via fetcher when provided
  useEffect(() => {
    if (!fetcher) return;
    // Reset and fetch page 1 on initial mount or fetcher prop changes
    dispatch({ type: "RESET" });
    fetchPage(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetcher]);

  // Initialize with provided items if fetcher is not used
  useEffect(() => {
    if (fetcher) return;
    // When items change, reflect into internal state for consistency
    const newData = items ?? [];
    if (newData.length === 0) {
      dispatch({ type: "FETCH_SUCCESS", payload: [] as unknown as T[] });
      // mark as empty
      // @ts-ignore
      dispatch({ type: "FETCH_SUCCESS", payload: [] });
    } else {
      // Replace internal data
      // @ts-ignore
      dispatch({ type: "FETCH_SUCCESS", payload: newData });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items, fetcher]);

  const fetchPage = useCallback(
    async (page: number) => {
      if (!fetcher) return;
      dispatch({ type: "FETCH" });
      try {
        const data = await fetcher({ page, pageSize });
        // Normalize payload typing
        dispatch({ type: "FETCH_SUCCESS", payload: data as T[] });
        // Log analytics
        logEvent("fetch_page", { page, pageSize, itemCount: data.length });
        if (data.length === 0) {
          // end reached, mark as loaded with no more
          dispatch({ type: "FETCH_SUCCESS", payload: [] });
        }
      } catch (err) {
        dispatch({ type: "FETCH_ERROR", error: (err as Error).message ?? "Fetch error" });
        logEvent("fetch_error", { page, pageSize, error: (err as Error).message });
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [fetcher, pageSize]
  );

  // Helper to load more
  const handleLoadMore = useCallback(() => {
    if (!fetcher) {
      // No-op if no fetcher
      return;
    }
    const nextPage = state.page + 1;
    dispatch({ type: "FETCH" });
    fetcher({ page: nextPage, pageSize })
      .then((data) => {
        const itemsArr = data as T[];
        dispatch({ type: "FETCH_SUCCESS", payload: itemsArr });
        // Update page in state immutably via re-dispatch path
        // Also log
        logEvent("load_more_success", { page: nextPage, count: itemsArr.length });
      })
      .catch((err) => {
        dispatch({ type: "FETCH_ERROR", error: (err as Error).message ?? "Load more error" });
        logEvent("load_more_error", { page: nextPage, error: (err as Error).message });
      });
    onLoadMore?.();
  }, [fetcher, pageSize, onLoadMore, state.page]);

  // Data source for rendering
  const dataSource: T[] = fetcher ? state.data : (items ?? []);

  // If no data and not fetching, render Empty
  const isEmpty = !fetcher && (!items || items.length === 0) || (fetcher && state.status === "empty");
  const isLoading = (fetcher && state.status === "loading") || (!fetcher && props.loadingPolicy === "eager" && !dataSource.length);

  // Virtualization (basic: fixed itemHeight, simple windowing)
  const itemHeight = props as any).itemHeight ?? 48; // allow pass-through if desired (not in API—just for internal)
  // We'll support a runtime prop if set via data-attribute or extra prop if needed
  // Since not in API, use a sensible default
  const effectiveItemHeight = 48; // px

  // SSR-safe container measurement
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const [viewportHeight, setViewportHeight] = useState<number>(320);
  const [scrollTop, setScrollTop] = useState<number>(0);

  // Measure height with ResizeObserver; guard SSR
  useEffect(() => {
    if (typeof window === "undefined") return;
    const el = viewportRef.current;
    if (!el) return;
    const measure = () => {
      setViewportHeight(el.clientHeight || 320);
    };
    measure();
    let ro: ResizeObserver | null = null;
    if (typeof ResizeObserver !== "undefined") {
      ro = new ResizeObserver(() => measure());
      ro.observe(el);
    } else {
      window.addEventListener("resize", measure);
    }
    return () => {
      if (ro) ro.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, []);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  };

  const totalCount = dataSource.length;
  const overscan = 2;
  const startIndex = Math.max(0, Math.floor(scrollTop / effectiveItemHeight) - overscan);
  const endIndex = Math.min(totalCount, Math.ceil((scrollTop + viewportHeight) / effectiveItemHeight) + overscan);
  const visibleItems = dataSource.slice(startIndex, endIndex);

  // Accessible helper
  const listRoleProps = {
    role: "list" as const,
    "aria-label": ariaLabel,
  };

  // Optional Loading / Empty components (lazy-loaded demo)
  const Empty = DataList.Empty as unknown as React.ComponentType<{ message?: string }>;
  const Loading = DataList.Loading as unknown as React.ComponentType;

  // Subcomponent rendering (lazy-ish pattern using Suspense)
  const Body = DataList.Body as unknown as React.ComponentType<{ items: typeof dataSource; renderItem: (item: any, index: number) => ReactNode; itemHeight?: number; startIndex: number; endIndex: number; onRender?: (idx: number) => void }>;

  // SSR guard: avoid accessing window on server
  const isClient = typeof window !== "undefined";

  // Render
  return (
    <DataListContainer
      className={className}
      dir={dir}
      ariaLabel={ariaLabel}
    >
      {/*
        Example: You can add a header/search zone here if required.
      */}
      <DataListHeader>Data List</DataListHeader>

      <div ref={viewportRef} onScroll={handleScroll} className="relative w-full" style={{ height: viewportHeight, overflowY: "auto" }} aria-label={ariaLabel || "Data list viewport"} role="group" dir={dir}>
        {isEmpty && (
          <Suspense fallback={<div/>}>
            <Empty message="No items to display." />
          </Suspense>
        )}
        {!isEmpty && totalCount > 0 && (
          <div style={{ position: "relative", height: totalCount * effectiveItemHeight }}>
            {visibleItems.map((item, idx) => {
              const globalIndex = startIndex + idx;
              const key = itemKey ? itemKey(item) : (item as any).id ?? String(globalIndex);
              return (
                <div
                  key={key}
                  role="listitem"
                  aria-label={`Item ${globalIndex + 1}`}
                  style={{
                    position: "absolute",
                    top: globalIndex * effectiveItemHeight,
                    height: effectiveItemHeight,
                    left: 0,
                    right: 0,
                    display: "flex",
                    alignItems: "center",
                    padding: "0 8px",
                  }}
                >
                  {renderItem(item, globalIndex)}
                </div>
              );
            })}
            {isLoading && (
              <div
                aria-live="polite"
                style={{
                  position: "absolute",
                  bottom: 8,
                  left: 0,
                  right: 0,
                  textAlign: "center",
                  fontSize: 12,
                  color: "var(--ts-text-muted, #6b7280)",
                }}
              >
                Loading...
              </div>
            )}
          </div>
        )}
      </div>

      {fetcher && (
        <div className="flex justify-center items-center py-2">
          <button
            type="button"
            className="px-3 py-1 rounded border border-gray-300 bg-white text-sm hover:bg-gray-50"
            onClick={handleLoadMore}
            aria-label="Load more items"
          >
            Load more
          </button>
        </div>
      )}
    </DataListContainer>
  );
}

// Lightweight skeleton-like subcomponents (compound API)
type DataListContainerProps = {
  children?: ReactNode;
  className?: string;
  ariaLabel?: string;
  dir?: Dir;
};
const DataListContainer: React.FC<DataListContainerProps> = memo(({ children, className, ariaLabel, dir }) => {
  // Tailwind-friendly container
  return (
    <div className={className} dir={dir} aria-label={ariaLabel} role="group" style={{ display: "block" }}>
      {children}
    </div>
  );
});

const DataListHeader: React.FC<{ children?: ReactNode }> = memo(({ children }) => {
  return (
    <div className="mb-2 flex items-center justify-between" aria-label="Data list header" role="region">
      <div className="text-sm font-semibold text-gray-700">{children}</div>
    </div>
  );
});

// Exposed API for DataList.Body: a minimal lazy wrapper to illustrate code-splitting pattern
const DataListBodyModule = {
  default: function DataListBody<T extends { id: string }>(props: {
    items: T[];
    renderItem: (item: T, index: number) => ReactNode;
    itemHeight?: number;
    startIndex: number;
    endIndex: number;
  }) {
    const { items, renderItem, startIndex, endIndex } = props as any;
    // Render windowed slice
    const slice = items.slice(startIndex, endIndex);
    return (
      <>
        {slice.map((it, i) => (
          <div key={(it as any).id ?? i} role="listitem" style={{ height: props.itemHeight ?? 48 }}>
            {renderItem(it, startIndex + i)}
          </div>
        ))}
      </>
    );
  },
} as const;

const LazyDataListBodyModule = React.lazy(async () => Promise.resolve(DataListBodyModule as any));

const DataListBody: React.FC<{
  items: any[];
  renderItem: (item: any, index: number) => ReactNode;
  itemHeight?: number;
  startIndex: number;
  endIndex: number;
}> = (props) => {
  return (
    <Suspense fallback={null}>
      <LazyDataListBodyModule
        items={props.items}
        renderItem={props.renderItem}
        itemHeight={props.itemHeight}
        startIndex={props.startIndex}
        endIndex={props.endIndex}
      />
    </Suspense>
  );
};

type DataListItemProps<T> = {
  item: T;
  index: number;
  renderItem?: (item: T, index: number) => ReactNode;
  className?: string;
  onClick?: () => void;
};

const DataListItem = memo(function DataListItem<T extends { id: string }>(props: DataListItemProps<T>) {
  const { item, index, renderItem, className, onClick } = props;
  const content = renderItem ? renderItem(item, index) : <span>{String((item as any).title ?? item.id)}</span>;
  return (
    <div
      role="listitem"
      aria-label={`Item ${index + 1}`}
      onClick={onClick}
      className={className}
      style={{ display: "flex", alignItems: "center" }}
    >
      {content}
    </div>
  );
});

const DataListEmpty: React.FC<{ message?: string }> = memo(({ message }) => {
  return (
    <div role="status" aria-label="No items" className="p-4 text-sm text-gray-500">
      {message ?? "No items"}
    </div>
  );
});

const DataListLoading: React.FC = memo(() => {
  return (
    <div className="p-4 text-sm text-gray-500" aria-live="polite">
      Loading...
    </div>
  );
};

// Attach subcomponents to DataList export (compound API)
(DataList as any).Container = DataListContainer;
(DataList as any).Header = DataListHeader;
(DataList as any).Body = DataListBody;
(DataList as any).Item = DataListItem;
(DataList as any).Empty = DataListEmpty;
(DataList as any).Loading = DataListLoading;

export { DataList };
export type { DataListProps };

// Default export (named): DataList is a function; consumers will use named import { DataList }
export default DataList;