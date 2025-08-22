import React from 'react';
import { useTranslation } from 'react-i18next';
import { ChartCard } from '../../../shared/components/ChartCard';

interface ChartData {
  name: string;
  value: number;
  timestamp: string;
}

interface PerformanceChartProps {
  data: ChartData[];
  loading?: boolean;
}

const PerformanceChart: React.FC<PerformanceChartProps> = ({ data, loading = false }) => {
  const { t } = useTranslation();

  // Calculate performance metrics
  const avgPerformance = data.length > 0 ? data.reduce((sum, item) => sum + item.value, 0) / data.length : 0;
  const maxPerformance = Math.max(...data.map(item => item.value), 0);
  const minPerformance = Math.min(...data.map(item => item.value), 0);
  const performanceScore = maxPerformance > 0 ? (avgPerformance / maxPerformance) * 100 : 0;

  // Performance rating
  const getPerformanceRating = (score: number) => {
    if (score >= 80) return { label: 'Excellent', color: 'text-green-600 dark:text-green-400' };
    if (score >= 60) return { label: 'Good', color: 'text-blue-600 dark:text-blue-400' };
    if (score >= 40) return { label: 'Fair', color: 'text-yellow-600 dark:text-yellow-400' };
    return { label: 'Poor', color: 'text-red-600 dark:text-red-400' };
  };

  const rating = getPerformanceRating(performanceScore);

  return (
    <ChartCard
      title={t('dashboard.charts.performance', 'Performance')}
      subtitle={t('dashboard.charts.performance.subtitle', 'System performance metrics')}
      loading={loading}
      className="h-80"
    >
      <div className="h-full flex flex-col">
        {/* Performance Score */}
        <div className="text-center mb-6">
          <div className="relative inline-flex items-center justify-center w-24 h-24 mb-4">
            {/* Background circle */}
            <svg className="absolute inset-0 w-24 h-24 transform -rotate-90">
              <circle
                cx="48"
                cy="48"
                r="40"
                stroke="currentColor"
                strokeWidth="8"
                fill="none"
                className="text-gray-200 dark:text-gray-600"
              />
              {/* Progress circle */}
              <circle
                cx="48"
                cy="48"
                r="40"
                stroke="currentColor"
                strokeWidth="8"
                fill="none"
                strokeLinecap="round"
                className={rating.color}
                strokeDasharray={`${2 * Math.PI * 40}`}
                strokeDashoffset={`${2 * Math.PI * 40 * (1 - performanceScore / 100)}`}
                style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}
              />
            </svg>
            {/* Score text */}
            <div className="text-center">
              <div className="text-xl font-bold text-gray-900 dark:text-white">
                {performanceScore.toFixed(0)}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                SCORE
              </div>
            </div>
          </div>
          <div className={`text-sm font-medium ${rating.color}`}>
            {t(`dashboard.charts.performance.rating.${rating.label.toLowerCase()}`, rating.label)}
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="text-center">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Average</p>
            <p className="text-sm font-semibold text-gray-900 dark:text-white">
              {avgPerformance.toFixed(1)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Peak</p>
            <p className="text-sm font-semibold text-gray-900 dark:text-white">
              {maxPerformance}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Low</p>
            <p className="text-sm font-semibold text-gray-900 dark:text-white">
              {minPerformance}
            </p>
          </div>
        </div>

        {/* Performance Bars */}
        <div className="flex-1 space-y-3">
          {data.slice(0, 5).map((item, index) => {
            const percentage = maxPerformance > 0 ? (item.value / maxPerformance) * 100 : 0;
            return (
              <div key={index} className="flex items-center space-x-3">
                <div className="w-16 text-xs text-gray-600 dark:text-gray-300 truncate">
                  {item.name}
                </div>
                <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${
                      percentage >= 80 ? 'bg-green-500' :
                      percentage >= 60 ? 'bg-blue-500' :
                      percentage >= 40 ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
                <div className="w-12 text-xs text-gray-600 dark:text-gray-300 text-right">
                  {item.value}
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
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
              <p className="text-gray-500 dark:text-gray-400">
                {t('dashboard.charts.noData', 'No performance data available')}
              </p>
            </div>
          </div>
        )}
      </div>
    </ChartCard>
  );
};

export default PerformanceChart;