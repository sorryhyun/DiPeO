"""URL value object."""
from dataclasses import dataclass
from urllib.parse import ParseResult, urlparse, urljoin
from typing import Optional


@dataclass(frozen=True)
class URL:
    """Represents a URL with validation and utility methods."""
    
    value: str
    
    def __post_init__(self) -> None:
        """Validate the URL."""
        if not self.value:
            raise ValueError("URL cannot be empty")
        
        # Basic URL validation
        parsed = self._parse()
        if not parsed.scheme:
            raise ValueError("URL must have a scheme (http/https)")
        if not parsed.netloc:
            raise ValueError("URL must have a network location (host)")
    
    def _parse(self) -> ParseResult:
        """Parse the URL."""
        return urlparse(self.value)
    
    @property
    def scheme(self) -> str:
        """Get the URL scheme (http/https)."""
        return self._parse().scheme
    
    @property
    def host(self) -> str:
        """Get the host part of the URL."""
        return self._parse().hostname or ""
    
    @property
    def port(self) -> Optional[int]:
        """Get the port if specified."""
        return self._parse().port
    
    @property
    def path(self) -> str:
        """Get the path part of the URL."""
        return self._parse().path
    
    @property
    def query(self) -> str:
        """Get the query string."""
        return self._parse().query
    
    @property
    def fragment(self) -> str:
        """Get the fragment (anchor)."""
        return self._parse().fragment
    
    @property
    def is_https(self) -> bool:
        """Check if URL uses HTTPS."""
        return self.scheme == "https"
    
    @property
    def base_url(self) -> 'URL':
        """Get the base URL (scheme + host + port)."""
        parsed = self._parse()
        base = f"{parsed.scheme}://{parsed.netloc}"
        return URL(base)
    
    def join(self, path: str) -> 'URL':
        """Join a path to this URL."""
        return URL(urljoin(self.value, path))
    
    def with_path(self, path: str) -> 'URL':
        """Replace the path component."""
        parsed = self._parse()
        # Ensure path starts with /
        if not path.startswith('/'):
            path = f'/{path}'
        new_url = f"{parsed.scheme}://{parsed.netloc}{path}"
        if parsed.query:
            new_url += f"?{parsed.query}"
        if parsed.fragment:
            new_url += f"#{parsed.fragment}"
        return URL(new_url)
    
    def with_query(self, query: str) -> 'URL':
        """Replace the query string."""
        parsed = self._parse()
        new_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if query:
            # Remove leading ? if present
            query = query.lstrip('?')
            new_url += f"?{query}"
        if parsed.fragment:
            new_url += f"#{parsed.fragment}"
        return URL(new_url)
    
    def __str__(self) -> str:
        """String representation."""
        return self.value