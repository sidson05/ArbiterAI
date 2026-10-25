from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Numeric, Date, DateTime, JSON, ForeignKey, func
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    from sqlalchemy import JSON as Vector

from src.core.config import settings
import uuid

Base = declarative_base()

class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    policy_type: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    effective_from: Mapped[Date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Date] = mapped_column(Date, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    clauses: Mapped[list["PolicyClause"]] = relationship("PolicyClause", back_populates="policy", cascade="all, delete-orphan")

class PolicyClause(Base):
    __tablename__ = "policy_clauses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    policy_id: Mapped[str] = mapped_column(String(64), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    clause_number: Mapped[str] = mapped_column(String(64), nullable=False)
    section_name: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    deductible: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    sub_limit: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    embedding = mapped_column(Vector(1536), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    policy: Mapped["Policy"] = relationship("Policy", back_populates="clauses")

class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    policy_id: Mapped[str] = mapped_column(String(64), ForeignKey("policies.id"), nullable=False)
    claimant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    incident_date: Mapped[Date] = mapped_column(Date, nullable=False)
    claimed_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    approved_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    document_s3_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    decision_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ClaimAuditLog(Base):
    __tablename__ = "claim_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[str] = mapped_column(String(64), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    step_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    input_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    output_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(nullable=True)
    token_cost: Mapped[Optional[float]] = mapped_column(Numeric(8, 6), nullable=True)
    performed_by: Mapped[str] = mapped_column(String(64), default="AGENT")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
