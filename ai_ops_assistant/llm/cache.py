"""Simple in-memory cache for LLM responses to reduce API calls."""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, Optional


class ResponseCache:
    """Thread-safe in-memory cache with TTL."""

    def __init__(self, ttl_seconds: int = 3600) -> None:
        """Initialize cache.
        
        Args:
            ttl_seconds: Time-to-live for cache entries (default: 1 hour)
        """
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._ttl = ttl_seconds

    def _make_key(self, system: str, user: str) -> str:
        """Create cache key from prompt."""
        content = f"{system}|||{user}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, system: str, user: str) -> Optional[Any]:
        """Get cached response if available and not expired."""
        key = self._make_key(system, user)
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return value
            # Expired - remove it
            del self._cache[key]
        return None

    def set(self, system: str, user: str, value: Any) -> None:
        """Cache a response."""
        key = self._make_key(system, user)
        self._cache[key] = (value, time.time())

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    def size(self) -> int:
        """Return number of cached entries."""
        return len(self._cache)
