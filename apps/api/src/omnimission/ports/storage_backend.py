"""Abstract storage backend port for multimodal assets (images, audio)."""

from typing import Protocol


class StorageBackend(Protocol):
    """Port interface for persisting, fetching, and deleting uploaded artifacts."""

    async def save(self, filename: str, content: bytes, content_type: str) -> str:
        """Save file bytes and return access URL.

        Args:
            filename: Destination unique filename
            content: Raw file bytes
            content_type: MIME type (e.g. image/jpeg, audio/webm)

        Returns:
            URL string where the file is accessible.
        """
        ...

    async def get(self, filename: str) -> bytes | None:
        """Retrieve raw file bytes by filename."""
        ...

    async def delete(self, filename: str) -> bool:
        """Remove file by filename."""
        ...

    def get_url(self, filename: str) -> str:
        """Resolve public or served URL for filename."""
        ...
