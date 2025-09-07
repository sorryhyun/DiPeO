import { toast } from 'sonner';

/**
 * Common response patterns in DiPeO GraphQL API
 */
export interface StandardResponse<T = any> {
  success: boolean;
  message?: string;
  error?: string;
  [key: string]: any; // Additional fields like 'diagram', 'api_key', etc.
}

/**
 * Handle standard mutation responses with success/error fields
 */
export function handleStandardResponse<T extends StandardResponse>(
  response: T,
  options?: {
    successMessage?: string | ((data: T) => string);
    errorMessage?: string | ((data: T) => string);
    onSuccess?: (data: T) => void;
    onError?: (data: T) => void;
    silent?: boolean;
  }
) {
  if (response.success) {
    // Handle success
    if (options?.onSuccess) {
      options.onSuccess(response);
    }

    if (!options?.silent) {
      const message = typeof options?.successMessage === 'function'
        ? options.successMessage(response)
        : options?.successMessage || response.message || 'Operation successful';
      toast.success(message);
    }

    return true;
  } else {
    // Handle error
    if (options?.onError) {
      options.onError(response);
    }

    if (!options?.silent) {
      const message = typeof options?.errorMessage === 'function'
        ? options.errorMessage(response)
        : options?.errorMessage || response.error || response.message || 'Operation failed';
      toast.error(message);
    }

    return false;
  }
}

/**
 * Extract data from standard response or throw error
 */
export function extractResponseData<T extends StandardResponse, K extends keyof T>(
  response: T,
  dataKey: K
): T[K] {
  if (!response.success) {
    throw new Error(response.error || response.message || 'Operation failed');
  }

  if (!(dataKey in response)) {
    throw new Error(`Expected data field "${String(dataKey)}" not found in response`);
  }

  return response[dataKey];
}

/**
 * Create a response handler for a specific entity type
 */
export function createResponseHandler<T extends StandardResponse>(
  entityName: string,
  operation: string
) {
  return (response: T, options?: Parameters<typeof handleStandardResponse>[1]) => {
    return handleStandardResponse(response, {
      successMessage: (data) => {
        if (options?.successMessage) {
          return typeof options.successMessage === 'function'
            ? options.successMessage(data)
            : options.successMessage;
        }
        return data.message || `${entityName} ${operation} successful`;
      },
      errorMessage: (data) => {
        if (options?.errorMessage) {
          return typeof options.errorMessage === 'function'
            ? options.errorMessage(data)
            : options.errorMessage;
        }
        return data.error || data.message || `Failed to ${operation} ${entityName}`;
      },
      ...options
    });
  };
}
