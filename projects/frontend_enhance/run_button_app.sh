#!/bin/bash

# Script to run the Button component React app

APP_DIR="/home/soryhyun/DiPeO/projects/frontend_enhance/button-app"

echo "🚀 Starting Button Component Demo App..."
echo "=================================="

cd "$APP_DIR"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    pnpm install
fi

echo ""
echo "🌟 Starting development server..."
echo "Open http://localhost:5173 in your browser"
echo ""

# Start the dev server
pnpm dev