from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TicketCreate(BaseModel):
    title: str
    description: str | None = None
    repository_url: str | None = None
    repository_path: str | None = None
    branch: str | None = None
    agent_provider: str | None = None
    ticket_type: Literal["request", "issue", "question"] = "request"
    complexity: Literal["low", "medium", "hard"] = "low"
    requester_name: str | None = None
    auto_process: bool = False


class TicketUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    repository_url: str | None = None
    repository_path: str | None = None
    branch: str | None = None
    agent_provider: str | None = None
    ticket_type: Literal["request", "issue", "question"] | None = None
    complexity: Literal["low", "medium", "hard"] | None = None
    requester_name: str | None = None
    review_status: str | None = None
    approved_by: str | None = None
    result: str | None = None
    execution_log: str | None = None
    diff: str | None = None


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str | None = None
    status: str
    repository_url: str | None = None
    repository_path: str | None = None
    branch: str | None = None
    agent_provider: str | None = None
    ticket_type: str
    complexity: str
    requester_name: str | None = None
    review_status: str
    approved_by: str | None = None
    result: str | None = None
    execution_log: str | None = None
    diff: str | None = None
    queued_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    updated_by: str | None = None


class TicketMessageCreate(BaseModel):
    content: str = Field(min_length=1)
    role: Literal["user", "admin"] = "user"


class TicketMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticket_id: str
    role: str
    content: str
    created_at: datetime


class TicketActionRequest(BaseModel):
    actor: str | None = None
