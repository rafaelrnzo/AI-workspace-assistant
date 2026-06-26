from datetime import datetime, timezone

from app.exceptions import TicketNotFoundException
from app.modules.ticket.domain.models import (
    MessageRole,
    ReviewStatus,
    Ticket,
    TicketComplexity,
    TicketMessage,
    TicketStatus,
    TicketType,
)
from app.modules.ticket.repository.ticket_repository import TicketRepository
from app.modules.ticket.schemas.ticket_schemas import (
    TicketCreate,
    TicketMessageCreate,
    TicketUpdate,
)


class TicketService:
    def __init__(self, repository: TicketRepository) -> None:
        self.repository = repository

    async def create_ticket(self, data: TicketCreate) -> Ticket:
        ticket_data = data.model_dump(exclude={"auto_process"})
        ticket_data["agent_provider"] = ticket_data["agent_provider"] or self.recommend_provider(
            ticket_data["ticket_type"], ticket_data["complexity"]
        )
        ticket = await self.repository.create(Ticket(**ticket_data))
        if ticket.description:
            await self.add_message(
                ticket.id,
                TicketMessageCreate(content=ticket.description, role=MessageRole.USER.value),
            )
        return ticket

    async def get_ticket(self, ticket_id: str) -> Ticket:
        ticket = await self.repository.get_by_id(ticket_id)
        if not ticket:
            raise TicketNotFoundException(ticket_id)
        return ticket

    async def list_tickets(self) -> list[Ticket]:
        return await self.repository.list_all()

    async def update_ticket(self, ticket_id: str, data: TicketUpdate) -> Ticket:
        ticket = await self.get_ticket(ticket_id)
        update_data = data.model_dump(exclude_unset=True)
        return await self.repository.update(ticket, update_data)

    async def delete_ticket(self, ticket_id: str) -> Ticket:
        ticket = await self.get_ticket(ticket_id)
        return await self.repository.soft_delete(ticket)

    async def add_message(
        self,
        ticket_id: str,
        data: TicketMessageCreate,
    ) -> TicketMessage:
        await self.get_ticket(ticket_id)
        return await self.repository.create_message(
            TicketMessage(ticket_id=ticket_id, role=data.role, content=data.content)
        )

    async def add_system_message(self, ticket_id: str, content: str) -> TicketMessage:
        return await self.repository.create_message(
            TicketMessage(ticket_id=ticket_id, role=MessageRole.SYSTEM.value, content=content)
        )

    async def add_assistant_message(self, ticket_id: str, content: str) -> TicketMessage:
        return await self.repository.create_message(
            TicketMessage(ticket_id=ticket_id, role=MessageRole.ASSISTANT.value, content=content)
        )

    async def list_messages(self, ticket_id: str) -> list[TicketMessage]:
        await self.get_ticket(ticket_id)
        return await self.repository.list_messages(ticket_id)

    async def route_ticket(self, ticket_id: str) -> tuple[Ticket, str]:
        ticket = await self.get_ticket(ticket_id)
        now = datetime.now(timezone.utc)

        if ticket.ticket_type == TicketType.QUESTION.value:
            ticket = await self.repository.update(
                ticket,
                {
                    "status": TicketStatus.IN_PROGRESS.value,
                    "review_status": ReviewStatus.NOT_REQUIRED.value,
                    "started_at": now,
                },
            )
            await self.add_system_message(ticket.id, "Question sent to the assistant.")
            return ticket, "question"

        if ticket.complexity == TicketComplexity.HARD.value:
            ticket = await self.repository.update(
                ticket,
                {
                    "status": TicketStatus.REVIEW_REQUIRED.value,
                    "review_status": ReviewStatus.PENDING.value,
                },
            )
            await self.add_system_message(ticket.id, "Hard ticket is waiting for backend review.")
            return ticket, "review"

        ticket = await self.repository.update(
            ticket,
            {
                "status": TicketStatus.QUEUED.value,
                "review_status": ReviewStatus.APPROVED.value,
                "queued_at": now,
            },
        )
        await self.add_system_message(ticket.id, "Ticket added to the execution queue.")
        return ticket, "queued"

    async def approve_ticket(self, ticket_id: str, actor: str | None = None) -> Ticket:
        ticket = await self.get_ticket(ticket_id)
        now = datetime.now(timezone.utc)
        ticket = await self.repository.update(
            ticket,
            {
                "status": TicketStatus.QUEUED.value,
                "review_status": ReviewStatus.APPROVED.value,
                "approved_by": actor,
                "queued_at": now,
            },
        )
        await self.add_system_message(ticket.id, f"Approved by {actor or 'admin'} and queued.")
        return ticket

    async def reject_ticket(self, ticket_id: str, actor: str | None = None) -> Ticket:
        ticket = await self.get_ticket(ticket_id)
        ticket = await self.repository.update(
            ticket,
            {
                "status": TicketStatus.FAILED.value,
                "review_status": ReviewStatus.REJECTED.value,
                "result": f"Rejected by {actor or 'admin'}",
            },
        )
        await self.add_system_message(ticket.id, f"Rejected by {actor or 'admin'}.")
        return ticket

    @staticmethod
    def recommend_provider(ticket_type: str, complexity: str) -> str:
        if ticket_type == TicketType.QUESTION.value:
            return "gemini_flash"
        if complexity == TicketComplexity.HARD.value:
            return "codex_pro_3_1"
        return "codex_low"
