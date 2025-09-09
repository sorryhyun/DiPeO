#!/usr/bin/env python3
"""Kill all claude processes to clean up accumulated subprocesses."""

import sys

import psutil


def kill_all_claude_processes():
    """Find and kill all claude processes."""
    killed_count = 0

    try:
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                # Check if it's a claude process
                if proc.info["name"] and "claude" in proc.info["name"].lower():
                    print(f"Killing claude process PID {proc.info['pid']}")
                    proc.kill()
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
            except Exception as e:
                print(f"Error checking process: {e}")

    except Exception as e:
        print(f"Error iterating processes: {e}")
        return 1

    print(f"\nKilled {killed_count} claude process(es)")
    return 0


if __name__ == "__main__":
    sys.exit(kill_all_claude_processes())
