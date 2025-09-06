# Base Configuration Files

This directory contains the base configuration files for the frontend auto-generation system. These files are treated as infrastructure and are copied to the `generated/` directory before any source code generation begins.

## Files Included

- **package.json** - Node.js dependencies and scripts
- **tsconfig.json** - TypeScript compiler configuration
- **tsconfig.node.json** - TypeScript config for Vite
- **vite.config.ts** - Vite bundler configuration
- **tailwind.config.js** - Tailwind CSS configuration
- **postcss.config.js** - PostCSS configuration
- **.eslintrc.json** - ESLint linting rules
- **index.html** - Entry HTML file
- **.gitignore** - Git ignore patterns

## How It Works

1. The `setup_generated_dir.py` script copies all these files to the `generated/` directory
2. The generation system then creates only source code files (src/*) 
3. Generated code automatically works with these base configurations

## Benefits

- **Separation of Concerns**: Infrastructure configs are separate from generated code
- **Version Control**: Base configs can be maintained and versioned independently
- **Compatibility**: All generated code is guaranteed to work with these configs
- **Customization**: Easy to modify configs without affecting generation logic

## Path Aliases

The configurations include pre-configured path aliases for clean imports:

- `@/` → `./src/`
- `@/core/*` → `./src/core/*`
- `@/app/*` → `./src/app/*`
- `@/providers/*` → `./src/providers/*`
- `@/services/*` → `./src/services/*`
- `@/hooks/*` → `./src/hooks/*`
- `@/components/*` → `./src/components/*`
- `@/features/*` → `./src/features/*`

These aliases are configured in both `tsconfig.json` and `vite.config.ts` for consistency.
