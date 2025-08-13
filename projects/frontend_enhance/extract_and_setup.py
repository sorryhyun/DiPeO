#!/usr/bin/env python3
"""Extract frontend code from JSON and set up React app structure."""

import json
import os
import re
from pathlib import Path

def extract_code_blocks(text):
    """Extract code blocks from the text with their filenames."""
    
    # Pattern to match the file descriptions and code blocks
    pattern = r'(\d+\))\s+([^`\n]+)\n[^`]*```(\w+)?\n(.*?)```'
    
    matches = re.findall(pattern, text, re.DOTALL)
    
    files = {}
    
    for match in matches:
        num, description, lang, code = match
        
        # Extract file path from description
        if 'src/' in description:
            # Extract path like "src/components/Button/Button.types.ts"
            path_match = re.search(r'(src/[^\s]+\.(?:ts|tsx|js|jsx|md))', description)
            if path_match:
                file_path = path_match.group(1)
                files[file_path] = code.strip()
        elif 'README.md' in description:
            files['src/components/Button/README.md'] = code.strip()
        elif 'clsxImportGuide.md' in description:
            files['src/utils/clsxImportGuide.md'] = code.strip()
        elif 'Button.stories.tsx' in description:
            files['src/story/Button.stories.tsx'] = code.strip()
    
    return files

