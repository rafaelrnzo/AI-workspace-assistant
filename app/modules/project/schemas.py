from pydantic import BaseModel


class ProjectResponse(BaseModel):
    name: str
    path: str
