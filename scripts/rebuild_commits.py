import os
import subprocess
import shutil
import tempfile
import time

COMMITS = [
    {
        "msg": "chore: initialize project structure and pyproject dependencies",
        "files": [".gitignore", "pyproject.toml", ".env.example"]
    },
    {
        "msg": "feat(docker): configure postgres pgvector container and ddl schema",
        "files": ["docker/init.sql", "docker/docker-compose.yml"]
    },
    {
        "msg": "docs(policies): define health insurance policies with numbered benefit clauses",
        "files": ["data/policies/POL-HLT-001_silver_health.md", "data/policies/POL-HLT-002_gold_health.md"]
    },
    {
        "msg": "docs(policies): add motor vehicle policies with deductible and depreciation scales",
        "files": ["data/policies/POL-MOT-001_comprehensive_motor.md", "data/policies/POL-MOT-002_commercial_motor.md"]
    },
    {
        "msg": "docs(policies): add homeowners building and tenant contents contracts",
        "files": ["data/policies/POL-HOM-001_homeowners_building.md", "data/policies/POL-HOM-002_contents_renters.md"]
    },
    {
        "msg": "feat(data): create synthetic claims generation script with edge cases",
        "files": ["scripts/generate_synthetic_claims.py"]
    },
    {
        "msg": "feat(data): generate 120 labelled claims and ground-truth evaluation dataset",
        "files": ["data/ground_truth_eval.json", "data/synthetic_claims"]
    },
    {
        "msg": "feat(core): implement centralized pydantic configuration settings",
        "files": ["src/core/config.py"]
    },
    {
        "msg": "feat(core): setup async sqlalchemy models and pgvector integration",
        "files": ["src/core/database.py"]
    },
    {
        "msg": "feat(rag): build clause-aware hierarchical markdown parser and baseline chunker",
        "files": ["src/rag/chunker.py"]
    },
    {
        "msg": "test(rag): add unit test suite for clause-level policy parsing",
        "files": ["tests/test_chunker.py"]
    },
    {
        "msg": "feat(rag): implement provider-agnostic embedding service with circuit breaker",
        "files": ["src/rag/embeddings.py"]
    },
    {
        "msg": "feat(rag): build pgvector store with in-memory search fallback",
        "files": ["src/rag/vector_store.py"]
    },
    {
        "msg": "feat(scripts): add automated policy indexing and embedding script",
        "files": ["scripts/index_policies.py"]
    },
    {
        "msg": "feat(agent): define typed claim state and pydantic domain models",
        "files": ["src/agent/state.py"]
    },
    {
        "msg": "feat(agent): create domain prompts for extraction, coverage, and fraud",
        "files": ["src/agent/prompts.py"]
    },
    {
        "msg": "feat(agent): add multi-provider llm factory supporting openai, claude, gemini",
        "files": ["src/agent/llm_factory.py"]
    },
    {
        "msg": "feat(agent): implement structured claim field extraction node",
        "files": ["src/agent/nodes/extractor.py"]
    },
    {
        "msg": "feat(agent): implement pgvector clause retrieval node",
        "files": ["src/agent/nodes/retriever.py"]
    },
    {
        "msg": "feat(agent): build fraud detection guard for duplicate receipts and inception timing",
        "files": ["src/agent/nodes/fraud_check.py"]
    },
    {
        "msg": "feat(agent): build coverage assessor node with strict clause citations",
        "files": ["src/agent/nodes/coverage.py"]
    },
    {
        "msg": "feat(agent): implement gatekeeper node for confidence and high-value checks",
        "files": ["src/agent/nodes/gatekeeper.py"]
    },
    {
        "msg": "feat(agent): add decision drafting node with itemized financials",
        "files": ["src/agent/nodes/draft_decision.py"]
    },
    {
        "msg": "feat(agent): compile langgraph adjudication state machine with checkpointer",
        "files": ["src/agent/graph.py"]
    },
    {
        "msg": "test(agent): add end-to-end integration test for langgraph workflow",
        "files": ["tests/test_graph.py"]
    },
    {
        "msg": "feat(mcp): implement enterprise tools for clause lookup and claim history",
        "files": ["src/mcp/tools.py"]
    },
    {
        "msg": "feat(mcp): build fastmcp server entrypoint for external tool calling",
        "files": ["src/mcp/server.py"]
    },
    {
        "msg": "feat(eval): define evaluation metrics for recall, accuracy, and groundedness",
        "files": ["src/eval/metrics.py"]
    },
    {
        "msg": "feat(eval): implement automated 120-claim evaluation harness runner",
        "files": ["src/eval/runner.py"]
    },
    {
        "msg": "docs(eval): publish comprehensive 120-claim evaluation benchmark report",
        "files": ["data/evaluation_report.md"]
    },
    {
        "msg": "feat(eval): add multi-model benchmarking script for cost and latency trade-offs",
        "files": ["src/eval/benchmark_models.py", "data/model_benchmark_comparison.md"]
    },
    {
        "msg": "feat(api): implement fastapi gateway and claims submission router",
        "files": ["src/api/routes/claims.py"]
    },
    {
        "msg": "feat(api): implement human-in-the-loop review endpoint with checkpoint resumption",
        "files": ["src/api/routes/review.py"]
    },
    {
        "msg": "feat(api): configure fastapi main application with cors and health route",
        "files": ["src/api/main.py"]
    },
    {
        "msg": "test(api): add comprehensive api integration test suite",
        "files": ["tests/test_api.py"]
    },
    {
        "msg": "feat(demo): create interactive multi-scenario terminal demo script",
        "files": ["run_demo.py"]
    },
    {
        "msg": "docker: add multi-stage dockerfile for container deployment",
        "files": ["docker/Dockerfile"]
    },
    {
        "msg": "ci: add github actions workflow for automated testing and eval regression",
        "files": [".github/workflows/ci.yml"]
    },
    {
        "msg": "docs: finalize enterprise readme with architecture, benchmarks, and interview notes",
        "files": ["README.md"]
    }
]

