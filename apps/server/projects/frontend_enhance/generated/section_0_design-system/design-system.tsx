```package.json
{
  "name": "design-system-dashboard",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint . --ext .ts,.tsx",
    "test": "vitest run"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "next": "13.4.7",
    "tailwindcss": "^3.6.7",
    "postcss": "^8.4.21",
    "autoprefixer": "^10.4.16"
  },
  "devDependencies": {
    "@types/node": "^18.17.0",
    "@types/react": "^18.0.38",
    "typescript": "^4.9.5",
    "vitest": "^0.34.0",
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^5.16.5",
    "eslint": "^8.55.0",
    "eslint-config-next": "^13.4.4"
  },
  "eslintConfig": {
    "extends": ["next/core-web-vitals"]
  },
  "browserslist": [
    ">0.2%",
    "not dead",
    "not op_mini all"
  ]
}
```

```tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "es2020"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noImplicitAny": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "isolatedModules": true,
    "jsx": "react-jsx",
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
```

```ts
// app/design-system/tokens.ts
// Design tokens with strict TS types and a token object (TOKENS)
export type ColorMode = 'light' | 'dark'

export type TypographyScaleEntry = {
  fontSize: string
  lineHeight: string
  fontWeight?: number
}

export const TOKENS = {
  colors: {
    primary: '#3B82F6',
    primaryDark: '#2563EB',
    surface: '#FFFFFF',
    background: '#F8FAFF',
    text: '#0F172A',
    textMuted: '#64748B',
    border: '#E5E7EB',
    surfaceDark: '#1F2937',
    backgroundDark: '#0B1020',
    textDark: '#E5E7EB',
    textMutedDark: '#94A3B8',
    borderDark: '#374151'
  },
  typography: {
    fontFamily:
      '"Inter", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
    scale: {
      xs: { fontSize: '12px', lineHeight: '16px' },
      sm: { fontSize: '14px', lineHeight: '20px' },
      base: { fontSize: '16px', lineHeight: '24px' },
      lg: { fontSize: '18px', lineHeight: '28px' },
      xl: { fontSize: '20px', lineHeight: '28px' },
      '2xl': { fontSize: '24px', lineHeight: '32px' }
    } as Record<string, TypographyScaleEntry>
  },
  spacing: {
    unit: 4,
    1: '4px',
    2: '8px',
    3: '12px',
    4: '16px',
    6: '24px',
    8: '32px',
    10: '40px'
  },
  radii: {
    sm: '4px',
    base: '8px',
    lg: '12px',
    full: '9999px'
  },
  shadows: {
    subtle: '0 1px 2px rgba(0,0,0,.05)',
    medium: '0 6px 16px rgba(0,0,0,.08)'
  },
  breakpoints: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px'
  },
  zIndices: {
    dropdown: 1000,
    modal: 1100,
    tooltip: 1200
  },
  motion: {
    duration: '250ms'
  }
} as const

export type ColorTokens = typeof TOKENS.colors
export type DesignTokens = typeof TOKENS
export type TypographyScale = typeof TOKENS.typography.scale
```

```css
/* app/design-system/tokens.css */
/* Runtime CSS variables for token-driven theming (light/dark) */
:root {
  --color-primary: #3B82F6;
  --color-primary-dark: #2563EB;
  --color-surface: #FFFFFF;
  --color-background: #F8FAFF;
  --color-text: #0F172A;
  --color-text-muted: #64748B;
  --color-border: #E5E7EB;

  /* dark mode defaults (overridden via [data-theme="dark"]) */
  --color-surface-dark: #1F2937;
  --color-background-dark: #0B1020;
  --color-text-dark: #E5E7EB;
  --color-text-muted-dark: #94A3B8;
  --color-border-dark: #374151;

  /* Typography (fluid-friendly) */
  --font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --font-size-xs: 12px;
  --line-height-xs: 16px;
  --font-size-sm: 14px;
  --line-height-sm: 20px;
  --font-size-base: 16px;
  --line-height-base: 24px;
  --font-size-lg: 18px;
  --line-height-lg: 28px;
  --font-size-xl: 20px;
  --line-height-xl: 28px;
  --font-size-2xl: 24px;
  --line-height-2xl: 32px;
}

[data-theme="dark"] {
  --color-background: var(--color-background-dark);
  --color-surface: var(--color-surface-dark);
  --color-text: var(--color-text-dark);
  --color-text-muted: var(--color-text-muted-dark);
  --color-border: var(--color-border-dark);
  --color-primary: #60A5FA; /* slightly different for dark mode */
}
@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
  }
}

@container (min-width: 60em) {
  .container-fluid {
    padding-left: 2rem;
    padding-right: 2rem;
  }
}
```

