"""PostgreSQL Hybrid Search adapter combining Vector, Full-Text, and Trigram matching via RRF."""

import uuid
from collections import defaultdict

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from omnimission.adapters.gemini_embedding import GeminiEmbeddingProvider
from omnimission.models.inventory import StoreInventory
from omnimission.models.product import Product
from omnimission.ports.embedding_provider import EmbeddingProvider
from omnimission.ports.search_backend import SearchBackend, SearchResult


class PgHybridSearch(SearchBackend):
    """Hybrid search adapter implementing Reciprocal Rank Fusion (RRF) on PostgreSQL."""

    def __init__(self, embedding_provider: EmbeddingProvider | None = None) -> None:
        self.embedding_provider = embedding_provider or GeminiEmbeddingProvider()
        self.rrf_k = 60  # Standard RRF smoothing constant

    async def search(
        self,
        session: object,  # AsyncSession
        query: str,
        store_ids: list[uuid.UUID],
        dietary_tags: list[str] | None = None,
        is_travel_size: bool | None = None,
        in_stock_only: bool = True,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Perform hybrid search over products joined to store inventory."""
        assert isinstance(session, AsyncSession)

        clean_query = query.strip()
        if not clean_query or not store_ids:
            return []

        # 1. Generate dense embedding vector for semantic search
        query_vector = await self.embedding_provider.embed_text(clean_query)

        # 2. Candidate stream A: Full-Text Search (FTS)
        fts_stmt = (
            select(
                Product.id,
                func.ts_rank(Product.tsv, func.plainto_tsquery("english", clean_query)).label(
                    "score"
                ),
            )
            .where(Product.tsv.op("@@")(func.plainto_tsquery("english", clean_query)))
            .order_by(text("score DESC"))
            .limit(50)
        )
        fts_res = (await session.execute(fts_stmt)).all()
        fts_ranks: dict[uuid.UUID, int] = {row[0]: idx + 1 for idx, row in enumerate(fts_res)}

        # 3. Candidate stream B: Trigram Fuzzy Similarity (Brand / Typo matching)
        trgm_stmt = (
            select(
                Product.id,
                func.similarity(func.concat(Product.name, " ", Product.brand), clean_query).label(
                    "score"
                ),
            )
            .where(
                func.similarity(func.concat(Product.name, " ", Product.brand), clean_query) > 0.12
            )
            .order_by(text("score DESC"))
            .limit(50)
        )
        trgm_res = (await session.execute(trgm_stmt)).all()
        trgm_ranks: dict[uuid.UUID, int] = {row[0]: idx + 1 for idx, row in enumerate(trgm_res)}

        # 4. Candidate stream C: Dense Vector Cosine Similarity (when embeddings present)
        dense_ranks: dict[uuid.UUID, int] = {}
        try:
            dense_stmt = (
                select(
                    Product.id,
                    Product.embedding.cosine_distance(query_vector).label("distance"),
                )
                .where(Product.embedding.is_not(None))
                .order_by(text("distance ASC"))
                .limit(50)
            )
            dense_res = (await session.execute(dense_stmt)).all()
            dense_ranks = {row[0]: idx + 1 for idx, row in enumerate(dense_res)}
        except Exception:
            # Graceful degradation if vector extension/column has no active vectors yet
            pass

        # 5. Compute Reciprocal Rank Fusion (RRF) scores
        all_candidate_ids = set(fts_ranks.keys()) | set(trgm_ranks.keys()) | set(dense_ranks.keys())
        if not all_candidate_ids:
            # Fallback: simple ILIKE matching if words weren't in dictionary
            words = [w for w in clean_query.split() if len(w) > 2]
            if words:
                ilike_conditions = [Product.name.ilike(f"%{w}%") for w in words]
                fallback_stmt = select(Product.id).where(*ilike_conditions).limit(20)
                fallback_res = (await session.execute(fallback_stmt)).scalars().all()
                for idx, pid in enumerate(fallback_res):
                    all_candidate_ids.add(pid)
                    fts_ranks[pid] = idx + 1

        rrf_scores: dict[uuid.UUID, float] = defaultdict(float)
        matched_methods: dict[uuid.UUID, list[str]] = defaultdict(list)

        for pid in all_candidate_ids:
            if pid in fts_ranks:
                rrf_scores[pid] += 1.0 / (self.rrf_k + fts_ranks[pid])
                matched_methods[pid].append(f"fts(rank={fts_ranks[pid]})")
            if pid in trgm_ranks:
                rrf_scores[pid] += 1.0 / (self.rrf_k + trgm_ranks[pid])
                matched_methods[pid].append(f"trgm(rank={trgm_ranks[pid]})")
            if pid in dense_ranks:
                rrf_scores[pid] += 1.0 / (self.rrf_k + dense_ranks[pid])
                matched_methods[pid].append(f"dense(rank={dense_ranks[pid]})")

        if not rrf_scores:
            return []

        # 6. Join with store inventory and apply hard constraints (store_ids, dietary, stock)
        inv_stmt = (
            select(Product, StoreInventory)
            .join(StoreInventory, StoreInventory.product_id == Product.id)
            .where(Product.id.in_(list(rrf_scores.keys())))
            .where(StoreInventory.store_id.in_(store_ids))
        )

        if in_stock_only:
            inv_stmt = inv_stmt.where(StoreInventory.stock_qty > 0)

        if is_travel_size is not None:
            inv_stmt = inv_stmt.where(Product.is_travel_size.is_(is_travel_size))

        if dietary_tags:
            for tag in dietary_tags:
                inv_stmt = inv_stmt.where(Product.dietary_tags.contains([tag.strip().lower()]))

        inventory_rows = (await session.execute(inv_stmt)).all()

        # 7. Build SearchResult DTOs and sort by RRF score descending
        results: list[SearchResult] = []
        for prod, inv in inventory_rows:
            score = rrf_scores.get(prod.id, 0.0)
            method = " + ".join(matched_methods.get(prod.id, ["keyword"]))
            results.append(
                SearchResult(
                    product_id=prod.id,
                    store_id=inv.store_id,
                    name=prod.name,
                    brand=prod.brand,
                    category=prod.category,
                    size_label=prod.size_label,
                    is_travel_size=prod.is_travel_size,
                    dietary_tags=prod.dietary_tags,
                    price=inv.price,
                    mrp=inv.mrp,
                    stock_qty=inv.stock_qty,
                    aisle=inv.aisle,
                    bay=inv.bay,
                    shelf=inv.shelf,
                    score=round(score, 6),
                    match_method=method,
                )
            )

        # Sort by RRF score descending, then stock quantity descending
        results.sort(key=lambda r: (r.score, r.stock_qty), reverse=True)
        return results[:limit]
