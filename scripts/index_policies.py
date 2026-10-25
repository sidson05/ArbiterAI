import asyncio
import glob
import os

from src.rag.chunker import ClauseAwareChunker
from src.rag.vector_store import vector_store


async def index_all_policies():
    policy_files = glob.glob("data/policies/*.md")
    print(f"Found {len(policy_files)} policy files to index.")
    
    total_indexed = 0
    for pf in policy_files:
        with open(pf, "r", encoding="utf-8") as f:
            text = f.read()
            
        chunks = ClauseAwareChunker.parse_markdown_policy(text)
        print(f"Indexing {len(chunks)} clauses from {os.path.basename(pf)}...")
        for c in chunks:
            await vector_store.index_clause(c)
            total_indexed += 1

    print(f"Successfully indexed {total_indexed} clauses into VectorStore.")

if __name__ == "__main__":
    asyncio.run(index_all_policies())