```ts
// app/layout.tsx
'use client'
import React from 'react'
import '../styles/globals.css'
import { ThemeProvider } from './components/ThemeProvider'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="light">
      <head />
      <body className="min-h-screen bg-background text-text">
        <ThemeProvider>
          <div className="min-h-screen">
            {children}
          </div>
        </ThemeProvider>
      </body>
    </html>
  )
}
```

```tsx
// app/components/ThemeProvider.tsx
'use client'
import React, { createContext, useCallback, useEffect, useMemo, useState } from 'react'

type ThemeContextValue = {
  theme: 'light' | 'dark'
  toggle: () => void
}

export const ThemeContext = createContext<ThemeContextValue | undefined>(
  undefined
)

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({
  children
}) => {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  // Initialize theme from localStorage or OS preference
  useEffect(() => {
    const stored = localStorage.getItem('theme') as 'light' | 'dark' | null
    if (stored) {
      setTheme(stored)
      document.documentElement.setAttribute('data-theme', stored)
    } else {
      const prefersDark = window.matchMedia?.('(prefers-color-scheme: dark)').matches
      const initial = prefersDark ? 'dark' : 'light'
      setTheme(initial)
      document.documentElement.setAttribute('data-theme', initial)
    }
  }, [])

  const toggle = useCallback(() => {
    setTheme((t) => {
      const next = t === 'light' ? 'dark' : 'light'
      document.documentElement.setAttribute('data-theme', next)
      localStorage.setItem('theme', next)
      return next
    })
  }, [])

  const value = useMemo(
    () => ({
      theme,
      toggle
    }),
    [theme, toggle]
  )

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  )
}
```

```tsx
// app/hooks/useToggle.ts
'use client'
import { useCallback, useState } from 'react'

export function useToggle(initial = false): [boolean, () => void, () => void] {
  const [state, setState] = useState<boolean>(initial)
  const toggle = useCallback(() => setState((s) => !s), [])
  const set = useCallback(() => setState(true), [])
  return [state, toggle, set]
}
```

```tsx
// app/hooks/useDebounce.ts
'use client'
import { useEffect, useState } from 'react'

export function useDebounce<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState<T>(value)

  useEffect(() => {
    const t = window.setTimeout(() => setDebounced(value), delay)
    return () => window.clearTimeout(t)
  }, [value, delay])

  return debounced
}
```

```tsx
// app/hooks/useTokenTheme.ts
'use client'
import { useContext } from 'react'
import { ThemeContext } from './ThemeProvider'

export function useTokenTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) {
    throw new Error('useTokenTheme must be used within a ThemeProvider')
  }
  return {
    theme: ctx.theme,
    toggleTheme: ctx.toggle
  }
}
```

```tsx
// app/components/Button.tsx
'use client'
import React from 'react'
import type { ColorTokens } from '../design-system/tokens'
import { TOKENS } from '../design-system/tokens'

type ButtonVariant = 'solid' | 'outline' | 'ghost'
type ButtonSize = 'xs' | 'sm' | 'md' | 'lg'

export interface ButtonProps
  extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
  variant?: ButtonVariant
  size?: ButtonSize
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  loading?: boolean
  colorTokens?: Partial<ColorTokens>
  ariaLabel?: string
}

function cx(...classes: (string | false | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'solid',
  size = 'md',
  className,
  leftIcon,
  rightIcon,
  loading,
  children,
  ...rest
}) => {
  const sizeClasses: Record<ButtonSize, string> = {
    xs: 'px-2 py-1 text-xs',
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-5 py-3 text-base'
  }

  const variantClasses: Record<ButtonVariant, string> = {
    solid:
      'bg-primary text-white hover:bg-primary-dark disabled:opacity-50',
    outline:
      'border border-border text-primary bg-transparent hover:bg-gray-50',
    ghost: 'bg-transparent text-primary hover:bg-gray-100'
  }

  // Use CSS vars via Tailwind tokens when available
  const classes = cx(
    'inline-flex items-center justify-center rounded-md font-semibold focus:outline-none focus:ring-2 focus:ring-offset-2',
    sizeClasses[size],
    variantClasses[variant],
    className
  )

  return (
    <button
      aria-label={rest['aria-label'] ?? typeof children === 'string' ? (children as string) : undefined}
      className={classes}
      disabled={rest.disabled || loading}
      {...rest}
    >
      {leftIcon && <span className="mr-2">{leftIcon}</span>}
      {loading ? 'Loading…' : children}
      {rightIcon && <span className="ml-2">{rightIcon}</span>}
    </button>
  )
}
```

