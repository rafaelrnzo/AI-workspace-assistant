import asyncio
import re
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.database import async_session
from app.modules.agent.domain.models import AgentTask
from app.modules.agent.service.agent_service import AgentService
from app.modules.agent.service.provider_factory import AgentProviderFactory
from app.modules.git.service.git_service import GitService
from app.modules.ticket.domain.models import TicketStatus, TicketType
from app.modules.ticket.repository.ticket_repository import TicketRepository
from app.modules.ticket.service.ticket_service import TicketService


class TicketQueue:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None
        self._question_tasks: set[asyncio.Task] = set()
        self._git_service = GitService()

    def start(self) -> None:
        if self._worker_task and not self._worker_task.done():
            return
        self._worker_task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        for task in self._question_tasks:
            task.cancel()
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    def enqueue(self, ticket_id: str) -> None:
        self._queue.put_nowait(ticket_id)

    def answer_question(self, ticket_id: str) -> None:
        task = asyncio.create_task(self._answer_question(ticket_id))
        self._question_tasks.add(task)
        task.add_done_callback(self._question_tasks.discard)

    async def _worker(self) -> None:
        while True:
            ticket_id = await self._queue.get()
            try:
                await self._execute_ticket(ticket_id)
            finally:
                self._queue.task_done()

    async def _answer_question(self, ticket_id: str) -> None:
        async with async_session() as session:
            repository = TicketRepository(session)
            service = TicketService(repository)
            ticket = await service.get_ticket(ticket_id)
            repository_path = self._repository_path(ticket.repository_path)
            prompt = await self._build_prompt(service, ticket_id)
            provider = AgentProviderFactory.create(ticket.agent_provider or "gemini_flash")
            agent_service = AgentService(provider)
            try:
                result = await agent_service.execute_task(
                    AgentTask(
                        prompt=prompt,
                        repository_path=repository_path,
                        context={"ticket_id": ticket.id, "ticket_type": ticket.ticket_type},
                    )
                )
                answer = result.output or result.error or "Agent finished without output."
                await service.add_assistant_message(ticket_id, answer)
                await repository.update(
                    ticket,
                    {
                        "status": (
                            TicketStatus.COMPLETED.value
                            if result.success
                            else TicketStatus.FAILED.value
                        ),
                        "result": answer,
                        "execution_log": self._format_execution_log(result.output, result.error),
                        "completed_at": datetime.now(timezone.utc),
                    },
                )
            except Exception as exc:
                await service.add_assistant_message(ticket_id, f"Failed: {exc}")
                await repository.update(
                    ticket,
                    {
                        "status": TicketStatus.FAILED.value,
                        "result": str(exc),
                        "completed_at": datetime.now(timezone.utc),
                    },
                )

    async def _execute_ticket(self, ticket_id: str) -> None:
        async with async_session() as session:
            repository = TicketRepository(session)
            service = TicketService(repository)
            ticket = await service.get_ticket(ticket_id)
            repository_path = self._repository_path(ticket.repository_path)
            prompt = await self._build_prompt(service, ticket_id)
            branch_name = ticket.branch or self._branch_name(ticket.title, ticket.id)

            await repository.update(
                ticket,
                {
                    "status": TicketStatus.IN_PROGRESS.value,
                    "branch": branch_name,
                    "started_at": datetime.now(timezone.utc),
                },
            )
            await service.add_system_message(ticket_id, "Execution started.")

            try:
                if settings.agent_execution_enabled:
                    await self._checkout_ticket_branch(repository_path, branch_name)

                provider = AgentProviderFactory.create(ticket.agent_provider or "codex_low")
                agent_service = AgentService(provider)
                result = await agent_service.execute_task(
                    AgentTask(
                        prompt=prompt,
                        repository_path=repository_path,
                        branch=branch_name,
                        context={"ticket_id": ticket.id, "ticket_type": ticket.ticket_type},
                    )
                )
                diff = await self._safe_diff(repository_path)
                status = TicketStatus.COMPLETED.value if result.success else TicketStatus.FAILED.value
                message = result.output or result.error or "Agent finished without output."
                await repository.update(
                    ticket,
                    {
                        "status": status,
                        "result": message,
                        "execution_log": self._format_execution_log(result.output, result.error),
                        "diff": diff,
                        "completed_at": datetime.now(timezone.utc),
                    },
                )
                await service.add_assistant_message(ticket_id, message)
            except Exception as exc:
                await repository.update(
                    ticket,
                    {
                        "status": TicketStatus.FAILED.value,
                        "result": str(exc),
                        "execution_log": str(exc),
                        "completed_at": datetime.now(timezone.utc),
                    },
                )
                await service.add_assistant_message(ticket_id, f"Execution failed: {exc}")

    async def _build_prompt(self, service: TicketService, ticket_id: str) -> str:
        ticket = await service.get_ticket(ticket_id)
        messages = await service.list_messages(ticket_id)
        conversation = "\n".join(f"{m.role}: {m.content}" for m in messages)
        if ticket.ticket_type == TicketType.QUESTION.value:
            instruction = (
                "Answer the user's question about this codebase. Do not change any code. "
                "Read the relevant source files, find the answer, and respond with a complete "
                "answer in one response. Do not say you are searching or will report back later — "
                "finish the entire task now and give the final answer."
            )
        else:
            instruction = (
                "Work inside the configured repository only. Make the requested code change, "
                "keep the scope focused, and summarize the result. "
                "Complete the entire task in one pass — do not defer or report intermediate progress."
            )
        return (
            f"{instruction}\n\n"
            f"Ticket: {ticket.title}\n"
            f"Type: {ticket.ticket_type}\n"
            f"Complexity: {ticket.complexity}\n"
            f"Conversation:\n{conversation}"
        )

    def _repository_path(self, ticket_repository_path: str | None) -> str:
        return str(Path(ticket_repository_path or settings.repository_path).expanduser().resolve())

    async def _checkout_ticket_branch(self, repository_path: str, branch_name: str) -> None:
        try:
            await self._git_service.create_branch(repository_path, branch_name)
        except Exception:
            await self._git_service.checkout(repository_path, branch_name)

    async def _safe_diff(self, repository_path: str) -> str:
        try:
            return await self._git_service.get_diff(repository_path)
        except Exception as exc:
            return f"Unable to read git diff: {exc}"

    @staticmethod
    def _branch_name(title: str, ticket_id: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:36] or "ticket"
        return f"ai-ticket/{ticket_id[:8]}-{slug}"

    @staticmethod
    def _format_execution_log(output: str, error: str | None) -> str:
        parts = []
        if output:
            parts.append(output)
        if error:
            parts.append(f"stderr:\n{error}")
        return "\n\n".join(parts)


ticket_queue = TicketQueue()
