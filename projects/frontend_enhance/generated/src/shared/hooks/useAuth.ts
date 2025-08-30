import React, { useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';

/**
 * Typed return shape for useAuth hook.
 * Exposes current user, authentication status and actions.
 */
type User = {
  id: string;
  email: string;
  role: string;
  token: string;
  expiresAt: string;
};

export interface AuthContextValue {
  currentUser?: User;
  isAuthenticated: boolean;
  hasRole: (role: string) => boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

/**
 * Hook: useAuth
 * - Consumes AuthContext and returns a strongly-typed AuthContextValue
 * - Throws a descriptive error if used outside an AuthProvider
 * - Provides convenient access to currentUser, isAuthenticated, and actions
 */
const useAuth = (): AuthContextValue => {
  const context = useContext<AuthContextValue | undefined>(AuthContext as any);

  if (!context) {
    throw new Error(
      'useAuth must be used within an AuthProvider. Ensure your app is wrapped with <AuthProvider>.'
    );
  }

  return context;
};

export default useAuth;
export { useAuth };