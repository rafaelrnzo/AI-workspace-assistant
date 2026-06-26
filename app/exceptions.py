class AppException(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, entity: str, entity_id: str):
        super().__init__(f"{entity} with id '{entity_id}' not found", status_code=404)


class TicketNotFoundException(NotFoundException):
    def __init__(self, ticket_id: str):
        super().__init__("Ticket", ticket_id)


class AgentExecutionException(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class GitOperationException(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=500)
