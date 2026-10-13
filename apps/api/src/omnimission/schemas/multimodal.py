"""Schemas for uploads, voice transcription, and visual image analysis."""

from typing import Any

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """File upload confirmation."""

    file_url: str = Field(description="URL to access uploaded asset")
    filename: str = Field(description="Original filename")
    content_type: str = Field(description="Verified MIME type")
    size_bytes: int = Field(description="File size in bytes")


class VoiceTranscribeResponse(BaseModel):
    """Speech-to-text response."""

    text: str = Field(description="Transcribed text")
    language: str = Field(description="Detected language code (e.g. en, hi)")
    confidence: float = Field(default=1.0, description="Confidence score between 0 and 1")


class VisionAnalyzeRequest(BaseModel):
    """Payload to request image visual parsing."""

    file_url: str = Field(description="URL of uploaded image (from /uploads)")
    prompt: str | None = Field(default=None, description="Optional shopper guidance or query")


class VisionAnalyzeResponse(BaseModel):
    """Visual analysis response with candidate search query."""

    primary_query: str
    description: str
    detected_items: list[dict[str, Any]] = Field(default_factory=list)
    suggested_action: str
