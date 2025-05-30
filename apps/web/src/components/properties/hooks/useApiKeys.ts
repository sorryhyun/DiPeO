import { useState, useEffect } from 'react';
import { getApiUrl, API_ENDPOINTS } from '@/utils/apiConfig';
import { type ApiKey } from '@repo/core-model';

export const useApiKeys = () => {
  const [apiKeysList, setApiKeysList] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchApiKeys = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(getApiUrl(API_ENDPOINTS.API_KEYS));
        if (!res.ok) throw new Error('Failed to load API keys');
        const body = await res.json();
        setApiKeysList(body.apiKeys);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load API keys');
      } finally {
        setLoading(false);
      }
    };
    fetchApiKeys();
  }, []);

  return { apiKeysList, loading, error };
};