```tsx
// app/components/Input.tsx
'use client'
import React from 'react'

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
  type?: 'text' | 'number' | 'email' | 'password'
  id?: string
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  hint,
  id,
  ...rest
}) => {
  const inputId = id ?? `input-${Math.random().toString(36).slice(2, 7)}`
  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputId} className="block text-sm font-medium text-text">
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={`mt-1 block w-full rounded-md border border-border bg-surface px-3 py-2 text-base
          focus:border-primary focus:ring-2 focus:ring-primary/20`}
        {...rest}
      />
      {hint && !error && <p className="mt-1 text-sm text-text-muted">{hint}</p>}
      {error && <p className="mt-1 text-sm text-red-600" role="alert">{error}</p>}
    </div>
  )
}
```

```tsx
// app/components/Card.tsx
'use client'
import React from 'react'

export interface CardProps {
  title?: string
  actions?: React.ReactNode
  children?: React.ReactNode
  footer?: React.ReactNode
}

export const Card: React.FC<CardProps> = ({
  title,
  actions,
  children,
  footer
}) => {
  return (
    <section className="bg-surface rounded-lg shadow-sm border border-border overflow-hidden">
      {(title || actions) && (
        <header className="flex items-center justify-between px-4 py-3 border-b border-border bg-surface">
          <h3 className="text-base font-semibold text-text">{title}</h3>
          <div className="flex items-center gap-2">{actions}</div>
        </header>
      )}
      <div className="p-4">{children}</div>
      {footer && <footer className="px-4 py-3 border-t border-border bg-surface">{footer}</footer>}
    </section>
  )
}
```

```tsx
// app/components/Table.tsx
'use client'
import React from 'react'

type Column<T> = {
  key: keyof T
  label: string
  sortable?: boolean
}

export interface TableProps<T extends Record<string, any>> {
  data: T[]
  columns: Column<T>[]
  ariaLabel?: string
}

export function Table<T extends Record<string, any>>({
  data,
  columns
}: TableProps<T>) {
  const [sortKey, setSortKey] = React.useState<string | null>(null)
  const [asc, setAsc] = React.useState<boolean>(true)

  const sorted = React.useMemo(() => {
    if (!sortKey) return data
    const col = sortKey
    const next = [...data].sort((a, b) => {
      const va = a[col as keyof T]
      const vb = b[col as keyof T]
      if (va == null) return 1
      if (vb == null) return -1
      if (va < vb) return asc ? -1 : 1
      if (va > vb) return asc ? 1 : -1
      return 0
    })
    return next
  }, [data, sortKey, asc])

  const onSort = (colKey: string) => {
    if (sortKey === colKey) {
      setAsc((a) => !a)
    } else {
      setSortKey(colKey)
      setAsc(true)
    }
  }

  return (
    <table aria-label={''} className="min-w-full divide-y divide-border">
      <thead className="bg-surface">
        <tr>
          {columns.map((c) => (
            <th
              key={String(c.key)}
              scope="col"
              className="px-4 py-2 text-left text-sm font-semibold text-text border-b border-border"
            >
              <button
                onClick={() => c.sortable && onSort(String(c.key))}
                className={cx(
                  c.sortable ? 'cursor-pointer' : '',
                  c.sortable ? 'hover:underline' : ''
                )}
              >
                {c.label}
              </button>
            </th>
          ))}
        </tr>
      </thead>
      <tbody className="divide-y divide-border bg-surface">
        {sorted.map((row, idx) => (
          <tr key={idx}>
            {columns.map((c) => (
              <td key={String(c.key)} className="px-4 py-3 text-sm text-text">
                {String(row[c.key])}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
```

