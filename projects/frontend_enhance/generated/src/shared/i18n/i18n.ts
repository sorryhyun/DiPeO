import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Define translation resources
const resources = {
  en: {
    translation: {
      // Auth
      'auth.signIn': 'Sign In',
      'auth.signOut': 'Sign Out',
      'auth.email': 'Email',
      'auth.password': 'Password',
      'auth.rememberMe': 'Remember me',
      'auth.forgotPassword': 'Forgot password?',
      'auth.signInButton': 'Sign in to your account',
      'auth.invalidCredentials': 'Invalid email or password',
      'auth.networkError': 'Network error. Please try again.',

      // Dashboard
      'dashboard.title': 'Dashboard',
      'dashboard.welcome': 'Welcome back',
      'dashboard.overview': 'Overview',
      'dashboard.analytics': 'Analytics',
      'dashboard.reports': 'Reports',
      'dashboard.settings': 'Settings',
      'dashboard.profile': 'Profile',

      // Data Table
      'table.search': 'Search...',
      'table.filter': 'Filter',
      'table.export': 'Export',
      'table.refresh': 'Refresh',
      'table.noData': 'No data available',
      'table.loading': 'Loading...',
      'table.error': 'Error loading data',
      'table.rowsPerPage': 'Rows per page',
      'table.page': 'Page',
      'table.of': 'of',

      // Live Updates
      'liveUpdates.title': 'Live Updates',
      'liveUpdates.connected': 'Connected',
      'liveUpdates.connecting': 'Connecting...',
      'liveUpdates.disconnected': 'Disconnected',
      'liveUpdates.error': 'Connection error',
      'liveUpdates.reconnecting': 'Reconnecting...',
      'liveUpdates.lastUpdate': 'Last update',

      // Chart Card
      'chart.loading': 'Loading chart data...',
      'chart.error': 'Error loading chart',
      'chart.noData': 'No chart data available',
      'chart.refresh': 'Refresh chart',

      // Common
      'common.loading': 'Loading...',
      'common.error': 'Error',
      'common.retry': 'Retry',
      'common.cancel': 'Cancel',
      'common.save': 'Save',
      'common.close': 'Close',
      'common.ok': 'OK',
      'common.yes': 'Yes',
      'common.no': 'No',
      'common.delete': 'Delete',
      'common.edit': 'Edit',
      'common.create': 'Create',
      'common.update': 'Update',

      // Theme
      'theme.light': 'Light mode',
      'theme.dark': 'Dark mode',
      'theme.system': 'System theme',
      'theme.toggle': 'Toggle theme',

      // Errors
      'error.generic': 'Something went wrong',
      'error.network': 'Network connection error',
      'error.unauthorized': 'Unauthorized access',
      'error.forbidden': 'Access forbidden',
      'error.notFound': 'Page not found',
      'error.serverError': 'Server error',
      'error.tryAgain': 'Try again',
    },
  },
};

// Initialize i18next
i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'en', // Default language
    fallbackLng: 'en',
    
    interpolation: {
      escapeValue: false, // React already does escaping
    },

    // Detection options
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
      lookupLocalStorage: 'i18nextLng',
    },

    // React specific options
    react: {
      useSuspense: false,
    },

    // Debug in development
    debug: process.env.NODE_ENV === 'development',
  });

export { i18n };
export default i18n;