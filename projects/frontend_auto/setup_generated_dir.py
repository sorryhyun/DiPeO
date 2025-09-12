#!/usr/bin/env python3
"""
Setup the generated directory with base configuration files and install dependencies.
This ensures all config files and libraries are in place before any source code generation.
"""

import json
import os
import shutil
import subprocess
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

    # Install dependencies using pnpm
    print("\n📦 Installing dependencies with pnpm...")
    try:
        result = subprocess.run(
            ["pnpm", "install"],
            cwd=generated_dir,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        if result.returncode == 0:
            print("✓ Dependencies installed successfully")
        else:
            print(f"⚠ Warning: pnpm install had issues: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("⚠ Warning: pnpm install timed out")
    except FileNotFoundError:
        print("⚠ Warning: pnpm not found, skipping dependency installation")
    except Exception as e:
        print(f"⚠ Warning: Failed to install dependencies: {e}")

    # Create UI components library structure (shadcn-style)
    ui_components_dir = generated_dir / "src" / "components" / "ui"
    ui_components_dir.mkdir(parents=True, exist_ok=True)

    # Create a lib/utils.ts file for cn helper
    lib_dir = generated_dir / "src" / "lib"
    lib_dir.mkdir(parents=True, exist_ok=True)

    utils_file = lib_dir / "utils.ts"
    utils_file.write_text("""import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
""")
    print("✓ Created lib/utils.ts with cn helper")

    # Create a components.json config for shadcn-style components
    components_json = generated_dir / "components.json"
    components_json.write_text(json.dumps({
        "$schema": "https://ui.shadcn.com/schema.json",
        "style": "default",
        "rsc": False,
        "tsx": True,
        "tailwind": {
            "config": "tailwind.config.js",
            "css": "src/styles/tailwind.css",
            "baseColor": "slate",
            "cssVariables": True,
            "prefix": ""
        },
        "aliases": {
            "components": "@/components",
            "utils": "@/lib/utils"
        }
    }, indent=2))
    print("✓ Created components.json for UI library configuration")

    # Create basic UI component exports that wrap Radix UI
    # This allows the generated code to import from @/components/ui/*
    ui_index = ui_components_dir / "index.ts"
    ui_index.write_text("""// Re-export all UI components from this central location
// These components wrap Radix UI primitives with app styling

export * from './button'
export * from './card'
export * from './dialog'
export * from './input'
export * from './select'
export * from './table'
export * from './toast'
export * from './tooltip'
export * from './checkbox'
export * from './switch'
export * from './popover'
export * from './separator'
export * from './scroll-area'
export * from './skeleton'
export * from './badge'
export * from './alert'
""")
    print("✓ Created UI components index")

    # Create a sample button component that wraps Radix with CVA
    button_file = ui_components_dir / "button.tsx"
    button_file.write_text("""import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
""")
    print("✓ Created Button component wrapper")

    # Return success status for diagram flow
    return {"success": True, "copied_files": copied_count, "generated_dir": str(generated_dir)}


if __name__ == "__main__":
    result = setup_generated_directory()
    print(json.dumps(result, indent=2))
