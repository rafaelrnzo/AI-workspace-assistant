from app.exceptions import AgentExecutionException
from app.modules.agent.domain.models import AgentExecutionResult, AgentTask
from app.modules.agent.providers.base import AgentProvider


class AgentService:
    def __init__(self, provider: AgentProvider) -> None:
        self._provider = provider

    async def ask(self, prompt: str) -> str:
        try:
            return await self._provider.ask(prompt)
        except Exception as e:
            raise AgentExecutionException(f"Agent ask failed: {e}") from e

    async def execute_task(self, task: AgentTask) -> AgentExecutionResult:
        try:
            return await self._provider.execute(task)
        except Exception as e:
            raise AgentExecutionException(f"Agent execution failed: {e}") from e
