import React, { useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { QueryProvider } from './shared/context/QueryProvider';
import { AuthProvider } from './shared/context/AuthContext';
import { SocketProvider } from './shared/context/SocketProvider';
import { ThemeProvider } from './shared/context/ThemeProvider';
import ErrorBoundary from './shared/context/ErrorBoundary';
import config from './config';

const AppRoot: React.FC = () => {
  useEffect(() => {
    let isMounted = true;
    (async () => {
      try {
        const cfg: any = config;
        const enableMock =
          !!(cfg?.development_mode?.enable_mock_data) ||
          !!(cfg?.developmentMode?.enable_mock_data);

        if (enableMock && isMounted) {
          const module = await import('./mocks/mockServer');
          if (module && typeof module.startMockServer === 'function') {
            await module.startMockServer();
          }
        }
      } catch (err) {
        // Best-effort logging; mock server is non-critical for app startup
        console.error('Failed to initialize mock server:', err);
      }
    })();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <ErrorBoundary>
      <QueryProvider>
        <AuthProvider>
          <ThemeProvider>
            <SocketProvider>
              <App />
            </SocketProvider>
          </ThemeProvider>
        </AuthProvider>
      </QueryProvider>
    </ErrorBoundary>
  );
};

const rootEl = document.getElementById('root');
if (!rootEl) {
  throw new Error('Root element with id "root" not found');
}

const root = createRoot(rootEl);
root.render(
  <React.StrictMode>
    <AppRoot />
  </React.StrictMode>
);