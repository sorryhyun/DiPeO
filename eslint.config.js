import js from '@eslint/js';
import typescript from '@typescript-eslint/eslint-plugin';
import typescriptParser from '@typescript-eslint/parser';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import globals from 'globals';

export default [
  // Ignore patterns
  {
    ignores: [
      '**/dist/**',
      '**/build/**',
      '**/node_modules/**',
      '**/.turbo/**',
      '**/coverage/**',
      '**/*.config.js',
      '**/*.config.ts',
      '**/vite.config.ts',
      'server/**', // Python backend
      'cli/**', // Python CLI
      '**/__generated__/**', // Generated GraphQL files
      '.venv/**', // Python virtual environment
      'files/**', // Diagram files
      'docs/**' // Documentation
    ],
  },

  {
    ...js.configs.recommended,
    languageOptions: {
      globals: {
        ...globals.browser,  // This adds all browser globals like document, window, etc.
        ...globals.es2021,   // ES2021 globals
      },
    },
  },

  // TypeScript files configuration
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      parser: typescriptParser,
      globals: {
        ...globals.browser,  // Also add here for TypeScript files
        ...globals.es2021,
      },
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: {
      '@typescript-eslint': typescript,
    },
    rules: {
      ...typescript.configs.recommended.rules,
      '@typescript-eslint/no-unused-vars': ['warn', {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
      }],
      'no-console': 'off',
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/explicit-module-boundary-types': 'off',
      '@typescript-eslint/no-non-null-assertion': 'off',
    },
  },

  // React files configuration
  {
    files: ['**/*.{jsx,tsx}'],
    plugins: {
      react,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    languageOptions: {
      globals: {
        ...globals.browser,  // And here for React files
      },
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
    rules: {
      ...react.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      'no-console': 'off',
      'react/react-in-jsx-scope': 'off', // Not needed in React 17+
      'react/prop-types': 'off', // Using TypeScript
      'react/display-name': 'off',
      'react-refresh/only-export-components': ['warn', {
        allowConstantExport: true
      }],
    },
  },

  // Node.js scripts configuration
  {
    files: ['scripts/**/*.{js,ts}'],
    languageOptions: {
      globals: {
        ...globals.node,  // Add Node.js globals for scripts
      },
    },
  },

  // General rules for all files
  {
    files: ['**/*.{js,jsx,ts,tsx}'],
    rules: {
      'no-console': 'off',
      'no-debugger': 'warn',
      'no-duplicate-imports': 'error',
      'no-unused-vars': 'off', // TypeScript handles this
      'prefer-const': 'warn',
      'no-var': 'error',
      'object-shorthand': 'warn',
      'prefer-template': 'warn',
    },
  },

  // Import restrictions to enforce module boundaries
  {
    files: ['apps/web/src/**/*.{js,jsx,ts,tsx}'],
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [
          // Prevent direct imports from feature internals
          {
            group: ['@features/*/components/*', '@features/*/hooks/*', '@features/*/store/*', '@features/*/services/*', '@features/*/utils/*', '@features/*/types/*'],
            message: 'Import from the feature\'s public API instead (e.g., @features/diagram-editor instead of @features/diagram-editor/components/...)',
          },
          // Prevent features from importing other features
          {
            group: ['@features/*'],
            message: 'Features cannot import from other features directly. Use the global store or events for inter-feature communication.',
          },
        ],
      }],
    },
  },

  // Core and shared modules cannot import from features
  {
    files: ['apps/web/src/core/**/*.{js,jsx,ts,tsx}', 'apps/web/src/shared/**/*.{js,jsx,ts,tsx}'],
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [
          {
            group: ['@features/*', '../features/*', '../../features/*'],
            message: 'Core and shared modules cannot import from features. Move shared logic to core or shared instead.',
          },
        ],
      }],
    },
  },

  // Library modules cannot import from app modules
  {
    files: ['apps/web/src/lib/**/*.{js,jsx,ts,tsx}'],
    rules: {
      'no-restricted-imports': ['error', {
        patterns: [
          {
            group: ['@core/*', '@shared/*', '@features/*', '../core/*', '../shared/*', '../features/*'],
            message: 'Library modules cannot import from app modules. Library should only contain generic utilities.',
          },
        ],
      }],
    },
  },
];