from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


LIBRARY_FILENAME = "project_library.json"


@dataclass
class ProjectRecord:
    path: str
    pinned: bool = False
    last_opened: str | None = None


class ProjectLibrary:
    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        self.library_path = self.data_dir / LIBRARY_FILENAME

    def load_records(self) -> list[ProjectRecord]:
        records = self._load_config_records()
        discovered_paths = self._discover_json_projects()

        by_path: dict[str, ProjectRecord] = {record.path: record for record in records}
        for path in discovered_paths:
            normalized = os.path.abspath(path)
            if normalized not in by_path:
                by_path[normalized] = ProjectRecord(path=normalized)

        valid_records = [
            record for record in by_path.values() if os.path.exists(record.path)
        ]
        valid_records.sort(key=self._sort_key)
        self.save_records(valid_records)
        return valid_records

    def save_records(self, records: list[ProjectRecord]) -> None:
        os.makedirs(self.data_dir, exist_ok=True)
        payload = {"projects": [asdict(record) for record in records]}
        with open(self.library_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

    def register_path(self, path: str) -> list[ProjectRecord]:
        normalized = os.path.abspath(path)
        records = self.load_records()
        for record in records:
            if record.path == normalized:
                return records
        records.append(ProjectRecord(path=normalized))
        records.sort(key=self._sort_key)
        self.save_records(records)
        return records

    def toggle_pin(self, path: str) -> list[ProjectRecord]:
        normalized = os.path.abspath(path)
        records = self.load_records()
        for record in records:
            if record.path == normalized:
                record.pinned = not record.pinned
                break
        records.sort(key=self._sort_key)
        self.save_records(records)
        return records

    def mark_opened(self, path: str) -> list[ProjectRecord]:
        normalized = os.path.abspath(path)
        records = self.load_records()
        target = None
        for record in records:
            if record.path == normalized:
                target = record
                break
        if target is None:
            target = ProjectRecord(path=normalized)
            records.append(target)
        target.last_opened = datetime.now().isoformat(timespec="seconds")
        records.sort(key=self._sort_key)
        self.save_records(records)
        return records

    def _load_config_records(self) -> list[ProjectRecord]:
        if not os.path.exists(self.library_path):
            return []
        try:
            with open(self.library_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return []

        raw_projects = payload.get("projects", [])
        records: list[ProjectRecord] = []
        for item in raw_projects:
            if not isinstance(item, dict):
                continue
            path = item.get("path")
            if not isinstance(path, str) or not path.strip():
                continue
            records.append(
                ProjectRecord(
                    path=os.path.abspath(path),
                    pinned=bool(item.get("pinned", False)),
                    last_opened=item.get("last_opened") if isinstance(item.get("last_opened"), str) else None,
                )
            )
        return records

    def _discover_json_projects(self) -> list[str]:
        if not os.path.isdir(self.data_dir):
            return []
        discovered: list[str] = []
        for name in os.listdir(self.data_dir):
            if not name.lower().endswith(".json") or name == LIBRARY_FILENAME:
                continue
            discovered.append(os.path.abspath(os.path.join(self.data_dir, name)))
        return discovered

    def _sort_key(self, record: ProjectRecord):
        last_opened = record.last_opened or ""
        return (0 if record.pinned else 1, -self._timestamp_value(last_opened), record.path.lower())

    def _timestamp_value(self, value: str) -> float:
        if not value:
            return 0.0
        try:
            return datetime.fromisoformat(value).timestamp()
        except ValueError:
            return 0.0


def describe_project(path: str) -> dict[str, str]:
    normalized = os.path.abspath(path)
    base_name = os.path.splitext(os.path.basename(normalized))[0]
    title = base_name
    summary = "Proyecto listo para abrir"

    try:
        with open(normalized, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        roots = payload.get("root_ids", [])
        nodes = payload.get("nodes", {})
        if roots and isinstance(nodes, dict):
            root_titles = []
            for root_id in roots[:3]:
                node = nodes.get(root_id, {})
                if isinstance(node, dict):
                    node_title = node.get("title")
                    if isinstance(node_title, str) and node_title.strip():
                        root_titles.append(node_title.strip())
            if root_titles:
                title = root_titles[0]
                extra = len(root_titles) - 1
                summary = (
                    f"{len(roots)} historia(s)"
                    if extra < 0
                    else f"{len(roots)} historia(s) en este proyecto"
                )
    except (OSError, json.JSONDecodeError):
        summary = "Archivo JSON disponible"

    return {
        "title": title,
        "subtitle": normalized,
        "summary": summary,
    }
