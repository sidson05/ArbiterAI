from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

class ExtractedClaimData(BaseModel):
    claimant_id: str
    claimant_name: Optional[str] = None
    policy_id: str
    incident_date: str
    claim_amount: float
    category: str
    claimed_items: List[Dict[str, Any]] = Field(default_factory=list)
    diagnosis_or_damage_desc: str
    receipt_hash: Optional[str] = None

class ClauseMatch(BaseModel):
    policy_id: str
    clause_number: str
    section_name: str
    title: str
    content: str
    deductible: float = 0.0
    sub_limit: Optional[float] = None
    similarity_score: float

class CoverageFinding(BaseModel):
    is_covered: bool
    cited_clause_numbers: List[str]
    verbatim_citations: List[str]
    confidence_score: float = Field(ge=0.0, le=1.0)
    deductibles_applied: float = 0.0
    sub_limits_applied: Optional[float] = None
    recommended_payout: float = 0.0
    reasoning: str

class FraudSignal(BaseModel):
    is_suspicious: bool
    risk_score: float = Field(ge=0.0, le=1.0)
    flags: List[str] = Field(default_factory=list)
    anomaly_rationale: Optional[str] = None

class ClaimState(TypedDict):
    claim_id: str
    raw_claim_text: str
    raw_document_url: Optional[str]
    extracted_data: Optional[ExtractedClaimData]
    retrieved_clauses: List[ClauseMatch]
    fraud_signals: Optional[FraudSignal]
    coverage_finding: Optional[CoverageFinding]
    requires_human_review: bool
    review_reasons: List[str]
    human_override: Optional[Dict[str, Any]]
    final_decision: Optional[str]  # APPROVED, REJECTED, ESCALATED
    final_explanation: Optional[str]
    audit_trail: List[Dict[str, Any]]
