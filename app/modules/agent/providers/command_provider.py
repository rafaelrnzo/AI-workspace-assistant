import asyncio
import shlex

from app.modules.agent.domain.models import AgentExecutionResult, AgentTask
from app.modules.agent.providers.base import AgentProvider


class CommandAgentProvider(AgentProvider):
    def __init__(
        self,
        provider_name: str,
        command: str,
        execution_enabled: bool,
        timeout_seconds: int,
    ) -> None:
        self.provider_name = provider_name
        self.command = command
        self.execution_enabled = execution_enabled
        self.timeout_seconds = timeout_seconds

    async def ask(self, prompt: str) -> str:
        if not self.execution_enabled:
            return (
                f"[dry-run:{self.provider_name}] Execution is disabled. "
                f"Prompt received: {prompt}"
            )
        result = await self._run(prompt=prompt, cwd=None)
        return result.output

    async def execute(self, task: AgentTask) -> AgentExecutionResult:
        if not self.execution_enabled:
            return AgentExecutionResult(
                success=True,
                output=(
                    f"[dry-run:{self.provider_name}] Execution is disabled. "
                    f"Task received: {task.prompt}"
                ),
                error=None,
                diff=None,
            )
        return await self._run(prompt=task.prompt, cwd=task.repository_path)

    async def _run(self, prompt: str, cwd: str | None) -> AgentExecutionResult:
        args = [*shlex.split(self.command), prompt]
        process = await asyncio.create_subprocess_exec(
            *args,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.communicate()
            return AgentExecutionResult(
                success=False,
                output="",
                error=f"{self.provider_name} timed out after {self.timeout_seconds}s",
            )

        output = stdout.decode().strip()
        error = stderr.decode().strip() or None
        return AgentExecutionResult(
            success=process.returncode == 0,
            output=output,
            error=error,
        )
