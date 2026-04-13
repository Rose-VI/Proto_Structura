import os
import re

from app.models import ChapterNode, NodeType, ProjectData
from app.services.chapter_service import get_root_story


def sanitize_filename(name: str) -> str:
    """Remove invalid characters for filenames."""
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    return cleaned if cleaned else "Sin_Nombre"


def export_story(project: ProjectData, story_id: str, base_export_dir: str) -> None:
    """Export a story and its nested content to plain text files."""
    story_node = get_root_story(project, story_id)
    if not story_node or story_node.node_type != NodeType.STORY:
        raise ValueError("Historia no encontrada en el proyecto.")

    story_name = sanitize_filename(story_node.title)
    story_path = os.path.join(base_export_dir, story_name)
    os.makedirs(story_path, exist_ok=True)

    chapter_index = 1
    for child_id in story_node.children:
        child_node = project.nodes.get(child_id)
        if not child_node:
            continue
        _export_chapter(project, child_node, story_path, chapter_index)
        chapter_index += 1


def _export_chapter(
    project: ProjectData,
    chapter_node: ChapterNode,
    story_path: str,
    index: int,
) -> None:
    chapter_name = sanitize_filename(chapter_node.title)
    filename = f"{index:02d} - {chapter_name}.txt"
    filepath = os.path.join(story_path, filename)

    with open(filepath, "w", encoding="utf-8") as handle:
        handle.write(f"# {chapter_node.title}\n\n")
        if chapter_node.content.strip():
            handle.write(f"{chapter_node.content.strip()}\n\n")

        for section_id in chapter_node.children:
            section_node = project.nodes.get(section_id)
            if not section_node:
                continue

            handle.write(f"## {section_node.title}\n\n")
            if section_node.content.strip():
                handle.write(f"{section_node.content.strip()}\n\n")
