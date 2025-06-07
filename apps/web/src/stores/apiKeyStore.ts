import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { entityIdGenerators } from '@/utils/id';
import { ApiKey } from '@/types';
import { api } from '@/utils';

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
        
        addApiKey: (apiKeyData: Omit<ApiKey, 'id'>) => {
          const newApiKey = {
            ...apiKeyData,
            id: entityIdGenerators.apiKey()
          } as ApiKey;
          set(state => ({ apiKeys: [...state.apiKeys, newApiKey] }));
        },
        
        updateApiKey: (id: string, data: Partial<ApiKey>) => {
          set(state => ({
            apiKeys: state.apiKeys.map(key => 
              key.id === id ? { ...key, ...data } : key
            )
          }));
        },
        
        deleteApiKey: (id: string) => {
          set(state => ({
            apiKeys: state.apiKeys.filter(key => key.id !== id)
          }));
        },
        
        getApiKeyById: (id: string) => {
          return get().apiKeys.find(key => key.id === id);
        },
        
        clearApiKeys: () => {
          set({ apiKeys: [] });
        },
        
        loadApiKeys: async () => {
          try {
            const data = await api.apiKeys.list();
            const apiKeys = data.map((key) => ({
              id: key.id,
              name: key.name,
              service: key.service as ApiKey['service'],
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