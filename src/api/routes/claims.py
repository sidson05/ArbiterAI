from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.agent.graph import claims_agent

router = APIRouter(prefix="/claims", tags=["Claims"])

# In-memory store for claims state / thread tracking
CLAIMS_DB: dict[str, dict[str, Any]] = {}

class SubmitClaimRequest(BaseModel):
    claim_id: str
    policy_id: str
    claimant_id: str
    incident_date: str
    claimed_amount: float
    category: str
    claim_text: str
    claimed_items: list[dict[str, Any]] = Field(default_factory=list)
    receipt_hash: str | None = None

class SubmitClaimResponse(BaseModel):
    claim_id: str
    thread_id: str
    status: str
    requires_human_review: bool
    review_reasons: list[str]
    final_decision: str | None = None
    approved_amount: float | None = None
    cited_clauses: list[str] = Field(default_factory=list)
    decision_summary: str | None = None

@router.post("", response_model=SubmitClaimResponse)
async def submit_claim(request: SubmitClaimRequest):
    thread_id = f"thread-{request.claim_id}"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "claim_id": request.claim_id,
        "raw_claim_text": request.model_dump_json(),
        "raw_document_url": None,
        "extracted_data": None,
        "retrieved_clauses": [],
        "fraud_signals": None,
        "coverage_finding": None,
        "requires_human_review": False,
        "review_reasons": [],
        "human_override": None,
        "final_decision": None,
        "final_explanation": None,
        "audit_trail": []
    }

    result = await claims_agent.ainvoke(initial_state, config=config)
    snapshot = claims_agent.get_state(config)

    requires_review = "human_review_interrupt" in snapshot.next or result.get("requires_human_review", False)
    status = "PENDING_HUMAN_REVIEW" if requires_review else (result.get("final_decision") or "COMPLETED")

    coverage = result.get("coverage_finding")
    cited = coverage.cited_clause_numbers if coverage else []
    approved_amt = coverage.recommended_payout if (coverage and result.get("final_decision") == "APPROVED") else 0.0

    record = {
        "claim_id": request.claim_id,
        "thread_id": thread_id,
        "status": status,
        "requires_human_review": requires_review,
        "review_reasons": result.get("review_reasons", []),
        "final_decision": result.get("final_decision"),
        "approved_amount": approved_amt,
        "cited_clauses": cited,
        "decision_summary": result.get("final_explanation"),
        "audit_trail": result.get("audit_trail", [])
    }
    CLAIMS_DB[request.claim_id] = record

    return SubmitClaimResponse(**record)

@router.get("/{claim_id}")
async def get_claim(claim_id: str):
    if claim_id not in CLAIMS_DB:
        raise HTTPException(status_code=404, detail=f"Claim '{claim_id}' not found.")
    return CLAIMS_DB[claim_id]

@router.get("/queue/pending")
async def get_pending_review_queue():
    """Retrieve all claims paused at HITL checkpoint awaiting adjuster sign-off."""
    pending = [c for c in CLAIMS_DB.values() if c["requires_human_review"] and c["status"] == "PENDING_HUMAN_REVIEW"]
    return {"pending_count": len(pending), "claims": pending}
