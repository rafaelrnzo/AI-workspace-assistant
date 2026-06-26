from app.modules.ticket.domain.models import Ticket
from app.modules.ticket.schemas.ticket_schemas import TicketCreate
from app.modules.ticket.service.ticket_service import TicketService


class CreateTicketUseCase:
    def __init__(self, service: TicketService) -> None:
        self.service = service

    async def execute(self, data: TicketCreate) -> Ticket:
        return await self.service.create_ticket(data)
