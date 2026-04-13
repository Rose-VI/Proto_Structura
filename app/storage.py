from app.models import ProjectData
from app.repository import JsonProjectRepository


_default_repository = JsonProjectRepository()


def save_project(project: ProjectData, path: str) -> None:
    """Backward-compatible wrapper around the default repository."""
    _default_repository.save(project, path)


def load_project(path: str) -> ProjectData:
    """Backward-compatible wrapper around the default repository."""
    return _default_repository.load(path)
