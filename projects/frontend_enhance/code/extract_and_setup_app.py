"""Extract frontend code from generated JSON and set up React app structure."""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, Tuple


def extract_code_blocks(content: str) -> Dict[str, str]:
    """Extract code blocks from the text with their filenames.
    
    Handles multiple formats:
    - Numbered lists with file paths
    - Direct file paths in comments
    - Section headers with code blocks
    """
    files = {}
    
    # Enhanced pattern to match various code block formats
    # Pattern 1: Numbered list format (1) path/to/file.ext)
    pattern1 = r'(\d+\))\s+([^`\n]+?)(?:\n[^`]*)?```(\w+)?\n(.*?)```'
    
    # Pattern 2: Comment format (// path/to/file.ext or # path/to/file.ext)
    pattern2 = r'(?://|#)\s*([\w/\-\.]+\.\w+)\s*\n```(\w+)?\n(.*?)```'
    
    # Pattern 3: Direct file path before code block
    pattern3 = r'^([\w/\-\.]+\.\w+)\s*:?\s*\n```(\w+)?\n(.*?)```'
    
    # Try all patterns
    for pattern in [pattern1, pattern2, pattern3]:
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            if len(match) == 4:  # Pattern 1
                num, description, lang, code = match
                file_path = extract_file_path(description)
            elif len(match) == 3:  # Pattern 2 or 3
                file_path_raw, lang, code = match
                file_path = file_path_raw.strip()
            else:
                continue
                
            if file_path and code.strip():
                # Normalize the file path
                if not file_path.startswith('src/') and 'src/' in file_path:
                    # Extract src/ path if embedded
                    src_match = re.search(r'(src/[^\s]+)', file_path)
                    if src_match:
                        file_path = src_match.group(1)
                
                # Clean up the code
                code = code.strip()
                
                # Store the file
                files[file_path] = code
    
    # Also try to extract inline file definitions
    inline_pattern = r'// ([\w/\-\.]+\.\w+)\n([^`]+?)(?=\n//|\n\n|\Z)'
    inline_matches = re.findall(inline_pattern, content, re.MULTILINE | re.DOTALL)
    for file_path, code in inline_matches:
        if file_path and code.strip() and file_path not in files:
            files[file_path] = code.strip()
    
    return files


