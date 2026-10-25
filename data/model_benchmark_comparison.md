# Multi-Model Benchmark Comparison (120 Labelled Claims Dataset)

| Provider | Model | Decision Accuracy | Groundedness | Recall@3 | Avg Latency | Est. Cost / 1k Claims | Recommended Enterprise Role |
|---|---|:---:|:---:|:---:|:---:|:---:|---|
| **OpenAI** | `gpt-4o-mini` | **89.17%** | 100.0% | 90.0% | 0.95s | **$0.72** | Best cost/performance for high-volume Tier-1 auto-adjudication |
| **Anthropic** | `claude-3-5-sonnet` | **93.33%** | 100.0% | 92.5% | 2.45s | **$8.40** | Ideal for complex legal exclusions and appeal disputes |
| **Google** | `gemini-1.5-flash` | **88.33%** | 98.3% | 89.2% | 0.82s | **$0.38** | Lowest cost, ideal for high-throughput initial triage |
| **Google** | `gemini-1.5-pro` | **92.5%** | 100.0% | 91.8% | 2.2s | **$4.10** | Strong multimodal understanding for complex damage inspection photos |

### Enterprise Architecture Recommendation (Hybrid Routing)
- **Tier 1 (Triage & Routine Claims < $2,500)**: Route via `gemini-1.5-flash` or `gpt-4o-mini` ($0.38 - $0.72 / 1k claims) for 70%+ Straight-Through Processing.
- **Tier 2 (High-Value > $10,000 / Disputed Claims)**: Escalate to `claude-3-5-sonnet` for edge-case reasoning prior to human adjuster sign-off.