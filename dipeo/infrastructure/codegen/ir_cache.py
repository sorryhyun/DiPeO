"""Cache for IR data with TTL support."""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from dipeo.config.base_logger import get_module_logger
from dipeo.config.paths import CACHE_DIR

logger = get_module_logger(__name__)


class IRCache:
    """Cache for IR data with TTL support."""

    def __init__(self, cache_dir: str | None = None, ttl_hours: int = 24):
        """Initialize IR cache.

        Args:
            cache_dir: Directory for cache files (defaults to CACHE_DIR/ir)
            ttl_hours: Time-to-live in hours
        """
        if cache_dir is None:
            cache_dir = str(CACHE_DIR / "ir")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)

    async def get(self, key: str) -> Any | None:
        """Get cached IR data.

        Args:
            key: Cache key

        Returns:
            Cached data if available and not expired, None otherwise
        """
        cache_file = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            logger.debug(f"Cache miss: {key}")
            return None

        # Check TTL
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        age = datetime.now() - mtime

        if age > self.ttl:
            logger.debug(f"Cache expired: {key} (age: {age})")
            cache_file.unlink()
            return None

        try:
            with open(cache_file) as f:
                data = json.load(f)
                logger.debug(f"Cache hit: {key} (age: {age})")
                return data
        except Exception as e:
            logger.error(f"Error reading cache file {cache_file}: {e}")
            # Remove corrupted cache file
            cache_file.unlink()
            return None

    async def set(self, key: str, data: Any) -> None:
        """Cache IR data.

        Args:
            key: Cache key
            data: Data to cache
        """
        cache_file = self.cache_dir / f"{key}.json"

        try:
            # Convert to dict if it's a Pydantic model
            if hasattr(data, "dict"):
                data_to_cache = data.dict()
            else:
                data_to_cache = data

            with open(cache_file, "w") as f:
                json.dump(data_to_cache, f, indent=2)

            logger.debug(f"Cached: {key}")
        except Exception as e:
            logger.error(f"Error writing cache file {cache_file}: {e}")
            # Remove partially written file
            if cache_file.exists():
                cache_file.unlink()

    def clear(self) -> None:
        """Clear all cached IR data."""
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        logger.info(f"Cleared {count} cached IR files")

    def clear_expired(self) -> None:
        """Clear only expired cached IR data."""
        count = 0
        now = datetime.now()

        for cache_file in self.cache_dir.glob("*.json"):
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            age = now - mtime

            if age > self.ttl:
                cache_file.unlink()
                count += 1

        if count > 0:
            logger.info(f"Cleared {count} expired cache files")

    def get_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        files = list(self.cache_dir.glob("*.json"))
        now = datetime.now()

        stats = {"total_files": len(files), "expired": 0, "valid": 0, "total_size_bytes": 0}

        for cache_file in files:
            stats["total_size_bytes"] += cache_file.stat().st_size
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            age = now - mtime

            if age > self.ttl:
                stats["expired"] += 1
            else:
                stats["valid"] += 1

        return stats