def extract_file_path(description: str) -> str:
    """Extract file path from a description string."""
    # Look for common file extensions
    extensions = r'\.(?:ts|tsx|js|jsx|css|scss|md|json|yaml|yml|txt|html)'
    
    # Try different path patterns
    patterns = [
        rf'((?:src/|components/|utils/|hooks/|contexts/|services/|tests?/)[^\s]+{extensions})',
        rf'([^\s/]+{extensions})',  # Just filename
        rf'([\w/\-\.]+{extensions})'  # Any path with extension
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return ""


def detect_dependencies(files: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Detect required dependencies based on code content."""
    dependencies = {
        "react": "^18.2.0",
        "react-dom": "^18.2.0"
    }
    dev_dependencies = {
        "@types/react": "^18.2.0",
        "@types/react-dom": "^18.2.0",
        "@vitejs/plugin-react": "^4.0.0",
        "typescript": "^5.3.3",
        "vite": "^5.0.0"
    }
    
    # Check all files for specific imports/usage
    all_code = "\n".join(files.values())
    
    # Detect styling libraries
    if "tailwind" in all_code.lower() or "@tailwind" in all_code:
        dependencies["clsx"] = "^2.0.0"
        dev_dependencies.update({
            "autoprefixer": "^10.4.16",
            "postcss": "^8.4.32",
            "tailwindcss": "^3.3.6"
        })
    
    # Detect testing libraries
    if "@testing-library" in all_code or "test(" in all_code or "describe(" in all_code:
        dev_dependencies.update({
            "@testing-library/react": "^14.0.0",
            "@testing-library/jest-dom": "^6.0.0",
            "vitest": "^1.0.0",
            "@vitest/ui": "^1.0.0"
        })
    
    # Detect form libraries
    if "react-hook-form" in all_code:
        dependencies["react-hook-form"] = "^7.48.0"
    
    # Detect data fetching
    if "react-query" in all_code or "@tanstack/react-query" in all_code:
        dependencies["@tanstack/react-query"] = "^5.0.0"
    elif "swr" in all_code.lower():
        dependencies["swr"] = "^2.2.0"
    
    # Detect routing
    if "react-router" in all_code or "useNavigate" in all_code:
        dependencies["react-router-dom"] = "^6.20.0"
        dev_dependencies["@types/react-router-dom"] = "^5.3.3"
    
    return dependencies, dev_dependencies


def create_config_files(app_path: Path, files: Dict[str, str], app_name: str = "generated-app"):
    """Create all configuration files for the React app."""
    # Detect dependencies from code
    deps, dev_deps = detect_dependencies(files)
    
    # Create package.json
    package_json = {
        "name": app_name,
        "version": "0.1.0",
        "private": True,
        "scripts": {
            "dev": "vite",
            "build": "tsc && vite build",
            "preview": "vite preview",
            "test": "vitest",
            "test:ui": "vitest --ui",
            "typecheck": "tsc --noEmit",
            "lint": "eslint src --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
        },
        "dependencies": deps,
        "devDependencies": dev_deps
    }
    
    with open(app_path / 'package.json', 'w') as f:
        json.dump(package_json, f, indent=2)
    
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


def detect_css_imports(files: Dict[str, str]) -> str:
    """Detect CSS file imports in the generated code to determine the expected CSS filename."""
    css_import_pattern = r"import\s+['\"]\./([\w/-]+\.css)['\"]"
    
    # Check all TypeScript/JavaScript files for CSS imports
    for file_path, content in files.items():
        if file_path.endswith(('.tsx', '.ts', '.jsx', '.js')):
            matches = re.findall(css_import_pattern, content)
            for match in matches:
                # Return the first CSS import found (prioritize main.tsx)
                if 'main' in file_path.lower():
                    return match
    
    # If no specific CSS import found in main, check other files
    for file_path, content in files.items():
        if file_path.endswith(('.tsx', '.ts', '.jsx', '.js')):
            matches = re.findall(css_import_pattern, content)
            if matches:
                return matches[0]
    
    # Default to index.css if no imports found
    return 'index.css'


def create_app_files(app_path: Path, files: Dict[str, str]):
    """Create main app files dynamically based on extracted components."""
    src_path = app_path / 'src'
    src_path.mkdir(exist_ok=True)
    
    # Check if files already contain these critical files
    has_main = any('main.tsx' in f or 'main.ts' in f or 'index.tsx' in f for f in files)
    has_app = any('App.tsx' in f or 'App.ts' in f for f in files)
    has_styles = any('.css' in f for f in files)
    
    # Detect if using Tailwind
    uses_tailwind = any('@tailwind' in content for content in files.values())
    
    # Detect expected CSS filename from imports
    expected_css_file = detect_css_imports(files) if not has_styles else None
    
    # Create CSS file if needed
    if not has_styles and expected_css_file:
        css_path = f"src/{expected_css_file}"
        
        if uses_tailwind:
            css_content = """@tailwind base;
@tailwind components;
@tailwind utilities;
"""
        else:
            css_content = """/* Global styles */
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
"""
        files[css_path] = css_content
    
    # Create src/main.tsx if not present
    if not has_main:
        # Determine style import based on what CSS files exist or are expected
        style_import = None
        if expected_css_file:
            style_import = f"./{expected_css_file}"
        elif 'src/index.css' in files:
            style_import = "./index.css"
        elif 'src/styles.css' in files:
            style_import = "./styles.css"
        elif 'src/styles/global.css' in files:
            style_import = "./styles/global.css"
        
        main_tsx = f"""import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
{f"import '{style_import}'" if style_import else ""}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
"""
        files['src/main.tsx'] = main_tsx
    
    # Create src/App.tsx if not present
    if not has_app:
        # Detect what components were generated
        component_imports = []
        component_names = set()
        
        for file_path in files:
            # Check for components in components/ subdirectory
            if 'components/' in file_path and file_path.endswith('.tsx'):
                # Extract component name
                match = re.search(r'components/(\w+)/(\w+)\.tsx', file_path)
                if match and match.group(1) == match.group(2):
                    comp_name = match.group(1)
                    if comp_name not in ['index']:
                        component_names.add(comp_name)
                        component_imports.append(f"import {{ {comp_name} }} from './components/{comp_name}'")
            
            # Also check for components directly in src/ (like src/List.tsx)
            elif file_path.startswith('src/') and file_path.endswith('.tsx'):
                # Skip main, App, test files, and supporting files
                if any(skip in file_path.lower() for skip in ['main', 'app', 'test', 'setup', 'types', 'adapter', 'context', 'hook', 'utils', 'stories', 'example']):
                    continue
                    
                # Extract component name from file (e.g., src/List.tsx -> List)
                file_name = Path(file_path).stem
                if file_name and file_name[0].isupper():  # Component names should start with uppercase
                    # Try to verify it's actually a React component by checking content
                    content = files.get(file_path, '')
                    if 'export' in content and ('function ' + file_name in content or 'const ' + file_name in content or 'export default' in content):
                        component_names.add(file_name)
                        component_imports.append(f"import {{ {file_name} }} from './{file_name}'")
        
        # Generate a dynamic App.tsx based on detected components
        if component_names:
            imports = "\n".join(component_imports[:3])  # Limit to first 3 components
            comp_name = list(component_names)[0]
            
            # Generate component usage based on component type
            component_usage = ""
            if 'List' in comp_name:
                # For List components, provide sample data
                component_usage = f"""
          <section>
            <h2 className="text-xl font-semibold mb-4">{comp_name} Component Demo</h2>
            <{comp_name} 
              items={{[
                {{ id: '1', name: 'First Item', description: 'This is the first item' }},
                {{ id: '2', name: 'Second Item', description: 'This is the second item' }},
                {{ id: '3', name: 'Third Item', description: 'This is the third item' }},
              ]}}
            />
          </section>"""
            elif 'Button' in comp_name:
                # For Button components, show variations
                component_usage = f"""
          <section>
            <h2 className="text-xl font-semibold mb-4">{comp_name} Component Demo</h2>
            <div className="space-x-4">
              <{comp_name} onClick={{() => alert('Primary clicked!')}}>Primary</{comp_name}>
              <{comp_name} variant="secondary" onClick={{() => alert('Secondary clicked!')}}>Secondary</{comp_name}>
              <{comp_name} variant="outline" onClick={{() => alert('Outline clicked!')}}>Outline</{comp_name}>
            </div>
          </section>"""
            else:
                # Default component usage
                component_usage = f"""
          <section>
            <h2 className="text-xl font-semibold mb-4">{comp_name} Component Demo</h2>
            <{comp_name} />
          </section>"""
            
            app_tsx = f"""{imports}

function App() {{
  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">{comp_name} Component Showcase</h1>
        
        <div className="space-y-8 bg-white p-8 rounded-lg shadow">{component_usage}
        </div>
      </div>
    </div>
  )
}}

export default App
"""
        else:
            # Fallback generic App
            app_tsx = """function App() {
  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">React App</h1>
        <p>Your generated components are ready!</p>
      </div>
    </div>
  )
}

