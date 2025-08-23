# DiPeO Frontend (Generated)

This is an auto-generated frontend application built with React, TypeScript, and Vite.

## Quick Start

### Install dependencies
```bash
pnpm install
```

### Development
```bash
pnpm run dev
```

### Build for production
```bash
pnpm run build
```

## Vercel Deployment

This project is configured for Vercel deployment. To deploy:

1. **Push to GitHub** (or connect your git repository)

2. **Import to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Click "Import Project"
   - Connect your GitHub repository
   - Vercel will auto-detect the configuration

3. **Set Environment Variables** (in Vercel dashboard):
   - `VITE_API_URL`: Your backend API URL
   - `VITE_ENABLE_MOCKS`: Set to `false` for production

4. **Deploy**: Vercel will automatically build and deploy

## Project Structure

```
src/
├── features/       # Feature modules (auth, chat, channels, etc.)
├── shared/         # Shared components and utilities
│   ├── components/ # Reusable UI components
│   ├── context/    # React context providers
│   └── hooks/      # Custom React hooks
├── services/       # API client and endpoints
├── routes/         # Application routing
└── types/          # TypeScript type definitions
```

## Technologies

- **React 18** with TypeScript
- **Vite** for fast builds and HMR
- **React Router v6** for routing
- **TanStack Query** for data fetching
- **Tailwind CSS** for styling
- **Mock Service Worker** for development mocking

## Development Notes

- Mock data is enabled by default in development
- API calls are proxied through `/api` to the backend
- WebSocket support included for real-time features
- Dark mode support via Tailwind CSS classes