import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class TicketType(str, enum.Enum):
    REQUEST = "request"
    ISSUE = "issue"
    QUESTION = "question"


class TicketComplexity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HARD = "hard"


class TicketStatus(str, enum.Enum):
    PENDING = "pending"
    REVIEW_REQUIRED = "review_required"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ReviewStatus(str, enum.Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ADMIN = "admin"


class Ticket(BaseModel):
    __tablename__ = "tickets"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default=TicketStatus.PENDING.value, nullable=False
    )
    repository_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    repository_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    agent_provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ticket_type: Mapped[str] = mapped_column(
        String(30), default=TicketType.REQUEST.value, nullable=False
    )
    complexity: Mapped[str] = mapped_column(
        String(20), default=TicketComplexity.LOW.value, nullable=False
    )
    requester_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    review_status: Mapped[str] = mapped_column(
        String(30), default=ReviewStatus.NOT_REQUIRED.value, nullable=False
    )
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    diff: Mapped[str | None] = mapped_column(Text, nullable=True)
    queued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TicketMessage(BaseModel):
    __tablename__ = "ticket_messages"

    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
