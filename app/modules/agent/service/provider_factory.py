from app.config import settings
from app.modules.agent.providers.command_provider import CommandAgentProvider


class AgentProviderFactory:
    @staticmethod
    def create(provider_name: str) -> CommandAgentProvider:
        return CommandAgentProvider(
            provider_name=provider_name,
            command=AgentProviderFactory._command_for(provider_name),
            execution_enabled=settings.agent_execution_enabled,
            timeout_seconds=settings.agent_timeout_seconds,
        )

    @staticmethod
    def _command_for(provider_name: str) -> str:
        if provider_name == "antigravity_pro_3_1":
            return settings.antigravity_command
        if provider_name == "gemini_flash":
            return settings.gemini_flash_command
        if provider_name == "codex_pro_3_1":
            return settings.codex_pro_command or settings.codex_command
        return settings.codex_command
