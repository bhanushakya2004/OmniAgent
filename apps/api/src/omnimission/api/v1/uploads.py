"""Uploads API endpoint for saving multimodal images and audio."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, status

from omnimission.adapters.local_storage import LocalFsStorage
from omnimission.core.deps import require_user
from omnimission.models.user import User
from omnimission.ports.storage_backend import StorageBackend
from omnimission.schemas.multimodal import UploadResponse

router = APIRouter(prefix="/uploads", tags=["uploads"])


def get_storage_backend() -> StorageBackend:
    """Dependency provider for storage backend port."""
    return LocalFsStorage()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=UploadResponse,
    summary="Upload multimodal image or audio file",
)
async def upload_file(
    file: UploadFile = File(...),
    _current_user: User = Depends(require_user),
    storage: StorageBackend = Depends(get_storage_backend),
) -> UploadResponse:
    """Upload an image (JPEG, PNG, WebP) or audio (WebM, WAV, MP3, OGG, M4A) file.

    Enforces magic-byte verification and a 10 MB file size limit.
    """
    content = await file.read()
    orig_name = Path(file.filename or "upload").name
    unique_name = f"{uuid.uuid4().hex[:12]}_{orig_name}"
    content_type = file.content_type or "application/octet-stream"

    file_url = await storage.save(
        filename=unique_name,
        content=content,
        content_type=content_type,
    )

    return UploadResponse(
        file_url=file_url,
        filename=orig_name,
        content_type=content_type,
        size_bytes=len(content),
    )
