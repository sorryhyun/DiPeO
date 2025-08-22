import React, { Suspense, lazy } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import DashboardLayout from '../components/DashboardLayout';
import LiveUpdates from '../components/LiveUpdates';
import DataTable from '../components/DataTable';
import { ChartCard } from '../../../shared/components/ChartCard';
import { Card } from '../../../shared/components/Card';
import { api } from '../../../shared/utils/api';
import { logger } from '../../../shared/utils/logger';

// Lazy load heavy chart components for better performance
const MetricsChart = lazy(() => import('../components/MetricsChart'));
const TrendChart = lazy(() => import('../components/TrendChart'));
const PerformanceChart = lazy(() => import('../components/PerformanceChart'));

interface DashboardMetrics {
  totalUsers: number;
  activeUsers: number;
  revenue: number;
  growth: number;
}

interface DashboardData {
  id: string;
  name: string;
  status: 'active' | 'inactive' | 'pending';
  value: number;
  lastUpdated: string;
}

interface ChartData {
  name: string;
  value: number;
  timestamp: string;
}

const Dashboard: React.FC = () => {
  const { t } = useTranslation();

  // Fetch dashboard metrics
  const {
    data: metrics,
    isLoading: metricsLoading,
    error: metricsError,
  } = useQuery<DashboardMetrics>({
    queryKey: ['dashboard-metrics'],
    queryFn: () => api.get('/api/dashboard/metrics'),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 30 * 1000, // 30 seconds
  });

  // Log metrics error if it occurs
  React.useEffect(() => {
    if (metricsError) {
      logger.error('Failed to fetch dashboard metrics', metricsError);
    }
  }, [metricsError]);

  // Fetch dashboard table data
  const {
    data: tableData,
    isLoading: tableLoading,
    error: tableError,
  } = useQuery<DashboardData[]>({
    queryKey: ['dashboard-data'],
    queryFn: () => api.get('/api/dashboard/data'),
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 60 * 1000, // 1 minute
  });

  // Log table error if it occurs
  React.useEffect(() => {
    if (tableError) {
      logger.error('Failed to fetch dashboard data', tableError);
    }
  }, [tableError]);

  // Fetch chart data
  const {
    data: chartData,
    isLoading: chartLoading,
    error: chartError,
  } = useQuery<ChartData[]>({
    queryKey: ['dashboard-charts'],
    queryFn: () => api.get('/api/dashboard/charts'),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 30 * 1000, // 30 seconds
  });

  // Log chart error if it occurs
  React.useEffect(() => {
    if (chartError) {
      logger.error('Failed to fetch chart data', chartError);
    }
  }, [chartError]);

  const isLoading = metricsLoading || tableLoading || chartLoading;
  const hasError = metricsError || tableError || chartError;

  if (hasError) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-96" role="alert">
          <Card className="p-8 text-center">
            <h2 className="text-xl font-semibold text-red-600 mb-2">
              {t('dashboard.error.title', 'Failed to Load Dashboard')}
            </h2>
            <p className="text-gray-600 dark:text-gray-300">
              {t('dashboard.error.message', 'Please try refreshing the page or contact support if the problem persists.')}
            </p>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  const metricsCards = [
    {
      title: t('dashboard.metrics.totalUsers', 'Total Users'),
      value: metrics?.totalUsers?.toLocaleString() || '0',
      change: '+12%',
      trend: 'up' as const,
    },
    {
      title: t('dashboard.metrics.activeUsers', 'Active Users'),
      value: metrics?.activeUsers?.toLocaleString() || '0',
      change: '+8%',
      trend: 'up' as const,
    },
    {
      title: t('dashboard.metrics.revenue', 'Revenue'),
      value: `$${metrics?.revenue?.toLocaleString() || '0'}`,
      change: '+15%',
      trend: 'up' as const,
    },
    {
      title: t('dashboard.metrics.growth', 'Growth Rate'),
      value: `${metrics?.growth || 0}%`,
      change: '+3%',
      trend: 'up' as const,
    },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header Section */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              {t('dashboard.title', 'Dashboard')}
            </h1>
            <p className="mt-2 text-gray-600 dark:text-gray-300">
              {t('dashboard.subtitle', 'Overview of your key metrics and data')}
            </p>
          </div>
          <LiveUpdates />
        </div>

        {/* Metrics Cards Grid */}
        <div 
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
          role="region"
          aria-label={t('dashboard.metrics.label', 'Key Performance Metrics')}
        >
          {metricsCards.map((metric) => (
            <Card 
              key={metric.title} 
              className="p-6 hover:shadow-lg transition-shadow duration-200"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-300">
                    {metric.title}
                  </p>
                  <p 
                    className="text-2xl font-bold text-gray-900 dark:text-white"
                    aria-label={`${metric.title}: ${metric.value}`}
                  >
                    {isLoading ? (
                      <div className="animate-pulse bg-gray-300 dark:bg-gray-600 h-8 w-20 rounded" />
                    ) : (
                      metric.value
                    )}
                  </p>
                </div>
                <div className="text-right">
                  <span 
                    className={`text-sm font-medium ${
                      metric.trend === 'up' 
                        ? 'text-green-600 dark:text-green-400' 
                        : 'text-red-600 dark:text-red-400'
                    }`}
                    aria-label={`Change: ${metric.change}`}
                  >
                    {isLoading ? (
                      <div className="animate-pulse bg-gray-300 dark:bg-gray-600 h-4 w-12 rounded" />
                    ) : (
                      metric.change
                    )}
                  </span>
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* Charts Section */}
        <div 
          className="grid grid-cols-1 lg:grid-cols-3 gap-6"
          role="region"
          aria-label={t('dashboard.charts.label', 'Data Visualizations')}
        >
          <Suspense fallback={
            <ChartCard 
              title={t('dashboard.charts.metrics', 'Metrics Overview')}
              className="h-80"
            >
              <div className="animate-pulse bg-gray-200 dark:bg-gray-700 h-full rounded" />
            </ChartCard>
          }>
            <MetricsChart data={chartData || []} loading={chartLoading} />
          </Suspense>

          <Suspense fallback={
            <ChartCard 
              title={t('dashboard.charts.trends', 'Trends')}
              className="h-80"
            >
              <div className="animate-pulse bg-gray-200 dark:bg-gray-700 h-full rounded" />
            </ChartCard>
          }>
            <TrendChart data={chartData || []} loading={chartLoading} />
          </Suspense>

          <Suspense fallback={
            <ChartCard 
              title={t('dashboard.charts.performance', 'Performance')}
              className="h-80"
            >
              <div className="animate-pulse bg-gray-200 dark:bg-gray-700 h-full rounded" />
            </ChartCard>
          }>
            <PerformanceChart data={chartData || []} loading={chartLoading} />
          </Suspense>
        </div>

        {/* Data Table Section */}
        <div 
          className="space-y-4"
          role="region"
          aria-label={t('dashboard.table.label', 'Detailed Data')}
        >
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              {t('dashboard.table.title', 'Recent Activity')}
            </h2>
          </div>
          
          <Card className="overflow-hidden">
            {tableError ? (
              <div className="p-8 text-center" role="alert">
                <p className="text-red-600 dark:text-red-400">
                  {t('dashboard.table.error', 'Failed to load table data')}
                </p>
              </div>
            ) : tableLoading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-2 text-gray-600 dark:text-gray-300">
                  {t('dashboard.table.loading', 'Loading table data...')}
                </p>
              </div>
            ) : (
              <DataTable 
                data={tableData || []}
                columns={[
                  {
                    key: 'name',
                    label: t('dashboard.table.columns.name', 'Name'),
                    sortable: true,
                  },
                  {
                    key: 'status',
                    label: t('dashboard.table.columns.status', 'Status'),
                    sortable: true,
                  },
                  {
                    key: 'value',
                    label: t('dashboard.table.columns.value', 'Value'),
                    sortable: true,
                  },
                  {
                    key: 'lastUpdated',
                    label: t('dashboard.table.columns.updated', 'Last Updated'),
                    sortable: true,
                  },
                ]}
                aria-label={t('dashboard.table.aria', 'Dashboard data table')}
              />
            )}
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Dashboard;
export { Dashboard };