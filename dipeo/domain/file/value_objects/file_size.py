"""File size value object."""
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class FileSize:
    """Represents a file size with validation and unit conversion."""
    
    bytes: int
    
    def __post_init__(self) -> None:
        """Validate the file size."""
        if self.bytes < 0:
            raise ValueError("File size cannot be negative")
    
    @property
    def kilobytes(self) -> float:
        """Return size in kilobytes."""
        return self.bytes / 1024
    
    @property
    def megabytes(self) -> float:
        """Return size in megabytes."""
        return self.bytes / (1024 * 1024)
    
    @property
    def gigabytes(self) -> float:
        """Return size in gigabytes."""
        return self.bytes / (1024 * 1024 * 1024)
    
    def human_readable(self, decimal_places: int = 2) -> str:
        """Return human-readable size string."""
        if self.bytes < 1024:
            return f"{self.bytes} B"
        elif self.bytes < 1024 * 1024:
            return f"{self.kilobytes:.{decimal_places}f} KB"
        elif self.bytes < 1024 * 1024 * 1024:
            return f"{self.megabytes:.{decimal_places}f} MB"
        else:
            return f"{self.gigabytes:.{decimal_places}f} GB"
    
    def is_within_limit(self, max_bytes: int) -> bool:
        """Check if size is within specified limit."""
        return self.bytes <= max_bytes
    
    def __add__(self, other: 'FileSize') -> 'FileSize':
        """Add two file sizes."""
        if not isinstance(other, FileSize):
            raise TypeError(f"Cannot add FileSize and {type(other)}")
        return FileSize(self.bytes + other.bytes)
    
    def __sub__(self, other: 'FileSize') -> 'FileSize':
        """Subtract two file sizes."""
        if not isinstance(other, FileSize):
            raise TypeError(f"Cannot subtract {type(other)} from FileSize")
        result = self.bytes - other.bytes
        if result < 0:
            raise ValueError("Result would be negative")
        return FileSize(result)
    
    def __lt__(self, other: 'FileSize') -> bool:
        """Less than comparison."""
        if not isinstance(other, FileSize):
            raise TypeError(f"Cannot compare FileSize with {type(other)}")
        return self.bytes < other.bytes
    
    def __le__(self, other: 'FileSize') -> bool:
        """Less than or equal comparison."""
        if not isinstance(other, FileSize):
            raise TypeError(f"Cannot compare FileSize with {type(other)}")
        return self.bytes <= other.bytes
    
    def __str__(self) -> str:
        """String representation."""
        return self.human_readable()