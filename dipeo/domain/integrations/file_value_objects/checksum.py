"""Checksum value object."""

import hashlib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ChecksumAlgorithm(Enum):
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    SHA512 = "sha512"


@dataclass(frozen=True)
class Checksum:
    value: str
    algorithm: ChecksumAlgorithm

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Checksum value cannot be empty")

        try:
            int(self.value, 16)
        except ValueError as e:
            raise ValueError("Checksum must be a valid hexadecimal string") from e

        expected_lengths = {
            ChecksumAlgorithm.MD5: 32,
            ChecksumAlgorithm.SHA1: 40,
            ChecksumAlgorithm.SHA256: 64,
            ChecksumAlgorithm.SHA512: 128,
        }

        expected_length = expected_lengths.get(self.algorithm)
        if expected_length and len(self.value) != expected_length:
            raise ValueError(
                f"{self.algorithm.value} checksum must be {expected_length} characters, "
                f"got {len(self.value)}"
            )

    @classmethod
    def compute(cls, data: bytes | str, algorithm: ChecksumAlgorithm) -> "Checksum":
        if isinstance(data, str):
            data = data.encode("utf-8")

        hasher = hashlib.new(algorithm.value)
        hasher.update(data)
        return cls(value=hasher.hexdigest(), algorithm=algorithm)

    @classmethod
    def compute_file(cls, file_path: str, algorithm: ChecksumAlgorithm) -> "Checksum":
        hasher = hashlib.new(algorithm.value)

        with Path(file_path).open("rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)

        return cls(value=hasher.hexdigest(), algorithm=algorithm)

    def verify(self, data: bytes | str) -> bool:
        computed = self.compute(data, self.algorithm)
        return computed.value.lower() == self.value.lower()

    def verify_file(self, file_path: str) -> bool:
        computed = self.compute_file(file_path, self.algorithm)
        return computed.value.lower() == self.value.lower()

    @property
    def short_value(self) -> str:
        return self.value[:8]

    def __str__(self) -> str:
        return f"{self.algorithm.value}:{self.value}"
