/**
 * Hook for managing API integrations
 */

import { useCallback, useEffect, useState } from 'react';
import { useQuery, useMutation, gql } from '@apollo/client';

// GraphQL queries and mutations
const GET_PROVIDERS = gql`
  query GetProviders {
    providers {
      name
      operations {
        name
        method
        path
        description
        required_scopes
      }
      metadata {
        version
        type
        description
        documentation_url
      }
      base_url
      default_timeout
    }
  }
`;

const GET_PROVIDER_OPERATIONS = gql`
  query GetProviderOperations($provider: String!) {
    provider_operations(provider: $provider) {
      name
      method
      path
      description
      required_scopes
      has_pagination
      timeout_override
    }
  }
`;

const GET_OPERATION_SCHEMA = gql`
  query GetOperationSchema($provider: String!, $operation: String!) {
    operation_schema(provider: $provider, operation: $operation) {
      operation
      method
      path
      description
      request_body
      query_params
      response
    }
  }
`;

// TODO: These mutations need to be implemented in the backend
// const TEST_INTEGRATION = gql`
//   mutation TestIntegration($input: TestIntegrationInput!) {
//     testIntegration(input: $input) {
//       success
//       provider
//       operation
//       status_code
//       response_time_ms
//       error
//       response_preview
//     }
//   }
// `;

// const EXECUTE_INTEGRATION = gql`
//   mutation ExecuteIntegration($input: ExecuteIntegrationInput!) {
//     executeIntegration(input: $input)
//   }
// `;

export interface Provider {
  name: string;
  operations: Operation[];
  metadata: ProviderMetadata;
  base_url?: string;
  default_timeout: number;
}

export interface Operation {
  name: string;
  method: string;
  path: string;
  description?: string;
  required_scopes?: string[];
  has_pagination?: boolean;
  timeout_override?: number;
}

export interface ProviderMetadata {
  version: string;
  type: string;
  description?: string;
  documentation_url?: string;
}

export interface OperationSchema {
  operation: string;
  method: string;
  path: string;
  description?: string;
  request_body?: any;
  query_params?: any;
  response?: any;
}

export interface TestResult {
  success: boolean;
  provider: string;
  operation: string;
  status_code: number;
  response_time_ms: number;
  error?: string;
  response_preview?: any;
}

/**
 * Hook for managing API integrations
 */
export function useIntegrations() {
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [selectedOperation, setSelectedOperation] = useState<string | null>(null);

  // Fetch all providers
  const {
    data: providersData,
    loading: providersLoading,
    error: providersError,
    refetch: refetchProviders,
  } = useQuery(GET_PROVIDERS);

  // Fetch operations for selected provider
  const {
    data: operationsData,
    loading: operationsLoading,
    error: operationsError,
    refetch: refetchOperations,
  } = useQuery(GET_PROVIDER_OPERATIONS, {
    variables: { provider: selectedProvider },
    skip: !selectedProvider,
  });

  // Fetch schema for selected operation
  const {
    data: schemaData,
    loading: schemaLoading,
    error: schemaError,
  } = useQuery(GET_OPERATION_SCHEMA, {
    variables: {
      provider: selectedProvider,
      operation: selectedOperation,
    },
    skip: !selectedProvider || !selectedOperation,
  });

  // Test integration mutation - TODO: implement backend mutation
  // const [testIntegration, { loading: testLoading }] = useMutation(TEST_INTEGRATION);
  const testLoading = false;

  // Execute integration mutation - TODO: implement backend mutation
  // const [executeIntegration, { loading: executeLoading }] = useMutation(EXECUTE_INTEGRATION);
  const executeLoading = false;

  // Handle provider selection
  const selectProvider = useCallback((providerName: string) => {
    setSelectedProvider(providerName);
    setSelectedOperation(null); // Reset operation when provider changes
  }, []);

  // Handle operation selection
  const selectOperation = useCallback((operationName: string) => {
    setSelectedOperation(operationName);
  }, []);

  // Test an integration - TODO: implement when backend mutation is ready
  const testIntegrationCall = useCallback(
    async (config: any, apiKeyId?: string, dryRun: boolean = false) => {
      if (!selectedProvider || !selectedOperation) {
        throw new Error('Provider and operation must be selected');
      }

      // TODO: Uncomment when backend mutation is implemented
      // const result = await testIntegration({
      //   variables: {
      //     input: {
      //       provider: selectedProvider,
      //       operation: selectedOperation,
      //       config_preview: config,
      //       api_key_id: apiKeyId,
      //       dry_run: dryRun,
      //     },
      //   },
      // });
      // return result.data?.testIntegration as TestResult;

      console.warn('Test integration not implemented yet');
      return null;
    },
    [selectedProvider, selectedOperation]
  );

  // Execute an integration - TODO: implement when backend mutation is ready
  const executeIntegrationCall = useCallback(
    async (config: any, resourceId?: string, apiKeyId?: string, timeout?: number) => {
      if (!selectedProvider || !selectedOperation) {
        throw new Error('Provider and operation must be selected');
      }

      // TODO: Uncomment when backend mutation is implemented
      // const result = await executeIntegration({
      //   variables: {
      //     input: {
      //       provider: selectedProvider,
      //       operation: selectedOperation,
      //       config,
      //       resource_id: resourceId,
      //       api_key_id: apiKeyId,
      //       timeout,
      //     },
      //   },
      // });
      // return result.data?.executeIntegration;

      console.warn('Execute integration not implemented yet');
      return null;
    },
    [selectedProvider, selectedOperation]
  );

  // Get available providers as options
  const providerOptions = providersData?.providers?.map((p: Provider) => ({
    value: p.name,
    label: p.name,
    description: p.metadata?.description,
  })) || [];

  // Get available operations as options
  const operationOptions = operationsData?.provider_operations?.map((op: Operation) => ({
    value: op.name,
    label: op.name,
    description: op.description,
  })) || [];

  return {
    // Data
    providers: providersData?.providers as Provider[],
    selectedProvider,
    selectedOperation,
    operations: operationsData?.provider_operations as Operation[],
    operationSchema: schemaData?.operation_schema as OperationSchema,
    providerOptions,
    operationOptions,

    // Loading states
    providersLoading,
    operationsLoading,
    schemaLoading,
    testLoading,
    executeLoading,

    // Errors
    providersError,
    operationsError,
    schemaError,

    // Actions
    selectProvider,
    selectOperation,
    testIntegration: testIntegrationCall,
    executeIntegration: executeIntegrationCall,
    refetchProviders,
    refetchOperations,
  };
}
