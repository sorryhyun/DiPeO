import asyncio
import os
import signal
import subprocess
import time
from datetime import datetime
from pathlib import Path

from .api_client import DiPeoAPIClient

# Global variable to track the server process
_server_process: subprocess.Popen | None = None


def _kill_process_on_port(port: int) -> None:
    """Kill any process listening on the specified port"""
    try:
        # Find process using the port
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGKILL)
                except (ProcessLookupError, ValueError):
                    pass
    except Exception:
        # lsof might not be available on all systems
        pass


async def restart_backend_server(debug_mode: bool = True) -> None:
    """Restart the backend server to ensure latest code is loaded"""
    global _server_process
    
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[🕰️ {timestamp}] 🐛 Debug: Restarting backend server with DEBUG logging...")

    # Kill any existing server processes
    try:
        # First try to kill the tracked process if we have one
        if _server_process and _server_process.poll() is None:
            try:
                # Send SIGTERM to the process group
                os.killpg(os.getpgid(_server_process.pid), signal.SIGTERM)
                _server_process.wait(timeout=2)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                # If SIGTERM didn't work, force kill
                try:
                    os.killpg(os.getpgid(_server_process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
            _server_process = None
        
        # Also kill any other processes that might be running
        subprocess.run(
            ["pkill", "-f", "python main.py"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Also try to kill hypercorn processes
        subprocess.run(
            ["pkill", "-f", "hypercorn"], check=False, capture_output=True, text=True
        )
        
        # Ensure port 8000 is free
        _kill_process_on_port(8000)

        # Give processes time to shut down
        await asyncio.sleep(1.0)

        print("🔄 Killed existing server processes")
    except Exception as e:
        print(f"⚠️  Could not kill existing processes: {e}")

    # Start new server process with DEBUG logging
    server_path = Path(__file__).parent.parent.parent.parent.parent / "apps" / "server"
    env = os.environ.copy()
    env["LOG_LEVEL"] = "DEBUG"

    start_cmd = ["python", "main.py"]

    try:
        # Start server in background 
        # In debug mode or with verbose flag, show all output
        # Otherwise, capture output to reduce noise
        verbose_debug = env.get("VERBOSE_DEBUG", "false").lower() == "true"
        show_output = debug_mode or verbose_debug
        
        _server_process = subprocess.Popen(
            start_cmd,
            cwd=server_path,
            env=env,
            stdout=None if show_output else subprocess.DEVNULL,  # Show output in debug mode
            stderr=None if show_output else subprocess.DEVNULL,  # Show errors in debug mode
            start_new_session=True,
        )

        # Wait for server to be ready with better health check
        print("⏳ Waiting for server to start...")
        max_wait_time = 10  # seconds
        start_time = time.time()
        server_ready = False

        while time.time() - start_time < max_wait_time:
            try:
                # Use client with retry logic
                async with DiPeoAPIClient(
                    "localhost:8000", max_retries=1, retry_delay=0.5
                ) as client:
                    # Try a simple health check query
                    query = """
                        query HealthCheck {
                            __typename
                        }
                    """
                    await client._execute_query(query)
                    server_ready = True
                    break
            except Exception as e:
                elapsed = time.time() - start_time
                if elapsed < max_wait_time:
                    # Show progress with timestamp
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    print(
                        f"   [🕰️ {timestamp}] Server not ready yet ({elapsed:.1f}s elapsed)..."
                    )
                    await asyncio.sleep(0.5)
                else:
                    print(f"❌ Server failed to start after {max_wait_time}s")
                    print(f"   Last error: {e!s}")
                    raise

        if not server_ready:
            print("❌ Failed to start backend server")
            raise Exception("Server startup timeout")

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[🕰️ {timestamp}] ✅ Backend server started with DEBUG logging")
        print("📋 You should see [DEBUG] messages in the server output\n")

    except Exception as e:
        print(f"❌ Error starting backend server: {e}")
        print(
            "Please start the server manually with: cd apps/server && LOG_LEVEL=DEBUG python main.py"
        )
        raise


async def stop_backend_server(show_message: bool = True) -> None:
    """Stop the backend server"""
    global _server_process
    
    if show_message:
        print("\n🐛 Debug: Stopping backend server to display final logs...")
    await asyncio.sleep(0.5)  # Brief pause to ensure all logs are flushed
    
    try:
        # First try to stop the tracked process
        if _server_process and _server_process.poll() is None:
            try:
                # Send SIGTERM to the process group for graceful shutdown
                os.killpg(os.getpgid(_server_process.pid), signal.SIGTERM)
                # Wait for up to 3 seconds for graceful shutdown
                _server_process.wait(timeout=3)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                # If SIGTERM didn't work or timed out, force kill
                try:
                    os.killpg(os.getpgid(_server_process.pid), signal.SIGKILL)
                    _server_process.wait(timeout=1)
                except (ProcessLookupError, subprocess.TimeoutExpired):
                    pass
            _server_process = None
        
        # Also clean up any lingering processes
        subprocess.run(
            ["pkill", "-f", "python main.py"], check=False, capture_output=True
        )
        subprocess.run(
            ["pkill", "-f", "hypercorn"], check=False, capture_output=True
        )
        
        # Ensure port 8000 is free
        _kill_process_on_port(8000)
    except Exception as e:
        if show_message:
            print(f"⚠️  Error stopping server: {e}")
