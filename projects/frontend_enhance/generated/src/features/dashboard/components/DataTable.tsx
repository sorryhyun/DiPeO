import React, { useCallback, useMemo, useState } from 'react';
import { FixedSizeList as List } from 'react-window';

export interface Column<T> {
  key: keyof T;
  label: string;
  width?: number;
  sortable?: boolean;
  filterable?: boolean;
  render?: (value: T[keyof T], row: T) => React.ReactNode;
}

export interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  onSort?: (key: keyof T, direction: 'asc' | 'desc') => void;
  onFilter?: (filters: Record<keyof T, string>) => void;
  height?: number;
  rowHeight?: number;
  className?: string;
}

type SortConfig<T> = {
  key: keyof T;
  direction: 'asc' | 'desc';
} | null;

export function DataTable<T extends Record<string, any>>({
  columns,
  data,
  onSort,
  onFilter,
  height = 400,
  rowHeight = 48,
  className = '',
}: DataTableProps<T>) {
  const [sortConfig, setSortConfig] = useState<SortConfig<T>>(null);
  const [filters, setFilters] = useState<Record<keyof T, string>>({} as Record<keyof T, string>);

  const handleSort = useCallback((key: keyof T) => {
    let direction: 'asc' | 'desc' = 'asc';
    
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }

    const newSortConfig = { key, direction };
    setSortConfig(newSortConfig);
    onSort?.(key, direction);
  }, [sortConfig, onSort]);

  const handleFilter = useCallback((key: keyof T, value: string) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilter?.(newFilters);
  }, [filters, onFilter]);

  const filteredData = useMemo(() => {
    let result = data;

    // Apply filters
    Object.entries(filters).forEach(([key, value]) => {
      if (value) {
        result = result.filter(row => {
          const cellValue = row[key];
          return String(cellValue).toLowerCase().includes(value.toLowerCase());
        });
      }
    });

    // Apply sorting
    if (sortConfig) {
      result = [...result].sort((a, b) => {
        const aValue = a[sortConfig.key];
        const bValue = b[sortConfig.key];

        if (aValue < bValue) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (aValue > bValue) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }

    return result;
  }, [data, filters, sortConfig]);

  const getSortIcon = (key: keyof T) => {
    if (!sortConfig || sortConfig.key !== key) {
      return '↕️';
    }
    return sortConfig.direction === 'asc' ? '↑' : '↓';
  };

  const getSortAriaSort = (key: keyof T): 'ascending' | 'descending' | 'none' => {
    if (!sortConfig || sortConfig.key !== key) {
      return 'none';
    }
    return sortConfig.direction === 'asc' ? 'ascending' : 'descending';
  };

  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const row = filteredData[index];
    
    return (
      <div
        style={style}
        className="flex border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800"
        role="row"
        aria-rowindex={index + 2} // +2 because header is row 1, data starts at row 2
      >
        {columns.map((column, columnIndex) => {
          const value = row[column.key];
          const displayValue = column.render ? column.render(value, row) : String(value);

          return (
            <div
              key={String(column.key)}
              className="flex items-center px-4 py-2 text-sm text-gray-900 dark:text-gray-100"
              style={{ width: column.width || `${100 / columns.length}%` }}
              role="gridcell"
              aria-describedby={`column-${columnIndex}-header`}
            >
              {displayValue}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className={`border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden ${className}`}>
      {/* Table Header */}
      <div className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex" role="row" aria-rowindex={1}>
          {columns.map((column, index) => (
            <div
              key={String(column.key)}
              className="flex flex-col px-4 py-3"
              style={{ width: column.width || `${100 / columns.length}%` }}
              role="columnheader"
              id={`column-${index}-header`}
              aria-sort={column.sortable ? getSortAriaSort(column.key) : undefined}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  {column.label}
                </span>
                {column.sortable && (
                  <button
                    onClick={() => handleSort(column.key)}
                    className="ml-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 rounded"
                    aria-label={`Sort by ${column.label}`}
                  >
                    <span aria-hidden="true">{getSortIcon(column.key)}</span>
                  </button>
                )}
              </div>
              
              {column.filterable && (
                <input
                  type="text"
                  placeholder={`Filter ${column.label.toLowerCase()}...`}
                  value={filters[column.key] || ''}
                  onChange={(e) => handleFilter(column.key, e.target.value)}
                  className="mt-2 block w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  aria-label={`Filter by ${column.label}`}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Virtualized Table Body */}
      <div
        role="grid"
        aria-label="Data table"
        aria-rowcount={filteredData.length + 1} // +1 for header
        aria-colcount={columns.length}
      >
        {filteredData.length === 0 ? (
          <div className="flex items-center justify-center py-12 text-gray-500 dark:text-gray-400">
            <p>No data available</p>
          </div>
        ) : (
          <List
            height={height}
            itemCount={filteredData.length}
            itemSize={rowHeight}
            width="100%"
          >
            {Row}
          </List>
        )}
      </div>

      {/* Screen reader summary */}
      <div className="sr-only" aria-live="polite">
        Showing {filteredData.length} of {data.length} rows
        {sortConfig && ` sorted by ${String(sortConfig.key)} ${sortConfig.direction}ending`}
      </div>
    </div>
  );
}

export default DataTable;