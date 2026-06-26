from pydantic import BaseModel


class AgentTask(BaseModel):
    prompt: str
    repository_path: str | None = None
    branch: str | None = None
    context: dict | None = None


class AgentExecutionResult(BaseModel):
    success: bool
    output: str
    error: str | None = None
    diff: str | None = None
