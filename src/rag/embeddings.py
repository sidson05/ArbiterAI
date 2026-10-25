import hashlib

import numpy as np

from src.core.config import settings


class EmbeddingService:
    def __init__(self):
        self.provider = settings.DEFAULT_LLM_PROVIDER
        self.embedding_dim = 1536
        self._openai_disabled = False
        self._gemini_disabled = False

    async def get_embedding(self, text: str) -> list[float]:
        # If API keys are present and configured, use live provider
        if not self._openai_disabled and settings.OPENAI_API_KEY and "your_openai" not in settings.OPENAI_API_KEY:
            try:
                from langchain_openai import OpenAIEmbeddings
                embedder = OpenAIEmbeddings(
                    model=settings.DEFAULT_EMBEDDING_MODEL,
                    openai_api_key=settings.OPENAI_API_KEY
                )
                return await embedder.aembed_query(text)
            except Exception as e:
                self._openai_disabled = True
                print(f"[Warning] OpenAI embedding failed ({e}), disabling for this session and using deterministic embedding.")

        if not self._gemini_disabled and settings.GEMINI_API_KEY and "your_gemini" not in settings.GEMINI_API_KEY:
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                embedder = GoogleGenerativeAIEmbeddings(
                    model="models/text-embedding-004",
                    google_api_key=settings.GEMINI_API_KEY
                )
                return await embedder.aembed_query(text)
            except Exception as e:
                self._gemini_disabled = True
                print(f"[Warning] Gemini embedding failed ({e}), disabling for this session and using deterministic embedding.")

        # Deterministic semantic hash embedding for offline CI/CD and tests
        return self._deterministic_hash_embedding(text)

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        results = []
        for t in texts:
            emb = await self.get_embedding(t)
            results.append(emb)
        return results

    def _deterministic_hash_embedding(self, text: str) -> list[float]:
        """
        Creates a normalized, pseudo-semantic vector representation based on
        token frequencies and hash buckets. Enables full local testing and deterministic eval.
        """
        vec = np.zeros(self.embedding_dim, dtype=np.float32)
        tokens = text.lower().split()
        for token in tokens:
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self.embedding_dim
            sign = 1.0 if (h >> 1) % 2 == 0 else -1.0
            vec[idx] += sign

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

embedding_service = EmbeddingService()
