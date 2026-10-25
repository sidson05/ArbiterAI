import os
import glob
from src.rag.chunker import ClauseAwareChunker

def test_chunker_on_all_policies():
    policy_files = glob.glob("data/policies/*.md")
    assert len(policy_files) == 6, f"Expected 6 policy files, found {len(policy_files)}"
    
    total_clauses = 0
    for pf in policy_files:
        with open(pf, "r", encoding="utf-8") as f:
            text = f.read()
        chunks = ClauseAwareChunker.parse_markdown_policy(text)
        assert len(chunks) > 0, f"No chunks parsed from {pf}"
        print(f"Policy: {os.path.basename(pf)} -> {len(chunks)} clauses parsed.")
        total_clauses += len(chunks)
        for c in chunks:
            assert c.policy_id != "", f"Missing policy_id in {pf}"
            assert c.clause_number.startswith("Clause"), f"Invalid clause_number: {c.clause_number}"
            assert len(c.content) > 10, f"Clause content too short in {c.clause_number}"
            
    print(f"Total clauses parsed across all policies: {total_clauses}")

if __name__ == "__main__":
    test_chunker_on_all_policies()
