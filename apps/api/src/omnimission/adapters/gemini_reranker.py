"""Gemini-powered listwise reranker with heuristic cross-scoring fallback."""

import json
import re
from typing import Any

from omnimission.core.config import get_settings
from omnimission.core.logging import get_logger
from omnimission.ports.reranker_port import RerankerPort


class GeminiReranker(RerankerPort):
    """Listwise neural reranker with deterministic lexical cross-scoring fallback."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.google_api_key
        self.model = model or settings.gemini_model_fast
        self.logger = get_logger("gemini_reranker")

    def _fallback_score(self, query: str, chunk: dict[str, Any]) -> float:
        """Compute heuristic cross-scoring based on query terms, title match, and section weight."""
        query_terms = set(re.findall(r"\w+", query.lower()))
        if not query_terms:
            return float(chunk.get("rrf_score", 0.0))

        text_content = (chunk.get("chunk_text", "") + " " + chunk.get("section_title", "")).lower()
        chunk_terms = set(re.findall(r"\w+", text_content))

        # Jaccard overlap on terms
        overlap = len(query_terms.intersection(chunk_terms))
        jaccard = overlap / len(query_terms.union(chunk_terms)) if chunk_terms else 0.0

        # Exact phrase match in text or title
        phrase_boost = 1.0
        if query.lower().strip() in text_content:
            phrase_boost = 1.5

        # Section priority: Overview and Ingredients are critical for planning
        sec = chunk.get("section_title", "").lower()
        sec_weight = 1.2 if "overview" in sec or "ingredients" in sec else 1.0

        rrf_base = float(chunk.get("rrf_score", 0.0))
        return (jaccard * 2.0 + phrase_boost * 0.5 + rrf_base) * sec_weight

    async def rerank(
        self, query: str, candidates: list[dict[str, Any]], top_k: int = 5
    ) -> list[dict[str, Any]]:
        """Rerank candidates using Gemini listwise ranking or fallback heuristic."""
        if not candidates:
            return []

        if len(candidates) <= 1:
            return candidates

        # Try Gemini API if configured
        if self.api_key and not self.api_key.startswith("change-me"):
            try:
                from google import genai

                client = genai.Client(api_key=self.api_key)
                prompt_snippets = [
                    f"[{idx}] Title: {c.get('section_title', '')}\nContent: {c.get('chunk_text', '')[:300]}"
                    for idx, c in enumerate(candidates[:15])
                ]
                sys_prompt = (
                    f"User Query: '{query}'\n"
                    "Rank the following candidate document snippets by relevance to the query from most relevant to least relevant.\n"
                    "Respond with a JSON list of indices: [idx_best, idx_second, ...]"
                )
                response = client.models.generate_content(
                    model=self.model,
                    contents=sys_prompt + "\n\n" + "\n\n".join(prompt_snippets),
                )
                text_out = response.text or ""
                # Parse JSON array of ints
                match = re.search(r"\[[\d,\s]+\]", text_out)
                if match:
                    indices: list[int] = json.loads(match.group(0))
                    ranked: list[dict[str, Any]] = []
                    seen: set[int] = set()
                    for i in indices:
                        if 0 <= i < len(candidates) and i not in seen:
                            seen.add(i)
                            c = dict(candidates[i])
                            c["reranker_score"] = 1.0 - (len(ranked) * 0.05)
                            ranked.append(c)
                    # Add any unranked candidates
                    for i, c in enumerate(candidates):
                        if i not in seen:
                            c_dict = dict(c)
                            c_dict["reranker_score"] = 0.1
                            ranked.append(c_dict)
                    return ranked[:top_k]
            except Exception as err:
                self.logger.warning("gemini_rerank_failed_fallback_heuristic", error=str(err))

        # Fallback cross-scoring
        scored: list[dict[str, Any]] = []
        for c in candidates:
            item = dict(c)
            item["reranker_score"] = self._fallback_score(query, item)
            scored.append(item)

        scored.sort(key=lambda x: float(x.get("reranker_score", 0.0)), reverse=True)
        return scored[:top_k]
