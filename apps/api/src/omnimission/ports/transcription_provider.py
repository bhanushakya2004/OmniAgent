"""Abstract transcription provider port for speech-to-text."""

from typing import Protocol

from pydantic import BaseModel


class TranscriptionResult(BaseModel):
    """Result of spoken audio transcription."""

    text: str
    language: str
    confidence: float = 1.0


class TranscriptionProvider(Protocol):
    """Port interface for transcribing voice audio files."""

    async def transcribe(
        self,
        audio_bytes: bytes,
        content_type: str,
        hint_language: str | None = None,
    ) -> TranscriptionResult:
        """Transcribe speech audio to text and detect spoken language."""
        ...
