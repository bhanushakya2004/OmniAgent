"""Unit and integration tests for multimodal uploads, storage, voice, and vision."""

import uuid

import pytest
from httpx import AsyncClient

from omnimission.adapters.local_storage import LocalFsStorage, validate_file_content
from omnimission.core.errors import BadRequestError

# Sample magic byte fixtures
VALID_JPEG_BYTES = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 100
VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\x00" * 100
VALID_WEBM_BYTES = b"\x1a\x45\xdf\xa3" + b"\x00" * 100
MALICIOUS_EXE_DISGUISED = b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 100


def test_magic_byte_validation_success() -> None:
    """Ensure authentic JPEG, PNG, and WebM bytes pass validation."""
    validate_file_content(VALID_JPEG_BYTES, "image/jpeg")
    validate_file_content(VALID_PNG_BYTES, "image/png")
    validate_file_content(VALID_WEBM_BYTES, "audio/webm")


def test_magic_byte_validation_rejects_disguised_file() -> None:
    """Ensure executables disguised with image MIME are rejected with MAGIC_BYTE_MISMATCH."""
    with pytest.raises(BadRequestError) as exc_info:
        validate_file_content(MALICIOUS_EXE_DISGUISED, "image/jpeg")
    assert exc_info.value.code == "MAGIC_BYTE_MISMATCH"


def test_magic_byte_validation_rejects_empty_file() -> None:
    """Ensure 0-byte file is rejected."""
    with pytest.raises(BadRequestError) as exc_info:
        validate_file_content(b"", "image/jpeg")
    assert exc_info.value.code == "EMPTY_FILE"


def test_magic_byte_validation_rejects_file_too_large() -> None:
    """Ensure files > 10MB are rejected."""
    large_content = b"\xff\xd8\xff" + b"\x00" * (11 * 1024 * 1024)
    with pytest.raises(BadRequestError) as exc_info:
        validate_file_content(large_content, "image/jpeg")
    assert exc_info.value.code == "FILE_TOO_LARGE"


def test_magic_byte_validation_rejects_unsupported_mime() -> None:
    """Ensure arbitrary MIME types are rejected."""
    with pytest.raises(BadRequestError) as exc_info:
        validate_file_content(b"console.log('hi')", "application/javascript")
    assert exc_info.value.code == "UNSUPPORTED_MEDIA_TYPE"


@pytest.mark.asyncio
async def test_local_storage_lifecycle(tmp_path) -> None:
    """Test LocalFsStorage save, get, and delete operations."""
    storage = LocalFsStorage(upload_dir=tmp_path)
    filename = "test_image.png"

    url = await storage.save(filename, VALID_PNG_BYTES, "image/png")
    assert url == f"/static/uploads/{filename}"

    retrieved = await storage.get(filename)
    assert retrieved == VALID_PNG_BYTES

    deleted = await storage.delete(filename)
    assert deleted is True

    # After delete
    assert await storage.get(filename) is None


@pytest.mark.asyncio
async def test_uploads_endpoint_and_static_serving(client: AsyncClient) -> None:
    """Test POST /uploads stores file and makes it accessible via /static/uploads."""
    # 1. Register test user
    email = f"upload_user_{uuid.uuid4().hex[:6]}@example.com"
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "Upload Tester",
            "role": "user",
        },
    )
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload valid image
    files = {"file": ("chocolate.png", VALID_PNG_BYTES, "image/png")}
    upload_resp = await client.post("/api/v1/uploads", headers=headers, files=files)
    assert upload_resp.status_code == 201
    data = upload_resp.json()
    assert "file_url" in data
    assert data["filename"] == "chocolate.png"
    assert data["content_type"] == "image/png"
    assert data["size_bytes"] == len(VALID_PNG_BYTES)

    # 3. Fetch uploaded file via static mount
    file_url = data["file_url"]
    static_resp = await client.get(file_url)
    assert static_resp.status_code == 200
    assert static_resp.content == VALID_PNG_BYTES


@pytest.mark.asyncio
async def test_voice_transcription_endpoint(client: AsyncClient) -> None:
    """Test POST /voice/transcribe processes audio and returns speech transcription."""
    email = f"voice_user_{uuid.uuid4().hex[:6]}@example.com"
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "Voice Tester",
            "role": "user",
        },
    )
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    files = {"file": ("query.webm", VALID_WEBM_BYTES, "audio/webm")}
    data = {"hint_language": "hi"}

    voice_resp = await client.post(
        "/api/v1/voice/transcribe", headers=headers, files=files, data=data
    )
    assert voice_resp.status_code == 200
    res = voice_resp.json()
    assert "text" in res
    assert len(res["text"]) > 0
    assert res["language"] == "hi"
    assert res["confidence"] > 0.0


@pytest.mark.asyncio
async def test_vision_analyze_endpoint(client: AsyncClient) -> None:
    """Test POST /vision/analyze processes uploaded image and extracts candidate search query."""
    email = f"vision_user_{uuid.uuid4().hex[:6]}@example.com"
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "Vision Tester",
            "role": "user",
        },
    )
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. First upload an image
    files = {"file": ("pantry_item.jpg", VALID_JPEG_BYTES, "image/jpeg")}
    upload_resp = await client.post("/api/v1/uploads", headers=headers, files=files)
    assert upload_resp.status_code == 201
    file_url = upload_resp.json()["file_url"]

    # 2. Analyze image
    analyze_resp = await client.post(
        "/api/v1/vision/analyze",
        headers=headers,
        json={
            "file_url": file_url,
            "prompt": "find this dark chocolate",
        },
    )
    assert analyze_resp.status_code == 200
    analysis = analyze_resp.json()
    assert "primary_query" in analysis
    assert len(analysis["detected_items"]) > 0
    assert analysis["suggested_action"] == "search_catalog"
