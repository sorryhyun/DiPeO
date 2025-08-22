import React from 'react';
import { useTranslation } from 'react-i18next';
import { ChartCard } from '../../../shared/components/ChartCard';

interface ChartData {
  name: string;
  value: number;
  timestamp: string;
}

interface TrendChartProps {
  data: ChartData[];
  loading?: boolean;
}

const TrendChart: React.FC<TrendChartProps> = ({ data, loading = false }) => {
  const { t } = useTranslation();

  // Calculate trend statistics
  const sortedData = [...data].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
  const trend = sortedData.length > 1 ? 
    ((sortedData[sortedData.length - 1].value - sortedData[0].value) / sortedData[0].value) * 100 : 0;
  const trendDirection = trend > 0 ? 'up' : trend < 0 ? 'down' : 'stable';
  
  const maxValue = Math.max(...sortedData.map(item => item.value), 0);
  const minValue = Math.min(...sortedData.map(item => item.value), 0);

  return (
    <ChartCard
      title={t('dashboard.charts.trends', 'Trends')}
      subtitle={t('dashboard.charts.trends.subtitle', 'Data trends over time')}
      loading={loading}
      className="h-80"
    >
      <div className="h-full flex flex-col">
        {/* Trend Summary */}
        <div className="flex justify-between mb-4 text-sm">
          <div className="text-center">
            <p className="text-gray-500 dark:text-gray-400">Trend</p>
            <div className="flex items-center justify-center space-x-1">
              <span className={`font-semibold ${
                trendDirection === 'up' ? 'text-green-600 dark:text-green-400' :
                trendDirection === 'down' ? 'text-red-600 dark:text-red-400' :
                'text-gray-600 dark:text-gray-300'
              }`}>
                {Math.abs(trend).toFixed(1)}%
              </span>
              <svg
                className={`w-4 h-4 ${
                  trendDirection === 'up' ? 'text-green-600 dark:text-green-400 rotate-0' :
                  trendDirection === 'down' ? 'text-red-600 dark:text-red-400 rotate-180' :
                  'text-gray-600 dark:text-gray-300'
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 17l9.2-9.2M17 17V7h-10"
                />
              </svg>
            </div>
          </div>
          <div className="text-center">
            <p className="text-gray-500 dark:text-gray-400">High</p>
            <p className="font-semibold text-gray-900 dark:text-white">
              {maxValue}
            </p>
          </div>
          <div className="text-center">
            <p className="text-gray-500 dark:text-gray-400">Low</p>
            <p className="font-semibold text-gray-900 dark:text-white">
              {minValue}
            </p>
          </div>
        </div>

        {/* Simple Line Chart */}
        <div className="flex-1 relative min-h-[180px]">
          <div className="absolute inset-0 flex items-end">
            <svg
              className="w-full h-full"
              viewBox="0 0 400 200"
              preserveAspectRatio="none"
            >
              {/* Grid lines */}
              <defs>
                <pattern
                  id="grid"
                  width="40"
                  height="40"
                  patternUnits="userSpaceOnUse"
                >
                  <path
                    d="M 40 0 L 0 0 0 40"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="0.5"
                    className="text-gray-200 dark:text-gray-600"
                  />
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#grid)" />

              {/* Line chart */}
              {sortedData.length > 1 && (
                <>
                  <polyline
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="text-indigo-500 dark:text-indigo-400"
                    points={sortedData.map((item, index) => {
                      const x = (index / (sortedData.length - 1)) * 380 + 10;
                      const y = 190 - ((item.value - minValue) / (maxValue - minValue || 1)) * 180;
                      return `${x},${y}`;
                    }).join(' ')}
                  />
                  
                  {/* Data points */}
                  {sortedData.map((item, index) => {
                    const x = (index / (sortedData.length - 1)) * 380 + 10;
                    const y = 190 - ((item.value - minValue) / (maxValue - minValue || 1)) * 180;
                    return (
                      <circle
                        key={index}
                        cx={x}
                        cy={y}
                        r="3"
                        fill="currentColor"
                        className="text-indigo-600 dark:text-indigo-300"
                      >
                        <title>{`${item.name}: ${item.value}`}</title>
                      </circle>
                    );
                  })}
                </>
              )}
            </svg>
          </div>
        </div>

        {/* Time labels */}
        {sortedData.length > 0 && (
          <div className="flex justify-between mt-2 text-xs text-gray-500 dark:text-gray-400">
            <span>{new Date(sortedData[0]?.timestamp).toLocaleDateString()}</span>
            <span>{new Date(sortedData[sortedData.length - 1]?.timestamp).toLocaleDateString()}</span>
          </div>
        )}

        {/* No Data State */}
        {sortedData.length === 0 && !loading && (
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
                    d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                  />
                </svg>
              </div>
              <p className="text-gray-500 dark:text-gray-400">
                {t('dashboard.charts.noData', 'No trend data available')}
              </p>
            </div>
          </div>
        )}
      </div>
    </ChartCard>
  );
};

export default TrendChart;