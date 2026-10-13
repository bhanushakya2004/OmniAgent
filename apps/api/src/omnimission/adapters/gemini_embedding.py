"""Google Gemini embedding provider adapter with deterministic fallback and local caching."""

import hashlib
import math
import struct

from omnimission.core.config import get_settings
from omnimission.core.logging import get_logger
from omnimission.ports.embedding_provider import EmbeddingProvider


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Generates 768-dimensional embeddings using Gemini or deterministic offline fallback."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.google_api_key
        self.model = model or settings.gemini_embedding_model
        self.dimension = 768
        self._cache: dict[str, list[float]] = {}
        self.logger = get_logger("gemini_embedding")

    def _generate_deterministic_vector(self, text: str) -> list[float]:
        """Generate a deterministic 768-dimensional unit vector from text for offline CI/local use."""
        clean_text = text.lower().strip()
        vector: list[float] = []

        # Generate 768 float numbers using seeded SHA-512 hashes
        chunk_idx = 0
        while len(vector) < self.dimension:
            h = hashlib.sha512(f"{clean_text}:{chunk_idx}".encode()).digest()
            # Unpack 16 floats from 64-byte digest (each 4 bytes)
            floats = struct.unpack("16f", h)
            for f in floats:
                if math.isfinite(f):
                    vector.append(f)
                else:
                    vector.append(0.1)
                if len(vector) >= self.dimension:
                    break
            chunk_idx += 1

        # Normalize to unit length
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text string."""
        clean_text = text.strip()
        if not clean_text:
            return [0.0] * self.dimension

        if clean_text in self._cache:
            return self._cache[clean_text]

        # Use Gemini API if configured
        if self.api_key and not self.api_key.startswith("change-me"):
            try:
                from google import genai

                client = genai.Client(api_key=self.api_key)
                response = client.models.embed_content(
                    model=self.model,
                    contents=clean_text,
                )
                if response.embeddings and response.embeddings[0].values:
                    vector = list(response.embeddings[0].values)
                    # Ensure 768 dimensions
                    if len(vector) > self.dimension:
                        vector = vector[: self.dimension]
                    elif len(vector) < self.dimension:
                        vector.extend([0.0] * (self.dimension - len(vector)))
                    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
                    normalized = [v / norm for v in vector]
                    self._cache[clean_text] = normalized
                    return normalized
            except Exception as err:
                self.logger.warning(
                    "gemini_embedding_failed_fallback_deterministic", error=str(err)
                )

        # Fallback to deterministic vector
        vec = self._generate_deterministic_vector(clean_text)
        self._cache[clean_text] = vec
        return vec

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple text strings."""
        return [await self.embed_text(t) for t in texts]
