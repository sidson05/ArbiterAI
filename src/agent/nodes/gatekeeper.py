from typing import Dict, Any, List
from src.agent.state import ClaimState
from src.core.config import settings

def evaluate_gatekeeper_node(state: ClaimState) -> Dict[str, Any]:
    extracted = state.get("extracted_data")
    coverage = state.get("coverage_finding")
    fraud = state.get("fraud_signals")

    review_reasons: List[str] = []
    requires_human_review = False

    # 1. High-Value Claim Rule
    if extracted and extracted.claim_amount > settings.HIGH_VALUE_THRESHOLD:
        requires_human_review = True
        review_reasons.append(f"Claim amount (${extracted.claim_amount:,.2f}) exceeds high-value threshold (${settings.HIGH_VALUE_THRESHOLD:,.2f}).")

    # 2. Fraud & Anomaly Flag Rule
    if fraud and fraud.is_suspicious:
        requires_human_review = True
        review_reasons.append(f"Fraud guard flagged claim: {', '.join(fraud.flags)}.")

    # 3. Low Confidence Scoring Rule
    if coverage and coverage.confidence_score < settings.CONFIDENCE_THRESHOLD:
        requires_human_review = True
        review_reasons.append(f"Confidence score ({coverage.confidence_score:.2f}) is below approval threshold ({settings.CONFIDENCE_THRESHOLD:.2f}).")

    audit_entry = {
        "step": "evaluate_gatekeeper_node",
        "requires_human_review": requires_human_review,
        "review_reasons": review_reasons,
        "status": "SUCCESS"
    }

    return {
        "requires_human_review": requires_human_review,
        "review_reasons": review_reasons,
        "audit_trail": state.get("audit_trail", []) + [audit_entry]
    }

def route_after_gate(state: ClaimState) -> str:
    """
    Conditional edge router for LangGraph.
    Routes to 'human_review_interrupt' if requires_human_review is True,
    else directly to 'draft_decision'.
    """
    if state.get("requires_human_review", False):
        return "human_review_interrupt"
    return "draft_decision"
