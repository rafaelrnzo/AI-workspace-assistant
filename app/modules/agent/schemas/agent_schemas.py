from pydantic import BaseModel


class AgentAskRequest(BaseModel):
    prompt: str


class AgentAskResponse(BaseModel):
    response: str


class AgentExecuteRequest(BaseModel):
    prompt: str
    repository_path: str | None = None
    branch: str | None = None


class AgentExecuteResponse(BaseModel):
    success: bool
    output: str
    error: str | None = None
    diff: str | None = None
