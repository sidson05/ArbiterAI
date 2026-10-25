from typing import Any

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class ExtractedClaimData(BaseModel):
    claimant_id: str
    claimant_name: str | None = None
    policy_id: str
    incident_date: str
    claim_amount: float
    category: str
    claimed_items: list[dict[str, Any]] = Field(default_factory=list)
    diagnosis_or_damage_desc: str
    receipt_hash: str | None = None

class ClauseMatch(BaseModel):
    policy_id: str
    clause_number: str
    section_name: str
    title: str
    content: str
    deductible: float = 0.0
    sub_limit: float | None = None
    similarity_score: float

class CoverageFinding(BaseModel):
    is_covered: bool
    cited_clause_numbers: list[str]
    verbatim_citations: list[str]
    confidence_score: float = Field(ge=0.0, le=1.0)
    deductibles_applied: float = 0.0
    sub_limits_applied: float | None = None
    recommended_payout: float = 0.0
    reasoning: str

class FraudSignal(BaseModel):
    is_suspicious: bool
    risk_score: float = Field(ge=0.0, le=1.0)
    flags: list[str] = Field(default_factory=list)
    anomaly_rationale: str | None = None

class ClaimState(TypedDict):
    claim_id: str
    raw_claim_text: str
    raw_document_url: str | None
    extracted_data: ExtractedClaimData | None
    retrieved_clauses: list[ClauseMatch]
    fraud_signals: FraudSignal | None
    coverage_finding: CoverageFinding | None
    requires_human_review: bool
    review_reasons: list[str]
    human_override: dict[str, Any] | None
    final_decision: str | None  # APPROVED, REJECTED, ESCALATED
    final_explanation: str | None
    audit_trail: list[dict[str, Any]]
