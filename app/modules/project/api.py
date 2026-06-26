from fastapi import APIRouter

from app.modules.project.schemas import ProjectResponse
from app.modules.project.service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectResponse])
async def list_projects() -> list[ProjectResponse]:
    return ProjectService().list_projects()
