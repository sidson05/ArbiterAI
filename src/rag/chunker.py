import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ClauseChunk(BaseModel):
    policy_id: str
    clause_number: str
    section_name: str
    title: str
    content: str
    deductible: float = 0.0
    sub_limit: Optional[float] = None

class ClauseAwareChunker:
    """
    Hierarchical clause-aware parser designed specifically for insurance policy contracts.
    Preserves clause boundaries, section context, and legal condition integrity.
    """

    @staticmethod
    def parse_markdown_policy(markdown_text: str, default_policy_id: str = "") -> List[ClauseChunk]:
        chunks: List[ClauseChunk] = []

        # Extract Policy Identifier
        policy_id_match = re.search(r"\*\*Policy Identifier:\*\*\s*([A-Z0-9\-]+)", markdown_text)
        policy_id = policy_id_match.group(1).strip() if policy_id_match else default_policy_id

        # Split into sections
        sections = re.split(r"\n##\s+", markdown_text)
        
        for sec in sections:
            if not sec.strip():
                continue
            
            lines = sec.split("\n", 1)
            section_header = lines[0].strip()
            section_body = lines[1] if len(lines) > 1 else ""

            # Split section body into clauses: '### Clause X.Y: Title'
            clause_blocks = re.split(r"\n###\s+", section_body)

            for cb in clause_blocks:
                if not cb.strip():
                    continue

                cb_lines = cb.split("\n", 1)
                first_line = cb_lines[0].strip()
                content = cb_lines[1].strip() if len(cb_lines) > 1 else ""

                # Match 'Clause X.Y: Title' or 'Clause X.Y.Z: Title'
                match = re.match(r"(Clause\s+[\d\.]+):\s*(.*)", first_line, re.IGNORECASE)
                if match:
                    clause_number = match.group(1).strip()
                    title = match.group(2).strip()

                    # Extract common dollar amounts for deductibles / sub-limits
                    deductible = 0.0
                    sub_limit = None

                    deduct_match = re.search(r"deductible\s+of\s+\$([\d,]+\.?\d*)", content, re.IGNORECASE)
                    if deduct_match:
                        deductible = float(deduct_match.group(1).replace(",", ""))

                    sub_match = re.search(r"(?:sub-limit|capped|limited)\s+(?:of|at|to)\s+\$([\d,]+\.?\d*)", content, re.IGNORECASE)
                    if sub_match:
                        sub_limit = float(sub_match.group(1).replace(",", ""))

                    chunk = ClauseChunk(
                        policy_id=policy_id,
                        clause_number=clause_number,
                        section_name=section_header,
                        title=title,
                        content=content,
                        deductible=deductible,
                        sub_limit=sub_limit
                    )
                    chunks.append(chunk)

        return chunks

class NaiveChunker:
    """
    Standard fixed-length chunker with overlap used as an ablation baseline
    in evaluation to prove the superiority of clause-aware chunking.
    """
    @staticmethod
    def chunk(text: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict[str, Any]]:
        chunks = []
        start = 0
        text_len = len(text)
        chunk_idx = 0

        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk_text = text[start:end]
            chunks.append({
                "chunk_id": f"chunk_{chunk_idx}",
                "content": chunk_text,
                "start": start,
                "end": end
            })
            chunk_idx += 1
            if end == text_len:
                break
            start += (chunk_size - overlap)

        return chunks
