from __future__ import annotations

from dataclasses import dataclass

from app.models import ChapterNode, Character, ProjectData
from app.repository import JsonProjectRepository, ProjectRepository
from app.services import chapter_service, character_service


@dataclass
class SaveResult:
    saved: bool
    path: str | None


class ProjectController:
    """Coordinate project state and domain operations for the UI."""

    def __init__(self, repository: ProjectRepository | None = None):
        self.repository = repository or JsonProjectRepository()
        self.project: ProjectData | None = None
        self.project_path: str | None = None
        self.project_modified = False
        self.current_node_id: str | None = None
        self.current_character_name: str | None = None

    def load_initial_project(self, path: str) -> ProjectData:
        self.project = self.repository.load(path)
        self.project_path = path
        self.project_modified = False
        self.current_node_id = None
        self.current_character_name = None
        return self.project

    def new_project(self, path: str) -> ProjectData:
        self.project = ProjectData()
        self.project_path = path
        self.project_modified = False
        self.current_node_id = None
        self.current_character_name = None
        self.repository.save(self.project, path)
        return self.project

    def open_project(self, path: str) -> ProjectData:
        self.project = self.repository.load(path)
        self.project_path = path
        self.project_modified = False
        self.current_node_id = None
        self.current_character_name = None
        return self.project

    def close_project(self) -> None:
        self.project = None
        self.project_path = None
        self.project_modified = False
        self.current_node_id = None
        self.current_character_name = None

    def save(self) -> SaveResult:
        if not self.project or not self.project_path:
            return SaveResult(saved=False, path=self.project_path)
        self.repository.save(self.project, self.project_path)
        self.project_modified = False
        return SaveResult(saved=True, path=self.project_path)

    def save_as(self, path: str) -> SaveResult:
        if not self.project:
            return SaveResult(saved=False, path=path)
        self.project_path = path
        self.repository.save(self.project, path)
        self.project_modified = False
        return SaveResult(saved=True, path=path)

    def mark_modified(self) -> None:
        self.project_modified = True

    def select_node(self, node_id: str | None) -> ChapterNode | None:
        self.current_node_id = node_id if self.project and node_id in self.project.nodes else None
        return self.get_current_node()

    def select_character(self, name: str | None) -> Character | None:
        self.current_character_name = (
            name if self.project and name in self.project.characters else None
        )
        return self.get_current_character()

    def get_current_node(self) -> ChapterNode | None:
        if not self.project or not self.current_node_id:
            return None
        return self.project.nodes.get(self.current_node_id)

    def get_current_character(self) -> Character | None:
        if not self.project or not self.current_character_name:
            return None
        return self.project.characters.get(self.current_character_name)

    def get_sorted_character_names(self) -> list[str]:
        if not self.project:
            return []
        return character_service.get_sorted_character_names(self.project)

    def get_root_story(self, node_id: str | None) -> ChapterNode | None:
        if not self.project:
            return None
        return chapter_service.get_root_story(self.project, node_id)

    def get_node_path(self, node_id: str | None) -> list[ChapterNode]:
        if not self.project:
            return []
        return chapter_service.get_node_path(self.project, node_id)

    def can_add_chapter(self, node_id: str | None = None) -> bool:
        if not self.project:
            return False
        target_id = node_id if node_id is not None else self.current_node_id
        return chapter_service.can_add_chapter(self.project, target_id)

    def can_add_section(self, node_id: str | None = None) -> bool:
        if not self.project:
            return False
        target_id = node_id if node_id is not None else self.current_node_id
        return chapter_service.can_add_section(self.project, target_id)
