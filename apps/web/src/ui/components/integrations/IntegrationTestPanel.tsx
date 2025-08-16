/**
 * Test results panel for API integrations
 */

import React from 'react';
import { TestResult } from '@/domain/integrations/hooks';

export interface IntegrationTestPanelProps {
  result: TestResult;
  onClose: () => void;
}

/**
 * Displays test results for an integration call
 */
export const IntegrationTestPanel: React.FC<IntegrationTestPanelProps> = ({
  result,
  onClose,
}) => {
  const getStatusColor = (statusCode: number) => {
    if (statusCode >= 200 && statusCode < 300) return 'text-green-600';
    if (statusCode >= 400 && statusCode < 500) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatResponseTime = (ms: number) => {
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <div className="border rounded-lg p-4 bg-white shadow-sm">
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <h3 className="font-medium text-gray-900">Test Results</h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
          aria-label="Close"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Status */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          {result.success ? (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
              ✓ Success
            </span>
          ) : (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
              ✗ Failed
            </span>
          )}
          {result.status_code && (
            <span className={`text-sm font-mono ${getStatusColor(result.status_code)}`}>
              {result.status_code}
            </span>
          )}
          {result.response_time_ms && (
            <span className="text-sm text-gray-500">
              {formatResponseTime(result.response_time_ms)}
            </span>
          )}
        </div>

        {/* Provider and Operation */}
        <div className="text-sm text-gray-600">
          <span className="font-medium">{result.provider}</span>
          {' → '}
          <span>{result.operation}</span>
        </div>

        {/* Error Message */}
        {result.error && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded">
            <p className="text-sm font-medium text-red-800 mb-1">Error</p>
            <p className="text-sm text-red-700">{result.error}</p>
          </div>
        )}

        {/* Response Preview */}
        {result.response_preview && (
          <div className="mt-3">
            <p className="text-sm font-medium text-gray-700 mb-1">Response</p>
            <div className="bg-gray-50 rounded p-3 max-h-64 overflow-auto">
              <pre className="text-xs font-mono text-gray-600">
                {typeof result.response_preview === 'string'
                  ? result.response_preview
                  : JSON.stringify(result.response_preview, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="mt-4 pt-3 border-t flex gap-2">
        <button
          onClick={() => {
            // Copy response to clipboard
            const text = typeof result.response_preview === 'string'
              ? result.response_preview
              : JSON.stringify(result.response_preview, null, 2);
            navigator.clipboard.writeText(text);
          }}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          Copy Response
        </button>
        {result.success && (
          <button
            onClick={() => {
              // Copy as template
              const template = {
                provider: result.provider,
                operation: result.operation,
                expected_response: result.response_preview,
              };
              navigator.clipboard.writeText(JSON.stringify(template, null, 2));
            }}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            Copy as Template
          </button>
        )}
      </div>
    </div>
  );
};