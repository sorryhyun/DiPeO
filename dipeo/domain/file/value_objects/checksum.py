"""Checksum value object."""
import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Union


class ChecksumAlgorithm(Enum):
    """Supported checksum algorithms."""
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    SHA512 = "sha512"


@dataclass(frozen=True)
class Checksum:
    """Represents a file checksum with validation."""
    
    value: str
    algorithm: ChecksumAlgorithm
    
    def __post_init__(self) -> None:
        """Validate the checksum."""
        if not self.value:
            raise ValueError("Checksum value cannot be empty")
        
        # Validate checksum format (must be hexadecimal)
        try:
            int(self.value, 16)
        except ValueError:
            raise ValueError("Checksum must be a valid hexadecimal string")
        
        # Validate checksum length based on algorithm
        expected_lengths = {
            ChecksumAlgorithm.MD5: 32,
            ChecksumAlgorithm.SHA1: 40,
            ChecksumAlgorithm.SHA256: 64,
            ChecksumAlgorithm.SHA512: 128
        }
        
        expected_length = expected_lengths.get(self.algorithm)
        if expected_length and len(self.value) != expected_length:
            raise ValueError(
                f"{self.algorithm.value} checksum must be {expected_length} characters, "
                f"got {len(self.value)}"
            )
    
    @classmethod
    def compute(cls, data: Union[bytes, str], algorithm: ChecksumAlgorithm) -> 'Checksum':
        """Compute checksum for given data."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        hasher = hashlib.new(algorithm.value)
        hasher.update(data)
        return cls(value=hasher.hexdigest(), algorithm=algorithm)
    
    @classmethod
    def compute_file(cls, file_path: str, algorithm: ChecksumAlgorithm) -> 'Checksum':
        """Compute checksum for a file."""
        hasher = hashlib.new(algorithm.value)
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        
        return cls(value=hasher.hexdigest(), algorithm=algorithm)
    
    def verify(self, data: Union[bytes, str]) -> bool:
        """Verify if data matches this checksum."""
        computed = self.compute(data, self.algorithm)
        return computed.value.lower() == self.value.lower()
    
    def verify_file(self, file_path: str) -> bool:
        """Verify if file matches this checksum."""
        computed = self.compute_file(file_path, self.algorithm)
        return computed.value.lower() == self.value.lower()
    
    @property
    def short_value(self) -> str:
        """Return first 8 characters of checksum for display."""
        return self.value[:8]
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.algorithm.value}:{self.value}"