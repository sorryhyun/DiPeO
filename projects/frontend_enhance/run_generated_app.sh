#!/bin/bash
# Auto-generated script to run generated-app
DIPEO_BASE="${DIPEO_BASE_DIR:-/home/soryhyun/DiPeO/projects/frontend_enhance}"
APP_DIR="${DIPEO_BASE}/generated-app"

echo "🚀 Starting generated-app..."
echo "📁 App directory: $APP_DIR"

cd "$APP_DIR" || exit 1

if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    pnpm install
fi

echo "🌟 Starting development server..."
echo "Open http://localhost:5173 in your browser"
pnpm dev
