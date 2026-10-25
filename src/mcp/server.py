from typing import Any

from src.mcp.tools import (
    get_claimant_history_tool,
    lookup_policy_clause_tool,
    verify_provider_network_tool,
)

try:
    from fastmcp import FastMCP
    mcp_server = FastMCP("InsuranceClaimsMCPServer")

    @mcp_server.tool()
    def lookup_policy_clause(policy_id: str, clause_number: str) -> dict[str, Any] | None:
        """Look up the exact legal text, deductibles, and sub-limits for a policy clause."""
        return lookup_policy_clause_tool(policy_id, clause_number)

    @mcp_server.tool()
    def get_claimant_history(claimant_id: str) -> list[dict[str, Any]]:
        """Retrieve claims history and flags for a claimant."""
        return get_claimant_history_tool(claimant_id)

    @mcp_server.tool()
    def verify_provider_network(provider_name: str, policy_type: str = "HEALTH") -> dict[str, Any]:
        """Verify whether a hospital or repair workshop is an authorized in-network partner."""
        return verify_provider_network_tool(provider_name, policy_type)

except ImportError:
    mcp_server = None

if __name__ == "__main__":
    if mcp_server:
        mcp_server.run()
    else:
        print("fastmcp not installed. Running tools locally.")
