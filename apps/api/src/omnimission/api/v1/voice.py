"""Voice transcription API endpoint."""

from fastapi import APIRouter, Depends, File, Form, UploadFile

from omnimission.adapters.gemini_transcription import GeminiTranscriptionProvider
from omnimission.adapters.local_storage import validate_file_content
from omnimission.core.deps import require_user
from omnimission.models.user import User
from omnimission.ports.transcription_provider import TranscriptionProvider
from omnimission.schemas.multimodal import VoiceTranscribeResponse

router = APIRouter(prefix="/voice", tags=["voice"])


def get_transcription_provider() -> TranscriptionProvider:
    """Dependency provider for TranscriptionProvider."""
    return GeminiTranscriptionProvider()


@router.post(
    "/transcribe",
    response_model=VoiceTranscribeResponse,
    summary="Transcribe spoken audio to text",
)
async def transcribe_voice(
    file: UploadFile = File(...),
    hint_language: str | None = Form(None),
    _current_user: User = Depends(require_user),
    provider: TranscriptionProvider = Depends(get_transcription_provider),
) -> VoiceTranscribeResponse:
    """Transcribe spoken audio in English, Hindi, Tamil, Kannada or other languages into text."""
    content = await file.read()
    content_type = file.content_type or "audio/webm"

    # Enforce magic-byte validation on audio
    validate_file_content(content, content_type)

    result = await provider.transcribe(
        audio_bytes=content,
        content_type=content_type,
        hint_language=hint_language,
    )

    return VoiceTranscribeResponse(
        text=result.text,
        language=result.language,
        confidence=result.confidence,
    )
