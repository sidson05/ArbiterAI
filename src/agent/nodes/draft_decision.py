from typing import Any

from src.agent.llm_factory import get_llm
from src.agent.prompts import DECISION_DRAFTER_SYSTEM_PROMPT
from src.agent.state import ClaimState


async def draft_decision_node(state: ClaimState) -> dict[str, Any]:
    extracted = state.get("extracted_data")
    coverage = state.get("coverage_finding")
    fraud = state.get("fraud_signals")
    human_override = state.get("human_override")
    requires_human_review = state.get("requires_human_review", False)

    # Determine status
    if human_override:
        final_decision = human_override.get("action", "APPROVED")
        override_reason = human_override.get("reason", "Adjuster manual review complete.")
    elif requires_human_review:
        final_decision = "ESCALATED"
    elif coverage and coverage.is_covered:
        final_decision = "APPROVED"
    else:
        final_decision = "REJECTED"

    # Financial details
    claimed_amt = extracted.claim_amount if extracted else 0.0
    deductibles = coverage.deductibles_applied if coverage else 0.0
    sub_limit = coverage.sub_limits_applied if coverage else None
    approved_amt = coverage.recommended_payout if (coverage and final_decision == "APPROVED") else 0.0
    if human_override and "approved_amount" in human_override:
        approved_amt = human_override["approved_amount"]

    clauses_cited = coverage.cited_clause_numbers if coverage else []

    # Letter generation (LLM or template)
    llm = get_llm()
    letter = ""
    if llm and final_decision != "ESCALATED":
        try:
            prompt = (
                f"Generate decision letter for:\n"
                f"Claim ID: {state.get('claim_id')}\n"
                f"Claimant: {extracted.claimant_name if extracted else 'Policyholder'}\n"
                f"Decision: {final_decision}\n"
                f"Claimed: ${claimed_amt:,.2f}\n"
                f"Approved: ${approved_amt:,.2f}\n"
                f"Deductibles: ${deductibles:,.2f}\n"
                f"Cited Clauses: {', '.join(clauses_cited)}\n"
                f"Reasoning: {coverage.reasoning if coverage else 'Adjudication completed.'}"
            )
            resp = await llm.ainvoke([
                {"role": "system", "content": DECISION_DRAFTER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ])
            letter = resp.content
        except Exception as e:
            print(f"[Decision Node] LLM letter generation skipped: {e}")

    if not letter:
        # Standard professional insurance determination summary
        lines = [
            "OFFICIAL CLAIMS ADJUDICATION DETERMINATION",
            f"Claim Reference: {state.get('claim_id')}",
            f"Policyholder ID: {extracted.claimant_id if extracted else 'N/A'}",
            f"Policy Contract: {extracted.policy_id if extracted else 'N/A'}",
            f"Status: {final_decision}",
            "",
            "Financial Settlement:",
            f"  - Claimed Amount:    ${claimed_amt:,.2f}",
            f"  - Deductibles:       ${deductibles:,.2f}",
        ]
        if sub_limit:
            lines.append(f"  - Applied Sub-limit: ${sub_limit:,.2f}")
        lines.extend([
            f"  - Net Payable:       ${approved_amt:,.2f}",
            "",
            f"Cited Contractual Clauses: {', '.join(clauses_cited) if clauses_cited else 'None'}",
            f"Reasoning & Findings: {coverage.reasoning if coverage else 'N/A'}"
        ])
        if requires_human_review and not human_override:
            lines.extend([
                "",
                f"Notice: This claim has been placed in pending status and escalated to an authorized senior claims adjuster for verification: {', '.join(state.get('review_reasons', []))}"
            ])
        letter = "\n".join(lines)

    audit_entry = {
        "step": "draft_decision_node",
        "final_decision": final_decision,
        "approved_amount": approved_amt,
        "cited_clauses": clauses_cited,
        "status": "SUCCESS"
    }

    return {
        "final_decision": final_decision,
        "final_explanation": letter,
        "audit_trail": state.get("audit_trail", []) + [audit_entry]
    }
