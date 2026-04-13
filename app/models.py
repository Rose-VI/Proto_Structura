from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Dict, List, Optional


SCHEMA_VERSION = 1


class NodeType(StrEnum):
    STORY = "story"
    CHAPTER = "chapter"
    SECTION = "section"


@dataclass
class Character:
    name: str
    description: str = ""
    highlight_enabled: bool = True
    highlight_color: str = "#ffd54f"


@dataclass
class ChapterNode:
    id: str
    title: str
    content: str = ""
    notes: str = ""
    children: List[str] = field(default_factory=list)
    parent_id: Optional[str] = None
    node_type: NodeType = NodeType.CHAPTER


@dataclass
class ProjectData:
    nodes: Dict[str, ChapterNode] = field(default_factory=dict)
    root_ids: List[str] = field(default_factory=list)
    characters: Dict[str, Character] = field(default_factory=dict)
    next_id: int = 1
    schema_version: int = SCHEMA_VERSION
