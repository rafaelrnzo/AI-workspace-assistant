from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ticket.domain.models import Ticket, TicketMessage


class TicketRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, ticket: Ticket) -> Ticket:
        self.session.add(ticket)
        await self.session.commit()
        await self.session.refresh(ticket)
        return ticket

    async def get_by_id(self, ticket_id: str) -> Ticket | None:
        stmt = select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Ticket]:
        stmt = (
            select(Ticket)
            .where(Ticket.deleted_at.is_(None))
            .order_by(Ticket.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, ticket: Ticket, data: dict) -> Ticket:
        for key, value in data.items():
            setattr(ticket, key, value)
        await self.session.commit()
        await self.session.refresh(ticket)
        return ticket

    async def soft_delete(self, ticket: Ticket) -> Ticket:
        ticket.deleted_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(ticket)
        return ticket

    async def create_message(self, message: TicketMessage) -> TicketMessage:
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def list_messages(self, ticket_id: str) -> list[TicketMessage]:
        stmt = (
            select(TicketMessage)
            .where(
                TicketMessage.ticket_id == ticket_id,
                TicketMessage.deleted_at.is_(None),
            )
            .order_by(TicketMessage.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
