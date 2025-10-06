"""Extract frontend code from generated JSON and set up React app structure."""

import json
import os
import re
from pathlib import Path
from typing import Any


def extract_code_blocks(content: str) -> dict[str, str]:
    """Extract code blocks with filenames. Handles numbered lists, comment headers, and direct paths."""
    files = {}

    pattern1 = r"(\d+\))\s+([^`\n]+?)(?:\n[^`]*)?```(\w+)?\n(.*?)```"
    pattern2 = r"(?://|#)\s*([\w/\-\.]+\.\w+)\s*\n```(\w+)?\n(.*?)```"
    pattern3 = r"^([\w/\-\.]+\.\w+)\s*:?\s*\n```(\w+)?\n(.*?)```"

    for pattern in [pattern1, pattern2, pattern3]:
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)

        for match in matches:
            if len(match) == 4:
                num, description, lang, code = match
                file_path = extract_file_path(description)
            elif len(match) == 3:
                file_path_raw, lang, code = match
                file_path = file_path_raw.strip()
            else:
                continue

            if file_path and code.strip():
                if not file_path.startswith("src/") and "src/" in file_path:
                    src_match = re.search(r"(src/[^\s]+)", file_path)
                    if src_match:
                        file_path = src_match.group(1)

                files[file_path] = code.strip()

    inline_pattern = r"// ([\w/\-\.]+\.\w+)\n([^`]+?)(?=\n//|\n\n|\Z)"
    inline_matches = re.findall(inline_pattern, content, re.MULTILINE | re.DOTALL)
    for file_path, code in inline_matches:
        if file_path and code.strip() and file_path not in files:
            files[file_path] = code.strip()

    return files


def extract_file_path(description: str) -> str:
    """Extract file path from a description string."""
    extensions = r"\.(?:ts|tsx|js|jsx|css|scss|md|json|yaml|yml|txt|html)"

    patterns = [
        rf"((?:src/|components/|utils/|hooks/|contexts/|services/|tests?/)[^\s]+{extensions})",
        rf"([^\s/]+{extensions})",
        rf"([\w/\-\.]+{extensions})",
    ]

    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(1)

    return ""


def detect_dependencies(files: dict[str, str]) -> tuple[dict[str, str], dict[str, str]]:
    """Detect required dependencies based on code content."""
    dependencies = {"react": "^18.2.0", "react-dom": "^18.2.0"}
    dev_dependencies = {
        "@types/react": "^18.2.0",
        "@types/react-dom": "^18.2.0",
        "@vitejs/plugin-react": "^4.0.0",
        "typescript": "^5.3.3",
        "vite": "^5.0.0",
    }

    all_code = "\n".join(files.values())

    if "tailwind" in all_code.lower() or "@tailwind" in all_code:
        dependencies["clsx"] = "^2.0.0"
        dev_dependencies.update(
            {"autoprefixer": "^10.4.16", "postcss": "^8.4.32", "tailwindcss": "^3.3.6"}
        )

    if "@testing-library" in all_code or "test(" in all_code or "describe(" in all_code:
        dev_dependencies.update(
            {
                "@testing-library/react": "^14.0.0",
                "@testing-library/jest-dom": "^6.0.0",
                "vitest": "^1.0.0",
                "@vitest/ui": "^1.0.0",
            }
        )

    if "react-hook-form" in all_code:
        dependencies["react-hook-form"] = "^7.48.0"

    if "react-query" in all_code or "@tanstack/react-query" in all_code:
        dependencies["@tanstack/react-query"] = "^5.0.0"
    elif "swr" in all_code.lower():
        dependencies["swr"] = "^2.2.0"

    if "react-router" in all_code or "useNavigate" in all_code:
        dependencies["react-router-dom"] = "^6.20.0"
        dev_dependencies["@types/react-router-dom"] = "^5.3.3"

    return dependencies, dev_dependencies


