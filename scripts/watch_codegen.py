#!/usr/bin/env python3
"""
Watch for changes in node specifications and automatically trigger code generation.
Usage: python scripts/watch_codegen.py [--interval SECONDS]
"""

import os
import sys
import json
import time
import hashlib
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

def get_file_checksum(filepath):
    """Calculate MD5 checksum of a file."""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def load_checksums(cache_file):
    """Load previous checksums from cache."""
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)
    return {}

def save_checksums(cache_file, checksums):
    """Save checksums to cache."""
    with open(cache_file, 'w') as f:
        json.dump(checksums, f, indent=2)

def check_for_changes(spec_dir, cache_file):
    """Check for changed specification files."""
    previous_checksums = load_checksums(cache_file)
    current_checksums = {}
    changed_specs = []
    
    # Check all spec files
    spec_path = Path(spec_dir)
    if spec_path.exists():
        for spec_file in spec_path.glob('*.json'):
            filename = spec_file.name
            checksum = get_file_checksum(spec_file)
            current_checksums[filename] = checksum
            
            # Check if file has changed
            if filename not in previous_checksums or previous_checksums[filename] != checksum:
                changed_specs.append(spec_file)
    
    # Save current checksums
    save_checksums(cache_file, current_checksums)
    
    return changed_specs, len(current_checksums)

def trigger_codegen(spec_file):
    """Trigger code generation for a specific spec file."""
    print(f"🔄 Regenerating code for: {spec_file.name}")
    
    cmd = [
        'dipeo', 'run', 'codegen/main',
        '--light',
        '--vars', f'NODE_SPEC_PATH={spec_file}',
        '--no-browser',
        '--timeout=60'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Successfully regenerated code for {spec_file.name}")
        else:
            print(f"❌ Failed to regenerate code for {spec_file.name}")
            if result.stderr:
                print(f"   Error: {result.stderr}")
    except Exception as e:
        print(f"❌ Error running code generation: {e}")

def main():
    parser = argparse.ArgumentParser(description='Watch node specifications for changes')
    parser.add_argument('--interval', type=int, default=5, help='Check interval in seconds')
    parser.add_argument('--spec-dir', default='files/specifications/nodes', help='Directory to watch')
    parser.add_argument('--cache-file', default='.spec_checksums.json', help='Cache file for checksums')
    args = parser.parse_args()
    
    print(f"👀 Watching for changes in: {args.spec_dir}")
    print(f"🔄 Check interval: {args.interval} seconds")
    print("Press Ctrl+C to stop watching\n")
    
    try:
        while True:
            changed_specs, total_specs = check_for_changes(args.spec_dir, args.cache_file)
            
            if changed_specs:
                print(f"\n📝 Detected {len(changed_specs)} changed specification(s):")
                for spec in changed_specs:
                    print(f"   - {spec.name}")
                print()
                
                # Trigger code generation for each changed spec
                for spec in changed_specs:
                    trigger_codegen(spec)
                print()
            else:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"\r[{timestamp}] No changes detected. Monitoring {total_specs} specifications...", end='', flush=True)
            
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopped watching for changes")
        sys.exit(0)

if __name__ == '__main__':
    main()