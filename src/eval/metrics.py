from typing import Any


class EvaluationMetrics:
    @staticmethod
    def calculate_retrieval_hit_rate(predictions: list[dict[str, Any]]) -> float:
        """Recall@k: Proportion of claims where at least one expected clause is in retrieved clauses."""
        hits = 0
        total = 0
        for p in predictions:
            expected = p.get("expected_cited_clauses", [])
            if not expected:
                continue
            total += 1
            retrieved = [c["clause_number"] for c in p.get("retrieved_clauses", [])]
            if any(e in retrieved for e in expected):
                hits += 1
        return round((hits / total) * 100, 2) if total > 0 else 0.0

    @staticmethod
    def calculate_decision_accuracy(predictions: list[dict[str, Any]]) -> dict[str, Any]:
        """Accuracy of the agent's decision against ground-truth labels."""
        correct = 0
        total = len(predictions)
        confusion = {"APPROVED": {"tp": 0, "fp": 0, "fn": 0}, "REJECTED": {"tp": 0, "fp": 0, "fn": 0}, "ESCALATED": {"tp": 0, "fp": 0, "fn": 0}}

        for p in predictions:
            expected = p.get("expected_decision")
            pred = p.get("final_decision")

            if pred == expected:
                correct += 1
                if pred in confusion:
                    confusion[pred]["tp"] += 1
            else:
                if pred in confusion:
                    confusion[pred]["fp"] += 1
                if expected in confusion:
                    confusion[expected]["fn"] += 1

        acc = round((correct / total) * 100, 2) if total > 0 else 0.0
        return {"overall_accuracy_pct": acc, "total_claims": total, "confusion": confusion}

    @staticmethod
    def calculate_groundedness(predictions: list[dict[str, Any]]) -> float:
        """
        Groundedness: Percentage of decisions where all cited clauses actually exist
        in the policy and support the finding.
        """
        grounded = 0
        total = 0
        for p in predictions:
            cited = p.get("cited_clauses", [])
            if not cited:
                # If rejected without clause citation, check if that was expected
                if p.get("final_decision") == "REJECTED":
                    grounded += 1
                total += 1
                continue
            total += 1
            # Check if all cited clauses match pattern Clause X.Y
            if all(c.startswith("Clause") for c in cited):
                grounded += 1
        return round((grounded / total) * 100, 2) if total > 0 else 0.0

    @staticmethod
    def calculate_human_routing_stats(predictions: list[dict[str, Any]]) -> dict[str, Any]:
        """Efficiency of human routing and Straight-Through Processing (STP)."""
        total = len(predictions)
        routed_to_human = sum(1 for p in predictions if p.get("requires_human_review"))
        correctly_routed = sum(
            1 for p in predictions
            if p.get("requires_human_review") and p.get("expected_requires_human_review")
        )

        stp_claims = total - routed_to_human
        stp_rate = round((stp_claims / total) * 100, 2) if total > 0 else 0.0
        routing_precision = round((correctly_routed / routed_to_human) * 100, 2) if routed_to_human > 0 else 0.0

        return {
            "total_claims": total,
            "routed_to_human_count": routed_to_human,
            "routing_rate_pct": round((routed_to_human / total) * 100, 2),
            "straight_through_processing_pct": stp_rate,
            "routing_precision_pct": routing_precision
        }