export default App
"""
        files['src/App.tsx'] = app_tsx
    
    # Create test setup if tests exist
    if any('test' in f.lower() for f in files):
        if 'src/test-setup.ts' not in files:
            files['src/test-setup.ts'] = "import '@testing-library/jest-dom'"


def create_run_script(base_path: Path, app_name: str):
    """Create a run script for the app."""
    script_name = f"run_{app_name.replace('-', '_')}.sh"
    
    run_script = f"""#!/bin/bash
# Auto-generated script to run {app_name}
DIPEO_BASE="${{DIPEO_BASE_DIR:-{base_path}}}"
APP_DIR="${{DIPEO_BASE}}/{app_name}"

echo "🚀 Starting {app_name}..."
echo "📁 App directory: $APP_DIR"

cd "$APP_DIR" || exit 1

if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    pnpm install
fi

echo "🌟 Starting development server..."
echo "Open http://localhost:5173 in your browser"
pnpm dev
"""
    
    run_script_path = base_path / script_name
    with open(run_script_path, 'w') as f:
        f.write(run_script)
    
    os.chmod(run_script_path, 0o755)
    
    print(f"✅ Created run script: {script_name}")


def get_app_name_from_content(files: Dict[str, str]) -> str:
    """Detect app name from generated content."""
    # Try to find component names
    for file_path in files:
        if 'components/' in file_path:
            match = re.search(r'components/(\w+)/', file_path)
            if match:
                return f"{match.group(1).lower()}-app"
    
    # Check for specific patterns in code
    all_code = " ".join(files.values())[:1000].lower()
    if 'list' in all_code:
        return "list-app"
    elif 'button' in all_code:
        return "button-app"
    elif 'dashboard' in all_code:
        return "dashboard-app"
    
    return "generated-app"


def validate_extracted_files(files: Dict[str, str]) -> Dict[str, Any]:
    """Validate extracted files and provide insights."""
    validation = {
        "total_files": len(files),
        "has_components": any('components/' in f for f in files),
        "has_tests": any('test' in f.lower() for f in files),
        "has_styles": any('.css' in f for f in files),
        "has_typescript": any('.ts' in f or '.tsx' in f for f in files),
        "component_count": len([f for f in files if 'components/' in f and '.tsx' in f]),
        "test_count": len([f for f in files if 'test' in f.lower()]),
    }
    return validation


def main(inputs):
    """Main function to extract and setup the React app."""
    # Get DiPeO base directory from environment
    dipeo_base = os.environ.get('DIPEO_BASE_DIR', '.')
    base_path = Path(dipeo_base)
    
    # Parse inputs
    generated_code = inputs.get('generated_code', '')
    section_id = inputs.get('section_id')  # optional section ID for naming
    
    if isinstance(generated_code, str):
        content = generated_code
    else:
        content = json.dumps(generated_code)
    
    # Extract code blocks with their filenames
    files = extract_code_blocks(content)
    
    if not files:
        return {
            "app_created": False,
            "error": "No code blocks found in generated content",
            "status": "Failed to extract code"
        }
    
    # Validate extracted files
    validation = validate_extracted_files(files)
    
    # Determine app name from content (or use section_id if provided)
    if section_id:
        app_name = f"section-{section_id}"
    else:
        app_name = get_app_name_from_content(files)
    
    # Create the app structure with proper base path
    app_path = base_path / 'projects' / 'frontend_enhance' / app_name
    app_path.mkdir(parents=True, exist_ok=True)
    
    # Create app files if missing (adds to files dict)
    create_app_files(app_path, files)
    
    # Create all files (both extracted and generated)
    for file_path, code in files.items():
        full_path = app_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Fix file extensions for TypeScript React files
        if file_path.endswith('.ts') and ('tsx' in code or 'JSX' in code or 'React' in code):
            full_path = full_path.with_suffix('.tsx')
        
        with open(full_path, 'w') as f:
            f.write(code)
    
    # Create configuration files
    create_config_files(app_path, files, app_name)
    
    # Create run script with proper base path
    create_run_script(base_path / 'projects' / 'frontend_enhance', app_name)
    
    # Calculate relative path for output
    try:
        relative_path = app_path.relative_to(base_path)
    except ValueError:
        relative_path = app_path
    
    result = {
        "app_created": True,
        "app_path": str(relative_path),
        "app_name": app_name,
        "files_created": len(files),
        "validation": validation,
        "run_command": f"cd {relative_path} && pnpm install && pnpm dev",
        "status": f"App '{app_name}' created successfully with {len(files)} files"
    }
    
    return result