def create_config_files(app_path: Path, files: dict[str, str], app_name: str = "generated-app"):
    """Create all configuration files for the React app."""
    deps, dev_deps = detect_dependencies(files)

    package_json = {
        "name": app_name,
        "version": "1.0.0",
        "private": True,
        "scripts": {
            "dev": "vite",
            "build": "tsc && vite build",
            "preview": "vite preview",
            "test": "vitest",
            "test:ui": "vitest --ui",
            "typecheck": "tsc --noEmit",
            "lint": "eslint src --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
        },
        "dependencies": deps,
        "devDependencies": dev_deps,
    }

    with (app_path / "package.json").open("w") as f:
        json.dump(package_json, f, indent=2)

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

    with (app_path / "vite.config.ts").open("w") as f:
        f.write(vite_config)

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
            "noFallthroughCasesInSwitch": True,
        },
        "include": ["src"],
        "references": [{"path": "./tsconfig.node.json"}],
    }

    with (app_path / "tsconfig.json").open("w") as f:
        json.dump(tsconfig, f, indent=2)

    tsconfig_node = {
        "compilerOptions": {
            "composite": True,
            "skipLibCheck": True,
            "module": "ESNext",
            "moduleResolution": "bundler",
            "allowSyntheticDefaultImports": True,
        },
        "include": ["vite.config.ts"],
    }

    with (app_path / "tsconfig.node.json").open("w") as f:
        json.dump(tsconfig_node, f, indent=2)

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

    with (app_path / "tailwind.config.js").open("w") as f:
        f.write(tailwind_config)

    postcss_config = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""

    with (app_path / "postcss.config.js").open("w") as f:
        f.write(postcss_config)

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

    with (app_path / "index.html").open("w") as f:
        f.write(index_html)


def detect_css_imports(files: dict[str, str]) -> str:
    """Detect CSS file imports in the generated code to determine the expected CSS filename."""
    css_import_pattern = r"import\s+['\"]\./([\w/-]+\.css)['\"]"

    for file_path, content in files.items():
        if file_path.endswith((".tsx", ".ts", ".jsx", ".js")):
            matches = re.findall(css_import_pattern, content)
            for match in matches:
                if "main" in file_path.lower():
                    return match

    for file_path, content in files.items():
        if file_path.endswith((".tsx", ".ts", ".jsx", ".js")):
            matches = re.findall(css_import_pattern, content)
            if matches:
                return matches[0]

    return "index.css"


def _check_existing_files(files: dict[str, str]) -> tuple[bool, bool, bool]:
    """Check if critical files already exist."""
    has_main = any("main.tsx" in f or "main.ts" in f or "index.tsx" in f for f in files)
    has_app = any("App.tsx" in f or "App.ts" in f for f in files)
    has_styles = any(".css" in f for f in files)
    return has_main, has_app, has_styles


def _detect_styling_config(files: dict[str, str]) -> tuple[bool, str | None]:
    """Detect styling configuration from files."""
    uses_tailwind = any("@tailwind" in content for content in files.values())
    expected_css_file = detect_css_imports(files)
    return uses_tailwind, expected_css_file


