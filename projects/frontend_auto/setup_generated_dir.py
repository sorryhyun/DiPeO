#!/usr/bin/env python3
"""
Setup the generated directory with base configuration files before generation starts.
This ensures all config files are in place before any source code generation.
"""

import json
import os
import shutil
from pathlib import Path


def setup_generated_directory(inputs=None):
    """
    Initialize the generated directory with base configuration files.

    This function:
    1. Creates the generated directory if it doesn't exist
    2. Copies all base configuration files from base_configs/
    3. Creates necessary subdirectories (src/, etc.)
    4. Returns status for the diagram flow
    """

    # Get base directory from environment or use current file's location
    dipeo_base = os.environ.get("DIPEO_BASE_DIR")
    if dipeo_base:
        project_dir = Path(dipeo_base) / "projects" / "frontend_auto"
    else:
        # Fallback to relative path from script location
        project_dir = Path(__file__).parent

    base_configs_dir = project_dir / "base_configs"
    generated_dir = project_dir / "generated"

    # Check if base_configs directory exists
    if not base_configs_dir.exists():
        print(f"Error: Base configs directory not found at {base_configs_dir}")
        return {"success": False, "error": "Base configs directory not found"}

    # Create generated directory if it doesn't exist
    generated_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Ensured generated directory exists at {generated_dir}")

    # Create src directory
    src_dir = generated_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created src directory at {src_dir}")

    # List of config files to copy
    config_files = [
        "package.json",
        "tsconfig.json",
        "tsconfig.node.json",
        "vite.config.ts",
        "vite-env.d.ts",
        "tailwind.config.js",
        "postcss.config.js",
        "index.html",
        ".gitignore",
        ".eslintrc.json",
    ]

    copied_count = 0
    for config_file in config_files:
        source = base_configs_dir / config_file
        target = generated_dir / config_file

        if source.exists():
            shutil.copy2(source, target)
            print(f"✓ Copied {config_file} to generated/")
            copied_count += 1
        else:
            print(f"⚠ Warning: {config_file} not found in base_configs/")

    # Create additional directories that might be needed
    additional_dirs = [
        "src/core",
        "src/app",
        "src/providers",
        "src/services",
        "src/hooks",
        "src/components",
        "src/components/shared",
        "src/components/nodes",
        "src/components/connections",
        "src/features",
        "src/pages",
        "src/utils",
        "src/constants",
        "src/styles",
        "src/mocks",
        "src/plugins",
        "src/workers",
    ]

    for dir_path in additional_dirs:
        full_path = generated_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)

    print("✓ Created all necessary subdirectories")

    # Create a basic styles/tailwind.css file if it doesn't exist
    tailwind_css = generated_dir / "src" / "styles" / "tailwind.css"
    if not tailwind_css.exists():
        tailwind_css.write_text("""@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
""")
        print("✓ Created src/styles/tailwind.css")

    print(
        f"\n✅ Setup complete! Copied {copied_count} config files and created directory structure"
    )

    # Return success status for diagram flow
    return {"success": True, "copied_files": copied_count, "generated_dir": str(generated_dir)}


if __name__ == "__main__":
    result = setup_generated_directory()
    print(json.dumps(result, indent=2))
