# DiPeO Enhanced Frontend

A modern React frontend application built with Vite, TypeScript, and Tailwind CSS.

## Features

- **React 18** with TypeScript
- **Tailwind CSS** for styling with dark mode support
- **React Router** for client-side routing
- **TanStack Query** for data fetching and caching
- **React i18next** for internationalization
- **WebSocket integration** for real-time updates
- **Error boundaries** for graceful error handling
- **Responsive design** with mobile-first approach

## Getting Started

### Prerequisites

- Node.js 18.0.0 or higher
- pnpm (preferred) or npm

### Installation

1. Install dependencies:
   ```bash
   pnpm install
   ```

2. Copy the environment variables template:
   ```bash
   cp .env.example .env
   ```

3. Update the environment variables in `.env` as needed.

### Development

Start the development server:
```bash
pnpm dev
```

The application will be available at `http://localhost:3000`.

### Building for Production

Build the application:
```bash
pnpm build
```

Preview the production build:
```bash
pnpm preview
```

### Code Quality

Run ESLint:
```bash
pnpm lint
```

Fix ESLint issues:
```bash
pnpm lint:fix
```

Type check:
```bash
pnpm type-check
```

## Project Structure

```
src/
├── app/                 # Application configuration and setup
│   ├── config/         # Configuration files
│   ├── main.tsx        # Application entry point
│   └── routes/         # Route components
├── features/           # Feature-based modules
│   ├── auth/           # Authentication feature
│   └── dashboard/      # Dashboard feature
├── shared/             # Shared utilities and components
│   ├── components/     # Reusable components
│   ├── hooks/          # Custom hooks
│   └── i18n/           # Internationalization setup
└── styles/             # Global styles
```

## Environment Variables

See `.env.example` for all available environment variables and their descriptions.

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Client-side routing
- **TanStack Query** - Data fetching
- **React i18next** - Internationalization
- **React Error Boundary** - Error handling

## License

This project is part of the DiPeO monorepo.