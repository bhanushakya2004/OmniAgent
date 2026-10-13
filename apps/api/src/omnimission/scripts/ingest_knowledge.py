"""CLI script for ingesting knowledge corpus documents and Knowledge Graph into PostgreSQL."""

import asyncio

from omnimission.services.knowledge_service import KnowledgeService


async def main() -> None:
    print("Ingesting knowledge corpus documents, chunks, embeddings, and Knowledge Graph...")
    service = KnowledgeService()
    counts = await service.ingest_knowledge_corpus()
    print("Knowledge Ingestion Completed Successfully:")
    print(f"  Documents:       {counts['docs']}")
    print(f"  Chunks:          {counts['chunks']}")
    print(f"  KG Nodes:        {counts['kg_nodes']}")
    print(f"  KG Edges:        {counts['kg_edges']}")


if __name__ == "__main__":
    asyncio.run(main())