def _create_css_content(uses_tailwind: bool) -> str:
    """Create CSS content based on styling configuration."""
    if uses_tailwind:
        return """@tailwind base;
@tailwind components;
@tailwind utilities;
"""
    else:
        return """/* Global styles */
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


def _create_main_tsx(files: dict[str, str], expected_css_file: str | None) -> str:
    """Create main.tsx content with appropriate style imports."""
    style_import = None
    if expected_css_file:
        style_import = f"./{expected_css_file}"
    elif "src/index.css" in files:
        style_import = "./index.css"
    elif "src/styles.css" in files:
        style_import = "./styles.css"
    elif "src/styles/global.css" in files:
        style_import = "./styles/global.css"

    return f"""import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
{f"import '{style_import}'" if style_import else ""}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
"""


def _detect_components(files: dict[str, str]) -> tuple[list[str], set[str]]:
    """Detect components from the files."""
    component_imports = []
    component_names = set()

    for file_path in files:
        if "components/" in file_path and file_path.endswith(".tsx"):
            match = re.search(r"components/(\w+)/(\w+)\.tsx", file_path)
            if match and match.group(1) == match.group(2):
                comp_name = match.group(1)
                if comp_name not in ["index"]:
                    component_names.add(comp_name)
                    component_imports.append(
                        f"import {{ {comp_name} }} from './components/{comp_name}'"
                    )

        elif file_path.startswith("src/") and file_path.endswith(".tsx"):
            if any(
                skip in file_path.lower()
                for skip in [
                    "main",
                    "app",
                    "test",
                    "setup",
                    "types",
                    "adapter",
                    "context",
                    "hook",
                    "utils",
                    "stories",
                    "example",
                ]
            ):
                continue

            file_name = Path(file_path).stem
            if file_name and file_name[0].isupper():
                content = files.get(file_path, "")
                if "export" in content and (
                    "function " + file_name in content
                    or "const " + file_name in content
                    or "export default" in content
                ):
                    component_names.add(file_name)
                    component_imports.append(f"import {{ {file_name} }} from './{file_name}'")

    return component_imports, component_names


def _generate_component_usage(comp_name: str) -> str:
    """Generate component usage based on component type."""
    if "List" in comp_name:
        # For List components, provide sample data
        return f"""
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
    elif "Button" in comp_name:
        # For Button components, show variations
        return f"""
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
        return f"""
          <section>
            <h2 className="text-xl font-semibold mb-4">{comp_name} Component Demo</h2>
            <{comp_name} />
          </section>"""


def _create_app_tsx(component_imports: list[str], component_names: set[str]) -> str:
    """Create App.tsx content based on detected components."""
    if component_names:
        imports = "\n".join(component_imports[:3])
        comp_name = next(iter(component_names))
        component_usage = _generate_component_usage(comp_name)

        return f"""{imports}

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
        return """function App() {
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


def create_app_files(app_path: Path, files: dict[str, str]):
    """Create main app files dynamically based on extracted components."""
    src_path = app_path / "src"
    src_path.mkdir(exist_ok=True)

    has_main, has_app, has_styles = _check_existing_files(files)
    uses_tailwind, expected_css_file = _detect_styling_config(files)

    if has_styles:
        expected_css_file = None

    if not has_styles and expected_css_file:
        css_path = f"src/{expected_css_file}"
        css_content = _create_css_content(uses_tailwind)
        files[css_path] = css_content

    if not has_main:
        main_tsx = _create_main_tsx(files, expected_css_file)
        files["src/main.tsx"] = main_tsx

    if not has_app:
        component_imports, component_names = _detect_components(files)
        app_tsx = _create_app_tsx(component_imports, component_names)
        files["src/App.tsx"] = app_tsx

    if any("test" in f.lower() for f in files):
        if "src/test-setup.ts" not in files:
            files["src/test-setup.ts"] = "import '@testing-library/jest-dom'"


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
    with run_script_path.open("w") as f:
        f.write(run_script)

    run_script_path.chmod(0o755)

    print(f"✅ Created run script: {script_name}")


def get_app_name_from_content(files: dict[str, str]) -> str:
    """Detect app name from generated content."""
    for file_path in files:
        if "components/" in file_path:
            match = re.search(r"components/(\w+)/", file_path)
            if match:
                return f"{match.group(1).lower()}-app"

    all_code = " ".join(files.values())[:1000].lower()
    if "list" in all_code:
        return "list-app"
    elif "button" in all_code:
        return "button-app"
    elif "dashboard" in all_code:
        return "dashboard-app"

    return "generated-app"


def validate_extracted_files(files: dict[str, str]) -> dict[str, Any]:
    """Validate extracted files and provide insights."""
    validation = {
        "total_files": len(files),
        "has_components": any("components/" in f for f in files),
        "has_tests": any("test" in f.lower() for f in files),
        "has_styles": any(".css" in f for f in files),
        "has_typescript": any(".ts" in f or ".tsx" in f for f in files),
        "component_count": len([f for f in files if "components/" in f and ".tsx" in f]),
        "test_count": len([f for f in files if "test" in f.lower()]),
    }
    return validation


def main(inputs):
    """Main function to extract and setup the React app."""
    dipeo_base = os.environ.get("DIPEO_BASE_DIR", ".")
    base_path = Path(dipeo_base)

    generated_code = inputs.get("generated_code", "")
    section_id = inputs.get("section_id")

    content = generated_code if isinstance(generated_code, str) else json.dumps(generated_code)

    files = extract_code_blocks(content)

    if not files:
        return {
            "app_created": False,
            "error": "No code blocks found in generated content",
            "status": "Failed to extract code",
        }

    validation = validate_extracted_files(files)
    app_name = f"section-{section_id}" if section_id else get_app_name_from_content(files)

    app_path = base_path / "projects" / "frontend_enhance" / app_name
    app_path.mkdir(parents=True, exist_ok=True)

    create_app_files(app_path, files)

    for file_path, code in files.items():
        full_path = app_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        if file_path.endswith(".ts") and ("tsx" in code or "JSX" in code or "React" in code):
            full_path = full_path.with_suffix(".tsx")

        with full_path.open("w") as f:
            f.write(code)

    create_config_files(app_path, files, app_name)
    create_run_script(base_path / "projects" / "frontend_enhance", app_name)

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
        "status": f"App '{app_name}' created successfully with {len(files)} files",
    }

    return result
