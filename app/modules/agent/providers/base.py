from abc import ABC, abstractmethod

from app.modules.agent.domain.models import AgentExecutionResult, AgentTask


class AgentProvider(ABC):
    @abstractmethod
    async def ask(self, prompt: str) -> str: ...

    @abstractmethod
    async def execute(self, task: AgentTask) -> AgentExecutionResult: ...
