"""File system locking utilities for safe concurrent access to cache files."""

import asyncio
import hashlib
import logging
import os
import sys
import time
from contextlib import asynccontextmanager, contextmanager, suppress
from pathlib import Path
from typing import Any

# Platform-specific imports for file locking
try:
    import fcntl

    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

if sys.platform == "win32":
    try:
        import msvcrt

        HAS_MSVCRT = True
    except ImportError:
        HAS_MSVCRT = False
else:
    HAS_MSVCRT = False

logger = logging.getLogger(__name__)


class FileLock:
    """File-based lock for coordinating access to shared resources.

    Uses fcntl on Unix systems or msvcrt on Windows for file locking.
    Falls back to simple file-based locking if platform APIs are unavailable.
    """

    def __init__(self, lock_file: Path, timeout: float = 30.0):
        """Initialize a file lock.

        Args:
            lock_file: Path to the lock file
            timeout: Maximum time to wait for lock acquisition in seconds
        """
        self.lock_file = lock_file
        self.timeout = timeout
        self.lock_fd = None
        self.use_fcntl = HAS_FCNTL
        self.use_msvcrt = HAS_MSVCRT

        # Ensure lock directory exists
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)

    def _lock_unix(self, fd: int, blocking: bool) -> bool:
        """Unix-specific file locking using fcntl.

        Args:
            fd: File descriptor
            blocking: Whether to block for lock acquisition

        Returns:
            True if lock acquired, False otherwise
        """
        if not self.use_fcntl:
            return self._lock_fallback(blocking)

        try:
            flags = fcntl.LOCK_EX
            if not blocking:
                flags |= fcntl.LOCK_NB
            fcntl.flock(fd, flags)
            return True
        except OSError:
            return False

    def _unlock_unix(self, fd: int) -> None:
        """Unix-specific file unlocking using fcntl.

        Args:
            fd: File descriptor
        """
        if self.use_fcntl:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except Exception as e:
                logger.error(f"Error unlocking file: {e}")

    def _lock_windows(self, fd: int, blocking: bool) -> bool:
        """Windows-specific file locking using msvcrt.

        Args:
            fd: File descriptor
            blocking: Whether to block for lock acquisition

        Returns:
            True if lock acquired, False otherwise
        """
        if not self.use_msvcrt:
            return self._lock_fallback(blocking)

        try:
            # Lock entire file (0 bytes from position 0)
            flags = msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK
            msvcrt.locking(fd, flags, 1)
            return True
        except OSError:
            return False

    def _unlock_windows(self, fd: int) -> None:
        """Windows-specific file unlocking using msvcrt.

        Args:
            fd: File descriptor
        """
        if self.use_msvcrt:
            try:
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            except Exception as e:
                logger.error(f"Error unlocking file: {e}")

    def _lock_fallback(self, blocking: bool) -> bool:
        """Fallback locking mechanism using simple file existence.

        This is a simple fallback that's not as robust as platform-specific
        locking but works across all platforms.

        Args:
            blocking: Whether to block for lock acquisition

        Returns:
            True if lock acquired, False otherwise
        """
        if blocking:
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                try:
                    # Try to create lock file exclusively
                    self.lock_fd = open(self.lock_file, "x")  # noqa: SIM115
                    return True
                except FileExistsError:
                    time.sleep(0.1)
            return False
        else:
            try:
                self.lock_fd = open(self.lock_file, "x")  # noqa: SIM115
                return True
            except FileExistsError:
                return False

    def acquire(self, blocking: bool = True) -> bool:
        """Acquire the lock.

        Args:
            blocking: If True, wait for lock. If False, return immediately.

        Returns:
            True if lock acquired, False otherwise
        """
        if self.lock_fd is not None:
            return True  # Already locked

        # Use fallback method if neither platform API is available
        if not self.use_fcntl and not self.use_msvcrt:
            return self._lock_fallback(blocking)

        # Open or create lock file
        try:
            self.lock_fd = open(self.lock_file, "w")  # noqa: SIM115
        except Exception as e:
            logger.error(f"Failed to open lock file {self.lock_file}: {e}")
            return False

        # Use platform-specific locking
        if self.use_fcntl:
            success = self._lock_unix_with_timeout(self.lock_fd.fileno(), blocking)
        elif self.use_msvcrt:
            success = self._lock_windows_with_timeout(self.lock_fd.fileno(), blocking)
        else:
            success = False

        if not success:
            self.lock_fd.close()
            self.lock_fd = None
            if blocking:
                logger.warning(f"Timeout acquiring lock for {self.lock_file}")

        return success

    def _lock_unix_with_timeout(self, fd: int, blocking: bool) -> bool:
        """Unix locking with timeout handling."""
        if blocking:
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                if self._lock_unix(fd, False):  # Non-blocking attempt
                    return True
                time.sleep(0.1)
            return False
        else:
            return self._lock_unix(fd, False)

    def _lock_windows_with_timeout(self, fd: int, blocking: bool) -> bool:
        """Windows locking with timeout handling."""
        if blocking:
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                if self._lock_windows(fd, False):  # Non-blocking attempt
                    return True
                time.sleep(0.1)
            return False
        else:
            return self._lock_windows(fd, False)

    def release(self):
        """Release the lock."""
        if self.lock_fd is not None:
            try:
                # Use platform-specific unlocking
                if self.use_fcntl:
                    self._unlock_unix(self.lock_fd.fileno())
                elif self.use_msvcrt:
                    self._unlock_windows(self.lock_fd.fileno())
                # For fallback method, just close the file

                self.lock_fd.close()

                # For fallback method, remove the lock file
                if not self.use_fcntl and not self.use_msvcrt:
                    with suppress(FileNotFoundError):
                        self.lock_file.unlink()

            except Exception as e:
                logger.error(f"Error releasing lock for {self.lock_file}: {e}")
            finally:
                self.lock_fd = None

    def __enter__(self):
        """Context manager entry."""
        if not self.acquire():
            raise TimeoutError(f"Could not acquire lock for {self.lock_file}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()


class AsyncFileLock:
    """Async version of FileLock for use with asyncio."""

    def __init__(self, lock_file: Path, timeout: float = 30.0):
        """Initialize an async file lock.

        Args:
            lock_file: Path to the lock file
            timeout: Maximum time to wait for lock acquisition in seconds
        """
        self.lock = FileLock(lock_file, timeout)
        self._loop = None

    async def acquire(self, blocking: bool = True) -> bool:
        """Acquire the lock asynchronously.

        Args:
            blocking: If True, wait for lock. If False, return immediately.

        Returns:
            True if lock acquired, False otherwise
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.lock.acquire, blocking)

    async def release(self):
        """Release the lock asynchronously."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.lock.release)

    async def __aenter__(self):
        """Async context manager entry."""
        if not await self.acquire():
            raise TimeoutError(f"Could not acquire lock for {self.lock.lock_file}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.release()


class CacheFileLock:
    """Specialized lock for cache file operations.

    Provides safe read/write operations for cache files with automatic locking.
    """

    def __init__(self, cache_dir: Path, lock_dir: Path | None = None):
        """Initialize cache file lock manager.

        Args:
            cache_dir: Directory containing cache files
            lock_dir: Directory for lock files (defaults to cache_dir/.locks)
        """
        self.cache_dir = Path(cache_dir)
        self.lock_dir = lock_dir or (self.cache_dir / ".locks")

        # Ensure directories exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.lock_dir.mkdir(parents=True, exist_ok=True)

    def _get_lock_path(self, cache_file: Path) -> Path:
        """Get the lock file path for a cache file.

        Args:
            cache_file: Path to the cache file

        Returns:
            Path to the corresponding lock file
        """
        # Use hash of file path to avoid path length issues
        path_hash = hashlib.md5(str(cache_file).encode()).hexdigest()[:8]
        lock_name = f"{cache_file.name}.{path_hash}.lock"
        return self.lock_dir / lock_name

    @contextmanager
    def read(self, cache_file: Path) -> Any:
        """Context manager for safe cache file reading.

        Args:
            cache_file: Path to the cache file to read

        Yields:
            The opened file object for reading
        """
        lock_path = self._get_lock_path(cache_file)
        with FileLock(lock_path):
            if cache_file.exists():
                with open(cache_file) as f:
                    yield f
            else:
                yield None

    @contextmanager
    def write(self, cache_file: Path) -> Any:
        """Context manager for safe cache file writing.

        Args:
            cache_file: Path to the cache file to write

        Yields:
            The opened file object for writing
        """
        lock_path = self._get_lock_path(cache_file)
        with FileLock(lock_path):
            # Write to temp file first
            temp_file = cache_file.with_suffix(".tmp")
            try:
                with open(temp_file, "w") as f:
                    yield f
                # Atomic rename
                temp_file.rename(cache_file)
            except Exception:
                # Clean up temp file on error
                if temp_file.exists():
                    temp_file.unlink()
                raise

    @asynccontextmanager
    async def async_read(self, cache_file: Path) -> Any:
        """Async context manager for safe cache file reading.

        Args:
            cache_file: Path to the cache file to read

        Yields:
            The opened file object for reading
        """
        lock_path = self._get_lock_path(cache_file)
        async with AsyncFileLock(lock_path):
            if cache_file.exists():
                # Use aiofiles if available, otherwise fall back to sync
                try:
                    import aiofiles

                    async with aiofiles.open(cache_file) as f:
                        yield f
                except ImportError:
                    loop = asyncio.get_event_loop()
                    f = await loop.run_in_executor(None, open, cache_file, "r")
                    try:
                        yield f
                    finally:
                        await loop.run_in_executor(None, f.close)
            else:
                yield None

    @asynccontextmanager
    async def async_write(self, cache_file: Path) -> Any:
        """Async context manager for safe cache file writing.

        Args:
            cache_file: Path to the cache file to write

        Yields:
            The opened file object for writing
        """
        lock_path = self._get_lock_path(cache_file)
        async with AsyncFileLock(lock_path):
            # Write to temp file first
            temp_file = cache_file.with_suffix(".tmp")
            try:
                # Use aiofiles if available, otherwise fall back to sync
                try:
                    import aiofiles

                    async with aiofiles.open(temp_file, "w") as f:
                        yield f
                except ImportError:
                    loop = asyncio.get_event_loop()
                    f = await loop.run_in_executor(None, open, temp_file, "w")
                    try:
                        yield f
                    finally:
                        await loop.run_in_executor(None, f.close)

                # Atomic rename
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, temp_file.rename, cache_file)
            except Exception:
                # Clean up temp file on error
                if temp_file.exists():
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, temp_file.unlink)
                raise


# Global cache lock manager instance
_cache_lock_manager = None


def get_cache_lock_manager(cache_dir: Path | None = None) -> CacheFileLock:
    """Get or create the global cache lock manager.

    Args:
        cache_dir: Cache directory path (defaults to DIPEO_BASE_DIR/temp)

    Returns:
        The cache lock manager instance
    """
    global _cache_lock_manager

    if _cache_lock_manager is None:
        if cache_dir is None:
            base_dir = Path(os.getenv("DIPEO_BASE_DIR", os.getcwd()))
            cache_dir = base_dir / "temp"

        _cache_lock_manager = CacheFileLock(cache_dir)

    return _cache_lock_manager
