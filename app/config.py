from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Assistant Code"
    database_url: str = "sqlite+aiosqlite:///./app.db"
    debug: bool = False
    repository_path: str = "."
    projects: str | None = None
    agent_execution_enabled: bool = False
    agent_timeout_seconds: int = 900
    codex_command: str = "codex exec"
    codex_pro_command: str | None = None
    antigravity_command: str = "antigravity"
    gemini_flash_command: str = "gemini"

    model_config = {"env_prefix": "APP_", "env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
