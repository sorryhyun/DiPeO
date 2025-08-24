# Frontend Auto - Lightweight AI Frontend Generator

## Overview

Frontend Auto is a streamlined version of the Frontend Enhance system, designed for rapid generation of production-ready React applications. It produces complete, Vercel-deployable frontend applications using DiPeO's agent-based architecture without the complex memory selection system, making it faster and more straightforward for standard use cases.

## Key Differences from Frontend Enhance

| Feature | Frontend Enhance                                   | Frontend Auto                  |
|---------|----------------------------------------------------|--------------------------------|
| Memory System | Advanced selector with LLM-based context filtering | Simplified context passing     |
| Generation Time | 60 minutes                                         | 30 minutes                     |
| Complexity | High (intelligent section dependencies)            | Medium (sequential generation) |
| Use Case | Complex enterprise applications                    | Standard web applications      |
| Configuration | Extensive customization                            | Pre-configured variants        |

## Quick Start

### 1. Generate a Frontend Application

```bash
# Default chat application
dipeo run projects/frontend_auto/consolidated_generator --light --debug --timeout=120

# Or use a specific variant
dipeo run projects/frontend_auto/consolidated_generator --light --debug --timeout=120 \
  --input-data '{"config_file": "variants/ecommerce_config.json"}'
```

### 2. Deploy to Vercel (Generated App)

The generated application in `generated/` is **fully Vercel-ready**:

```bash
cd projects/frontend_auto/generated

# Install dependencies
pnpm install

# Test locally
pnpm run dev  # Runs on http://localhost:3001

# Build for production
pnpm run build

# Deploy to Vercel
vercel deploy
```

## Available Variants

Frontend Auto includes pre-configured templates for common application types:

| Variant | Description | Key Features |
|---------|-------------|--------------|
| `chat_application_config.json` | Slack-like chat app | Channels, DMs, threads, real-time |
| `ecommerce_config.json` | Online store | Product catalog, cart, checkout |
| `analytics_platform_config.json` | Data dashboard | Charts, metrics, real-time updates |
| `banking_config.json` | Financial portal | Transactions, accounts, security |
| `cms_config.json` | Content management | WYSIWYG editor, media library |
| `healthcare_portal_config.json` | Patient portal | Appointments, records, messaging |
| `learning_platform_config.json` | E-learning | Courses, progress tracking, quizzes |
| `project_management_config.json` | Task tracking | Kanban, sprints, collaboration |
| `social_media_config.json` | Social network | Feed, profiles, interactions |
| `minimal_config.json` | Bare minimum | Basic routing and auth |

## Generated Application Structure

```
generated/
├── 📦 Package & Config Files
│   ├── package.json              # Dependencies & scripts (Vercel-ready)
│   ├── vercel.json              # Vercel deployment config
│   ├── vite.config.ts           # Build configuration
│   ├── tsconfig.json            # TypeScript config
│   ├── tailwind.config.js       # Tailwind CSS config
│   ├── postcss.config.js        # PostCSS config
│   ├── index.html               # Entry HTML
│   └── .env.example             # Environment variables template
│
├── 📁 src/
│   ├── 🎯 Entry Points
│   │   ├── main.tsx             # Application bootstrap
│   │   ├── App.tsx              # Root component
│   │   └── index.css            # Global styles
│   │
│   ├── ⚙️ config/
│   │   ├── config.ts            # Main configuration
│   │   ├── appConfig.ts         # Application settings
│   │   └── devConfig.ts         # Development settings
│   │
│   ├── 🚀 features/             # Feature modules
│   │   ├── auth/                # Authentication
│   │   ├── chat/                # Chat functionality
│   │   ├── channels/            # Channel management
│   │   ├── files/               # File handling
│   │   └── search/              # Search features
│   │
│   ├── 🔄 routes/
│   │   └── AppRouter.tsx        # Application routing
│   │
│   ├── 🌐 services/
│   │   ├── apiClient.ts         # API client
│   │   ├── endpoints/           # API endpoints
│   │   └── mock/                # Mock data & server
│   │
│   ├── 🎨 shared/
│   │   ├── components/          # Reusable UI components
│   │   │   ├── atoms/           # Basic components
│   │   │   ├── molecules/       # Composite components
│   │   │   └── organisms/       # Complex components
│   │   ├── context/             # React contexts
│   │   ├── hooks/               # Custom React hooks
│   │   └── ErrorBoundary.tsx    # Error handling
│   │
│   ├── 📝 types/
│   │   └── index.ts             # TypeScript definitions
│   │
│   └── 🛠️ utils/
│       ├── formatDate.ts        # Date utilities
│       └── generateId.ts        # ID generation
```

## GitHub Repository Example

When pushing the generated app to GitHub:

### Repository Structure
```
your-app-name/
├── .github/
│   └── workflows/
│       └── deploy.yml           # GitHub Actions for Vercel
├── src/                         # Generated source code
├── public/                      # Static assets
├── package.json                 # Dependencies
├── vercel.json                 # Deployment config
├── README.md                    # Project documentation
└── .gitignore                  # Git ignore rules
```

### Example GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Vercel
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'pnpm'
      - run: pnpm install
      - run: pnpm run build
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
```

### Example Repository README

```markdown
# [Your App Name]

A modern React application built with AI-powered code generation.

## Tech Stack
- React 18 + TypeScript
- Vite for blazing fast builds
- Tailwind CSS for styling
- TanStack Query for data fetching
- React Router v6 for navigation

## Quick Start