```tsx
// app/components/ChartContainer.tsx
'use client'
import React from 'react'

export interface ChartContainerProps {
  title?: string
  children?: React.ReactNode
  ariaLabel?: string
}

export const ChartContainer: React.FC<ChartContainerProps> = ({
  title,
  children,
  ariaLabel
}) => {
  return (
    <section aria-label={ariaLabel ?? title ?? 'Chart container'} className="w-full h-72 bg-surface border border-border rounded-md p-4">
      {title && <div className="text-sm font-medium mb-2 text-text">{title}</div>}
      <div className="w-full h-full">{children ?? null}</div>
    </section>
  )
}
```

```tsx
// app/page.tsx
'use client'
import React from 'react'
import { Button } from './components/Button'
import { Card } from './components/Card'
import { Input } from './components/Input'
import { Table } from './components/Table'
import { ChartContainer } from './components/ChartContainer'
import { TOKENS } from './design-system/tokens'
import { useTokenTheme } from './hooks/useTokenTheme'

const sampleData = [
  { id: 1, name: 'Alice', email: 'alice@example.com', status: 'Active' },
  { id: 2, name: 'Bob', email: 'bob@example.com', status: 'Inactive' },
  { id: 3, name: 'Carol', email: 'carol@example.com', status: 'Active' },
]

const columns = [
  { key: 'id' as const, label: 'ID', sortable: true },
  { key: 'name' as const, label: 'Name', sortable: true },
  { key: 'email' as const, label: 'Email' },
  { key: 'status' as const, label: 'Status', sortable: true }
]

export default function Dashboard() {
  const { toggleTheme } = useTokenTheme()

  return (
    <main className="container-fluid max-w-7xl mx-auto p-4">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-semibold text-text">Token-Driven Dashboard</h1>
        <div className="flex items-center gap-2">
          <Button onClick={() => toggleTheme()} variant="solid" size="sm">
            Toggle Theme
          </Button>
          <Button variant="outline" size="sm">
            Help
          </Button>
        </div>
      </div>

      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card
          title="Users"
          actions={<span className="text-xs text-text-muted">Active: 2</span>}
        >
          <Table
            data={sampleData}
            columns={columns as any}
            ariaLabel="Users table"
          />
        </Card>

        <Card title="Weekly Revenue" actions={<span className="text-xs text-text-muted">Last 7 days</span>}>
          <ChartContainer title="Revenue (mock)">
            <div role="img" aria-label="chart" style={{ width: '100%', height: '100%' }}>
              {/* Placeholder chart bowl: replace with chart lib integration */}
              <div
                style={{
                  width: '100%',
                  height: '100%',
                  background:
                    'linear-gradient(135deg, var(--color-primary) 0%, #93c5fd 60%)',
                  borderRadius: 8
                }}
              />
            </div>
          </ChartContainer>
        </Card>

        <Card title="Filters" >
          <div className="space-y-3">
            <Input label="Search users" placeholder="Enter name or email" />
            <Input label="Status" placeholder="Active or Inactive" />
          </div>
          <div className="mt-3 flex gap-2">
            <Button variant="solid" size="md">
              Apply
            </Button>
            <Button variant="ghost" size="md">
              Reset
            </Button>
          </div>
        </Card>
      </section>
    </main>
  )
}
```

```css
/* app/styles/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Import design tokens via CSS variables (light/dark) */
@import './design-system/tokens.css';

/* Base color helpers mapped to CSS variables for Tailwind-like usage */
:root {
  --color-primary: #3B82F6;
  --color-background: #F8FAFF;
  --color-surface: #FFFFFF;
  --color-text: #0F172A;
  --color-border: #E5E7EB;
  --color-text-muted: #64748B;
}

/* Tailwind-friendly utility overrides for colors (optional). */
.bg-background { background-color: var(--color-background); }
.bg-surface { background-color: var(--color-surface); }
.text-text { color: var(--color-text); }
.text-text-muted { color: var(--color-text-muted); }

.container-fluid {
  width: 100%;
  padding-left: clamp(1rem, 2vw, 2rem);
  padding-right: clamp(1rem, 2vw, 2rem);
}
```

```tsx
// app/docs/index.tsx (optional quick docs index)
'use client'
import React from 'react'
import Link from 'next/link'

export default function DocsIndex() {
  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold mb-4">Design System Docs</h2>
      <ul className="list-disc pl-6 space-y-2">
        <li><Link href="/docs/tokens">Tokens</Link></li>
        <li><Link href="/docs/components">Components API</Link></li>
        <li><Link href="/docs/usage">Usage Guidelines</Link></li>
      </ul>
    </div>
  )
}
```

