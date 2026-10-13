"""Embedding provider port definition."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Abstract protocol for text embedding vector generation."""

    async def embed_text(self, text: str) -> list[float]:
        """Generate a dense vector embedding for single text string."""
        ...

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate dense vector embeddings for batch of text strings."""
        ...
