import React, { useState, useEffect } from 'react';
import { Button, Input, Modal, Select } from '@/components/ui';
import { DomainApiKey, apiKeyId, createErrorHandlerFactory, ApiKeyID } from '@/types';
import { useUnifiedStore } from '@/hooks/useUnifiedStore';
import { Trash2, Plus, Eye, EyeOff } from 'lucide-react';
import { API_ENDPOINTS, getApiUrl } from '@/utils/api';
import { toast } from 'sonner';

interface ApiKeysModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const API_SERVICES = [
  { value: 'anthropic', label: 'Claude (Anthropic)' },
  { value: 'openai', label: 'ChatGPT (OpenAI)' },
  { value: 'grok', label: 'Grok' },
  { value: 'gemini', label: 'Gemini (Google)' },
  { value: 'custom', label: 'Custom' },
] as const;

const ApiKeysModal: React.FC<ApiKeysModalProps> = ({ isOpen, onClose }) => {
  const { apiKeys, deleteApiKey } = useUnifiedStore();
  
  // Convert Map to array for display
  const apiKeysArray = Array.from(apiKeys.values());
  const [newKeyForm, setNewKeyForm] = useState<Partial<DomainApiKey> & { key?: string }>({
    label: '',
    service: 'openai',
    key: '',
  });
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [_loading, setLoading] = useState(false);

  // Create error handler for API key operations
  const createErrorHandler = createErrorHandlerFactory('ApiKeysModal');

  // Load API keys when modal opens
  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      // API keys are already in the unified store
      setLoading(false);
    }
  }, [isOpen]);

  const handleAddKey = async () => {
    setErrors({});
    
    if (!newKeyForm.label?.trim()) {
      setErrors({ label: 'Name is required' });
      return;
    }
    
    if (!newKeyForm.key?.trim()) {
      setErrors({ key: 'API key is required' });
      return;
    }

    try {
      // Call backend API to create API key
      const response = await fetch(getApiUrl(API_ENDPOINTS.API_KEYS), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          label: newKeyForm.label.trim(),
          service: newKeyForm.service || 'claude',
          key: newKeyForm.key.trim()
        })
      });

      if (!response.ok) {
        const error = await response.json();
        setErrors({ key: error.error || 'Failed to create API key' });
        return;
      }

      const result = await response.json();
      
      // Directly add to store with backend ID - don't use addApiKey which generates its own ID
      const newKey: DomainApiKey = {
        id: apiKeyId(result.id),
        label: result.label || newKeyForm.label.trim(),
        service: result.service || newKeyForm.service || 'claude',
        // key is optional - not stored in frontend for security
      };

      // Manually add to store with the backend's ID
      const { apiKeys } = useUnifiedStore.getState();
      const newApiKeys = new Map(apiKeys);
      newApiKeys.set(newKey.id, newKey);
      useUnifiedStore.setState({ apiKeys: newApiKeys });
      
      // Reset form
      setNewKeyForm({
        label: '',
        service: 'openai',
        key: '',
      });
      
      toast.success(`API key "${newKey.label}" added successfully`);
    } catch {
      setErrors({ keyReference: 'Network error: Failed to create API key' });
    }
  };

  const handleDeleteKey = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this API key?')) {
      try {
        // Call backend API to delete
        const response = await fetch(getApiUrl(API_ENDPOINTS.API_KEY_BY_ID(id)), {
          method: 'DELETE'
        });

        if (!response.ok) {
          throw new Error('Failed to delete API key');
        }

        // Remove from local store
        deleteApiKey(apiKeyId(id));
      } catch (error) {
        createErrorHandler(error);
      }
    }
  };

  const toggleShowKey = (id: string) => {
    setShowKeys(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const maskApiKey = (key: string) => {
    if (!key) return '';
    const visibleChars = 4;
    if (key.length <= visibleChars * 2) return '••••••••';
    return `${key.slice(0, visibleChars)}••••••••${key.slice(-visibleChars)}`;
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="API Keys" className="max-w-2xl">
      <div className="space-y-6">
        {/* Existing API Keys */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Configured API Keys
          </h3>
          {apiKeysArray.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 italic">
              No API keys configured yet. Add one below.
            </p>
          ) : (
            <div className="space-y-2">
              {apiKeysArray.map((key: DomainApiKey) => (
                <div
                  key={key.id}
                  className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{key.label}</span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        ({API_SERVICES.find(s => s.value === key.service)?.label})
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <code className="text-xs font-mono text-gray-600 dark:text-gray-400">
                        {showKeys[key.id] ? '***hidden***' : maskApiKey('***hidden***')}
                      </code>
                      <button
                        onClick={() => toggleShowKey(key.id)}
                        className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
                      >
                        {showKeys[key.id] ? (
                          <EyeOff className="w-3 h-3 text-gray-500" />
                        ) : (
                          <Eye className="w-3 h-3 text-gray-500" />
                        )}
                      </button>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteKey(key.id)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Add New Key Form */}
        <div className="border-t pt-6">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Add New API Key
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Name
              </label>
              <Input
                placeholder="e.g., Production Claude Key"
                value={newKeyForm.label || ''}
                onChange={(e) => setNewKeyForm({ ...newKeyForm, label: e.target.value })}
                className={errors.name ? 'border-red-500' : ''}
              />
              {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Service
              </label>
              <Select
                value={newKeyForm.service || 'claude'}
                onValueChange={(value) => setNewKeyForm({ ...newKeyForm, service: value as DomainApiKey['service'] })}
              >
                {API_SERVICES.map((service) => (
                  <option key={service.value} value={service.value}>
                    {service.label}
                  </option>
                ))}
              </Select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                API Key
              </label>
              <Input
                type="password"
                placeholder="sk-..."
                value={newKeyForm.key || ''}
                onChange={(e) => setNewKeyForm({ ...newKeyForm, key: e.target.value })}
                className={errors.key ? 'border-red-500' : ''}
              />
              {errors.key && <p className="text-red-500 text-sm mt-1">{errors.key}</p>}
            </div>
            
            <Button
              onClick={handleAddKey}
              className="w-full"
              disabled={!newKeyForm.label || !newKeyForm.key}
            >
              <Plus className="w-4 h-4 mr-2" />
              Add API Key
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default ApiKeysModal;