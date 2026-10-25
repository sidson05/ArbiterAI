from typing import Any

from src.agent.state import ClaimState, ClauseMatch
from src.rag.vector_store import vector_store


async def retrieve_clauses_node(state: ClaimState) -> dict[str, Any]:
    extracted = state.get("extracted_data")
    if not extracted:
        return {"retrieved_clauses": []}

    query = f"{extracted.category} {extracted.diagnosis_or_damage_desc}"
    policy_id = extracted.policy_id

    raw_matches = await vector_store.search_clauses(query=query, policy_id=policy_id, k=3)
    
    clause_matches: list[ClauseMatch] = [
        ClauseMatch(
            policy_id=m["policy_id"],
            clause_number=m["clause_number"],
            section_name=m["section_name"],
            title=m["title"],
            content=m["content"],
            deductible=m["deductible"],
            sub_limit=m["sub_limit"],
            similarity_score=m["similarity_score"]
        )
        for m in raw_matches
    ]

    audit_entry = {
        "step": "retrieve_clauses_node",
        "retrieved_count": len(clause_matches),
        "top_clauses": [c.clause_number for c in clause_matches],
        "status": "SUCCESS"
    }

    return {
        "retrieved_clauses": clause_matches,
        "audit_trail": state.get("audit_trail", []) + [audit_entry]
    }
