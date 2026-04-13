from __future__ import annotations

import json
import os
import tempfile
from abc import ABC, abstractmethod
from dataclasses import asdict
from typing import Any

from app.models import (
    SCHEMA_VERSION,
    ChapterNode,
    Character,
    NodeType,
    ProjectData,
)


class ProjectValidationError(ValueError):
    """Raised when persisted project data is invalid."""


class ProjectRepository(ABC):
    """Persistence contract for loading and saving projects."""

    @abstractmethod
    def load(self, path: str) -> ProjectData:
        raise NotImplementedError

    @abstractmethod
    def save(self, project: ProjectData, path: str) -> None:
        raise NotImplementedError


class JsonProjectRepository(ProjectRepository):
    """JSON-backed repository compatible with the original project format."""

    def load(self, path: str) -> ProjectData:
        if not os.path.exists(path):
            return ProjectData()

        with open(path, "r", encoding="utf-8") as handle:
            raw_data = json.load(handle)

        return self._deserialize(raw_data)

    def save(self, project: ProjectData, path: str) -> None:
        payload = self._serialize(project)
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        fd, temp_path = tempfile.mkstemp(
            prefix="story_project_",
            suffix=".tmp",
            dir=directory or None,
            text=True,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
            os.replace(temp_path, path)
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def _serialize(self, project: ProjectData) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "next_id": project.next_id,
            "root_ids": list(project.root_ids),
            "nodes": {
                node_id: {
                    **asdict(node),
                    "node_type": node.node_type.value,
                }
                for node_id, node in project.nodes.items()
            },
            "characters": {
                name: asdict(character)
                for name, character in project.characters.items()
            },
        }

    def _deserialize(self, raw_data: dict[str, Any]) -> ProjectData:
        if not isinstance(raw_data, dict):
            raise ProjectValidationError("El archivo del proyecto no tiene un formato válido.")

        schema_version = raw_data.get("schema_version", 0)
        if not isinstance(schema_version, int):
            raise ProjectValidationError("La versión del proyecto es inválida.")
        if schema_version > SCHEMA_VERSION:
            raise ProjectValidationError(
                "La versión del proyecto es más nueva que la soportada por esta app."
            )

        project = ProjectData(schema_version=SCHEMA_VERSION)
        project.next_id = self._require_int(raw_data.get("next_id", 1), "next_id")
        project.root_ids = self._require_string_list(raw_data.get("root_ids", []), "root_ids")

        raw_nodes = raw_data.get("nodes", {})
        if not isinstance(raw_nodes, dict):
            raise ProjectValidationError("La colección de nodos es inválida.")

        project.nodes = {}
        for node_id, node_payload in raw_nodes.items():
            if not isinstance(node_id, str):
                raise ProjectValidationError("Se encontró un id de nodo inválido.")
            if not isinstance(node_payload, dict):
                raise ProjectValidationError(f"El nodo '{node_id}' tiene un formato inválido.")

            node_type_value = node_payload.get("node_type", NodeType.CHAPTER.value)
            try:
                node_type = NodeType(node_type_value)
            except ValueError as error:
                raise ProjectValidationError(
                    f"El tipo de nodo '{node_type_value}' no es válido."
                ) from error

            project.nodes[node_id] = ChapterNode(
                id=self._require_string(node_payload.get("id", node_id), "node.id"),
                title=self._require_string(node_payload.get("title", ""), "node.title"),
                content=self._require_string(node_payload.get("content", ""), "node.content"),
                notes=self._require_string(node_payload.get("notes", ""), "node.notes"),
                children=self._require_string_list(node_payload.get("children", []), "node.children"),
                parent_id=self._optional_string(node_payload.get("parent_id")),
                node_type=node_type,
            )

        raw_characters = raw_data.get("characters", {})
        if not isinstance(raw_characters, dict):
            raise ProjectValidationError("La colección de personajes es inválida.")

        project.characters = {}
        for name, character_payload in raw_characters.items():
            if not isinstance(character_payload, dict):
                raise ProjectValidationError(f"El personaje '{name}' tiene un formato inválido.")
            project.characters[name] = Character(
                name=self._require_string(character_payload.get("name", name), "character.name"),
                description=self._require_string(
                    character_payload.get("description", ""), "character.description"
                ),
                highlight_enabled=self._require_bool(
                    character_payload.get("highlight_enabled", True), "character.highlight_enabled"
                ),
                highlight_color=self._require_string(
                    character_payload.get("highlight_color", "#ffd54f"),
                    "character.highlight_color",
                ),
            )

        self._validate_relationships(project)
        return project

    def _validate_relationships(self, project: ProjectData) -> None:
        for root_id in project.root_ids:
            node = project.nodes.get(root_id)
            if node is None:
                raise ProjectValidationError(
                    f"El nodo raíz '{root_id}' no existe dentro del proyecto."
                )
            if node.parent_id is not None:
                raise ProjectValidationError(
                    f"El nodo raíz '{root_id}' no debería tener padre."
                )

        for node_id, node in project.nodes.items():
            if node.parent_id and node.parent_id not in project.nodes:
                raise ProjectValidationError(
                    f"El padre del nodo '{node_id}' no existe en el proyecto."
                )
            for child_id in node.children:
                child = project.nodes.get(child_id)
                if child is None:
                    raise ProjectValidationError(
                        f"El hijo '{child_id}' del nodo '{node_id}' no existe."
                    )
                if child.parent_id != node_id:
                    raise ProjectValidationError(
                        f"El nodo '{child_id}' no referencia correctamente a su padre '{node_id}'."
                    )

    def _require_string(self, value: Any, field_name: str) -> str:
        if not isinstance(value, str):
            raise ProjectValidationError(f"El campo '{field_name}' debe ser texto.")
        return value

    def _optional_string(self, value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ProjectValidationError("Un identificador opcional tiene un formato inválido.")
        return value

    def _require_int(self, value: Any, field_name: str) -> int:
        if not isinstance(value, int):
            raise ProjectValidationError(f"El campo '{field_name}' debe ser un número entero.")
        return value

    def _require_bool(self, value: Any, field_name: str) -> bool:
        if not isinstance(value, bool):
            raise ProjectValidationError(f"El campo '{field_name}' debe ser booleano.")
        return value

    def _require_string_list(self, value: Any, field_name: str) -> list[str]:
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ProjectValidationError(f"El campo '{field_name}' debe ser una lista de texto.")
        return list(value)
