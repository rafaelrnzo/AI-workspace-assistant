from app.modules.agent.domain.models import AgentExecutionResult, AgentTask
from app.modules.agent.providers.base import AgentProvider


# ponytail: stub provider — implement subprocess call to claude-code CLI when ready
class ClaudeProvider(AgentProvider):
    async def ask(self, prompt: str) -> str:
        return f"[stub] received prompt: {prompt}"

    async def execute(self, task: AgentTask) -> AgentExecutionResult:
        return AgentExecutionResult(success=True, output="stub", error=None, diff=None)
