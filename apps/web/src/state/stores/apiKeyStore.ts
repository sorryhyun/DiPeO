import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { ApiKey } from '@/common/types';
import { createApiKeyCrudActions } from "@/common/utils/storeCrudUtils";
import { api } from '@/common/utils/apiClient';

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
          try {
            const data = await api.apiKeys.list();
            const apiKeys = data.map((key) => ({
              id: key.id,
              name: key.name,
              service: key.service as ApiKey['service'],
              keyReference: '***hidden***' // Don't store raw keys in frontend
            }));
            
            set({ apiKeys });
          } catch (error) {
            console.error('Error loading API keys:', error);
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