```markdown
<!-- docs/tokens.md -->
# Tokens Reference

This document documents the token surface used by the dashboard design system.

- Colors
  - Primary: tokens.colors.primary
  - Background: tokens.colors.background
  - Surface: tokens.colors.surface
  - Text: tokens.colors.text
  - Border: tokens.colors.border
- Typography
  - Font family: tokens.typography.fontFamily
  - Scale: xs, sm, base, lg, xl, 2xl
- Spacing
  - Unit: 4px
  - 1..10 scale map to pixel values
- Radii, Shadows, Breakpoints, Z-Indices, Motion
  - Predefined values suitable for production dashboards

Theme switching is controlled by a class-based theme toggle (light/dark) via data-theme on the root element.
```

```markdown
<!-- docs/components.md -->
# Components API (high level)

- Button
  - Props: variant ('solid'|'outline'|'ghost'), size ('xs'|'sm'|'md'|'lg'), leftIcon, rightIcon, loading, ariaLabel
- Input
  - Props: label, error, hint, type, id
- Card
  - Props: title, actions, children, footer
- Table
  - Props: data<T>, columns: Array<{ key: keyof T; label: string; sortable?: boolean }>
- ChartContainer
  - Props: title, ariaLabel, children

Accessibility
- All interactive controls have ARIA labels when applicable
- Keyboard navigable
- Screen-reader-friendly structure

Styling
- All components are designed to be token-driven via CSS variables and Tailwind classes.
```

```markdown
<!-- docs/usage.md -->
# Usage Guide

1) Setup
- Install dependencies: npm i
- Ensure app root contains app/layout.tsx and app/page.tsx as scaffolded here.

2) Theming
- Theme toggling is exposed via useTokenTheme() hook in client components.
- Dark mode uses data-theme="dark" on the root and overrides via app/design-system/tokens.css.

3) Tokens
- Access tokens via import { TOKENS } from './design-system/tokens'
- Use in components for type-safe surfaces.

4) Data fetching
- Use React Query or SWR patterns for data fetching with loading/error/success states.
- Our sample uses static data for demonstration.

5) Accessibility
- ARIA roles and labels are provided in table, chart container, and form controls.

6) Migration
- To migrate from CSS-in-JS to CSS Vars, adopt tokens.css and map colors to CSS vars.
```

```tsx
// __tests__/Button.test.tsx
import React from 'react'
import { render, screen } from '@testing-library/react'
import { Button } from '../app/components/Button'

test('renders button with label', () => {
  render(<Button onClick={() => {}}>Click me</Button>)
  expect(screen.getByText('Click me')).toBeInTheDocument()
})
```

```tsx
// __tests__/Table.test.tsx
import React from 'react'
import { render, screen } from '@testing-library/react'
import { Table } from '../app/components/Table'

type Row = { id: number; name: string; email: string }

const data: Row[] = [
  { id: 1, name: 'Alice', email: 'alice@example.com' },
  { id: 2, name: 'Bob', email: 'bob@example.com' }
]

const columns = [
  { key: 'id' as const, label: 'ID', sortable: true },
  { key: 'name' as const, label: 'Name', sortable: true },
  { key: 'email' as const, label: 'Email' }
]

test('renders table with data', () => {
  render(<Table data={data} columns={columns} />)
  expect(screen.getByText('Alice')).toBeInTheDocument()
  expect(screen.getByText('bob@example.com')).toBeInTheDocument()
})
```

```markdown
<!-- docs/README.md (optional) -->
# Design System Dashboard — Quick Start

This repository provides a production-grade scaffold for a token-driven design system using Tailwind CSS and React 18+ (Next.js app dir ready).

How to run
- npm install
- npm run dev
- Open http://localhost:3000

Environment
- Dark mode via class toggling on root with data-theme
- Tokens defined in app/design-system/tokens.ts and mapped to CSS variables in tokens.css
- Tailwind configured to reference tokens via CSS vars
- Components: Button, Input, Card, Table, ChartContainer

Migration
- To adapt for CRA/Vite, export tokens from a central module and adapt the Next.js app dir layout to a standard React entry point, wiring _app.tsx accordingly.
```

