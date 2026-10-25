import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from src.api.main import app
from src.rag.chunker import ClauseAwareChunker
from src.rag.vector_store import vector_store
import glob

def init_test_policies():
    async def _index_all():
        policy_files = glob.glob("data/policies/*.md")
        for pf in policy_files:
            with open(pf, "r", encoding="utf-8") as f:
                text = f.read()
            chunks = ClauseAwareChunker.parse_markdown_policy(text)
            for c in chunks:
                await vector_store.index_clause(c)
    asyncio.run(_index_all())

# Run index initialization once at module import
init_test_policies()

@pytest.mark.asyncio
async def test_api_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "HEALTHY"

@pytest.mark.asyncio
async def test_submit_and_review_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Submit High-Value claim ($15,000) that requires review
        high_val_claim = {
            "claim_id": "CLM-API-TEST-001",
            "policy_id": "POL-HOM-001",
            "claimant_id": "CUST-999",
            "incident_date": "2026-04-10",
            "claimed_amount": 15000.00,
            "category": "Major Fire Damage",
            "claim_text": "Roof timber and electrical damage from lightning strike.",
            "claimed_items": [{"item": "Roof rebuild", "amount": 15000.00}],
            "receipt_hash": None
        }

        resp1 = await client.post("/api/v1/claims", json=high_val_claim)
        assert resp1.status_code == 200
        d1 = resp1.json()
        assert d1["status"] == "PENDING_HUMAN_REVIEW"
        assert d1["requires_human_review"] is True

        # 2. Check pending queue
        queue_resp = await client.get("/api/v1/claims/queue/pending")
        assert queue_resp.status_code == 200
        q_data = queue_resp.json()
        assert any(c["claim_id"] == "CLM-API-TEST-001" for c in q_data["claims"])

        # 3. Adjuster Review
        review_payload = {
            "action": "APPROVED",
            "approved_amount": 14500.00,
            "adjuster_id": "ADJ-7721",
            "notes": "Verified lightning storm date with meteorological agency and confirmed contractor estimates."
        }
        review_resp = await client.post("/api/v1/claims/CLM-API-TEST-001/review", json=review_payload)
        assert review_resp.status_code == 200
        d2 = review_resp.json()
        assert d2["status"] == "APPROVED"
        assert d2["approved_amount"] == 14500.00
        assert d2["requires_human_review"] is False
        assert "HUMAN_ADJ-7721" in d2["adjudicated_by"]

if __name__ == "__main__":
    async def _run_manual():
        print("Running test_api_health_check...")
        await test_api_health_check()
        print("Running test_submit_and_review_flow...")
        await test_submit_and_review_flow()
        print("All API tests passed successfully!")

    asyncio.run(_run_manual())
