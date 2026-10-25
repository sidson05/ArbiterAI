import asyncio
import glob
from src.agent.graph import build_claims_graph
from src.rag.chunker import ClauseAwareChunker
from src.rag.vector_store import vector_store

async def setup_test_index():
    policy_files = glob.glob("data/policies/*.md")
    for pf in policy_files:
        with open(pf, "r", encoding="utf-8") as f:
            text = f.read()
        chunks = ClauseAwareChunker.parse_markdown_policy(text)
        for c in chunks:
            await vector_store.index_clause(c)

async def test_claims_graph():
    await setup_test_index()
    agent = build_claims_graph()

    # 1. Test Approved Inpatient Health Claim
    approved_claim = {
        "claim_id": "TEST-CLM-001",
        "raw_claim_text": (
            '{"claimant_id": "CUST-101", "policy_id": "POL-HLT-001", "incident_date": "2026-03-12", '
            '"claimed_amount": 3450.00, "category": "Inpatient Hospitalization", '
            '"claim_text": "Claimant admitted to hospital for 3 days due to pneumonia. IV antibiotics, room rent, doctor fees.", '
            '"claimed_items": [{"item": "Room & Board", "amount": 900.00}, {"item": "Treatment", "amount": 2550.00}]}'
        ),
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

    config_1 = {"configurable": {"thread_id": "thread-001"}}
    result_1 = await agent.ainvoke(approved_claim, config=config_1)
    
    assert result_1["final_decision"] == "APPROVED", f"Expected APPROVED, got {result_1['final_decision']}"
    assert len(result_1["coverage_finding"].cited_clause_numbers) > 0
    print("[PASS] Test 1: Standard Claim correctly APPROVED with clause citations.")

    # 2. Test Excluded Cosmetic Surgery Claim
    excluded_claim = {
        "claim_id": "TEST-CLM-002",
        "raw_claim_text": (
            '{"claimant_id": "CUST-102", "policy_id": "POL-HLT-001", "incident_date": "2026-06-15", '
            '"claimed_amount": 6200.00, "category": "Cosmetic Exclusion", '
            '"claim_text": "Patient underwent elective aesthetic rhinoplasty for nasal shape improvement.", '
            '"claimed_items": [{"item": "Rhinoplasty Surgical Fee", "amount": 6200.00}]}'
        ),
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

    config_2 = {"configurable": {"thread_id": "thread-002"}}
    result_2 = await agent.ainvoke(excluded_claim, config=config_2)
    assert result_2["final_decision"] == "REJECTED", f"Expected REJECTED, got {result_2['final_decision']}"
    assert "Clause 4.2" in result_2["coverage_finding"].cited_clause_numbers
    print("[PASS] Test 2: Cosmetic Surgery correctly REJECTED under Clause 4.2.")

    # 3. Test High-Value Claim (> $10k) Triggering Human Interrupt
    high_value_claim = {
        "claim_id": "TEST-CLM-003",
        "raw_claim_text": (
            '{"claimant_id": "CUST-103", "policy_id": "POL-HOM-001", "incident_date": "2026-04-02", '
            '"claimed_amount": 28500.00, "category": "Major Fire Damage", '
            '"claim_text": "Kitchen grease fire spread to roof and rafters. Major structural charring.", '
            '"claimed_items": [{"item": "Roof Rebuilding", "amount": 28500.00}]}'
        ),
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

    config_3 = {"configurable": {"thread_id": "thread-003"}}
    # First invocation: should pause at interrupt
    paused_state = await agent.ainvoke(high_value_claim, config=config_3)
    
    # Verify it paused before drafting final decision alone
    snapshot = agent.get_state(config_3)
    assert "human_review_interrupt" in snapshot.next, f"Expected interrupt before human_review_interrupt, next is: {snapshot.next}"
    print(f"[PASS] Test 3A: High-Value claim ($28.5k) paused at interrupt. Reasons: {snapshot.values['review_reasons']}")

    # Adjuster provides human override
    agent.update_state(
        config_3,
        {"human_override": {"action": "APPROVED", "approved_amount": 28000.00, "reason": "Adjuster inspected site and contractor quotes."}}
    )
    # Resume graph execution
    final_resumed = await agent.ainvoke(None, config=config_3)
    assert final_resumed["final_decision"] == "APPROVED"
    print(f"[PASS] Test 3B: Resumed from checkpoint after human adjuster sign-off. Decision: {final_resumed['final_decision']}")

if __name__ == "__main__":
    asyncio.run(test_claims_graph())
