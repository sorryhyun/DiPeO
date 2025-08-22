import React, { Suspense, useEffect, useState, createContext, useContext } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { I18nProvider } from '../shared/i18n/i18n';
import ProtectedRoute from './routes/ProtectedRoute';
import SignIn from '../../features/auth/components/SignIn';
import Dashboard from '../../features/dashboard/pages/Dashboard';
import '../styles/tailwind.css';

// Lightweight error boundary
class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean }> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(_error: any) {
    return { hasError: true };
  }

  componentDidCatch(error: any, info: any) {
    // You could log to an external service here
    console.error('Unhandled error:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div role="alert" aria-live="polite" style={{ padding: 16, color: '#991b1b' }}>
          Something went wrong. Please try again.
        </div>
      );
    }
    return this.props.children;
  }
}

// Simple loading fallback for Suspense
const LoadingFallback: React.FC = () => (
  <div style={{ padding: 16 }}>Loading...</div>
);

// Theme system (dark mode aware)
type Theme = 'light' | 'dark';
type ThemeContextValue = { theme: Theme; toggleTheme: () => void };

const ThemeContext = createContext<ThemeContextValue>({
  theme: 'light',
  toggleTheme: () => {},
});

const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<Theme>(() => {
    // Prefer localStorage, otherwise respect OS setting
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('theme') as Theme | null;
      if (saved === 'light' || saved === 'dark') return saved;
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
      }
    }
    return 'light';
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [theme]);

  useEffect(() => {
    try {
      localStorage.setItem('theme', theme);
    } catch {
      // ignore
    }
  }, [theme]);

  const toggleTheme = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'));

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('ThemeContext not available');
  return ctx;
}

// TanStack Query client with sensible defaults
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      cacheTime: 1000 * 60 * 30, // 30 minutes
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// Main application root
const AppRoot: React.FC = () => {
  // Optional: expose a toggle for quick manual theme switch (e.g., via a button somewhere in UI)
  const { theme, toggleTheme } = useTheme();

  // Service Worker registration for offline support (best-effort)
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      const shouldRegister = true; // could be tied to config/env in future
      if (shouldRegister) {
        navigator.serviceWorker
          .register('/service-worker.js')
          .then(() => {
            console.info('Service worker registered');
          })
          .catch((err) => {
            console.error('Service worker registration failed:', err);
          });
      }
    }
  }, []);

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <I18nProvider>
          <ThemeProvider>
            <BrowserRouter>
              <Suspense fallback={<LoadingFallback />}>
                <Routes>
                  <Route path="/signin" element={<SignIn />} />
                  <Route
                    path="/"
                    element={
                      <ProtectedRoute>
                        <Dashboard />
                      </ProtectedRoute>
                    }
                  />
                  <Route path="*" element={<Navigate to="/" />} />
                </Routes>
              </Suspense>
            </BrowserRouter>
          </ThemeProvider>
        </I18nProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

// Render to DOM
const rootEl = document.getElementById('root');
if (rootEl) {
  const root = createRoot(rootEl);
  root.render(
    <React.StrictMode>
      <AppRoot />
    </React.StrictMode>
  );
}