import React, { Suspense, useEffect, useState } from 'react';
import Spinner from './shared/components/Spinner';
import Header from './shared/components/Header';
import useI18n from './shared/hooks/useI18n';
import Routes from './routes/Routes';

const App: React.FC = () => {
  // Initialize i18n resources
  useI18n();

  // Local UI state for global search openness (triggered by shortcut)
  const [isSearchOpen, setSearchOpen] = useState<boolean>(false);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      const isMac = navigator.platform.toLowerCase().includes('mac');
      const modKeyPressed = isMac ? e.metaKey : e.ctrlKey;
      const key = e.key.toLowerCase();

      // Cmd/Ctrl + K to toggle global search
      if (modKeyPressed && key === 'k') {
        e.preventDefault();
        const nextOpen = !isSearchOpen;
        setSearchOpen(nextOpen);
        // Notify any global search listeners without coupling
        window.dispatchEvent(
          new CustomEvent<{ open: boolean }>('OPEN_SEARCH', { detail: { open: nextOpen } })
        );
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [isSearchOpen]);

  return (
    <div className="min-h-screen bg-white text-gray-900 dark:bg-gray-900 dark:text-gray-100">
      <Header />
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Suspense fallback={<Spinner />}>
          <Routes />
        </Suspense>
      </main>
    </div>
  );
};

export default App;