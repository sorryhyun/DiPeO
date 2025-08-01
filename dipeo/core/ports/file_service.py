"""File Service port interface."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class FileServicePort(Protocol):

    def read(
        self,
        file_id: str,
        person_id: str | None = None,
        directory: str | None = None,
    ) -> dict[str, Any]:
        ...

    async def write(
        self,
        file_id: str,
        person_id: str | None = None,
        directory: str | None = None,
        content: str | None = None,
    ) -> dict[str, Any]:
        ...

    async def save_file(
        self, content: bytes, filename: str, target_path: str | None = None
    ) -> dict[str, Any]:
        ...