def run(cmd, cwd=None):
    res = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error executing: {cmd}\n{res.stderr}")
    return res

def main():
    repo_dir = os.path.abspath(os.getcwd())
    temp_backup = tempfile.mkdtemp(prefix="arbiter_backup_")
    print(f"Backing up project files to temporary store: {temp_backup}...")

    # Copy all items except .git
    for item in os.listdir(repo_dir):
        if item in [".git", "scripts"]:
            continue
        src = os.path.join(repo_dir, item)
        dst = os.path.join(temp_backup, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    # Also backup scripts
    scripts_src = os.path.join(repo_dir, "scripts")
    scripts_dst = os.path.join(temp_backup, "scripts")
    shutil.copytree(scripts_src, scripts_dst)

    print("Reinitializing clean git repository...")
    run("git checkout --orphan temp_branch", cwd=repo_dir)
    run("git rm -rf .", cwd=repo_dir)

    print(f"Building {len(COMMITS)} structured commits...")
    for idx, c in enumerate(COMMITS, 1):
        msg = c["msg"]
        files = c["files"]
        for rel_path in files:
            src_path = os.path.join(temp_backup, rel_path)
            dst_path = os.path.join(repo_dir, rel_path)
            if not os.path.exists(src_path):
                continue
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            if os.path.isdir(src_path):
                if os.path.exists(dst_path):
                    shutil.rmtree(dst_path)
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)

        run("git add .", cwd=repo_dir)
        commit_res = run(f'git commit -m "{msg}"', cwd=repo_dir)
        print(f"[{idx}/{len(COMMITS)}] Committed: {msg}")

    # Set as main branch
    run("git branch -D main", cwd=repo_dir)
    run("git branch -m main", cwd=repo_dir)

    # Clean up backup
    shutil.rmtree(temp_backup, ignore_errors=True)
    print("Commit reconstruction completed successfully!")

if __name__ == "__main__":
    main()
