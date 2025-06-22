"""Utility GraphQL mutations."""

import base64
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path

import strawberry

from ..context import GraphQLContext
from ..graphql_types import (
    DeleteResult,
    FileUploadInput,
    FileUploadResult,
)

logger = logging.getLogger(__name__)


@strawberry.type
class UtilityMutations:
    """Utility mutations for file uploads, memory management, etc."""

    @strawberry.mutation
    async def clear_conversations(self, info) -> DeleteResult:
        """Clear all conversation history."""
        try:
            context: GraphQLContext = info.context
            memory_service = context.memory_service

            # Clear all conversations
            memory_service.clear_all_conversations()

            return DeleteResult(success=True, message="All conversations cleared")

        except Exception as e:
            logger.error(f"Failed to clear conversations: {e}")
            return DeleteResult(
                success=False, error=f"Failed to clear conversations: {e!s}"
            )

    @strawberry.mutation
    async def upload_file(self, input: FileUploadInput, info) -> FileUploadResult:
        """Upload a file to the server (replaces REST endpoint)."""
        try:
            import aiofiles

            # Decode base64 content
            try:
                file_content = base64.b64decode(input.content_base64)
            except Exception as e:
                return FileUploadResult(
                    success=False, error=f"Invalid base64 encoding: {e!s}"
                )

            # Create uploads directory if it doesn't exist
            upload_dir = Path("files/uploads")
            upload_dir.mkdir(parents=True, exist_ok=True)

            # Generate unique filename to avoid conflicts
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename_parts = os.path.splitext(input.filename)
            safe_filename = (
                f"{filename_parts[0]}_{timestamp}_{unique_id}{filename_parts[1]}"
            )

            # Full path for the file
            file_path = upload_dir / safe_filename

            # Write file asynchronously
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(file_content)

            # Get file size
            file_size = len(file_content)

            return FileUploadResult(
                success=True,
                path=str(file_path),
                size_bytes=file_size,
                content_type=input.content_type,
                message=f"File uploaded successfully to {file_path}",
            )

        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            return FileUploadResult(
                success=False, error=f"Failed to upload file: {e!s}"
            )
