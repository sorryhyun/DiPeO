"""Async/sync operation adapters for file operations."""

import asyncio
import shutil
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from typing import Any, Callable, Optional

import aiofiles


class AsyncFileAdapter:
    """Adapts between sync and async file operations."""
    
    def __init__(self, executor: Optional[ThreadPoolExecutor] = None):
        """Initialize with optional thread pool executor."""
        self._executor = executor
    
    async def run_sync_in_thread(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> Any:
        """Run a synchronous function in a thread pool."""
        loop = asyncio.get_event_loop()
        
        # Use partial to bind arguments
        bound_func = partial(func, *args, **kwargs)
        
        # Run in executor
        return await loop.run_in_executor(self._executor, bound_func)
    
    async def read_text_async(self, file_path: Path) -> str:
        """Read text file asynchronously."""
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
            return await f.read()
    
    async def write_text_async(self, file_path: Path, content: str) -> None:
        """Write text file asynchronously."""
        async with aiofiles.open(file_path, mode='w', encoding='utf-8') as f:
            await f.write(content)
    
    async def read_bytes_async(self, file_path: Path) -> bytes:
        """Read binary file asynchronously."""
        async with aiofiles.open(file_path, mode='rb') as f:
            return await f.read()
    
    async def write_bytes_async(self, file_path: Path, content: bytes) -> None:
        """Write binary file asynchronously."""
        async with aiofiles.open(file_path, mode='wb') as f:
            await f.write(content)
    
    def read_text_sync(self, file_path: Path) -> str:
        """Read text file synchronously."""
        return file_path.read_text(encoding='utf-8')
    
    def write_text_sync(self, file_path: Path, content: str) -> None:
        """Write text file synchronously."""
        file_path.write_text(content, encoding='utf-8')
    
    def read_bytes_sync(self, file_path: Path) -> bytes:
        """Read binary file synchronously."""
        return file_path.read_bytes()
    
    def write_bytes_sync(self, file_path: Path, content: bytes) -> None:
        """Write binary file synchronously."""
        file_path.write_bytes(content)
    
    async def append_text_async(self, file_path: Path, content: str, encoding: str = 'utf-8') -> None:
        """Append text to file asynchronously."""
        async with aiofiles.open(file_path, mode='a', encoding=encoding) as f:
            await f.write(content)
    
    async def copy_file_async(self, src_path: Path, dst_path: Path) -> None:
        """Copy file asynchronously."""
        # Use thread pool for shutil.copy2
        await self.run_sync_in_thread(shutil.copy2, str(src_path), str(dst_path))
    
    async def delete_file_async(self, file_path: Path) -> None:
        """Delete file asynchronously."""
        # Use thread pool for file deletion
        await self.run_sync_in_thread(file_path.unlink)