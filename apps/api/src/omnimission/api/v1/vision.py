"""Vision analysis API endpoint for grounding product photos."""

from pathlib import Path

from fastapi import APIRouter, Depends

from omnimission.adapters.local_storage import LocalFsStorage
from omnimission.agents.vision_agent import VisionAgentRunner
from omnimission.core.deps import require_user
from omnimission.core.errors import BadRequestError, NotFoundError
from omnimission.models.user import User
from omnimission.ports.storage_backend import StorageBackend
from omnimission.schemas.multimodal import VisionAnalyzeRequest, VisionAnalyzeResponse

router = APIRouter(prefix="/vision", tags=["vision"])


def get_storage_backend() -> StorageBackend:
    """Dependency provider for StorageBackend."""
    return LocalFsStorage()


def get_vision_runner() -> VisionAgentRunner:
    """Dependency provider for VisionAgentRunner."""
    return VisionAgentRunner()


@router.post(
    "/analyze",
    response_model=VisionAnalyzeResponse,
    summary="Analyze uploaded product or shelf image",
)
async def analyze_vision_image(
    request: VisionAnalyzeRequest,
    _current_user: User = Depends(require_user),
    storage: StorageBackend = Depends(get_storage_backend),
    vision_runner: VisionAgentRunner = Depends(get_vision_runner),
) -> VisionAnalyzeResponse:
    """Analyze a previously uploaded product photo or pantry shelf image.

    Formulates optimal catalog search queries and detects candidate items.
    """
    # Extract filename from URL (e.g. /static/uploads/abcd_photo.jpg)
    raw_filename = Path(request.file_url).name
    if not raw_filename:
        raise BadRequestError(detail="Invalid file URL", code="INVALID_FILE_URL")

    content = await storage.get(raw_filename)
    if not content:
        raise NotFoundError(detail=f"Uploaded file '{raw_filename}' not found", code="FILE_NOT_FOUND")

    # Detect extension MIME
    ext = Path(raw_filename).suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    content_type = mime_map.get(ext, "image/jpeg")

    analysis = await vision_runner.analyze_image(
        image_bytes=content,
        content_type=content_type,
        user_prompt=request.prompt,
    )

    return VisionAnalyzeResponse(
        primary_query=analysis.primary_query,
        description=analysis.description,
        detected_items=[item.model_dump() for item in analysis.detected_items],
        suggested_action=analysis.suggested_action,
    )
