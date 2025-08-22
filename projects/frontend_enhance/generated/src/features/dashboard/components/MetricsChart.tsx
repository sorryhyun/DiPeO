import React from 'react';
import { useTranslation } from 'react-i18next';
import { ChartCard } from '../../../shared/components/ChartCard';

interface ChartData {
  name: string;
  value: number;
  timestamp: string;
}

interface MetricsChartProps {
  data: ChartData[];
  loading?: boolean;
}

const MetricsChart: React.FC<MetricsChartProps> = ({ data, loading = false }) => {
  const { t } = useTranslation();

  // Calculate simple metrics from data
  const maxValue = Math.max(...data.map(item => item.value), 0);
  const avgValue = data.length > 0 ? data.reduce((sum, item) => sum + item.value, 0) / data.length : 0;

  return (
    <ChartCard
      title={t('dashboard.charts.metrics', 'Metrics Overview')}
      subtitle={t('dashboard.charts.metrics.subtitle', 'Key performance indicators')}
      loading={loading}
      className="h-80"
    >
      <div className="h-full flex flex-col">
        {/* Summary Stats */}
        <div className="flex justify-between mb-4 text-sm">
          <div className="text-center">
            <p className="text-gray-500 dark:text-gray-400">Average</p>
            <p className="font-semibold text-gray-900 dark:text-white">
              {avgValue.toFixed(1)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-gray-500 dark:text-gray-400">Peak</p>
            <p className="font-semibold text-gray-900 dark:text-white">
              {maxValue}
            </p>
          </div>
          <div className="text-center">
            <p className="text-gray-500 dark:text-gray-400">Data Points</p>
            <p className="font-semibold text-gray-900 dark:text-white">
              {data.length}
            </p>
          </div>
        </div>

        {/* Simple Bar Chart */}
        <div className="flex-1 flex items-end justify-between space-x-2 min-h-[180px]">
          {data.slice(0, 8).map((item, index) => {
            const height = maxValue > 0 ? (item.value / maxValue) * 100 : 0;
            return (
              <div
                key={index}
                className="flex flex-col items-center flex-1 min-w-0"
              >
                <div
                  className="w-full bg-blue-500 dark:bg-blue-400 rounded-t transition-all duration-300 hover:bg-blue-600 dark:hover:bg-blue-300"
                  style={{ height: `${height}%`, minHeight: '4px' }}
                  title={`${item.name}: ${item.value}`}
                />
                <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 truncate w-full text-center">
                  {item.name.substring(0, 8)}
                </div>
              </div>
            );
          })}
        </div>

        {/* No Data State */}
        {data.length === 0 && !loading && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
              <p className="text-gray-500 dark:text-gray-400">
                {t('dashboard.charts.noData', 'No data available')}
              </p>
            </div>
          </div>
        )}
      </div>
    </ChartCard>
  );
};

export default MetricsChart;