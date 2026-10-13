"""Port definition for neural / listwise chunk reranker."""

from abc import ABC, abstractmethod
from typing import Any


class RerankerPort(ABC):
    """Abstract port for reranking retrieved knowledge chunks according to query relevance."""

    @abstractmethod
    async def rerank(
        self, query: str, candidates: list[dict[str, Any]], top_k: int = 5
    ) -> list[dict[str, Any]]:
        """Rerank candidates and return the top_k most relevant items with relevance scores."""
        pass