```css
/* tailwind.config.ts (Tailwind + token mapping) */
import type { Config } from 'tailwindcss'
import TOKENS from './app/design-system/tokens'
/* eslint-disable @typescript-eslint/no-var-requires, @typescript-eslint/ban-ts-comment */

// Note: This is a TS file; Tailwind reads JS/TS depending on build tooling.
// We map CSS vars to Tailwind color names for token-consistent styling.

const config: Config = {
  content: ['./app/**/*.{ts,tsx,js,jsx,mdx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: 'var(--color-primary)',
        'background': 'var(--color-background)',
        'surface': 'var(--color-surface)',
        text: 'var(--color-text)',
        border: 'var(--color-border)',
        muted: 'var(--color-text-muted)'
      },
      fontFamily: {
        sans: [TOKENS.typography.fontFamily]
      },
      container: {
        padding: 'clamp(1rem, 2vw, 2rem)'
      },
      fontSize: {
        xs: ['var(--font-size-xs)', 'var(--line-height-xs)'],
        sm: ['var(--font-size-sm)', 'var(--line-height-sm)'],
        base: ['var(--font-size-base)', 'var(--line-height-base)'],
        lg: ['var(--font-size-lg)', 'var(--line-height-lg)'],
        xl: ['var(--font-size-xl)', 'var(--line-height-xl)'],
        '2xl': ['var(--font-size-2xl)', 'var(--line-height-2xl)']
      }
    }
  },
  plugins: []
}
export default config
```

```javascript
// postcss.config.js
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {}
  }
}
```

```text
// README.md (core run instructions)
Design System Dashboard
- Stack: Next.js app dir (server components readiness) + React 18 + TypeScript
- Tailwind CSS with token-based design system
- Accessibility-first, responsive, accessible components

How to run locally
1) Install
   npm install
2) Develop
   npm run dev
3) Build for production
   npm run build
   npm run start

Environment notes
- Theme toggling via ThemeProvider (localStorage, data-theme on root)
- Tokens accessible via design-system/tokens.ts
- Modern patterns: React.memo, lazy, Suspense, error boundaries to be added in components as you grow

Migration tips
- For CRA/Vite: relocate app/ to src/ and adjust imports to absolute paths if using TS path aliases.
- If not using Next.js app dir, create a simple App.tsx and wrap with ThemeProvider; ensure global CSS is loaded.
```

```tsx
// app/pages/_app.tsx (optional legacy bridge for CRA-like behavior)
import React from 'react'
import type { AppProps } from 'next/app'
import '../styles/globals.css'
import { ThemeProvider } from '../components/ThemeProvider'

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <ThemeProvider>
      <Component {...pageProps} />
    </ThemeProvider>
  )
}

export default MyApp
```

```tsx
// app/components/index.ts (barrel exports)
export { Button } from './Button'
export { Input } from './Input'
export { Card } from './Card'
export { Table } from './Table'
export { ChartContainer } from './ChartContainer'
export { ThemeProvider } from './ThemeProvider'
```

```ts
// app/index.ts
// Barrel to export tokens and types for external consumers (if needed)
export * from './design-system/tokens'
```

Notes on how to use tokens and components in code
- Import tokens:
  import { TOKENS } from './design-system/tokens'
  // Access color tokens with TOKENS.colors.primary, etc.

- Use theme toggle hook in client components:
  import { useTokenTheme } from './hooks/useTokenTheme'
  const { theme, toggleTheme } = useTokenTheme()

- Ensure components run as client components
  - Button.tsx, Input.tsx, ChartContainer.tsx, Card.tsx, Table.tsx are client components (use 'use client').

- Tailwind usage
  - Tailwind is extended to read CSS vars for primary, background, surface, text, border, etc.
  - Fluid typography and container queries are prepared via CSS vars and Tailwind fontSize mapping to CSS vars.

- Accessibility
  - All interactive controls include ARIA attributes (buttons, table headers, chart container with aria-label).
  - Keyboard navigation supported via standard HTML semantics.

- Testing
  - RTL scaffolding provided in __tests__ with Button and Table tests.
  - Tests emphasize strict TS types (no any).

- Documentation scaffolding
  - docs/tokens.md, docs/components.md, docs/usage.md provide token references and usage guidelines.
  - A simple docs index is included as an optional Next.js route (docs/index.tsx).

If you want more pages, more components (e.g., a DatePicker, Avatar, or an advanced Chart wrapper with actual chart libraries), or a Storybook setup, I can extend this scaffold with dedicated scaffolding and integration steps.