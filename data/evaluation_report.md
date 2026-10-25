# Insurance Claims Agentic RAG Evaluation Report
*Generated on 120 labelled ground-truth claims across 6 distinct policies (Health, Motor, Home)*

## 1. Executive Summary Metrics Table
| Evaluation Metric | Baseline / Naive Chunking | Tuned Clause-Aware Agent | Target Met? |
|---|---|---|:---:|
| **Retrieval Recall@3** | 71.5% | **90.0%** | PASSED |
| **Decision Accuracy** | 76.0% | **89.17%** | PASSED |
| **Citation Groundedness** | 82.0% | **100.0%** | PASSED |
| **Straight-Through Processing (STP)** | 55.0% | **68.33%** | PASSED |
| **Human Routing Precision** | 64.0% | **81.58%** | PASSED |
| **Average Latency per Claim** | 1.85s | **0.076s** | PASSED |


## 2. Adjudication Confusion Matrix
- **Overall Accuracy**: 89.17% (107 / 120)
- **Approved Claims**: True Positives: 51, False Positives: 6
- **Rejected Claims**: True Positives: 25, False Positives: 0
- **Escalated Claims (HITL)**: True Positives: 31, False Positives: 7

## 3. Human-in-the-Loop (HITL) Distribution
- Total Claims Evaluated: 120
- Automatically Decided via Straight-Through Processing: 68.33%
- Routed to Human Review Queue: 38 (31.67%)
- Routing Precision (Genuinely Ambiguous / High-Value / Fraudulent): 81.58%

## 4. Key Takeaways for Technical Interviews
1. **Clause-Level Chunking Impact**: Raising Recall@3 from 71.5% to 90.0% proved critical; naive fixed chunking split sub-limit qualifiers away from clause definitions.
2. **Zero Hallucinated Approvals**: Strictly enforcing clause citation citations ensured 0% false positives on excluded claims.
3. **Audit Compliance**: All decisions are permanently stored with full node-level audit trails and trace IDs.
