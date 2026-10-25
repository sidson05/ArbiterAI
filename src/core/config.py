
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Insurance Claims Agentic RAG"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/insurance_claims"
    SYNC_DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/insurance_claims"

    # LLM Settings
    DEFAULT_LLM_PROVIDER: str = "openai"  # openai, anthropic, or gemini
    DEFAULT_MODEL_NAME: str = "gpt-4o-mini"
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None

    # Thresholds
    HIGH_VALUE_THRESHOLD: float = 10000.00
    CONFIDENCE_THRESHOLD: float = 0.85

    # Langfuse
    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: str | None = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # AWS
    AWS_REGION: str = "us-east-1"
    AWS_S3_CLAIM_BUCKET: str = "insurance-claims-vault-dev"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
