#!/usr/bin/env python3
"""
DiPeO Frontend Static Server
Serves the built frontend files and opens browser
"""

import subprocess
import webbrowser
import time
import os
import sys
from pathlib import Path
import http.server
import socketserver
import threading

PORT = 3000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add headers for better compatibility
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()
    
    def do_GET(self):
        # Serve index.html for all routes (SPA support)
        if not self.path.startswith('/assets') and not '.' in self.path.split('/')[-1]:
            self.path = '/index.html'
        return super().do_GET()

def serve_forever(httpd):
    """Run the server in a thread"""
    with httpd:
        httpd.serve_forever()

def main():
    # Get the directory where this script is located
    if getattr(sys, 'frozen', False):
        # If running as compiled exe
        script_dir = Path(sys.executable).parent
    else:
        # If running as script
        script_dir = Path(__file__).parent
    
    # Look for the dist directory
    dist_dir = script_dir / "dist"
    if not dist_dir.exists() and (script_dir / "web-dist").exists():
        dist_dir = script_dir / "web-dist"
    
    if not dist_dir.exists():
        print("ERROR: Frontend build files not found!")
        print(f"Expected at: {dist_dir}")
        print("\nPlease build the frontend first with:")
        print("  cd apps/web")
        print("  pnpm build")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Change to the dist directory
    os.chdir(dist_dir)
    
    print("DiPeO Frontend Server")
    print("====================")
    print(f"Serving files from: {dist_dir}")
    print(f"Starting server on http://localhost:{PORT}")
    
    # Create and start the server
    handler = MyHTTPRequestHandler
    httpd = socketserver.TCPServer(("", PORT), handler)
    
    # Start server in a thread
    server_thread = threading.Thread(target=serve_forever, args=(httpd,))
    server_thread.daemon = True
    server_thread.start()
    
    # Wait a moment then open browser
    time.sleep(1)
    url = f"http://localhost:{PORT}"
    print(f"\nOpening browser at {url}")
    webbrowser.open(url)
    
    print("\nServer is running. Press Ctrl+C to stop.")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        httpd.shutdown()
        print("Server stopped.")

if __name__ == "__main__":
    main()