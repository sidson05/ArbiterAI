from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.agent.graph import claims_agent
from src.api.routes.claims import CLAIMS_DB

router = APIRouter(prefix="/claims", tags=["Human Review"])

class HumanReviewRequest(BaseModel):
    action: str = Field(description="APPROVED or REJECTED")
    approved_amount: float = Field(ge=0.0)
    adjuster_id: str
    notes: str

@router.post("/{claim_id}/review")
async def review_and_decide_claim(claim_id: str, review: HumanReviewRequest):
    if claim_id not in CLAIMS_DB:
        raise HTTPException(status_code=404, detail=f"Claim '{claim_id}' not found.")

    claim_record = CLAIMS_DB[claim_id]
    thread_id = claim_record["thread_id"]
    config = {"configurable": {"thread_id": thread_id}}

    snapshot = claims_agent.get_state(config)
    if "human_review_interrupt" not in snapshot.next and not claim_record["requires_human_review"]:
        raise HTTPException(
            status_code=400,
            detail=f"Claim '{claim_id}' is not currently awaiting human review (Status: {claim_record['status']})."
        )

    # Inject human override into LangGraph state
    human_override = {
        "action": review.action.upper(),
        "approved_amount": review.approved_amount,
        "adjuster_id": review.adjuster_id,
        "notes": review.notes
    }

    claims_agent.update_state(config, {"human_override": human_override})

    # Resume graph execution past the checkpoint
    resumed_result = await claims_agent.ainvoke(None, config=config)

    coverage = resumed_result.get("coverage_finding")
    cited = coverage.cited_clause_numbers if coverage else []

    updated_record = {
        "claim_id": claim_id,
        "thread_id": thread_id,
        "status": resumed_result.get("final_decision", review.action.upper()),
        "requires_human_review": False,
        "review_reasons": claim_record["review_reasons"],
        "final_decision": resumed_result.get("final_decision", review.action.upper()),
        "approved_amount": review.approved_amount,
        "cited_clauses": cited,
        "decision_summary": resumed_result.get("final_explanation"),
        "adjudicated_by": f"HUMAN_{review.adjuster_id}",
        "adjuster_notes": review.notes,
        "audit_trail": resumed_result.get("audit_trail", [])
    }
    CLAIMS_DB[claim_id] = updated_record

    return updated_record
