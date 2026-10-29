import glob
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.claims import router as claims_router
from src.api.routes.review import router as review_router
from src.core.config import settings
from src.rag.chunker import ClauseAwareChunker
from src.rag.vector_store import vector_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-index policy documents on startup
    policy_files = glob.glob("data/policies/*.md")
    for pf in policy_files:
        with open(pf, "r", encoding="utf-8") as f:
            text = f.read()
        chunks = ClauseAwareChunker.parse_markdown_policy(text)
        for c in chunks:
            await vector_store.index_clause(c)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Compliance-bound Agentic RAG Claims Adjudication API with LangGraph, pgvector, and Human-in-the-Loop review.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(claims_router, prefix="/api/v1")
app.include_router(review_router, prefix="/api/v1")

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "HEALTHY",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "default_llm_provider": settings.DEFAULT_LLM_PROVIDER
    }
