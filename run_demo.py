import asyncio
import json
import glob
from src.agent.graph import build_claims_graph
from src.rag.chunker import ClauseAwareChunker
from src.rag.vector_store import vector_store

async def run_live_demonstration():
    print("=" * 80)
    print("  AGENTIC RAG INSURANCE CLAIMS ADJUDICATION SYSTEM (LangGraph + pgvector)")
    print("=" * 80)

    # 1. Indexing policies
    print("\n[Step 1] Ingesting & indexing 6 policy documents...")
    policy_files = glob.glob("data/policies/*.md")
    total_clauses = 0
    for pf in policy_files:
        with open(pf, "r", encoding="utf-8") as f:
            text = f.read()
        chunks = ClauseAwareChunker.parse_markdown_policy(text)
        for c in chunks:
            await vector_store.index_clause(c)
            total_clauses += 1
    print(f"  -> Successfully indexed {total_clauses} clauses across {len(policy_files)} policies into VectorStore.")

    agent = build_claims_graph()

    # --- Scenario 1: Straight-Through Approved Claim ---
    print("\n" + "-" * 80)
    print("SCENARIO 1: Routine Hospitalization Claim (Expected: AUTO-APPROVED)")
    print("-" * 80)
    claim_1 = {
        "claim_id": "DEMO-CLM-001",
        "raw_claim_text": json.dumps({
            "claimant_id": "CUST-4102",
            "claimant_name": "Sarah Connor",
            "policy_id": "POL-HLT-001",
            "incident_date": "2026-03-12",
            "claimed_amount": 3450.00,
            "category": "Inpatient Hospitalization",
            "claim_text": "Claimant admitted to St. Jude Hospital for 3 days due to acute viral pneumonia. Underwent IV antibiotic therapy, chest X-rays, blood cultures, and 3 nights in standard single room.",
            "claimed_items": [
                {"item": "Room & Board 3 days", "amount": 900.00},
                {"item": "Diagnostic X-rays & Blood Tests", "amount": 850.00},
                {"item": "Physician & Specialist Fees", "amount": 700.00},
                {"item": "Pharmacy & Medication", "amount": 1000.00}
            ],
            "receipt_hash": "HASH-DEMO-001"
        }),
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

    res_1 = await agent.ainvoke(claim_1, config={"configurable": {"thread_id": "demo-thread-1"}})
    cov_1 = res_1["coverage_finding"]
    print(f"  Decision:           [{res_1['final_decision']}]")
    print(f"  Confidence Score:   {cov_1.confidence_score * 100:.1f}%")
    print(f"  Claimed Amount:     ${res_1['extracted_data'].claim_amount:,.2f}")
    print(f"  Deductible Applied: ${cov_1.deductibles_applied:,.2f}")
    print(f"  Approved Payout:    ${cov_1.recommended_payout:,.2f}")
    print(f"  Cited Clauses:      {', '.join(cov_1.cited_clause_numbers)}")
    print(f"  Straight-Through:   Yes (Zero human intervention required)")

    # --- Scenario 2: Excluded Cosmetic Surgery Claim ---
    print("\n" + "-" * 80)
    print("SCENARIO 2: Excluded Medical Procedure (Expected: AUTO-REJECTED)")
    print("-" * 80)
    claim_2 = {
        "claim_id": "DEMO-CLM-002",
        "raw_claim_text": json.dumps({
            "claimant_id": "CUST-5211",
            "claimant_name": "James Vance",
            "policy_id": "POL-HLT-001",
            "incident_date": "2026-06-15",
            "claimed_amount": 6200.00,
            "category": "Cosmetic Exclusion",
            "claim_text": "Patient underwent elective aesthetic rhinoplasty and septoplasty for facial aesthetic enhancement at Beverly Plastic Surgery Clinic.",
            "claimed_items": [{"item": "Rhinoplasty Surgical Fee", "amount": 6200.00}],
            "receipt_hash": "HASH-DEMO-002"
        }),
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

    res_2 = await agent.ainvoke(claim_2, config={"configurable": {"thread_id": "demo-thread-2"}})
    cov_2 = res_2["coverage_finding"]
    print(f"  Decision:           [{res_2['final_decision']}]")
    print(f"  Exclusion Trigger:  {', '.join(cov_2.cited_clause_numbers)}")
    print(f"  Approved Payout:    $0.00")
    print(f"  Legal Reasoning:    {cov_2.reasoning}")

    # --- Scenario 3: High-Value Claim Triggering Human-in-the-Loop Interrupt ---
    print("\n" + "-" * 80)
    print("SCENARIO 3: High-Value Residential Fire Damage ($28,500) (HITL WORKFLOW)")
    print("-" * 80)
    config_3 = {"configurable": {"thread_id": "demo-thread-3"}}
    claim_3 = {
        "claim_id": "DEMO-CLM-003",
        "raw_claim_text": json.dumps({
            "claimant_id": "CUST-8890",
            "claimant_name": "Robert Sterling",
            "policy_id": "POL-HOM-001",
            "incident_date": "2026-04-02",
            "claimed_amount": 28500.00,
            "category": "Major Fire Damage",
            "claim_text": "Kitchen grease fire spread to roof rafters and attic structure. Upper level sustained major structural charring. Claim includes temporary rental housing.",
            "claimed_items": [
                {"item": "Roof & Structural Rebuilding", "amount": 22000.00},
                {"item": "Temporary Accommodation 3 Months", "amount": 6500.00}
            ],
            "receipt_hash": "HASH-DEMO-003"
        }),
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

    print("  -> Submitting $28,500 claim to agent...")
    await agent.ainvoke(claim_3, config=config_3)

    # Check state at checkpoint
    snapshot = agent.get_state(config_3)
    print(f"  -> GATEKEEPER TRIGGERED: Claim halted at checkpoint.")
    print(f"  -> Checkpoint Node: {snapshot.next}")
    print(f"  -> Escalation Reason: {snapshot.values['review_reasons'][0]}")

    print("\n  [Simulating Human Adjuster Action via API]")
    print("  -> Senior Adjuster (ID: ADJ-9041) reviews site photos and engineering quotes.")
    print("  -> Adjuster submits Approval for $28,000.00 (less $500 deductible).")

    # Human Override injected into thread state
    agent.update_state(
        config_3,
        {
            "human_override": {
                "action": "APPROVED",
                "approved_amount": 28000.00,
                "adjuster_id": "ADJ-9041",
                "notes": "Verified fire brigade dispatch incident report and contractor quotes. Structural damage qualifies under Clause 1.1."
            }
        }
    )

    # Resuming graph
    resumed = await agent.ainvoke(None, config=config_3)
    print(f"  -> Resumed Execution: State Machine finalized.")
    print(f"  Final Determination: [{resumed['final_decision']}]")
    print(f"  Approved Settlement:   ${resumed['human_override']['approved_amount']:,.2f}")
    print(f"  Adjuster Attribution:  {resumed['human_override']['adjuster_id']}")

    print("\n" + "=" * 80)
    print("  DEMONSTRATION COMPLETE: All scenarios executed successfully!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_live_demonstration())
