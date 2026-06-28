from fastapi import APIRouter, Depends

from app.modules.auth import User, get_current_user
from app.modules.project.schemas import ProjectResponse
from app.modules.project.service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_user),
) -> list[ProjectResponse]:
    return ProjectService().list_projects()
