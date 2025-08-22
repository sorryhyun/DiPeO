import { useCallback } from 'react';
import { useAuthContext, AuthContextType } from '../context/AuthContext';
import { logger } from '../../../shared/utils/logger';

// Extended auth hook interface with additional utility methods
export interface UseAuthReturn extends AuthContextType {
  // Convenience methods
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  isAdmin: () => boolean;
  canAccess: (requiredRole?: string) => boolean;
  
  // User info utilities
  getUserInitials: () => string;
  getFullName: () => string;
  getUserEmail: () => string;
  
  // Token utilities
  getTokenTimeRemaining: () => number;
  isTokenExpired: () => boolean;
  
  // Profile utilities
  getUserPreference: (key: string, defaultValue?: any) => any;
  setUserPreference: (key: string, value: any) => Promise<void>;
}

// Role hierarchy for permissions
const ROLE_HIERARCHY = {
  'admin': ['admin', 'manager', 'user'],
  'manager': ['manager', 'user'],
  'user': ['user'],
} as const;

/**
 * Enhanced authentication hook that provides authentication state and methods
 * along with additional utility functions for role-based access control,
 * user information, and token management.
 */
export const useAuth = (): UseAuthReturn => {
  const authContext = useAuthContext();
  
  const {
    user,
    token,
    tokenExpiry,
    isAuthenticated,
    login,
    logout,
    refreshToken,
    clearError,
    isTokenNearExpiry,
    updateUserProfile,
    isLoading,
    error,
  } = authContext;

  // Role-based access control methods
  const hasRole = useCallback((role: string): boolean => {
    if (!user || !user.role) return false;
    
    const userRoles = ROLE_HIERARCHY[user.role as keyof typeof ROLE_HIERARCHY] || [user.role];
    return userRoles.some(r => r === role);
  }, [user]);

  const hasAnyRole = useCallback((roles: string[]): boolean => {
    return roles.some(role => hasRole(role));
  }, [hasRole]);

  const isAdmin = useCallback((): boolean => {
    return hasRole('admin');
  }, [hasRole]);

  const canAccess = useCallback((requiredRole?: string): boolean => {
    if (!isAuthenticated) return false;
    if (!requiredRole) return true;
    return hasRole(requiredRole);
  }, [isAuthenticated, hasRole]);

  // User information utilities
  const getUserInitials = useCallback((): string => {
    if (!user || !user.name) return '';
    
    const nameParts = user.name.trim().split(' ');
    if (nameParts.length === 1) {
      return nameParts[0].charAt(0).toUpperCase();
    }
    
    return (nameParts[0].charAt(0) + nameParts[nameParts.length - 1].charAt(0)).toUpperCase();
  }, [user]);

  const getFullName = useCallback((): string => {
    return user?.name || '';
  }, [user]);

  const getUserEmail = useCallback((): string => {
    return user?.email || '';
  }, [user]);

  // Token utilities
  const getTokenTimeRemaining = useCallback((): number => {
    if (!tokenExpiry) return 0;
    const remaining = tokenExpiry - Date.now();
    return Math.max(0, remaining);
  }, [tokenExpiry]);

  const isTokenExpired = useCallback((): boolean => {
    if (!tokenExpiry) return true;
    return Date.now() >= tokenExpiry;
  }, [tokenExpiry]);

  // User preferences utilities
  const getUserPreference = useCallback((key: string, defaultValue: any = null): any => {
    if (!user?.preferences) return defaultValue;
    return user.preferences[key] ?? defaultValue;
  }, [user]);

  const setUserPreference = useCallback(async (key: string, value: any): Promise<void> => {
    if (!user) {
      throw new Error('User not authenticated');
    }

    try {
      const currentPreferences = user.preferences || {};
      const updatedPreferences = {
        ...currentPreferences,
        [key]: value,
      };

      await updateUserProfile({
        preferences: updatedPreferences,
      });

      logger.info('User preference updated', { key, value }, 'auth');
    } catch (error) {
      logger.error('Failed to update user preference', { key, value, error }, 'auth');
      throw error;
    }
  }, [user, updateUserProfile]);

  // Enhanced login with additional logging and error handling
  const enhancedLogin = useCallback(async (email: string, password: string): Promise<void> => {
    try {
      await login(email, password);
      logger.info('User login successful', { email }, 'auth');
    } catch (error) {
      logger.error('User login failed', { email, error }, 'auth');
      throw error;
    }
  }, [login]);

  // Enhanced logout with cleanup
  const enhancedLogout = useCallback((): void => {
    const userEmail = getUserEmail();
    logout();
    logger.info('User logout completed', { email: userEmail }, 'auth');
  }, [logout, getUserEmail]);

  // Enhanced token refresh with retry logic
  const enhancedRefreshToken = useCallback(async (retries: number = 1): Promise<void> => {
    let lastError: Error | undefined;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        await refreshToken();
        return;
      } catch (error) {
        lastError = error as Error;
        
        if (attempt < retries) {
          const delay = Math.pow(2, attempt) * 1000; // Exponential backoff
          await new Promise(resolve => setTimeout(resolve, delay));
          logger.warn(`Token refresh attempt ${attempt + 1} failed, retrying...`, error, 'auth');
        }
      }
    }

    logger.error('Token refresh failed after all retries', lastError, 'auth');
    throw lastError || new Error('Token refresh failed');
  }, [refreshToken]);

  return {
    // Original auth context values
    user,
    token,
    tokenExpiry,
    isAuthenticated,
    isLoading,
    error,
    clearError,
    updateUserProfile,

    // Enhanced methods
    login: enhancedLogin,
    logout: enhancedLogout,
    refreshToken: enhancedRefreshToken,
    isTokenNearExpiry,

    // Role-based access control
    hasRole,
    hasAnyRole,
    isAdmin,
    canAccess,

    // User information utilities
    getUserInitials,
    getFullName,
    getUserEmail,

    // Token utilities
    getTokenTimeRemaining,
    isTokenExpired,

    // User preferences
    getUserPreference,
    setUserPreference,
  };
};

export default useAuth;

