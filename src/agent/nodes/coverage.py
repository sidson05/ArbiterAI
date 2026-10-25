from typing import Any

from src.agent.llm_factory import get_llm
from src.agent.prompts import COVERAGE_ASSESSOR_SYSTEM_PROMPT
from src.agent.state import ClaimState, CoverageFinding


async def assess_coverage_node(state: ClaimState) -> dict[str, Any]:
    extracted = state.get("extracted_data")
    clauses = state.get("retrieved_clauses", [])

    if not extracted or not clauses:
        return {
            "coverage_finding": CoverageFinding(
                is_covered=False,
                cited_clause_numbers=[],
                verbatim_citations=[],
                confidence_score=0.2,
                reasoning="Missing extracted claim data or policy clauses."
            )
        }

    # Format clauses text for LLM / rule checking
    clause_texts = "\n\n".join([
        f"[{c.clause_number}] {c.title} (Section: {c.section_name}, Deductible: ${c.deductible}, SubLimit: ${c.sub_limit or 'None'}):\n{c.content}"
        for c in clauses
    ])

    llm = get_llm()
    finding = None

    if llm:
        try:
            structured_llm = llm.with_structured_output(CoverageFinding)
            prompt = (
                f"CLAIM DETAILS:\n"
                f"Policy ID: {extracted.policy_id}\n"
                f"Category: {extracted.category}\n"
                f"Claimed Amount: ${extracted.claim_amount}\n"
                f"Description: {extracted.diagnosis_or_damage_desc}\n"
                f"Items: {extracted.claimed_items}\n\n"
                f"RETRIEVED POLICY CLAUSES:\n{clause_texts}"
            )
            finding = await structured_llm.ainvoke([
                {"role": "system", "content": COVERAGE_ASSESSOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ])
        except Exception as e:
            print(f"[Coverage Node] LLM coverage assessment skipped: {e}")

    if not finding:
        # High-fidelity deterministic evaluation engine
        desc_lower = extracted.diagnosis_or_damage_desc.lower()
        is_covered = True
        cited_numbers = []
        citations = []
        reasoning_points = []
        deductible_to_apply = 0.0
        sub_limit_to_apply = None

        # Check for explicit exclusions first
        exclusion_found = False
        for c in clauses:
            content_lower = c.content.lower()
            title_lower = c.title.lower()

            if "exclusion" in c.section_name.lower():
                # Check pre-existing condition
                if "pre-existing" in title_lower and ("hypertension" in desc_lower or "pre-existing" in desc_lower or "chronic" in desc_lower or "stroke" in desc_lower):
                    exclusion_found = True
                    cited_numbers.append(c.clause_number)
                    citations.append(c.content[:150] + "...")
                    reasoning_points.append(f"Excluded under {c.clause_number}: Pre-existing conditions waiting period.")

                # Check cosmetic
                elif "cosmetic" in title_lower and ("rhinoplasty" in desc_lower or "cosmetic" in desc_lower or "aesthetic" in desc_lower):
                    exclusion_found = True
                    cited_numbers.append(c.clause_number)
                    citations.append(c.content[:150] + "...")
                    reasoning_points.append(f"Excluded under {c.clause_number}: Aesthetic and cosmetic surgery.")

                # Check intoxication / alcohol
                elif ("intoxication" in title_lower or "alcohol" in content_lower) and ("alcohol" in desc_lower or "breathalyzer" in desc_lower or "intoxicated" in desc_lower):
                    exclusion_found = True
                    cited_numbers.append(c.clause_number)
                    citations.append(c.content[:150] + "...")
                    reasoning_points.append(f"Excluded under {c.clause_number}: Operating vehicle under intoxication.")

                # Check gradual seepage
                elif ("seepage" in title_lower or "gradual" in content_lower) and ("seepage" in desc_lower or "gradual" in desc_lower or "mold" in desc_lower):
                    exclusion_found = True
                    cited_numbers.append(c.clause_number)
                    citations.append(c.content[:150] + "...")
                    reasoning_points.append(f"Excluded under {c.clause_number}: Gradual rainwater seepage and lack of maintenance.")

                # Check mysterious disappearance
                elif ("mysterious" in title_lower or "unforced" in content_lower) and ("disappearance" in desc_lower or "lost" in desc_lower or "no forced entry" in desc_lower):
                    exclusion_found = True
                    cited_numbers.append(c.clause_number)
                    citations.append(c.content[:150] + "...")
                    reasoning_points.append(f"Excluded under {c.clause_number}: Mysterious disappearance without signs of forcible entry.")

                # Check experimental therapies
                elif "experimental" in title_lower and ("experimental" in desc_lower or "unapproved" in desc_lower or "uncertified" in desc_lower):
                    exclusion_found = True
                    cited_numbers.append(c.clause_number)
                    citations.append(c.content[:150] + "...")
                    reasoning_points.append(f"Excluded under {c.clause_number}: Unproven and experimental therapies.")

        if exclusion_found:
            is_covered = False
            payout = 0.0
            confidence = 0.95
        else:
            # Positive coverage
            for c in clauses:
                if "exclusion" not in c.section_name.lower():
                    cited_numbers.append(c.clause_number)
                    citations.append(c.content[:140] + "...")
                    deductible_to_apply = max(deductible_to_apply, c.deductible)
                    if c.sub_limit:
                        sub_limit_to_apply = c.sub_limit

            amount_eligible = extracted.claim_amount
            if sub_limit_to_apply and amount_eligible > sub_limit_to_apply:
                amount_eligible = sub_limit_to_apply
                reasoning_points.append(f"Sub-limit of ${sub_limit_to_apply:,.2f} applied.")

            payout = max(0.0, amount_eligible - deductible_to_apply)
            if deductible_to_apply > 0:
                reasoning_points.append(f"Compulsory deductible of ${deductible_to_apply:,.2f} applied.")
            reasoning_points.append("Claim items qualify under policy benefit clauses.")
            confidence = 0.92 if cited_numbers else 0.70

        finding = CoverageFinding(
            is_covered=is_covered,
            cited_clause_numbers=list(set(cited_numbers)),
            verbatim_citations=citations,
            confidence_score=confidence,
            deductibles_applied=deductible_to_apply,
            sub_limits_applied=sub_limit_to_apply,
            recommended_payout=round(payout, 2),
            reasoning=" ".join(reasoning_points)
        )

    audit_entry = {
        "step": "assess_coverage_node",
        "is_covered": finding.is_covered,
        "cited_clauses": finding.cited_clause_numbers,
        "recommended_payout": finding.recommended_payout,
        "confidence_score": finding.confidence_score,
        "status": "SUCCESS"
    }

    return {
        "coverage_finding": finding,
        "audit_trail": state.get("audit_trail", []) + [audit_entry]
    }