def create_react_app_structure(base_path):
    """Create a basic React app structure."""
    
    # Read the JSON file
    json_path = Path(base_path) / 'generated' / 'frontend_generator.json'
    
    with open(json_path, 'r') as f:
        content = json.load(f)
    
    # Extract code blocks from the content
    files = extract_code_blocks(content)
    
    # Create the app directory
    app_path = Path(base_path) / 'button-app'
    app_path.mkdir(exist_ok=True)
    
    # Create all necessary directories and files
    for file_path, code in files.items():
        full_path = app_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w') as f:
            f.write(code)
        
        print(f"Created: {full_path}")
    
    # Create package.json
    package_json = {
        "name": "button-app",
        "version": "0.1.0",
        "private": True,
        "scripts": {
            "dev": "vite",
            "build": "tsc && vite build",
            "preview": "vite preview",
            "test": "vitest",
            "typecheck": "tsc --noEmit"
        },
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "clsx": "^2.0.0"
        },
        "devDependencies": {
            "@types/react": "^18.2.0",
            "@types/react-dom": "^18.2.0",
            "@testing-library/react": "^14.0.0",
            "@testing-library/jest-dom": "^6.0.0",
            "@vitejs/plugin-react": "^4.0.0",
            "autoprefixer": "^10.4.16",
            "postcss": "^8.4.32",
            "tailwindcss": "^3.3.6",
            "typescript": "^5.3.3",
            "vite": "^5.0.0",
            "vitest": "^1.0.0"
        }
    }
    
    with open(app_path / 'package.json', 'w') as f:
        json.dump(package_json, f, indent=2)
    
    print(f"Created: {app_path / 'package.json'}")
    
    # Create vite.config.ts
    vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test-setup.ts'
  }
})
"""
    
    with open(app_path / 'vite.config.ts', 'w') as f:
        f.write(vite_config)
    
    print(f"Created: {app_path / 'vite.config.ts'}")
    
    # Create tsconfig.json
    tsconfig = {
        "compilerOptions": {
            "target": "ES2020",
            "useDefineForClassFields": True,
            "lib": ["ES2020", "DOM", "DOM.Iterable"],
            "module": "ESNext",
            "skipLibCheck": True,
            "moduleResolution": "bundler",
            "allowImportingTsExtensions": True,
            "resolveJsonModule": True,
            "isolatedModules": True,
            "noEmit": True,
            "jsx": "react-jsx",
            "strict": True,
            "noUnusedLocals": True,
            "noUnusedParameters": True,
            "noFallthroughCasesInSwitch": True
        },
        "include": ["src"],
        "references": [{ "path": "./tsconfig.node.json" }]
    }
    
    with open(app_path / 'tsconfig.json', 'w') as f:
        json.dump(tsconfig, f, indent=2)
    
    print(f"Created: {app_path / 'tsconfig.json'}")
    
    # Create tsconfig.node.json
    tsconfig_node = {
        "compilerOptions": {
            "composite": True,
            "skipLibCheck": True,
            "module": "ESNext",
            "moduleResolution": "bundler",
            "allowSyntheticDefaultImports": True
        },
        "include": ["vite.config.ts"]
    }
    
    with open(app_path / 'tsconfig.node.json', 'w') as f:
        json.dump(tsconfig_node, f, indent=2)
    
    print(f"Created: {app_path / 'tsconfig.node.json'}")
    
    # Create tailwind.config.js
    tailwind_config = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
"""
    
    with open(app_path / 'tailwind.config.js', 'w') as f:
        f.write(tailwind_config)
    
    print(f"Created: {app_path / 'tailwind.config.js'}")
    
    # Create postcss.config.js
    postcss_config = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""
    
    with open(app_path / 'postcss.config.js', 'w') as f:
        f.write(postcss_config)
    
    print(f"Created: {app_path / 'postcss.config.js'}")
    
    # Create src/index.css
    index_css = """@tailwind base;
@tailwind components;
@tailwind utilities;
"""
    
    src_path = app_path / 'src'
    src_path.mkdir(exist_ok=True)
    
    with open(src_path / 'index.css', 'w') as f:
        f.write(index_css)
    
    print(f"Created: {src_path / 'index.css'}")
    
    # Create src/main.tsx
    main_tsx = """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
"""
    
    with open(src_path / 'main.tsx', 'w') as f:
        f.write(main_tsx)
    
    print(f"Created: {src_path / 'main.tsx'}")
    
    # Create src/App.tsx
    app_tsx = """import Button from './components/Button'

function App() {
  const handleClick = () => {
    alert('Button clicked!')
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Button Component Demo</h1>
        
        <div className="space-y-8 bg-white p-8 rounded-lg shadow">
          <section>
            <h2 className="text-xl font-semibold mb-4">Variants</h2>
            <div className="flex gap-4 flex-wrap">
              <Button variant="solid" onClick={handleClick}>Solid</Button>
              <Button variant="outline" onClick={handleClick}>Outline</Button>
              <Button variant="ghost" onClick={handleClick}>Ghost</Button>
              <Button variant="link" onClick={handleClick}>Link</Button>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-4">Sizes</h2>
            <div className="flex gap-4 items-center flex-wrap">
              <Button size="xs" onClick={handleClick}>Extra Small</Button>
              <Button size="sm" onClick={handleClick}>Small</Button>
              <Button size="md" onClick={handleClick}>Medium</Button>
              <Button size="lg" onClick={handleClick}>Large</Button>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-4">States</h2>
            <div className="flex gap-4 flex-wrap">
              <Button onClick={handleClick}>Normal</Button>
              <Button loading onClick={handleClick}>Loading</Button>
              <Button disabled onClick={handleClick}>Disabled</Button>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-4">With Icons</h2>
            <div className="flex gap-4 flex-wrap">
              <Button leftIcon={<span>⬅️</span>} onClick={handleClick}>
                Left Icon
              </Button>
              <Button rightIcon={<span>➡️</span>} onClick={handleClick}>
                Right Icon
              </Button>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-4">Polymorphic</h2>
            <div className="flex gap-4 flex-wrap">
              <Button as="a" href="#" variant="outline">
                As Anchor
              </Button>
              <Button as="div" variant="ghost" onClick={handleClick}>
                As Div
              </Button>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-4">Full Width</h2>
            <Button fullWidth onClick={handleClick}>
              Full Width Button
            </Button>
          </section>
        </div>
      </div>
    </div>
  )
}

export default App
"""
    
    with open(src_path / 'App.tsx', 'w') as f:
        f.write(app_tsx)
    
    print(f"Created: {src_path / 'App.tsx'}")
    
    # Create src/test-setup.ts
    test_setup = """import '@testing-library/jest-dom'
"""
    
    with open(src_path / 'test-setup.ts', 'w') as f:
        f.write(test_setup)
    
    print(f"Created: {src_path / 'test-setup.ts'}")
    
    # Create missing test utility file referenced in tests
    test_utils_path = src_path / 'components' / 'Button' / '__test-utils__'
    test_utils_path.mkdir(parents=True, exist_ok=True)
    
    custom_comp = """import React from 'react'

const CustomComp = React.forwardRef<HTMLDivElement, any>((props, ref) => (
  <div ref={ref} {...props} />
))

export default CustomComp
"""
    
    with open(test_utils_path / 'CustomComp.tsx', 'w') as f:
        f.write(custom_comp)
    
    print(f"Created: {test_utils_path / 'CustomComp.tsx'}")
    
    # Create index.html
    index_html = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Button Component Demo</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""
    
    with open(app_path / 'index.html', 'w') as f:
        f.write(index_html)
    
    print(f"Created: {app_path / 'index.html'}")
    
    return app_path

if __name__ == '__main__':
    base_path = Path('/home/soryhyun/DiPeO/projects/frontend_enhance')
    app_path = create_react_app_structure(base_path)
    
    print(f"\n✅ React app structure created at: {app_path}")
    print("\nNext steps:")
    print(f"1. cd {app_path}")
    print("2. pnpm install")
    print("3. pnpm dev")