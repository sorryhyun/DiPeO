import asyncio
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

from .api_client import DiPeoAPIClient


async def restart_backend_server() -> None:
    """Restart the backend server to ensure latest code is loaded"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[🕰️ {timestamp}] 🐛 Debug: Restarting backend server with DEBUG logging...")

    # Kill any existing server processes
    try:
        # Kill processes listening on port 8000
        kill_result = subprocess.run(
            ["pkill", "-f", "python main.py"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Also try to kill hypercorn processes
        subprocess.run(
            ["pkill", "-f", "hypercorn"], check=False, capture_output=True, text=True
        )

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
        # In debug mode with verbose flag, show all output
        # Otherwise, capture output to reduce noise
        verbose_debug = env.get("VERBOSE_DEBUG", "false").lower() == "true"
        
        process = subprocess.Popen(
            start_cmd,
            cwd=server_path,
            env=env,
            stdout=None if verbose_debug else subprocess.DEVNULL,  # Show output only in verbose mode
            stderr=None if verbose_debug else subprocess.DEVNULL,  # Show errors only in verbose mode
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


async def stop_backend_server() -> None:
    """Stop the backend server"""
    print("\n🐛 Debug: Stopping backend server to display final logs...")
    await asyncio.sleep(0.5)  # Brief pause to ensure all logs are flushed
    try:
        subprocess.run(
            ["pkill", "-f", "python main.py"], check=False, capture_output=True
        )
        subprocess.run(
            ["pkill", "-f", "hypercorn"], check=False, capture_output=True
        )
    except Exception:
        pass
