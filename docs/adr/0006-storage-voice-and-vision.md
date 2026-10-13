# ADR 0006: Multimodal Ingestion: Magic-Byte Validation, Speech Transcription, and Visual Grounding

## Status
Accepted

## Context
OmniMission AI supports multimodal mission entry: text prompts, spoken queries across Indian languages (Hindi, English, Tamil, Kannada), and uploaded product/pantry photos. Unrestricted file uploads create security vectors (executable masquerading, memory exhaustion, malware). Furthermore, audio transcription and vision understanding must work gracefully in both connected GCP/Gemini production environments and air-gapped local or CI test environments.

## Decision
1. **Ports and Adapters Architecture:**
   - **`StorageBackend` Port:** Abstract storage contract (`save`, `get`, `delete`, `get_url`). Implemented locally by `LocalFsStorage` (persisting to `.data/uploads` and served via `/static/uploads`). In Phase 2, this is a drop-in replacement with `GcsStorageBackend` (Google Cloud Storage) requiring zero changes to business logic.
   - **`TranscriptionProvider` Port:** Abstract speech-to-text contract (`transcribe`). Implemented by `GeminiTranscriptionProvider` utilizing Gemini 2.0 Flash multimodal audio when `GOOGLE_API_KEY` is present, with deterministic language and query heuristic fallbacks for offline testing.
2. **Strict Magic-Byte and Size Verification:**
   Before any upload is accepted, `validate_file_content` verifies:
   - File size under 10 MB.
   - Header magic-byte signature matching against declared MIME types (JPEG `\xff\xd8\xff`, PNG `\x89PNG`, WebP `RIFF....WEBP`, WebM `\x1a\x45\xdf\xa3`, WAV `RIFF....WAVE`, MP3 `ID3`, OGG `OggS`, M4A `ftypM4A`).
   - Masqueraded executables (`MZ`, ELF, shell scripts) are rejected with RFC 7807 `400 Bad Request` (`MAGIC_BYTE_MISMATCH`).
3. **Vision Agent Entity Grounding:**
   The `VisionAgentRunner` inspects product labels and packaging in uploaded images, extracting candidate brand names, product titles, and categories. It translates images into high-precision text search queries dispatched to the hybrid search catalog.

## Consequences
- Clean separation between storage mechanisms (local disk vs. GCS) and model providers.
- Safe, tamper-proof multimodal ingestion with zero arbitrary code execution risk.
- End-to-end multimodal testing runs completely offline with 100% deterministic reproducibility.
