import React, { createContext, useContext, useReducer, useEffect, useCallback } from 'react';
import { setAuthToken, getAuthToken, api } from '../../../shared/utils/api';
import { logger } from '../../../shared/utils/logger';

// User interface
export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  avatar?: string;
  preferences?: Record<string, any>;
}

// Auth state interface
export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  tokenExpiry: number | null;
  isLoading: boolean;
  error: string | null;
}

// Auth context interface
export interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  clearError: () => void;
  isTokenNearExpiry: () => boolean;
  updateUserProfile: (updates: Partial<User>) => Promise<void>;
}

// Action types for auth reducer
type AuthAction =
  | { type: 'AUTH_START' }
  | { type: 'AUTH_SUCCESS'; payload: { user: User; token: string; tokenExpiry: number } }
  | { type: 'AUTH_FAILURE'; payload: string }
  | { type: 'AUTH_LOGOUT' }
  | { type: 'AUTH_REFRESH_SUCCESS'; payload: { token: string; tokenExpiry: number } }
  | { type: 'AUTH_CLEAR_ERROR' }
  | { type: 'AUTH_UPDATE_USER'; payload: Partial<User> };

// Initial auth state
const initialAuthState: AuthState = {
  isAuthenticated: false,
  user: null,
  token: null,
  tokenExpiry: null,
  isLoading: true, // Start as loading to check existing auth
  error: null,
};

// Auth reducer
const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'AUTH_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      };

    case 'AUTH_SUCCESS':
      return {
        ...state,
        isAuthenticated: true,
        user: action.payload.user,
        token: action.payload.token,
        tokenExpiry: action.payload.tokenExpiry,
        isLoading: false,
        error: null,
      };

    case 'AUTH_FAILURE':
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        token: null,
        tokenExpiry: null,
        isLoading: false,
        error: action.payload,
      };

    case 'AUTH_LOGOUT':
      return {
        ...initialAuthState,
        isLoading: false,
      };

    case 'AUTH_REFRESH_SUCCESS':
      return {
        ...state,
        token: action.payload.token,
        tokenExpiry: action.payload.tokenExpiry,
        error: null,
      };

    case 'AUTH_CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };

    case 'AUTH_UPDATE_USER':
      return {
        ...state,
        user: state.user ? { ...state.user, ...action.payload } : null,
      };

    default:
      return state;
  }
};

// Create auth context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Token expiry constants
const TOKEN_EXPIRY_BUFFER = 5 * 60 * 1000; // 5 minutes in milliseconds
const TOKEN_REFRESH_INTERVAL = 15 * 60 * 1000; // 15 minutes in milliseconds

