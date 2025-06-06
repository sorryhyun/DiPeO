import React from 'react';
import { useApiKeyStore } from '@/stores/apiKeyStore';

export const useApiKeySelectors = () => {
  const apiKeys = useApiKeyStore(state => state.apiKeys);
  
  return React.useMemo(() => ({
    apiKeys,
  }), [apiKeys]);
};

// Utility function for direct access
export const getApiKeys = () => useApiKeyStore.getState().apiKeys;