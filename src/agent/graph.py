from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.agent.state import ClaimState
from src.agent.nodes.extractor import extract_claim_node
from src.agent.nodes.retriever import retrieve_clauses_node
from src.agent.nodes.fraud_check import check_fraud_node
from src.agent.nodes.coverage import assess_coverage_node
from src.agent.nodes.gatekeeper import evaluate_gatekeeper_node, route_after_gate
from src.agent.nodes.draft_decision import draft_decision_node

def human_review_interrupt_node(state: ClaimState) -> Dict[str, Any]:
    """
    Breakpoint node for human adjuster inspection.
    The graph pauses here before finalization if triggered by the gatekeeper.
    """
    audit_entry = {
        "step": "human_review_interrupt_node",
        "status": "AWAITING_ADJUSTER_ACTION",
        "reasons": state.get("review_reasons", [])
    }
    return {
        "audit_trail": state.get("audit_trail", []) + [audit_entry]
    }

def build_claims_graph(checkpointer: Optional[Any] = None) -> Any:
    workflow = StateGraph(ClaimState)

    # Add Nodes
    workflow.add_node("extract_claim", extract_claim_node)
    workflow.add_node("retrieve_clauses", retrieve_clauses_node)
    workflow.add_node("check_fraud", check_fraud_node)
    workflow.add_node("assess_coverage", assess_coverage_node)
    workflow.add_node("evaluate_gatekeeper", evaluate_gatekeeper_node)
    workflow.add_node("human_review_interrupt", human_review_interrupt_node)
    workflow.add_node("draft_decision", draft_decision_node)

    # Build Pipeline
    workflow.add_edge(START, "extract_claim")
    workflow.add_edge("extract_claim", "retrieve_clauses")
    workflow.add_edge("retrieve_clauses", "check_fraud")
    workflow.add_edge("check_fraud", "assess_coverage")
    workflow.add_edge("assess_coverage", "evaluate_gatekeeper")

    # Conditional Branching at Gatekeeper
    workflow.add_conditional_edges(
        "evaluate_gatekeeper",
        route_after_gate,
        {
            "human_review_interrupt": "human_review_interrupt",
            "draft_decision": "draft_decision"
        }
    )

    workflow.add_edge("human_review_interrupt", "draft_decision")
    workflow.add_edge("draft_decision", END)

    cp = checkpointer if checkpointer is not None else MemorySaver()
    
    # Interrupt before human_review_interrupt to allow human review via API
    return workflow.compile(
        checkpointer=cp,
        interrupt_before=["human_review_interrupt"]
    )

claims_agent = build_claims_graph()