// Auth provider component
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialAuthState);

  // Check if token is near expiry
  const isTokenNearExpiry = useCallback((): boolean => {
    if (!state.tokenExpiry) return false;
    return Date.now() + TOKEN_EXPIRY_BUFFER >= state.tokenExpiry;
  }, [state.tokenExpiry]);

  // Refresh auth token
  const refreshToken = useCallback(async (): Promise<void> => {
    try {
      logger.debug('Attempting to refresh auth token', undefined, 'auth');
      
      const currentToken = getAuthToken();
      const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      
      // Handle mock token refresh
      if (isDevelopment && currentToken?.startsWith('mock-jwt-token-')) {
        const newMockToken = 'mock-jwt-token-' + Date.now();
        const tokenExpiry = Date.now() + 24 * 60 * 60 * 1000; // 24 hours from now
        
        setAuthToken(newMockToken);
        
        dispatch({
          type: 'AUTH_REFRESH_SUCCESS',
          payload: {
            token: newMockToken,
            tokenExpiry,
          },
        });
        
        logger.info('Mock token refreshed successfully', undefined, 'auth');
        return;
      }
      
      // Real API call (will fail if backend is not running)
      const response = await api.post('/api/auth/refresh');
      
      if (response.token && response.expiresAt) {
        const tokenExpiry = new Date(response.expiresAt).getTime();
        setAuthToken(response.token);
        
        dispatch({
          type: 'AUTH_REFRESH_SUCCESS',
          payload: {
            token: response.token,
            tokenExpiry,
          },
        });
        
        logger.info('Token refreshed successfully', undefined, 'auth');
      } else {
        throw new Error('Invalid refresh response');
      }
    } catch (error) {
      logger.error('Failed to refresh token', error, 'auth');
      // Don't dispatch failure here - let the caller handle it
      throw error;
    }
  }, []);

  // Login function
  const login = useCallback(async (email: string, password: string): Promise<void> => {
    dispatch({ type: 'AUTH_START' });
    
    try {
      logger.debug('Attempting login', { email }, 'auth');
      
      // MOCK AUTHENTICATION FOR DEVELOPMENT
      // Test credentials:
      // - admin@example.com / admin123 (Admin role)
      // - user@example.com / user123 (User role)  
      // - test@test.com / test123 (User role)
      
      const mockUsers: Record<string, { password: string; role: string; name: string }> = {
        'admin@example.com': { password: 'admin123', role: 'admin', name: 'Admin User' },
        'user@example.com': { password: 'user123', role: 'user', name: 'Regular User' },
        'test@test.com': { password: 'test123', role: 'user', name: 'Test User' },
      };
      
      // Check if we're in development mode
      const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      
      if (isDevelopment && mockUsers[email]) {
        // Mock authentication
        if (mockUsers[email].password === password) {
          const mockToken = 'mock-jwt-token-' + Date.now();
          const mockUser: User = {
            id: Math.random().toString(36).substr(2, 9),
            email,
            name: mockUsers[email].name,
            role: mockUsers[email].role,
            preferences: {},
          };
          const tokenExpiry = Date.now() + 24 * 60 * 60 * 1000; // 24 hours from now
          
          setAuthToken(mockToken);
          
          // Store user data for persistence
          localStorage.setItem('auth_user', JSON.stringify(mockUser));
          
          dispatch({
            type: 'AUTH_SUCCESS',
            payload: {
              user: mockUser,
              token: mockToken,
              tokenExpiry,
            },
          });
          
          logger.info('Login successful (mock)', { userId: mockUser.id }, 'auth');
          return;
        } else {
          throw new Error('Invalid password');
        }
      }
      
      // Real API call (will fail if backend is not running)
      const response = await api.post('/api/auth/login', { email, password });
      
      if (response.user && response.token && response.expiresAt) {
        const tokenExpiry = new Date(response.expiresAt).getTime();
        setAuthToken(response.token);
        
        dispatch({
          type: 'AUTH_SUCCESS',
          payload: {
            user: response.user,
            token: response.token,
            tokenExpiry,
          },
        });
        
        logger.info('Login successful', { userId: response.user.id }, 'auth');
      } else {
        throw new Error('Invalid login response');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      logger.error('Login failed', error, 'auth');
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
      throw error;
    }
  }, []);

  // Logout function
  const logout = useCallback((): void => {
    logger.info('User logging out', undefined, 'auth');
    
    // Clear token and user data from storage
    setAuthToken(null);
    localStorage.removeItem('auth_user');
    
    // Only attempt to notify server if not using mock auth
    const currentToken = getAuthToken();
    const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    
    if (!isDevelopment || !currentToken?.startsWith('mock-jwt-token-')) {
      // Attempt to notify server about logout (fire and forget)
      api.post('/api/auth/logout').catch((error) => {
        logger.warn('Failed to notify server about logout', error, 'auth');
      });
    }
    
    dispatch({ type: 'AUTH_LOGOUT' });
  }, []);

  // Clear error function
  const clearError = useCallback((): void => {
    dispatch({ type: 'AUTH_CLEAR_ERROR' });
  }, []);

  // Update user profile
  const updateUserProfile = useCallback(async (updates: Partial<User>): Promise<void> => {
    try {
      logger.debug('Updating user profile', updates, 'auth');
      
      const response = await api.patch('/api/user/profile', updates);
      
      if (response.user) {
        dispatch({
          type: 'AUTH_UPDATE_USER',
          payload: response.user,
        });
        
        logger.info('User profile updated successfully', undefined, 'auth');
      }
    } catch (error) {
      logger.error('Failed to update user profile', error, 'auth');
      throw error;
    }
  }, []);

  // Verify existing token on app start
  const verifyExistingToken = useCallback(async (): Promise<void> => {
    const existingToken = getAuthToken();
    
    if (!existingToken) {
      dispatch({ type: 'AUTH_FAILURE', payload: 'No existing token' });
      return;
    }

    try {
      logger.debug('Verifying existing token', undefined, 'auth');
      
      // Check if we're in development mode and using mock auth
      const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      
      if (isDevelopment && existingToken.startsWith('mock-jwt-token-')) {
        // Mock token verification - restore from localStorage
        const storedUser = localStorage.getItem('auth_user');
        
        if (storedUser) {
          const user = JSON.parse(storedUser);
          const tokenExpiry = Date.now() + 24 * 60 * 60 * 1000; // 24 hours from now
          
          dispatch({
            type: 'AUTH_SUCCESS',
            payload: {
              user,
              token: existingToken,
              tokenExpiry,
            },
          });
          
          logger.info('Mock token verified successfully', { userId: user.id }, 'auth');
          return;
        } else {
          throw new Error('No user data found for mock token');
        }
      }
      
      // Real API verification (will fail if backend is not running)
      const response = await api.get('/api/auth/verify');
      
      if (response.user && response.expiresAt) {
        const tokenExpiry = new Date(response.expiresAt).getTime();
        
        dispatch({
          type: 'AUTH_SUCCESS',
          payload: {
            user: response.user,
            token: existingToken,
            tokenExpiry,
          },
        });
        
        logger.info('Existing token verified successfully', { userId: response.user.id }, 'auth');
      } else {
        throw new Error('Invalid verification response');
      }
    } catch (error) {
      logger.warn('Token verification failed', error, 'auth');
      setAuthToken(null);
      dispatch({ type: 'AUTH_FAILURE', payload: 'Token verification failed' });
    }
  }, []);

  // Check and refresh token periodically
  useEffect(() => {
    if (!state.isAuthenticated) return;

    const interval = setInterval(() => {
      if (isTokenNearExpiry()) {
        refreshToken().catch((error) => {
          logger.error('Automatic token refresh failed', error, 'auth');
          // If refresh fails, we might need to log the user out
          logout();
        });
      }
    }, TOKEN_REFRESH_INTERVAL);

    return () => clearInterval(interval);
  }, [state.isAuthenticated, isTokenNearExpiry, refreshToken, logout]);

  // Verify existing token on mount
  useEffect(() => {
    verifyExistingToken();
  }, [verifyExistingToken]);

  // Context value
  const contextValue: AuthContextType = {
    ...state,
    login,
    logout,
    refreshToken,
    clearError,
    isTokenNearExpiry,
    updateUserProfile,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook to use auth context
export const useAuthContext = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;