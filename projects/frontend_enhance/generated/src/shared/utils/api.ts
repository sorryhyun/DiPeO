import { getApiBaseUrl, isDevelopment } from '../../app/config/config';

// Types for API responses and requests
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: number;
}

export interface ApiError {
  message: string;
  status: number;
  details?: any;
}

export interface RequestOptions {
  headers?: Record<string, string>;
  timeout?: number;
  retries?: number;
}

// Custom error class for API errors
export class ApiRequestError extends Error {
  status: number;
  details?: any;

  constructor(message: string, status: number, details?: any) {
    super(message);
    this.name = 'ApiRequestError';
    this.status = status;
    this.details = details;
  }
}

// Token management
let authToken: string | null = null;

export const setAuthToken = (token: string | null): void => {
  authToken = token;
  if (token) {
    localStorage.setItem('auth_token', token);
  } else {
    localStorage.removeItem('auth_token');
  }
};

export const getAuthToken = (): string | null => {
  if (authToken) return authToken;
  
  // Try to get from localStorage on initialization
  const storedToken = localStorage.getItem('auth_token');
  if (storedToken) {
    authToken = storedToken;
    return storedToken;
  }
  
  return null;
};

// Default headers
const getDefaultHeaders = (): Record<string, string> => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };

  const token = getAuthToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return headers;
};

// Request timeout helper
const withTimeout = <T>(promise: Promise<T>, ms: number): Promise<T> => {
  const timeout = new Promise<never>((_, reject) =>
    setTimeout(() => reject(new Error('Request timeout')), ms)
  );
  return Promise.race([promise, timeout]);
};

// Mock data for development
const getMockData = (url: string): any => {
  const isDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  
  if (!isDev) return null;
  
  // Dashboard metrics mock
  if (url.includes('/api/dashboard/metrics')) {
    return {
      totalUsers: 15234,
      activeUsers: 3421,
      revenue: 485920,
      growth: 12.5
    };
  }
  
  // Dashboard data mock
  if (url.includes('/api/dashboard/data')) {
    return [
      { id: '1', name: 'Product Sales', status: 'active', value: 125000, lastUpdated: new Date(Date.now() - 3600000).toISOString() },
      { id: '2', name: 'User Signups', status: 'active', value: 543, lastUpdated: new Date(Date.now() - 7200000).toISOString() },
      { id: '3', name: 'API Requests', status: 'active', value: 892341, lastUpdated: new Date(Date.now() - 1800000).toISOString() },
      { id: '4', name: 'Error Rate', status: 'inactive', value: 0.23, lastUpdated: new Date(Date.now() - 600000).toISOString() },
      { id: '5', name: 'Response Time', status: 'active', value: 145, lastUpdated: new Date(Date.now() - 300000).toISOString() },
    ];
  }
  
  // Dashboard charts mock
  if (url.includes('/api/dashboard/charts')) {
    const now = Date.now();
    return Array.from({ length: 12 }, (_, i) => ({
      name: `Point ${i + 1}`,
      value: Math.floor(Math.random() * 100) + 50,
      timestamp: new Date(now - (11 - i) * 3600000).toISOString()
    }));
  }
  
  return null;
};

// Base request function with error handling
const makeRequest = async <T>(
  url: string,
  options: RequestInit & RequestOptions = {}
): Promise<T> => {
  const { headers, timeout = 10000, retries = 1, ...fetchOptions } = options;
  
  const fullUrl = url.startsWith('http') ? url : `${getApiBaseUrl()}${url}`;
  
  // Check for mock data in development
  const mockData = getMockData(fullUrl);
  if (mockData !== null) {
    if (isDevelopment()) {
      console.log(`[API] [MOCK] ${fetchOptions.method || 'GET'} ${fullUrl}`, mockData);
    }
    return Promise.resolve(mockData);
  }
  
  const requestHeaders = {
    ...getDefaultHeaders(),
    ...headers,
  };

  let lastError: Error;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      if (isDevelopment()) {
        console.log(`[API] ${fetchOptions.method || 'GET'} ${fullUrl}`, {
          headers: requestHeaders,
          body: fetchOptions.body,
        });
      }

      const response = await withTimeout(
        fetch(fullUrl, {
          ...fetchOptions,
          headers: requestHeaders,
        }),
        timeout
      );

      // Handle different response statuses
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        let errorDetails;

        try {
          const errorBody = await response.text();
          if (errorBody) {
            try {
              errorDetails = JSON.parse(errorBody);
              errorMessage = errorDetails.message || errorMessage;
            } catch {
              errorMessage = errorBody;
            }
          }
        } catch {
          // If we can't read the error body, use the default message
        }

        throw new ApiRequestError(errorMessage, response.status, errorDetails);
      }

      // Handle empty responses
      const contentLength = response.headers.get('content-length');
      if (contentLength === '0' || !response.headers.get('content-type')?.includes('json')) {
        return {} as T;
      }

      const data = await response.json();
      
      if (isDevelopment()) {
        console.log(`[API] Response:`, data);
      }

      return data;
    } catch (error) {
      lastError = error as Error;
      
      if (isDevelopment()) {
        console.error(`[API] Request failed (attempt ${attempt + 1}/${retries + 1}):`, error);
      }

      // Don't retry on authentication errors or client errors (4xx)
      if (error instanceof ApiRequestError && error.status >= 400 && error.status < 500) {
        throw error;
      }

      // Don't retry on the last attempt
      if (attempt === retries) {
        throw error;
      }

      // Wait before retrying (exponential backoff)
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
    }
  }

  throw lastError!;
};

// API methods
const api = {
  // GET request
  get: async <T = any>(url: string, options: RequestOptions = {}): Promise<T> => {
    return makeRequest<T>(url, {
      method: 'GET',
      ...options,
    });
  },

  // POST request
  post: async <T = any>(
    url: string,
    data?: any,
    options: RequestOptions = {}
  ): Promise<T> => {
    return makeRequest<T>(url, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    });
  },

  // PUT request
  put: async <T = any>(
    url: string,
    data?: any,
    options: RequestOptions = {}
  ): Promise<T> => {
    return makeRequest<T>(url, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    });
  },

  // PATCH request
  patch: async <T = any>(
    url: string,
    data?: any,
    options: RequestOptions = {}
  ): Promise<T> => {
    return makeRequest<T>(url, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    });
  },

  // DELETE request
  delete: async <T = any>(url: string, options: RequestOptions = {}): Promise<T> => {
    return makeRequest<T>(url, {
      method: 'DELETE',
      ...options,
    });
  },

  // Upload file
  upload: async <T = any>(
    url: string,
    formData: FormData,
    options: Omit<RequestOptions, 'headers'> & { 
      headers?: Omit<Record<string, string>, 'Content-Type'> 
    } = {}
  ): Promise<T> => {
    const { headers, ...restOptions } = options;
    const token = getAuthToken();
    
    const uploadHeaders: Record<string, string> = {
      ...(headers || {}),
    };
    
    if (token) {
      uploadHeaders.Authorization = `Bearer ${token}`;
    }

    return makeRequest<T>(url, {
      method: 'POST',
      body: formData,
      headers: uploadHeaders,
      ...restOptions,
    });
  },
};

// Export default and named exports
export default api;
export { api };