from typing import Any

from src.agent.llm_factory import get_llm
from src.agent.prompts import FRAUD_DETECTOR_SYSTEM_PROMPT
from src.agent.state import ClaimState, FraudSignal

KNOWN_DUPLICATE_RECEIPT_HASHES = {
    "DUP-HASH-99812-REPAIR",
    "DUP-HASH-ALREADY-PAID",
    "REUSED-INVOICE-001"
}

async def check_fraud_node(state: ClaimState) -> dict[str, Any]:
    extracted = state.get("extracted_data")
    if not extracted:
        return {"fraud_signals": FraudSignal(is_suspicious=False, risk_score=0.0)}

    flags: list[str] = []
    risk_score = 0.0
    rationale_parts: list[str] = []

    # 1. Deterministic Rule Check: Duplicate Invoice Hash
    if extracted.receipt_hash and (
        extracted.receipt_hash in KNOWN_DUPLICATE_RECEIPT_HASHES or
        "DUP-HASH" in extracted.receipt_hash
    ):
        flags.append("DUPLICATE_RECEIPT_DETECTED")
        risk_score = max(risk_score, 0.95)
        rationale_parts.append(f"Receipt hash '{extracted.receipt_hash}' has been previously submitted and settled.")

    # 2. Deterministic Rule Check: Inception Timing
    # Incident within 48 hours of inception with historical treatments
    desc_lower = extracted.diagnosis_or_damage_desc.lower()
    if "prior to policy" in desc_lower or "preexisting" in desc_lower or "24 hours of policy inception" in desc_lower:
        flags.append("INCEPTION_TIMING_ANOMALY")
        risk_score = max(risk_score, 0.88)
        rationale_parts.append("Claim timeline indicates treatment commenced prior to policy bound date.")

    # 3. LLM Evaluator (if configured)
    llm = get_llm()
    if llm and risk_score < 0.5:
        try:
            structured_llm = llm.with_structured_output(FraudSignal)
            prompt = (
                f"Claim Details:\nAmount: ${extracted.claim_amount}\nCategory: {extracted.category}\n"
                f"Description: {extracted.diagnosis_or_damage_desc}\nItems: {extracted.claimed_items}"
            )
            llm_result = await structured_llm.ainvoke([
                {"role": "system", "content": FRAUD_DETECTOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ])
            if llm_result.is_suspicious:
                flags.extend(llm_result.flags)
                risk_score = max(risk_score, llm_result.risk_score)
                if llm_result.anomaly_rationale:
                    rationale_parts.append(llm_result.anomaly_rationale)
        except Exception as e:
            print(f"[Fraud Node] LLM evaluation skipped: {e}")

    is_suspicious = len(flags) > 0 or risk_score >= 0.70
    signal = FraudSignal(
        is_suspicious=is_suspicious,
        risk_score=risk_score,
        flags=flags,
        anomaly_rationale="; ".join(rationale_parts) if rationale_parts else "No anomalous risk indicators detected."
    )

    audit_entry = {
        "step": "check_fraud_node",
        "is_suspicious": is_suspicious,
        "risk_score": risk_score,
        "flags": flags,
        "status": "SUCCESS"
    }

    return {
        "fraud_signals": signal,
        "audit_trail": state.get("audit_trail", []) + [audit_entry]
    }
