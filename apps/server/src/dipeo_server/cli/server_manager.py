"""Background server manager for CLI debug mode."""

import asyncio
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import httpx

from dipeo.config.base_logger import get_module_logger

logger = get_module_logger(__name__)


class ServerManager:
    """Manages background server process for CLI debug mode."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.process: subprocess.Popen | None = None
        self._health_url = f"http://localhost:{port}/health"
        self._stdout_file = None
        self._stderr_file = None

    async def start_async(self) -> None:
        """Start the background server without waiting for health check.

        The server will start in the background and health checks can be done later.
        This is used when the server is optional (e.g., for monitoring only).
        """
        if self.process is not None:
            logger.warning("Server already running")
            return

        try:
            # Build command to start server
            python_exe = sys.executable

            # Start uvicorn directly (server module exports the app)
            cmd = [
                python_exe,
                "-m",
                "uvicorn",
                "apps.server.main:app",
                "--host",
                self.host,
                "--port",
                str(self.port),
                "--log-level",
                "error",  # Suppress output
            ]

            # Start process with output captured for debugging
            import tempfile
            self._stdout_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='_server_stdout.log')
            self._stderr_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='_server_stderr.log')

            self.process = subprocess.Popen(
                cmd,
                stdout=self._stdout_file,
                stderr=self._stderr_file,
                start_new_session=True,  # Allow process to survive parent termination
            )

            logger.info(f"Started background server (PID: {self.process.pid}) - will be ready shortly")

        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            if self.process:
                await self.stop()

    async def start(self, timeout: int = 30) -> bool:
        """Start the background server.

        Args:
            timeout: Maximum time to wait for server to be ready (seconds)

        Returns:
            True if server started successfully, False otherwise
        """
        if self.process is not None:
            logger.warning("Server already running")
            return True

        try:
            # Build command to start server
            python_exe = sys.executable

            # Start uvicorn directly (server module exports the app)
            cmd = [
                python_exe,
                "-m",
                "uvicorn",
                "apps.server.main:app",
                "--host",
                self.host,
                "--port",
                str(self.port),
                "--log-level",
                "error",  # Suppress output
            ]

            # Start process with output captured for debugging
            import tempfile
            self._stdout_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='_server_stdout.log')
            self._stderr_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='_server_stderr.log')

            self.process = subprocess.Popen(
                cmd,
                stdout=self._stdout_file,
                stderr=self._stderr_file,
                start_new_session=True,  # Allow process to survive parent termination
            )

            logger.info(f"Started background server (PID: {self.process.pid})")

            # Wait for server to be ready
            if await self._wait_for_health(timeout):
                logger.info(f"Server ready at http://{self.host}:{self.port}")
                return True
            else:
                logger.error("Server failed to start within timeout")
                # Log server output for debugging
                if self._stderr_file:
                    self._stderr_file.seek(0)
                    stderr_content = self._stderr_file.read()
                    if stderr_content:
                        logger.error(f"Server stderr:\n{stderr_content}")
                if self._stdout_file:
                    self._stdout_file.seek(0)
                    stdout_content = self._stdout_file.read()
                    if stdout_content:
                        logger.error(f"Server stdout:\n{stdout_content}")
                await self.stop()
                return False

        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            if self.process:
                await self.stop()
            return False

    async def stop(self) -> None:
        """Stop the background server gracefully."""
        if self.process is None:
            return

        try:
            logger.info(f"Stopping background server (PID: {self.process.pid})")

            # Try graceful shutdown first (SIGTERM)
            self.process.terminate()

            # Wait up to 5 seconds for graceful shutdown
            try:
                self.process.wait(timeout=5)
                logger.info("Server stopped gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if still running
                logger.warning("Server did not stop gracefully, forcing shutdown")
                self.process.kill()
                self.process.wait(timeout=2)
                logger.info("Server forcefully stopped")

        except Exception as e:
            logger.error(f"Error stopping server: {e}")
        finally:
            self.process = None
            # Clean up temp files
            if self._stdout_file:
                try:
                    self._stdout_file.close()
                    import os
                    os.unlink(self._stdout_file.name)
                except Exception:
                    pass
            if self._stderr_file:
                try:
                    self._stderr_file.close()
                    import os
                    os.unlink(self._stderr_file.name)
                except Exception:
                    pass

    async def _wait_for_health(self, timeout: int) -> bool:
        """Wait for server health check to succeed.

        Args:
            timeout: Maximum time to wait (seconds)

        Returns:
            True if health check succeeded, False if timeout
        """
        start_time = time.time()
        retry_interval = 0.2  # Start with 200ms
        last_log_time = start_time

        while time.time() - start_time < timeout:
            elapsed = time.time() - start_time

            # Log progress every 5 seconds
            if elapsed - (last_log_time - start_time) >= 5:
                logger.info(f"Waiting for server... ({elapsed:.1f}s elapsed)")
                last_log_time = time.time()

            try:
                async with httpx.AsyncClient(timeout=1.0) as client:
                    response = await client.get(self._health_url)
                    if response.status_code == 200:
                        logger.info(f"Server ready after {elapsed:.1f}s")
                        return True
            except (httpx.ConnectError, httpx.TimeoutException):
                # Server not ready yet, wait and retry
                pass
            except Exception as e:
                logger.debug(f"Health check error: {e}")

            await asyncio.sleep(retry_interval)

            # Exponential backoff up to 1 second
            retry_interval = min(retry_interval * 1.5, 1.0)

        return False

    async def is_running(self) -> bool:
        """Check if server is running and responsive.

        Returns:
            True if server is healthy, False otherwise
        """
        if self.process is None:
            return False

        # Check if process is still alive
        if self.process.poll() is not None:
            logger.warning("Server process died unexpectedly")
            self.process = None
            return False

        # Check health endpoint
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                response = await client.get(self._health_url)
                return response.status_code == 200
        except Exception:
            return False

    async def __aenter__(self):
        """Context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.stop()
