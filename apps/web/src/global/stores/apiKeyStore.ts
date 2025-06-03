import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { ApiKey, createErrorHandlerFactory } from '@/shared/types';
import { createApiKeyCrudActions } from "@/shared/utils/storeCrudUtils";
import { API_ENDPOINTS, getApiUrl } from '@/shared/utils/apiConfig';
import { toast } from 'sonner';

export interface ApiKeyState {
  apiKeys: ApiKey[];
  
  addApiKey: (apiKey: Omit<ApiKey, 'id'>) => void;
  updateApiKey: (apiKeyId: string, apiKeyData: Partial<ApiKey>) => void;
  deleteApiKey: (apiKeyId: string) => void;
  getApiKeyById: (apiKeyId: string) => ApiKey | undefined;
  clearApiKeys: () => void;
  loadApiKeys: () => Promise<void>;
  setApiKeys: (apiKeys: ApiKey[]) => void;
}

const createErrorHandler = createErrorHandlerFactory(toast);

export const useApiKeyStore = create<ApiKeyState>()(
  devtools(
    subscribeWithSelector(
      (set, get) => ({
        apiKeys: [],
        
        // API key operations using generic CRUD
        ...createApiKeyCrudActions<ApiKey>(
          () => get().apiKeys,
          (apiKeys) => set({ apiKeys }),
          'APIKEY'
        ),
        
        loadApiKeys: async () => {
          const errorHandler = createErrorHandler('Load API Keys');
          try {
            const response = await fetch(getApiUrl(API_ENDPOINTS.API_KEYS));
            if (!response.ok) {
              throw new Error(`Failed to load API keys: ${response.statusText}`);
            }
            
            const data = await response.json();
            const apiKeys = (Array.isArray(data) ? data : data.apiKeys || []).map((key: {id: string; name: string; service: string}) => ({
              id: key.id,
              name: key.name,
              service: key.service,
              keyReference: '***hidden***' // Don't store raw keys in frontend
            }));
            
            set({ apiKeys });
          } catch (error) {
            console.error('Error loading API keys:', error);
            errorHandler(error as Error);
            throw error;
          }
        },
        
        setApiKeys: (apiKeys: ApiKey[]) => {
          set({ apiKeys });
        },
      })
    )
  )
);