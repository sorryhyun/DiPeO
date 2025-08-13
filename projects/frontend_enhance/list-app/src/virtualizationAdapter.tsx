// src/virtualizationAdapter.ts
import React, { CSSProperties, useMemo } from "react";

export type VirtualListProps<T> = {
  items: T[];
  height: number;
  itemHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  itemKey?: (item: T) => string;
  overscan?: number;
};

export function VirtualList<T>({
  items,
  height,
  itemHeight,
  renderItem,
  itemKey,
  overscan = 2,
}: VirtualListProps<T>): JSX.Element {
  const totalHeight = items.length * itemHeight;
  const [scrollTop, setScrollTop] = React.useState(0);

  const onScroll = (e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop((e.target as HTMLDivElement).scrollTop);
  };

  // Compute visible window
  const startIndex = Math.max(
    0,
    Math.floor(scrollTop / itemHeight) - overscan
  );
  const visibleCount = Math.ceil(height / itemHeight) + overscan * 2;
  const endIndex = Math.min(items.length, startIndex + visibleCount);

  const containerStyle: CSSProperties = {
    height,
    overflow: "auto",
    width: "100%",
  };

  const innerStyle: CSSProperties = {
    position: "relative",
    height: totalHeight,
    width: "100%",
  };

  const renderSlot = (idx: number) => {
    const item = items[idx];
    const top = idx * itemHeight;
    const key = itemKey ? itemKey(item) : `vh-${idx}`;

    return (
      <div
        key={key}
        style={{
          position: "absolute",
          top,
          height: itemHeight,
          left: 0,
          right: 0,
          width: "100%",
          display: "block",
        }}
        role="listitem"
        aria-label={`Item ${idx + 1}`}
      >
        {renderItem(item, idx)}
      </div>
    );
  };

  return (
    <div style={containerStyle} onScroll={onScroll} role="list" aria-label="Data list">
      <div style={innerStyle}>
        {Array.from({ length: endIndex - startIndex }).map((_, i) =>
          renderSlot(startIndex + i)
        )}
      </div>
    </div>
  );
}