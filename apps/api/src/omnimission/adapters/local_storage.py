"""Local filesystem storage adapter implementing StorageBackend port."""

from pathlib import Path

import anyio

from omnimission.core.config import get_settings
from omnimission.core.errors import BadRequestError

MAGIC_SIGNATURES: dict[str, list[bytes]] = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/webp": [b"RIFF"],  # followed by WEBP
    "image/gif": [b"GIF87a", b"GIF89a"],
    "audio/webm": [b"\x1a\x45\xdf\xa3"],
    "audio/wav": [b"RIFF"],  # followed by WAVE
    "audio/x-wav": [b"RIFF"],
    "audio/mpeg": [b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"],
    "audio/mp3": [b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"],
    "audio/ogg": [b"OggS"],
    "audio/m4a": [b"\x00\x00\x00\x18ftypM4A", b"\x00\x00\x00\x20ftypM4A", b"ftyp"],
    "audio/mp4": [b"ftyp"],
}

ALLOWED_MIME_TYPES = set(MAGIC_SIGNATURES.keys())
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def validate_file_content(content: bytes, declared_type: str) -> None:
    """Validate file size and magic bytes to prevent masqueraded executable uploads."""
    if len(content) == 0:
        raise BadRequestError(detail="Uploaded file is empty", code="EMPTY_FILE")

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise BadRequestError(
            detail=f"File exceeds maximum allowed size of 10 MB ({len(content)} bytes)",
            code="FILE_TOO_LARGE",
        )

    norm_type = declared_type.lower().split(";")[0].strip()
    if norm_type not in ALLOWED_MIME_TYPES:
        raise BadRequestError(
            detail=f"Unsupported file MIME type '{declared_type}'. Allowed types: images (JPEG, PNG, WebP) and audio (WebM, WAV, MP3, OGG, M4A)",
            code="UNSUPPORTED_MEDIA_TYPE",
        )

    signatures = MAGIC_SIGNATURES[norm_type]
    matched = False
    for sig in signatures:
        if norm_type in ("image/webp", "audio/wav", "audio/x-wav"):
            if content.startswith(b"RIFF") and len(content) >= 12:
                subtype = content[8:12]
                if (norm_type == "image/webp" and subtype == b"WEBP") or (
                    norm_type in ("audio/wav", "audio/x-wav") and subtype == b"WAVE"
                ):
                    matched = True
                    break
        elif norm_type in ("audio/m4a", "audio/mp4"):
            if b"ftyp" in content[:32]:
                matched = True
                break
        elif content.startswith(sig):
            matched = True
            break

    if not matched:
        raise BadRequestError(
            detail=f"File content does not match declared MIME signature '{declared_type}'",
            code="MAGIC_BYTE_MISMATCH",
        )


class LocalFsStorage:
    """Local filesystem storage implementation for development and testing."""

    def __init__(self, upload_dir: str | Path | None = None) -> None:
        settings = get_settings()
        self.upload_dir = Path(upload_dir or settings.local_storage_path).resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, filename: str, content: bytes, content_type: str) -> str:
        """Validate and write bytes to disk, returning static access URL."""
        validate_file_content(content, content_type)
        target_path = self.upload_dir / filename

        def _write() -> None:
            target_path.write_bytes(content)

        await anyio.to_thread.run_sync(_write)
        return self.get_url(filename)

    async def get(self, filename: str) -> bytes | None:
        """Read bytes from local disk."""
        target_path = self.upload_dir / filename
        if not target_path.exists():
            return None

        def _read() -> bytes:
            return target_path.read_bytes()

        return await anyio.to_thread.run_sync(_read)

    async def delete(self, filename: str) -> bool:
        """Remove file from disk."""
        target_path = self.upload_dir / filename
        if not target_path.exists():
            return False

        def _delete() -> None:
            target_path.unlink(missing_ok=True)

        await anyio.to_thread.run_sync(_delete)
        return True

    def get_url(self, filename: str) -> str:
        """Format relative served URL."""
        return f"/static/uploads/{filename}"

    def get_absolute_path(self, filename: str) -> Path:
        """Get absolute path on disk for local processing (e.g. vision or ffmpeg)."""
        return (self.upload_dir / filename).resolve()
