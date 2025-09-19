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

from dipeo.config.paths import BASE_DIR

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
        """Initialize file lock with path and timeout."""
        self.lock_file = lock_file
        self.timeout = timeout
        self.lock_fd = None
        self.use_fcntl = HAS_FCNTL
        self.use_msvcrt = HAS_MSVCRT

        self.lock_file.parent.mkdir(parents=True, exist_ok=True)

    def _lock_unix(self, fd: int, blocking: bool) -> bool:
        """Unix file locking using fcntl."""
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
        """Unix file unlocking using fcntl."""
        if self.use_fcntl:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except Exception as e:
                logger.error(f"Error unlocking file: {e}")

    def _lock_windows(self, fd: int, blocking: bool) -> bool:
        """Windows file locking using msvcrt."""
        if not self.use_msvcrt:
            return self._lock_fallback(blocking)

        try:
            flags = msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK
            msvcrt.locking(fd, flags, 1)
            return True
        except OSError:
            return False

    def _unlock_windows(self, fd: int) -> None:
        """Windows file unlocking using msvcrt."""
        if self.use_msvcrt:
            try:
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            except Exception as e:
                logger.error(f"Error unlocking file: {e}")

    def _lock_fallback(self, blocking: bool) -> bool:
        """Fallback locking using file existence check."""
        if blocking:
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                try:
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
        """Acquire the lock, optionally blocking until available."""
        if self.lock_fd is not None:
            return True

        if not self.use_fcntl and not self.use_msvcrt:
            return self._lock_fallback(blocking)

        try:
            self.lock_fd = open(self.lock_file, "w")  # noqa: SIM115
        except Exception as e:
            logger.error(f"Failed to open lock file {self.lock_file}: {e}")
            return False

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
        if blocking:
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                if self._lock_unix(fd, False):
                    return True
                time.sleep(0.1)
            return False
        else:
            return self._lock_unix(fd, False)

    def _lock_windows_with_timeout(self, fd: int, blocking: bool) -> bool:
        if blocking:
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                if self._lock_windows(fd, False):
                    return True
                time.sleep(0.1)
            return False
        else:
            return self._lock_windows(fd, False)

    def release(self):
        if self.lock_fd is not None:
            try:
                if self.use_fcntl:
                    self._unlock_unix(self.lock_fd.fileno())
                elif self.use_msvcrt:
                    self._unlock_windows(self.lock_fd.fileno())

                self.lock_fd.close()

                if not self.use_fcntl and not self.use_msvcrt:
                    with suppress(FileNotFoundError):
                        self.lock_file.unlink()

            except Exception as e:
                logger.error(f"Error releasing lock for {self.lock_file}: {e}")
            finally:
                self.lock_fd = None

    def __enter__(self):
        if not self.acquire():
            raise TimeoutError(f"Could not acquire lock for {self.lock_file}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class AsyncFileLock:
    """Async version of FileLock for use with asyncio."""

    def __init__(self, lock_file: Path, timeout: float = 30.0):
        """Initialize async file lock with path and timeout."""
        self.lock = FileLock(lock_file, timeout)
        self._loop = None

    async def acquire(self, blocking: bool = True) -> bool:
        """Acquire the lock asynchronously, optionally blocking."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.lock.acquire, blocking)

    async def release(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.lock.release)

    async def __aenter__(self):
        if not await self.acquire():
            raise TimeoutError(f"Could not acquire lock for {self.lock.lock_file}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()


class CacheFileLock:
    """Specialized lock for cache file operations.

    Provides safe read/write operations for cache files with automatic locking.
    """

    def __init__(self, cache_dir: Path, lock_dir: Path | None = None):
        """Initialize cache file lock manager with directories."""
        self.cache_dir = Path(cache_dir)
        self.lock_dir = lock_dir or (self.cache_dir / ".locks")

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.lock_dir.mkdir(parents=True, exist_ok=True)

    def _get_lock_path(self, cache_file: Path) -> Path:
        """Get lock file path for cache file."""
        path_hash = hashlib.md5(str(cache_file).encode()).hexdigest()[:8]
        lock_name = f"{cache_file.name}.{path_hash}.lock"
        return self.lock_dir / lock_name

    @contextmanager
    def read(self, cache_file: Path) -> Any:
        """Context manager for safe cache file reading."""
        lock_path = self._get_lock_path(cache_file)
        with FileLock(lock_path):
            if cache_file.exists():
                with open(cache_file) as f:
                    yield f
            else:
                yield None

    @contextmanager
    def write(self, cache_file: Path) -> Any:
        """Context manager for safe cache file writing."""
        lock_path = self._get_lock_path(cache_file)
        with FileLock(lock_path):
            temp_file = cache_file.with_suffix(".tmp")
            try:
                with open(temp_file, "w") as f:
                    yield f
                temp_file.rename(cache_file)
            except Exception:
                if temp_file.exists():
                    temp_file.unlink()
                raise

    @asynccontextmanager
    async def async_read(self, cache_file: Path) -> Any:
        """Async context manager for safe cache file reading."""
        lock_path = self._get_lock_path(cache_file)
        async with AsyncFileLock(lock_path):
            if cache_file.exists():
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
        """Async context manager for safe cache file writing."""
        lock_path = self._get_lock_path(cache_file)
        async with AsyncFileLock(lock_path):
            temp_file = cache_file.with_suffix(".tmp")
            try:
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

                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, temp_file.rename, cache_file)
            except Exception:
                if temp_file.exists():
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, temp_file.unlink)
                raise


_cache_lock_manager = None


def get_cache_lock_manager(cache_dir: Path | None = None) -> CacheFileLock:
    """Get or create global cache lock manager."""
    global _cache_lock_manager
    if _cache_lock_manager is None:
        if cache_dir is None:
            base_dir = BASE_DIR
            cache_dir = base_dir / "temp"

        _cache_lock_manager = CacheFileLock(cache_dir)

    return _cache_lock_manager
