from typing import Dict, Any, List, Optional
from src.rag.vector_store import vector_store

MOCK_PROVIDER_REGISTRY = {
    "St. Jude Hospital": {"accredited": True, "tier": "Tier-1 Preferred", "type": "HEALTH"},
    "City Eye Institute": {"accredited": True, "tier": "Tier-1 Preferred", "type": "HEALTH"},
    "Metropolitan University Hospital": {"accredited": True, "tier": "Tier-1 Preferred", "type": "HEALTH"},
    "Apex Authorized Collision Center": {"accredited": True, "tier": "Network Partner", "type": "MOTOR"},
    "Precision Auto Body": {"accredited": True, "tier": "Network Partner", "type": "MOTOR"},
    "Uncertified Offshore Wellness": {"accredited": False, "tier": "Blacklisted", "type": "HEALTH"},
}

MOCK_CLAIMANT_HISTORIES = {
    "CUST-101": [
        {"claim_id": "CLM-2025-1002", "amount": 800.00, "status": "APPROVED", "date": "2025-04-12"}
    ],
    "CUST-102": [],
    "CUST-103": [
        {"claim_id": "CLM-2024-5512", "amount": 1200.00, "status": "APPROVED", "date": "2024-11-05"}
    ]
}

def lookup_policy_clause_tool(policy_id: str, clause_number: str) -> Optional[Dict[str, Any]]:
    """Look up a specific policy clause by ID and clause number."""
    for item in vector_store._memory_index:
        if item["policy_id"] == policy_id and item["clause_number"].lower() == clause_number.lower():
            return {
                "policy_id": item["policy_id"],
                "clause_number": item["clause_number"],
                "section": item["section_name"],
                "title": item["title"],
                "content": item["content"],
                "deductible": item["deductible"],
                "sub_limit": item["sub_limit"]
            }
    return None

def get_claimant_history_tool(claimant_id: str) -> List[Dict[str, Any]]:
    """Retrieve historical claims filed by a claimant in the past 24 months."""
    return MOCK_CLAIMANT_HISTORIES.get(claimant_id, [])

def verify_provider_network_tool(provider_name: str, policy_type: str = "HEALTH") -> Dict[str, Any]:
    """Verify if a hospital, doctor, or garage is an authorized in-network partner."""
    info = MOCK_PROVIDER_REGISTRY.get(provider_name)
    if info:
        return {
            "provider_name": provider_name,
            "is_in_network": info["accredited"],
            "network_tier": info["tier"],
            "eligible_for_cashless": info["accredited"]
        }
    return {
        "provider_name": provider_name,
        "is_in_network": False,
        "network_tier": "Out-of-Network",
        "eligible_for_cashless": False
    }
