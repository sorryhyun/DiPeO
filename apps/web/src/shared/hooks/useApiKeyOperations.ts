import { useQuery, useMutation } from '@apollo/client';
import { toast } from 'sonner';
import { 
  GetApiKeysDocument,
  CreateApiKeyDocument,
  DeleteApiKeyDocument,
  TestApiKeyDocument,
  GetAvailableModelsDocument
} from '@/__generated__/graphql';
import { ApiKeyID, DomainApiKey, apiKeyId } from '@/core/types';

export const useApiKeyOperations = () => {
  // Query to get all API keys
  const { data: apiKeysData, loading: loadingApiKeys, refetch: refetchApiKeys } = useQuery(GetApiKeysDocument);

  // Mutation to create API key
  const [createApiKeyMutation, { loading: creatingApiKey }] = useMutation(CreateApiKeyDocument, {
    onCompleted: (data) => {
      if (data.createApiKey.success && data.createApiKey.apiKey) {
        toast.success(`API key "${data.createApiKey.apiKey.label}" added successfully`);
      } else {
        toast.error(data.createApiKey.error || 'Failed to create API key');
      }
    },
    onError: (error) => {
      toast.error(`Failed to create API key: ${error.message}`);
    },
    refetchQueries: [{ query: GetApiKeysDocument }]
  });

  // Mutation to delete API key
  const [deleteApiKeyMutation, { loading: deletingApiKey }] = useMutation(DeleteApiKeyDocument, {
    onCompleted: (data) => {
      if (data.deleteApiKey.success && data.deleteApiKey.deletedId) {
        toast.success('API key deleted successfully');
      } else {
        toast.error(data.deleteApiKey.error || 'Failed to delete API key');
      }
    },
    onError: (error) => {
      toast.error(`Failed to delete API key: ${error.message}`);
    },
    refetchQueries: [{ query: GetApiKeysDocument }]
  });

  // Mutation to test API key
  const [testApiKeyMutation, { loading: testingApiKey }] = useMutation(TestApiKeyDocument);

  // Function to create API key
  const createApiKey = async (label: string, service: string, key: string) => {
    return createApiKeyMutation({
      variables: {
        input: {
          label,
          service,
          key
        }
      }
    });
  };

  // Function to delete API key
  const deleteApiKey = async (id: string) => {
    return deleteApiKeyMutation({
      variables: { id }
    });
  };

  // Function to test API key
  const testApiKey = async (id: string) => {
    return testApiKeyMutation({
      variables: { id }
    });
  };

  // Function to get available models
  const getAvailableModels = (service: string, apiKeyId: string) => {
    return useQuery(GetAvailableModelsDocument, {
      variables: { service, apiKeyId },
      skip: !service || !apiKeyId
    });
  };

  return {
    // Data
    apiKeys: apiKeysData?.apiKeys || [],
    
    // Loading states
    loadingApiKeys,
    creatingApiKey,
    deletingApiKey,
    testingApiKey,
    
    // Operations
    createApiKey,
    deleteApiKey,
    testApiKey,
    getAvailableModels,
    refetchApiKeys
  };
};