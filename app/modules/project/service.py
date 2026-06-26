from pathlib import Path

from app.config import settings
from app.modules.project.schemas import ProjectResponse


class ProjectService:
    def list_projects(self) -> list[ProjectResponse]:
        configured_projects = self._parse_projects(settings.projects)
        if configured_projects:
            return configured_projects
        return [
            ProjectResponse(
                name="Default project",
                path=str(Path(settings.repository_path).expanduser().resolve()),
            )
        ]

    @staticmethod
    def _parse_projects(raw_projects: str | None) -> list[ProjectResponse]:
        if not raw_projects:
            return []

        projects: list[ProjectResponse] = []
        for raw_project in raw_projects.split(","):
            project_config = raw_project.strip()
            if not project_config:
                continue

            if "=" in project_config:
                name, path = project_config.split("=", 1)
            else:
                path = project_config
                name = Path(path).expanduser().name or "Project"

            resolved_path = str(Path(path.strip()).expanduser().resolve())
            projects.append(ProjectResponse(name=name.strip() or resolved_path, path=resolved_path))
        return projects