\`\`\`bash
# Install dependencies
pnpm install

# Start development server
pnpm run dev

# Build for production
pnpm run build
\`\`\`

## Deployment

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/yourapp)

## Features
- 🔐 Authentication system
- 💬 Real-time chat
- 📁 File management
- 🔍 Advanced search
- 🌙 Dark mode support
- 📱 Responsive design

Generated with [DiPeO Frontend Auto](https://github.com/soryhyun/DiPeO)
```

## Deployment Guide

### Vercel Deployment (Recommended)

1. **Push to GitHub**
   ```bash
   cd generated/
   git init
   git add .
   git commit -m "Initial commit - AI-generated React app"
   git remote add origin https://github.com/yourusername/yourapp.git
   git push -u origin main
   ```

2. **Import to Vercel**
   - Go to [vercel.com/new](https://vercel.com/new)
   - Import your GitHub repository
   - Configure environment variables:
     - `VITE_API_URL`: Your backend API URL
     - `VITE_ENABLE_MOCKS`: `false` for production
   - Deploy!

### Alternative Deployment Options

#### Netlify
```bash
# Install Netlify CLI
npm i -g netlify-cli

# Deploy
netlify deploy --dir=dist --prod
```

#### AWS Amplify
```bash
# Install Amplify CLI
npm i -g @aws-amplify/cli

# Initialize and deploy
amplify init
amplify publish
```

#### Docker
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN pnpm install
COPY . .
RUN pnpm run build
CMD ["pnpm", "preview"]
```

## Configuration

### Environment Variables

Create `.env.local` for local development:

```env
VITE_API_URL=http://localhost:8000
VITE_ENABLE_MOCKS=true
VITE_WS_URL=ws://localhost:8000/ws
```

### API Proxy Configuration

The generated `vite.config.ts` includes proxy configuration:

```typescript
proxy: {
  '/api': {
    target: process.env.VITE_API_URL || 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, '')
  }
}
```

## Customization

### Adding New Features

1. **Create Feature Module**
   ```
   src/features/new-feature/
   ├── components/
   ├── pages/
   ├── hooks/
   └── types.ts
   ```

2. **Add Route**
   ```tsx
   // In AppRouter.tsx
   <Route path="/new-feature" element={<NewFeaturePage />} />
   ```

3. **Create API Endpoint**
   ```typescript
   // In services/endpoints/newFeature.ts
   export const getNewFeatureData = async () => {
     return api.get('/api/new-feature');
   };
   ```

### Theming

Modify `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        50: '#eff6ff',
        500: '#3b82f6',
        900: '#1e3a8a',
      }
    }
  }
}
```

## Performance Optimization

The generated app includes several optimizations:

- **Code Splitting**: Lazy loading for routes
- **Suspense Boundaries**: Smooth loading states
- **React Query**: Intelligent caching and refetching
- **Vite**: Fast HMR and optimized builds
- **Tree Shaking**: Automatic dead code elimination

## Testing

Add testing capabilities:

```bash
pnpm add -D vitest @testing-library/react @testing-library/user-event
```

Create test files:
```typescript
// Button.test.tsx
import { render, screen } from '@testing-library/react';
import Button from './Button';

test('renders button with text', () => {
  render(<Button>Click me</Button>);
  expect(screen.getByText('Click me')).toBeInTheDocument();
});
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 3001 in use | Change port in `vite.config.ts` |
| TypeScript errors | Run `pnpm typecheck` to identify issues |
| Build fails | Check Node version (requires 18+) |
| Mock data not working | Ensure `VITE_ENABLE_MOCKS=true` |
| Vercel deployment fails | Check environment variables in Vercel dashboard |

## Workflow Details

### Generation Process

1. **Section Planning**: Analyzes requirements and creates 8-10 sections
2. **Sequential Generation**: Each section builds on previous ones
3. **File Organization**: Automatically structures files
4. **Dependency Detection**: Identifies required npm packages
5. **Configuration Setup**: Creates all necessary config files

### Key Files

| File | Purpose |
|------|---------|
| `consolidated_generator.light.yaml` | Main workflow definition |
| `frontend_generator.txt` | Generation prompt template |
| `section_models.py` | Data models for sections |
| `rename_generated_files.py` | File organization utility |

## Comparison with Frontend Enhance

### When to Use Frontend Auto
- Standard web applications
- Quick prototypes
- MVPs and demos
- Time-constrained projects
- Pre-defined application types

### When to Use Frontend Enhance
- Complex enterprise applications
- Custom architectural requirements
- Applications requiring specific context management
- Projects needing fine-grained control
- Novel application patterns

## Contributing

To add new variants:

1. Create config in `variants/`:
   ```json
   {
     "app_name": "Your App",
     "app_type": "custom",
     "features": ["feature1", "feature2"],
     "dependencies": ["package1", "package2"]
   }
   ```

2. Test generation:
   ```bash
   dipeo run projects/frontend_auto/consolidated_generator --light \
     --input-data '{"config_file": "variants/your_config.json"}'
   ```

## Future Enhancements

- [ ] Next.js support (SSR/SSG)
- [ ] Vue.js templates
- [ ] GraphQL integration
- [ ] Storybook generation
- [ ] E2E test generation
- [ ] CI/CD pipeline templates
- [ ] Monorepo support
- [ ] Micro-frontend architecture

## License

Part of the DiPeO project. See main repository for license details.

## Related Projects

- **[Frontend Enhance](../frontend_enhance/)**: Advanced version with intelligent memory selection
- **[DiPeO Core](https://github.com/soryhyun/DiPeO)**: The underlying workflow orchestration engine
- **[DiPeO Codegen](../codegen/)**: Code generation system for DiPeO itself

---

Generated with DiPeO - AI-Powered Application Generation 🚀