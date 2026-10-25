import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_
from src.core.database import AsyncSessionLocal, Policy, PolicyClause
from src.rag.embeddings import embedding_service
from src.rag.chunker import ClauseChunk

class VectorStore:
    def __init__(self):
        # In-memory fallback index for local unit tests without live postgres
        self._memory_index: List[Dict[str, Any]] = []

    async def index_clause(self, chunk: ClauseChunk):
        emb = await embedding_service.get_embedding(f"{chunk.title}\n{chunk.content}")
        
        # Store in memory cache
        self._memory_index.append({
            "policy_id": chunk.policy_id,
            "clause_number": chunk.clause_number,
            "section_name": chunk.section_name,
            "title": chunk.title,
            "content": chunk.content,
            "deductible": chunk.deductible,
            "sub_limit": chunk.sub_limit,
            "embedding": np.array(emb, dtype=np.float32)
        })

        # Persist to Postgres if available
        try:
            async with AsyncSessionLocal() as session:
                clause_db = PolicyClause(
                    policy_id=chunk.policy_id,
                    clause_number=chunk.clause_number,
                    section_name=chunk.section_name,
                    title=chunk.title,
                    content=chunk.content,
                    deductible=chunk.deductible,
                    sub_limit=chunk.sub_limit,
                    embedding=emb
                )
                session.add(clause_db)
                await session.commit()
        except Exception:
            # Fallback quietly to memory index if postgres is not currently active
            pass

    async def search_clauses(self, query: str, policy_id: str, k: int = 3) -> List[Dict[str, Any]]:
        query_emb = await embedding_service.get_embedding(query)
        q_vec = np.array(query_emb, dtype=np.float32)

        # 1. Try PostgreSQL pgvector search
        try:
            async with AsyncSessionLocal() as session:
                stmt = (
                    select(
                        PolicyClause,
                        PolicyClause.embedding.cosine_distance(query_emb).label("distance")
                    )
                    .where(PolicyClause.policy_id == policy_id)
                    .order_by("distance")
                    .limit(k)
                )
                result = await session.execute(stmt)
                rows = result.all()
                if rows:
                    return [
                        {
                            "policy_id": row.PolicyClause.policy_id,
                            "clause_number": row.PolicyClause.clause_number,
                            "section_name": row.PolicyClause.section_name,
                            "title": row.PolicyClause.title,
                            "content": row.PolicyClause.content,
                            "deductible": float(row.PolicyClause.deductible or 0.0),
                            "sub_limit": float(row.PolicyClause.sub_limit) if row.PolicyClause.sub_limit else None,
                            "similarity_score": round(1.0 - float(row.distance), 4)
                        }
                        for row in rows
                    ]
        except Exception:
            pass

        # 2. In-Memory fallback cosine search
        matches = []
        for item in self._memory_index:
            if item["policy_id"] == policy_id:
                target_vec = item["embedding"]
                dot = np.dot(q_vec, target_vec)
                norm_q = np.linalg.norm(q_vec)
                norm_t = np.linalg.norm(target_vec)
                sim = dot / (norm_q * norm_t) if (norm_q > 0 and norm_t > 0) else 0.0

                # Also boost if title words appear in query
                tokens = query.lower().split()
                title_matches = sum(1 for t in tokens if t in item["title"].lower() or t in item["content"].lower())
                boosted_sim = min(1.0, float(sim) + (0.05 * title_matches))

                matches.append({
                    "policy_id": item["policy_id"],
                    "clause_number": item["clause_number"],
                    "section_name": item["section_name"],
                    "title": item["title"],
                    "content": item["content"],
                    "deductible": item["deductible"],
                    "sub_limit": item["sub_limit"],
                    "similarity_score": round(boosted_sim, 4)
                })

        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        return matches[:k]

vector_store = VectorStore()
