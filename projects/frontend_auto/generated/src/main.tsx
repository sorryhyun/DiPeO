import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { QueryProvider } from './shared/context/QueryProvider';
import { AuthProvider } from './shared/context/AuthContext';
import { SocketProvider } from './shared/context/SocketProvider';
import { ThemeProvider } from './shared/context/ThemeProvider';
import ErrorBoundary from './shared/context/ErrorBoundary';
import config from './config';

const bootstrap = async (): Promise<void> => {
  try {
    const devMode = (config as any)?.development_mode;
    if (devMode && devMode.enable_mock_data) {
      const mod = await import('./mocks/mockServer');
      const startMockServer = (mod as any).startMockServer;
      if (typeof startMockServer === 'function') {
        await startMockServer();
      }
    }
  } catch (error) {
    console.error('Failed to initialize mock server:', error);
  }

  const rootContainer = document.getElementById('root');
  if (!rootContainer) {
    throw new Error('Root element with id "root" not found');
  }

  const root = createRoot(rootContainer);
  root.render(
    <React.StrictMode>
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
    </React.StrictMode>
  );
};

bootstrap().catch((err) => {
  console.error('Application bootstrap failed:', err);
});

export {};