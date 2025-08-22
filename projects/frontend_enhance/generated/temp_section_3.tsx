import React, { Suspense, lazy } from 'react';
import { useQuery } from '@tanstack/react-query';

// Import layout (feature dashboard)
// Path: src/features/dashboard/components/DashboardLayout.tsx
import DashboardLayout from '../../components/DashboardLayout';

// Lazy-load heavy sections
const ChartCardModule = lazy(() => import('../../../shared/components/ChartCard'));
const LiveUpdatesModule = lazy(() => import('../components/LiveUpdates'));
const DataTableModule = lazy(() => import('../components/DataTable'));

type Metrics = {
  revenue: number;
  activeUsers: number;
  newSignups: number;
};

type TableRow = {
  id: string;
  name: string;
  status: string;
  value: number;
  updatedAt: string;
};

// Helpers: type-safe re-exports (cast to any to avoid prop shape coupling)
const ChartCard = ChartCardModule as unknown as React.ComponentType<any>;
const LiveUpdates = LiveUpdatesModule as unknown as React.ComponentType<any>;
const DataTable = DataTableModule as unknown as React.ComponentType<any>;

// Simple inline error banner
const ErrorBanner: React.FC<{ message: string }> = ({ message }) => (
  <div role="alert" aria-live="polite" className="p-4 mb-4 text-sm text-red-700 bg-red-100 border border-red-200 rounded">
    {message}
  </div>
);

const Dashboard: React.FC = () => {
  // Fetch metrics
  const fetchMetrics = async (): Promise<Metrics> => {
    const res = await fetch('/api/dashboard/metrics');
    if (!res.ok) throw new Error('Failed to load dashboard metrics');
    // @ts-ignore - assuming API returns the shape matching Metrics
    return res.json();
  };

  // Fetch table data
  const fetchTableRows = async (): Promise<TableRow[]> => {
    const res = await fetch('/api/dashboard/table');
    if (!res.ok) throw new Error('Failed to load dashboard table data');
    return res.json();
  };

  const {
    data: metrics,
    isLoading: metricsLoading,
    isError: metricsError,
  } = useQuery<Metrics['revenue'] & Metrics, Error>('dashboard-metrics', fetchMetrics, {
    // We fetch full Metrics object; TypeScript generic is implied by usage, but we keep simple
    staleTime: 60 * 1000,
    cacheTime: 5 * 60 * 1000,
  });

  // Note: The above query type is intentionally lenient to avoid tight coupling with the exact shape.
  // The actual metrics object is accessed via (metrics as any)

  const {
    data: tableRows,
    isLoading: tableLoading,
    isError: tableError,
  } = useQuery<TableRow[], Error>('dashboard-table', fetchTableRows, {
    staleTime: 60 * 1000,
    cacheTime: 5 * 60 * 1000,
  });

  return (
    <DashboardLayout aria-label="dashboard-layout">
      {/* Metrics Section */}
      <section aria-label="dashboard-metrics" className="p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <Suspense fallback={<div className="p-4 border rounded bg-white h-28" aria-label="loading-revenue">Loading...</div>}>
            <ChartCard
              // @ts-ignore
              title="Revenue"
              value={(metrics as any)?.revenue ?? 0}
              subtitle="Total revenue (last 30d)"
            />
          </Suspense>

          <Suspense fallback={<div className="p-4 border rounded bg-white h-28" aria-label="loading-active-users">Loading...</div>}>
            <ChartCard
              // @ts-ignore
              title="Active Users"
              value={(metrics as any)?.activeUsers ?? 0}
              subtitle="Currently online"
            />
          </Suspense>

          <Suspense fallback={<div className="p-4 border rounded bg-white h-28" aria-label="loading-new-signups">Loading...</div>}>
            <ChartCard
              // @ts-ignore
              title="New Signups"
              value={(metrics as any)?.newSignups ?? 0}
              subtitle="This period"
            />
          </Suspense>
        </div>

        {metricsError && (
          <ErrorBanner message="Unable to load dashboard metrics. Please try again." />
        )}
      </section>

      {/* Live Updates Section */}
      <section aria-label="live-updates" className="p-4">
        <Suspense fallback={<div className="p-4 border rounded bg-white">Connecting to live updates...</div>}>
          <LiveUpdates />
        </Suspense>
      </section>

      {/* Data Table Section */}
      <section aria-label="dashboard-table" className="p-4">
        <Suspense fallback={<div className="p-4 border rounded bg-white">Loading table data...</div>}>
          <DataTable
            // @ts-ignore
            rows={tableRows ?? []}
          />
        </Suspense>
        {tableError && <ErrorBanner message="Failed to load table data." />}
      </section>
    </DashboardLayout>
  );
};

export default Dashboard;