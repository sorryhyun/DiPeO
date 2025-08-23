import React, { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';
import * as realAuthService from '../services/authService';
import { mockAuthUsers } from '../../dev/mocks/mockData';

type AuthUser = {
  id: string;
  email: string;
  role: string;
  token: string;
  expiresAt: string;
};

type AuthContextValue = {
  currentUser?: AuthUser;
  isAuthenticated: boolean;
  hasRole: (role: string) => boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
};

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const getAuthContext = (): React.Context<AuthContextValue | undefined> => AuthContext;

/**
 * Helpers for lightweight localStorage persistence in development.
 * Persistence is toggled via DEV_USE_LOCALSTORAGE_PERSISTENCE env flag or defaults to development mode.
 */
const STORAGE_KEY_USER = 'auth_user';
const SHOULD_PERSIST_STORAGE = (): boolean => {
  try {
    const envFlag = (process.env as any).DEV_USE_LOCALSTORAGE_PERSISTENCE;
    if (typeof envFlag === 'boolean') return envFlag;
    if (typeof envFlag === 'string') return envFlag.toLowerCase() === 'true';
  } catch {
    // ignore
  }
  // Default to persistence in development
  try {
    return process.env.NODE_ENV === 'development';
  } catch {
    return false;
  }
};

const loadFromStorage = (): AuthUser | undefined => {
  if (!SHOULD_PERSIST_STORAGE()) return undefined;
  try {
    const raw = localStorage.getItem(STORAGE_KEY_USER);
    if (!raw) return undefined;
    const user = JSON.parse(raw) as AuthUser;
    if (user?.expiresAt && new Date(user.expiresAt) > new Date()) {
      return user;
    }
    // expired
    localStorage.removeItem(STORAGE_KEY_USER);
    return undefined;
  } catch {
    return undefined;
  }
};

const saveToStorage = (user: AuthUser) => {
  if (!SHOULD_PERSIST_STORAGE()) return;
  try {
    localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(user));
  } catch {
    // ignore
  }
};

const clearStorage = () => {
  if (!SHOULD_PERSIST_STORAGE()) return;
  try {
    localStorage.removeItem(STORAGE_KEY_USER);
  } catch {
    // ignore
  }
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<AuthUser | undefined>(undefined);
  const expiryTimer = useRef<number | null>(null);
  const [hydrated, setHydrated] = useState(false);

  // Determine mock mode
  const isMockEnabled = useMemo(() => {
    // Try global dev config
    try {
      const g = (window as any).__DEV_CONFIG__;
      if (g && typeof g.enable_mock_data === 'boolean') return g.enable_mock_data;
    } catch {
      // ignore
    }
    // Try env var
    try {
      const v = (process.env as any).DEV_MOCK_DATA;
      if (typeof v === 'boolean') return v;
      if (typeof v === 'string') return v.toLowerCase() === 'true';
    } catch {
      // ignore
    }
    // Default to development mode
    try {
      return process.env.NODE_ENV === 'development';
    } catch {
      return false;
    }
  }, []);

  // Persist setting (development-only)
  const SHOULD_PERSIST = SHOULD_PERSIST_STORAGE();

  // Load persisted user on mount
  useEffect(() => {
    const stored = loadFromStorage();
    if (stored) {
      if (new Date(stored.expiresAt) > new Date()) {
        setCurrentUser(stored);
        scheduleExpiry(stored.expiresAt);
      } else {
        // expired
        clearStorage();
      }
    }
    setHydrated(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const scheduleExpiry = (expiresAt: string) => {
    if (expiryTimer.current) window.clearTimeout(expiryTimer.current);
    const ms = new Date(expiresAt).getTime() - Date.now();
    if (ms > 0) {
      expiryTimer.current = window.setTimeout(() => {
        // Auto sign-out on expiry
        signOut().catch(() => {});
      }, ms) as unknown as number;
    }
  };

  const signIn = async (email: string, password: string): Promise<void> => {
    if (isMockEnabled) {
      const found = mockAuthUsers.find(
        (u) => u.email.toLowerCase() === email.toLowerCase() && u.password === password
      );
      if (!found) throw new Error('Invalid credentials');
      const token = `mock-token-${found.id}`;
      const expiresAt = new Date(Date.now() + 60 * 60 * 1000).toISOString(); // 1 hour validity
      const user: AuthUser = {
        id: found.id,
        email: found.email,
        role: found.role,
        token,
        expiresAt,
      };
      setCurrentUser(user);
      if (SHOULD_PERSIST) saveToStorage(user);
      scheduleExpiry(expiresAt);
      return;
    }

    // Real API call
    const data = await realAuthService.signIn(email, password);
    // Expected data shape: { id, email, role, token, expiresIn }
    const expiresIn = typeof data?.expiresIn === 'number' ? data.expiresIn : 3600;
    const expiresAt = new Date(Date.now() + expiresIn * 1000).toISOString();
    const user: AuthUser = {
      id: data.id,
      email: data.email,
      role: data.role,
      token: data.token,
      expiresAt,
    };
    setCurrentUser(user);
    if (SHOULD_PERSIST) saveToStorage(user);
    scheduleExpiry(expiresAt);
  };

  const signOut = async (): Promise<void> => {
    setCurrentUser(undefined);
    if (expiryTimer.current) {
      window.clearTimeout(expiryTimer.current);
      expiryTimer.current = null;
    }
    clearStorage();
    try {
      await realAuthService.signOut?.();
    } catch {
      // ignore errors on sign out
    }
  };

  const hasRole = (role: string) => {
    if (!currentUser) return false;
    // Simple role check; could be extended to support hierarchical roles
    return currentUser.role === role;
  };

  const value = useMemo(
    (): AuthContextValue => ({
      currentUser,
      isAuthenticated: Boolean(currentUser),
      hasRole,
      signIn,
      signOut,
    }),
    [currentUser]
  );

  if (!hydrated) {
    // Optionally render nothing or a fallback; keep empty during hydration to avoid flicker
    return null;
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};