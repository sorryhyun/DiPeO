import React, { Suspense, useEffect, useState } from 'react';
import Routes from './routes/Routes';
import Spinner from './shared/components/Spinner';
import Header from './shared/components/Header';
import { useI18n } from './shared/hooks/useI18n';

const App: React.FC = (): JSX.Element => {
  // Initialize i18n translations
  useI18n();

  // Global search overlay state
  const [isSearchOpen, setSearchOpen] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Open search handler (used by keyboard shortcut as well as potential header interactions)
  const openSearch = (): void => {
    setSearchOpen(true);
    // Optionally focus input can be done here if we exposed a ref to the input element
  };

  const closeSearch = (): void => {
    setSearchOpen(false);
    setSearchQuery('');
  };

  // Global keyboard shortcut: Cmd/Ctrl + K to open search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent): void => {
      const isModPressed = e.metaKey || e.ctrlKey;
      if (isModPressed && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        openSearch();
      }
      if (e.key === 'Escape' && isSearchOpen) {
        closeSearch();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isSearchOpen]);

  // Simple global search overlay component
  const SearchOverlay = (): JSX.Element | null => {
    if (!isSearchOpen) return null;

    return (
      <div
        role="dialog"
        aria-label="Global search"
        className="fixed inset-0 z-50 bg-black/60 flex items-start justify-center pt-20"
        onClick={closeSearch}
      >
        <div
          className="bg-white dark:bg-gray-800 rounded-lg shadow-lg w-11/12 max-w-md p-4"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center gap-2">
            <span aria-hidden="true">🔎</span>
            <input
              autoFocus
              className="flex-1 bg-transparent outline-none border-none px-2 py-2 text-lg"
              placeholder="Search (press Enter to execute)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button
              className="ml-2 px-3 py-1 rounded bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600"
              onClick={closeSearch}
              aria-label="Close search"
            >
              Esc
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-white">
      <Header />
      <main className="px-4 py-2">
        <Suspense fallback={<Spinner />}>
          <Routes />
        </Suspense>
      </main>

      <SearchOverlay />
    </div>
  );
};

export default App;