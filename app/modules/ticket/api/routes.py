from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.modules.ticket.repository.ticket_repository import TicketRepository
from app.modules.ticket.schemas.ticket_schemas import (
    TicketActionRequest,
    TicketCreate,
    TicketMessageCreate,
    TicketMessageResponse,
    TicketResponse,
    TicketUpdate,
)
from app.modules.ticket.service.ticket_service import TicketService
from app.modules.ticket.service.ticket_queue import ticket_queue

router = APIRouter(prefix="/tickets", tags=["tickets"])


def _get_service(session: AsyncSession) -> TicketService:
    return TicketService(TicketRepository(session))


@router.post("/", response_model=TicketResponse, status_code=201)
async def create_ticket(
    data: TicketCreate,
    session: AsyncSession = Depends(get_session),
) -> TicketResponse:
    service = _get_service(session)
    ticket = await service.create_ticket(data)
    if data.auto_process:
        ticket, action = await service.route_ticket(ticket.id)
        if action == "queued":
            ticket_queue.enqueue(ticket.id)
        if action == "question":
            ticket_queue.answer_question(ticket.id)
    return TicketResponse.model_validate(ticket)


@router.get("/", response_model=list[TicketResponse])
async def list_tickets(
    session: AsyncSession = Depends(get_session),
) -> list[TicketResponse]:
    service = _get_service(session)
    tickets = await service.list_tickets()
    return [TicketResponse.model_validate(t) for t in tickets]


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    session: AsyncSession = Depends(get_session),
) -> TicketResponse:
    service = _get_service(session)
    ticket = await service.get_ticket(ticket_id)
    return TicketResponse.model_validate(ticket)


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str,
    data: TicketUpdate,
    session: AsyncSession = Depends(get_session),
) -> TicketResponse:
    service = _get_service(session)
    ticket = await service.update_ticket(ticket_id, data)
    return TicketResponse.model_validate(ticket)


@router.post(
    "/{ticket_id}/messages",
    response_model=TicketMessageResponse,
    status_code=201,
)
async def add_message(
    ticket_id: str,
    data: TicketMessageCreate,
    session: AsyncSession = Depends(get_session),
) -> TicketMessageResponse:
    service = _get_service(session)
    message = await service.add_message(ticket_id, data)
    ticket = await service.get_ticket(ticket_id)
    if data.role == "user" and ticket.ticket_type == "question" and ticket.status != "in_progress":
        ticket, action = await service.route_ticket(ticket.id)
        if action == "question":
            ticket_queue.answer_question(ticket.id)
    elif ticket.status == "pending":
        ticket, action = await service.route_ticket(ticket.id)
        if action == "queued":
            ticket_queue.enqueue(ticket.id)
        if action == "question":
            ticket_queue.answer_question(ticket.id)
    return TicketMessageResponse.model_validate(message)


@router.get("/{ticket_id}/messages", response_model=list[TicketMessageResponse])
async def list_messages(
    ticket_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[TicketMessageResponse]:
    service = _get_service(session)
    messages = await service.list_messages(ticket_id)
    return [TicketMessageResponse.model_validate(m) for m in messages]


@router.post("/{ticket_id}/approve", response_model=TicketResponse)
async def approve_ticket(
    ticket_id: str,
    data: TicketActionRequest | None = None,
    session: AsyncSession = Depends(get_session),
) -> TicketResponse:
    service = _get_service(session)
    ticket = await service.approve_ticket(ticket_id, actor=data.actor if data else None)
    ticket_queue.enqueue(ticket.id)
    return TicketResponse.model_validate(ticket)


@router.post("/{ticket_id}/reject", response_model=TicketResponse)
async def reject_ticket(
    ticket_id: str,
    data: TicketActionRequest | None = None,
    session: AsyncSession = Depends(get_session),
) -> TicketResponse:
    service = _get_service(session)
    ticket = await service.reject_ticket(ticket_id, actor=data.actor if data else None)
    return TicketResponse.model_validate(ticket)


@router.post("/{ticket_id}/retry", response_model=TicketResponse)
async def retry_ticket(
    ticket_id: str,
    session: AsyncSession = Depends(get_session),
) -> TicketResponse:
    service = _get_service(session)
    ticket, action = await service.route_ticket(ticket_id)
    if action == "queued":
        ticket_queue.enqueue(ticket.id)
    if action == "question":
        ticket_queue.answer_question(ticket.id)
    return TicketResponse.model_validate(ticket)


@router.delete("/{ticket_id}", response_model=TicketResponse)
async def delete_ticket(
    ticket_id: str,
    session: AsyncSession = Depends(get_session),
) -> TicketResponse:
    service = _get_service(session)
    ticket = await service.delete_ticket(ticket_id)
    return TicketResponse.model_validate(ticket)
