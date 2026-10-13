"""Knowledge Base ingestion, hybrid retrieval, Knowledge Graph expansion, and reranking."""

import re
import uuid
from typing import Any

from sqlalchemy import delete, func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from omnimission.adapters.gemini_embedding import GeminiEmbeddingProvider
from omnimission.adapters.gemini_reranker import GeminiReranker
from omnimission.core.logging import get_logger
from omnimission.db.session import async_session_factory
from omnimission.models.knowledge import KGEdge, KGNode, KnowledgeChunk, KnowledgeDoc
from omnimission.ports.embedding_provider import EmbeddingProvider
from omnimission.ports.reranker_port import RerankerPort
from omnimission.seed.build_knowledge import generate_full_knowledge_corpus
from omnimission.seed.knowledge_data import KnowledgeDocDict


class KnowledgeService:
    """Manages multi-corpora RAG: ingestion, structure-aware chunking, hybrid search, and KG expansion."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        reranker: RerankerPort | None = None,
    ) -> None:
        self.session_factory = session_factory or async_session_factory
        self.embedding_provider = embedding_provider or GeminiEmbeddingProvider()
        self.reranker = reranker or GeminiReranker()
        self.logger = get_logger("knowledge_service")

    async def ingest_knowledge_corpus(self) -> dict[str, int]:
        """Ingest all 65+ structured knowledge documents, chunks, embeddings, and Knowledge Graph."""
        docs_data = generate_full_knowledge_corpus()
        self.logger.info("starting_knowledge_ingestion", doc_count=len(docs_data))

        doc_count = 0
        chunk_count = 0
        node_count = 0
        edge_count = 0

        async with self.session_factory() as session:
            # 1. Ingest Docs and Chunks
            for d in docs_data:
                # Upsert KnowledgeDoc
                stmt = (
                    insert(KnowledgeDoc)
                    .values(
                        id=uuid.uuid5(uuid.NAMESPACE_DNS, d["doc_id"]),
                        doc_id=d["doc_id"],
                        title=d["title"],
                        type=d["type"],
                        tags=d["tags"],
                        diet_tags=d["diet_tags"],
                        servings_base=d["servings_base"],
                        ingredients=d["ingredients"],
                        summary=d["summary"],
                        content=d["content"],
                    )
                    .on_conflict_do_update(
                        index_elements=["doc_id"],
                        set_={
                            "title": d["title"],
                            "type": d["type"],
                            "tags": d["tags"],
                            "diet_tags": d["diet_tags"],
                            "servings_base": d["servings_base"],
                            "ingredients": d["ingredients"],
                            "summary": d["summary"],
                            "content": d["content"],
                        },
                    )
                )
                await session.execute(stmt)
                doc_count += 1
                doc_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, d["doc_id"])

                # Remove prior chunks for fresh rebuild
                await session.execute(
                    delete(KnowledgeChunk).where(KnowledgeChunk.doc_id == doc_uuid)
                )

                # Structure-aware Chunking
                chunks_to_create = self._create_structure_chunks(d)
                for c_idx, c_info in enumerate(chunks_to_create):
                    vec = await self.embedding_provider.embed_text(c_info["text"])
                    chunk_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"{d['doc_id']}:chunk:{c_idx}")

                    chunk_stmt = insert(KnowledgeChunk).values(
                        id=chunk_id,
                        doc_id=doc_uuid,
                        chunk_index=c_idx,
                        section_title=c_info["title"],
                        chunk_text=c_info["text"],
                        embedding=vec,
                        tsv=func.to_tsvector("english", c_info["text"]),
                    )
                    await session.execute(chunk_stmt)
                    chunk_count += 1

                # 2. Knowledge Graph: Document Node
                doc_node_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"node:{d['doc_id']}")
                node_stmt = (
                    insert(KGNode)
                    .values(
                        id=doc_node_id,
                        name=d["title"],
                        entity_type=d["type"],
                        properties={
                            "doc_id": d["doc_id"],
                            "diet_tags": d["diet_tags"],
                            "servings_base": d["servings_base"],
                        },
                    )
                    .on_conflict_do_update(
                        index_elements=["name", "entity_type"],
                        set_={"properties": {"doc_id": d["doc_id"], "diet_tags": d["diet_tags"]}},
                    )
                )
                await session.execute(node_stmt)
                node_count += 1

                # Dietary tags in KG
                for dt in d["diet_tags"]:
                    dt_node_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"node:diet:{dt}")
                    await session.execute(
                        insert(KGNode)
                        .values(id=dt_node_id, name=dt, entity_type="dietary_tag", properties={})
                        .on_conflict_do_nothing()
                    )
                    edge_id = uuid.uuid5(
                        uuid.NAMESPACE_DNS, f"edge:{doc_node_id}:{dt_node_id}:satisfies"
                    )
                    await session.execute(
                        insert(KGEdge)
                        .values(
                            id=edge_id,
                            source_node_id=doc_node_id,
                            target_node_id=dt_node_id,
                            relation_type="satisfies_diet",
                            weight=1.0,
                            properties={},
                        )
                        .on_conflict_do_nothing()
                    )
                    edge_count += 1

                # Ingredients in KG
                for ing in d.get("ingredients", []):
                    ing_name = ing["name"]
                    ing_node_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"node:ing:{ing_name}")
                    await session.execute(
                        insert(KGNode)
                        .values(
                            id=ing_node_id,
                            name=ing_name,
                            entity_type="ingredient",
                            properties={"category": ing.get("category", "")},
                        )
                        .on_conflict_do_nothing()
                    )
                    node_count += 1

                    edge_id = uuid.uuid5(
                        uuid.NAMESPACE_DNS, f"edge:{doc_node_id}:{ing_node_id}:requires"
                    )
                    await session.execute(
                        insert(KGEdge)
                        .values(
                            id=edge_id,
                            source_node_id=doc_node_id,
                            target_node_id=ing_node_id,
                            relation_type="requires",
                            weight=1.0,
                            properties={
                                "qty": ing.get("qty", 1),
                                "unit": ing.get("unit", "piece"),
                                "optional": ing.get("optional", False),
                            },
                        )
                        .on_conflict_do_nothing()
                    )
                    edge_count += 1

                    # Substitutes
                    for sub in ing.get("substitutes", []):
                        sub_node_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"node:ing:{sub}")
                        await session.execute(
                            insert(KGNode)
                            .values(
                                id=sub_node_id,
                                name=sub,
                                entity_type="ingredient",
                                properties={"is_substitute": True},
                            )
                            .on_conflict_do_nothing()
                        )
                        sub_edge_id = uuid.uuid5(
                            uuid.NAMESPACE_DNS, f"edge:{sub_node_id}:{ing_node_id}:sub"
                        )
                        await session.execute(
                            insert(KGEdge)
                            .values(
                                id=sub_edge_id,
                                source_node_id=sub_node_id,
                                target_node_id=ing_node_id,
                                relation_type="substitutes_for",
                                weight=1.0,
                                properties={},
                            )
                            .on_conflict_do_nothing()
                        )
                        edge_count += 1

            await session.commit()

        self.logger.info(
            "knowledge_ingestion_complete",
            docs=doc_count,
            chunks=chunk_count,
            kg_nodes=node_count,
            kg_edges=edge_count,
        )
        return {
            "docs": doc_count,
            "chunks": chunk_count,
            "kg_nodes": node_count,
            "kg_edges": edge_count,
        }

    def _create_structure_chunks(
        self, doc: KnowledgeDocDict | dict[str, Any]
    ) -> list[dict[str, str]]:
        """Create clean section chunks: Overview, Ingredients/Supplies, Instructions, Dietary."""
        chunks: list[dict[str, str]] = []

        # Chunk 1: Overview
        tags_str = ", ".join(doc.get("tags", []))
        diet_str = ", ".join(doc.get("diet_tags", []))
        serv_str = f"Serves {doc['servings_base']}" if doc.get("servings_base") else ""
        overview_text = (
            f"Title: {doc['title']}\n"
            f"Category/Type: {doc['type']}\n"
            f"Summary: {doc['summary']}\n"
            f"Dietary: {diet_str}\n"
            f"Tags: {tags_str}\n"
            f"{serv_str}"
        )
        chunks.append({"title": "Overview & Summary", "text": overview_text.strip()})

        # Chunk 2: Ingredients / Supplies
        if doc.get("ingredients"):
            ing_lines: list[str] = [f"Ingredients & Supplies for {doc['title']}:"]
            for ing in doc["ingredients"]:
                line = f"- {ing['name']}: {ing.get('qty', '')} {ing.get('unit', '')}"
                if ing.get("substitutes"):
                    line += f" (Substitutes: {', '.join(ing['substitutes'])})"
                ing_lines.append(line)
            chunks.append({"title": "Ingredients & Supplies", "text": "\n".join(ing_lines)})

        # Chunk 3: Instructions & Method
        if doc.get("content"):
            chunks.append(
                {
                    "title": "Preparation & Instructions",
                    "text": f"Instructions for {doc['title']}:\n{doc['content']}",
                }
            )

        return chunks

    def decompose_query(self, raw_query: str) -> dict[str, Any]:
        """Decompose compound query into goal keywords, servings, and dietary constraints."""
        clean = raw_query.strip()

        # 1. Servings / People
        servings: int | None = None
        serv_match = re.search(
            r"(\d+)\s*(people|persons|servings|guests|pax)", clean, re.IGNORECASE
        )
        if serv_match:
            servings = int(serv_match.group(1))

        # 2. Dietary Tags
        diet_tags: list[str] = []
        lower = clean.lower()
        if "eggless" in lower:
            diet_tags.append("eggless")
        if "gluten free" in lower or "gluten-free" in lower:
            diet_tags.append("gluten_free")
        if "vegan" in lower:
            diet_tags.append("vegan")
        if "vegetarian" in lower:
            diet_tags.append("vegetarian")
        if "protein" in lower:
            diet_tags.append("high_protein")
        if "keto" in lower:
            diet_tags.append("keto")

        # 3. Cleaned Search Goal
        goal = re.sub(
            r"for\s+\d+\s*(people|persons|servings|guests|pax)", "", clean, flags=re.IGNORECASE
        )
        goal = re.sub(
            r"eggless|gluten[-\s]free|vegan|vegetarian|high[-\s]protein|keto",
            "",
            goal,
            flags=re.IGNORECASE,
        )
        goal = re.sub(r"i want (to make|everything needed to make)?", "", goal, flags=re.IGNORECASE)
        goal = goal.strip(" ,.-")

        return {
            "original_query": raw_query,
            "goal": goal or clean,
            "servings": servings,
            "dietary_tags": diet_tags,
        }

    async def hybrid_search_chunks(
        self, query: str, limit: int = 10, diet_filter: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Perform dense vector + sparse tsvector retrieval with Reciprocal Rank Fusion (RRF)."""
        vec = await self.embedding_provider.embed_text(query)
        rrf_k = 60

        pool_limit = max(30, limit * 3)
        dense_stmt = (
            select(
                KnowledgeChunk.id,
                KnowledgeChunk.doc_id,
                KnowledgeChunk.section_title,
                KnowledgeChunk.chunk_text,
                KnowledgeDoc.title,
                KnowledgeDoc.type,
                KnowledgeDoc.diet_tags,
                KnowledgeChunk.embedding.cosine_distance(vec).label("distance"),
            )
            .join(KnowledgeDoc, KnowledgeChunk.doc_id == KnowledgeDoc.id)
            .where(KnowledgeChunk.embedding.is_not(None))
            .order_by(text("distance ASC"))
            .limit(pool_limit)
        )

        stop_words = {
            "i",
            "want",
            "everything",
            "needed",
            "to",
            "make",
            "an",
            "a",
            "the",
            "for",
            "people",
            "persons",
            "guests",
            "with",
            "and",
            "in",
            "of",
            "some",
            "give",
            "me",
            "need",
            "find",
            "get",
            "looking",
            "all",
        }
        words = [w for w in re.findall(r"\w+", query.lower()) if len(w) > 1 and w not in stop_words]
        or_terms = " | ".join(words) if words else query
        sparse_stmt = (
            select(
                KnowledgeChunk.id,
                KnowledgeChunk.doc_id,
                KnowledgeChunk.section_title,
                KnowledgeChunk.chunk_text,
                KnowledgeDoc.title,
                KnowledgeDoc.type,
                KnowledgeDoc.diet_tags,
                func.ts_rank(KnowledgeChunk.tsv, func.to_tsquery("english", or_terms)).label(
                    "rank"
                ),
            )
            .join(KnowledgeDoc, KnowledgeChunk.doc_id == KnowledgeDoc.id)
            .where(KnowledgeChunk.tsv.op("@@")(func.to_tsquery("english", or_terms)))
            .order_by(text("rank DESC"))
            .limit(pool_limit)
        )

        candidates: dict[str, dict[str, Any]] = {}

        async with self.session_factory() as session:
            # 1. Run Dense Search
            dense_res = await session.execute(dense_stmt)
            for rank_idx, r in enumerate(dense_res.mappings().all(), start=1):
                cid = str(r["id"])
                if cid not in candidates:
                    candidates[cid] = {
                        "id": cid,
                        "doc_id": str(r["doc_id"]),
                        "title": r["title"],
                        "section_title": r["section_title"],
                        "chunk_text": r["chunk_text"],
                        "type": r["type"],
                        "diet_tags": r["diet_tags"],
                        "dense_rank": rank_idx,
                        "sparse_rank": None,
                        "rrf_score": 0.0,
                    }
                else:
                    candidates[cid]["dense_rank"] = rank_idx
                candidates[cid]["rrf_score"] += 1.0 / (rrf_k + rank_idx)

            # 2. Run Sparse Search
            sparse_res = await session.execute(sparse_stmt)
            for rank_idx, r in enumerate(sparse_res.mappings().all(), start=1):
                cid = str(r["id"])
                if cid not in candidates:
                    candidates[cid] = {
                        "id": cid,
                        "doc_id": str(r["doc_id"]),
                        "title": r["title"],
                        "section_title": r["section_title"],
                        "chunk_text": r["chunk_text"],
                        "type": r["type"],
                        "diet_tags": r["diet_tags"],
                        "dense_rank": None,
                        "sparse_rank": rank_idx,
                        "rrf_score": 0.0,
                    }
                else:
                    candidates[cid]["sparse_rank"] = rank_idx
                candidates[cid]["rrf_score"] += 1.0 / (rrf_k + rank_idx)

        # Apply diet filtering if specified
        results = list(candidates.values())
        if diet_filter:
            filtered: list[dict[str, Any]] = []
            for item in results:
                item_tags = set(item.get("diet_tags", []))
                # Check if matches any of requested diet filter
                if any(tag in item_tags for tag in diet_filter):
                    filtered.append(item)
            if filtered:
                results = filtered

        results.sort(key=lambda x: float(x.get("rrf_score", 0.0)), reverse=True)
        return results[:limit]

    async def expand_knowledge_graph(self, recipe_titles: list[str]) -> dict[str, Any]:
        """Expand recipe nodes via Knowledge Graph to find required ingredients, substitutions, and diets."""
        if not recipe_titles:
            return {"ingredients": [], "substitutions": [], "diets": []}

        from sqlalchemy.orm import aliased

        target_node = aliased(KGNode)
        sub_node = aliased(KGNode)
        orig_node = aliased(KGNode)

        kg_stmt = (
            select(
                KGNode.name.label("recipe_title"),
                KGEdge.relation_type,
                target_node.name.label("entity_name"),
                target_node.entity_type,
                KGEdge.properties,
            )
            .select_from(KGNode)
            .join(KGEdge, KGNode.id == KGEdge.source_node_id)
            .join(target_node, KGEdge.target_node_id == target_node.id)
            .where(KGNode.name.in_(recipe_titles))
        )

        sub_stmt = (
            select(
                sub_node.name.label("substitute_name"),
                orig_node.name.label("original_name"),
            )
            .select_from(KGEdge)
            .join(sub_node, KGEdge.source_node_id == sub_node.id)
            .join(orig_node, KGEdge.target_node_id == orig_node.id)
            .where(KGEdge.relation_type == "substitutes_for")
        )

        ingredients: list[dict[str, Any]] = []
        diets: list[str] = []
        substitutions: list[dict[str, str]] = []

        async with self.session_factory() as session:
            res = await session.execute(kg_stmt)
            for row in res.mappings().all():
                rel = row["relation_type"]
                if rel == "requires":
                    props = row["properties"] or {}
                    ingredients.append(
                        {
                            "name": row["entity_name"],
                            "qty": props.get("qty", 1),
                            "unit": props.get("unit", "piece"),
                            "optional": props.get("optional", False),
                        }
                    )
                elif rel == "satisfies_diet":
                    diets.append(row["entity_name"])

            sub_res = await session.execute(sub_stmt)
            for row in sub_res.mappings().all():
                substitutions.append(
                    {
                        "substitute": row["substitute_name"],
                        "replaces": row["original_name"],
                    }
                )

        return {
            "ingredients": ingredients,
            "diets": list(set(diets)),
            "substitutions": substitutions,
        }

    async def retrieve_and_plan(self, raw_query: str, top_k: int = 5) -> dict[str, Any]:
        """Full pipeline: query decomposition -> hybrid chunk retrieval -> graph expansion -> reranking."""
        decomp = self.decompose_query(raw_query)
        goal = decomp["goal"]
        diet_filter = decomp["dietary_tags"] or None

        # 1. Hybrid Search
        candidates = await self.hybrid_search_chunks(
            query=f"{goal} {' '.join(decomp['dietary_tags'])}".strip(),
            limit=top_k * 2,
            diet_filter=diet_filter,
        )

        # 2. Listwise Reranking
        reranked = await self.reranker.rerank(raw_query, candidates, top_k=top_k)

        # 3. Knowledge Graph Expansion for top matched recipes
        top_titles = list({c["title"] for c in reranked if c.get("title")})
        graph_data = await self.expand_knowledge_graph(top_titles)

        return {
            "query_decomposition": decomp,
            "retrieved_chunks": reranked,
            "graph_expansion": graph_data,
        }
