/**
 * Dynamic form component for API integrations
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useIntegrations } from '@/domain/integrations/hooks';
import { Button } from '@/ui/components/common/forms/buttons';
import { Select } from '@/ui/components/common/forms';
import { Spinner } from '@/ui/components/common/feedback';
import { IntegrationConfigEditor } from './IntegrationConfigEditor';
import { IntegrationTestPanel } from './IntegrationTestPanel';

export interface IntegrationFormProps {
  value?: {
    provider?: string;
    operation?: string;
    config?: any;
    resource_id?: string;
    timeout?: number;
    max_retries?: number;
  };
  onChange?: (value: any) => void;
  apiKeyId?: string;
  readOnly?: boolean;
}

/**
 * Dynamic form for configuring API integrations
 */
export const IntegrationForm: React.FC<IntegrationFormProps> = ({
  value = {},
  onChange,
  apiKeyId,
  readOnly = false,
}) => {
  const {
    providers,
    providerOptions,
    operationOptions,
    selectedProvider,
    selectedOperation,
    operationSchema,
    selectProvider,
    selectOperation,
    providersLoading,
    operationsLoading,
    schemaLoading,
    testIntegration,
    testLoading,
  } = useIntegrations();

  const [config, setConfig] = useState<any>(value.config || {});
  const [showTestPanel, setShowTestPanel] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  // Initialize selections from value prop
  useEffect(() => {
    if (value.provider && value.provider !== selectedProvider) {
      selectProvider(value.provider);
    }
    if (value.operation && value.operation !== selectedOperation) {
      selectOperation(value.operation);
    }
    if (value.config) {
      setConfig(value.config);
    }
  }, [value.provider, value.operation, value.config]);

  // Update parent when values change
  useEffect(() => {
    if (onChange) {
      onChange({
        ...value,
        provider: selectedProvider,
        operation: selectedOperation,
        config,
      });
    }
  }, [selectedProvider, selectedOperation, config]);

  // Handle provider change
  const handleProviderChange = useCallback((newProvider: string) => {
    selectProvider(newProvider);
    // Reset config when provider changes
    setConfig({});
    setTestResult(null);
  }, [selectProvider]);

  // Handle operation change
  const handleOperationChange = useCallback((newOperation: string) => {
    selectOperation(newOperation);
    // Reset config when operation changes
    setConfig({});
    setTestResult(null);
  }, [selectOperation]);

  // Handle config change
  const handleConfigChange = useCallback((newConfig: any) => {
    setConfig(newConfig);
  }, []);

  // Test the integration
  const handleTest = useCallback(async () => {
    try {
      const result = await testIntegration(config, apiKeyId, false);
      setTestResult(result);
      setShowTestPanel(true);
    } catch (error) {
      setTestResult({
        success: false,
        error: error instanceof Error ? error.message : 'Test failed',
      });
      setShowTestPanel(true);
    }
  }, [config, apiKeyId, testIntegration]);

  // Dry run test (validation only)
  const handleDryRun = useCallback(async () => {
    try {
      const result = await testIntegration(config, apiKeyId, true);
      setTestResult(result);
      setShowTestPanel(true);
    } catch (error) {
      setTestResult({
        success: false,
        error: error instanceof Error ? error.message : 'Validation failed',
      });
      setShowTestPanel(true);
    }
  }, [config, apiKeyId, testIntegration]);

  // Get provider metadata
  const currentProvider = useMemo(() => {
    return providers?.find(p => p.name === selectedProvider);
  }, [providers, selectedProvider]);

  // Get operation metadata
  const currentOperation = useMemo(() => {
    return operationOptions?.find((op: { value: string; label: string; description?: string }) => op.value === selectedOperation);
  }, [operationOptions, selectedOperation]);

  if (providersLoading) {
    return <Spinner size="sm" />;
  }

  return (
    <div className="space-y-4">
      {/* Provider Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Provider
        </label>
        <Select
          value={selectedProvider || ''}
          onChange={(e: React.ChangeEvent<HTMLSelectElement>) => handleProviderChange(e.target.value)}
          disabled={readOnly}
        >
          <option value="">Select a provider...</option>
          {providerOptions?.map((option: { value: string; label: string }) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
        {currentProvider?.metadata?.description && (
          <p className="mt-1 text-sm text-gray-500">
            {currentProvider.metadata.description}
          </p>
        )}
      </div>

      {/* Operation Selection */}
      {selectedProvider && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Operation
          </label>
          {operationsLoading ? (
            <Spinner size="sm" />
          ) : (
            <>
              <Select
                value={selectedOperation || ''}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => handleOperationChange(e.target.value)}
                disabled={readOnly}
              >
                <option value="">Select an operation...</option>
                {operationOptions?.map((option: { value: string; label: string }) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
              {currentOperation?.description && (
                <p className="mt-1 text-sm text-gray-500">
                  {currentOperation.description}
                </p>
              )}
            </>
          )}
        </div>
      )}

      {/* Configuration Editor */}
      {selectedOperation && operationSchema && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Configuration
          </label>
          {schemaLoading ? (
            <Spinner size="sm" />
          ) : (
            <IntegrationConfigEditor
              schema={operationSchema}
              value={config}
              onChange={handleConfigChange}
              readOnly={readOnly}
            />
          )}
        </div>
      )}

      {/* Resource ID (optional) */}
      {selectedOperation && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Resource ID (optional)
          </label>
          <input
            type="text"
            value={value.resource_id || ''}
            onChange={(e) => onChange?.({ ...value, resource_id: e.target.value })}
            disabled={readOnly}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., channel ID, page ID..."
          />
        </div>
      )}

      {/* Advanced Settings */}
      <details className="border border-gray-200 rounded-md p-3">
        <summary className="cursor-pointer font-medium text-sm">
          Advanced Settings
        </summary>
        <div className="mt-3 space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Timeout (seconds)
            </label>
            <input
              type="number"
              value={value.timeout || 30}
              onChange={(e) => onChange?.({ ...value, timeout: parseInt(e.target.value) })}
              disabled={readOnly}
              min={1}
              max={300}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max Retries
            </label>
            <input
              type="number"
              value={value.max_retries || 3}
              onChange={(e) => onChange?.({ ...value, max_retries: parseInt(e.target.value) })}
              disabled={readOnly}
              min={0}
              max={10}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </details>

      {/* Test Actions */}
      {!readOnly && selectedOperation && (
        <div className="flex gap-2">
          <Button
            onClick={handleDryRun}
            variant="secondary"
            size="sm"
            disabled={testLoading}
          >
            Validate Config
          </Button>
          <Button
            onClick={handleTest}
            variant="primary"
            size="sm"
            disabled={testLoading || !apiKeyId}
          >
            {testLoading ? <Spinner size="sm" /> : 'Test Integration'}
          </Button>
          {!apiKeyId && (
            <span className="text-sm text-yellow-600 self-center">
              ⚠️ API key required for testing
            </span>
          )}
        </div>
      )}

      {/* Test Results Panel */}
      {showTestPanel && testResult && (
        <IntegrationTestPanel
          result={testResult}
          onClose={() => setShowTestPanel(false)}
        />
      )}

      {/* Documentation Link */}
      {currentProvider?.metadata?.documentation_url && (
        <div className="text-sm text-gray-500">
          <a
            href={currentProvider.metadata.documentation_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            View API Documentation →
          </a>
        </div>
      )}
    </div>
  );
};