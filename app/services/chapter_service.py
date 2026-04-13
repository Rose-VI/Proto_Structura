from __future__ import annotations

from app.models import ChapterNode, NodeType, ProjectData


class ChapterStructureError(ValueError):
    """Raised when a node operation would break the story hierarchy."""


def new_node_id(project: ProjectData) -> str:
    node_id = f"node_{project.next_id}"
    project.next_id += 1
    return node_id


def create_story(project: ProjectData, title: str) -> ChapterNode:
    node = ChapterNode(
        id=new_node_id(project),
        title=title.strip(),
        node_type=NodeType.STORY,
    )
    project.nodes[node.id] = node
    project.root_ids.append(node.id)
    return node


def create_chapter(project: ProjectData, parent_id: str, title: str) -> ChapterNode:
    if not can_add_chapter(project, parent_id):
        raise ChapterStructureError("Solo puedes agregar capítulos directamente a una historia.")

    node = ChapterNode(
        id=new_node_id(project),
        title=title.strip(),
        parent_id=parent_id,
        node_type=NodeType.CHAPTER,
    )
    project.nodes[node.id] = node
    project.nodes[parent_id].children.append(node.id)
    return node


def create_section(project: ProjectData, parent_id: str, title: str) -> ChapterNode:
    if not can_add_section(project, parent_id):
        raise ChapterStructureError("Solo puedes agregar escenas dentro de un capítulo.")

    node = ChapterNode(
        id=new_node_id(project),
        title=title.strip(),
        parent_id=parent_id,
        node_type=NodeType.SECTION,
    )
    project.nodes[node.id] = node
    project.nodes[parent_id].children.append(node.id)
    return node


def rename_node(project: ProjectData, node_id: str, new_title: str) -> None:
    project.nodes[node_id].title = new_title.strip()


def update_node_content(project: ProjectData, node_id: str, content: str) -> None:
    project.nodes[node_id].content = content.rstrip()


def update_node_notes(project: ProjectData, node_id: str, notes: str) -> None:
    project.nodes[node_id].notes = notes.rstrip()


def delete_node_recursive(project: ProjectData, node_id: str) -> list[str]:
    node = project.nodes[node_id]
    deleted_ids: list[str] = []

    for child_id in list(node.children):
        deleted_ids.extend(delete_node_recursive(project, child_id))

    if node.parent_id:
        parent = project.nodes[node.parent_id]
        if node_id in parent.children:
            parent.children.remove(node_id)
    elif node_id in project.root_ids:
        project.root_ids.remove(node_id)

    del project.nodes[node_id]
    deleted_ids.append(node_id)
    return deleted_ids


def get_root_story(project: ProjectData, node_id: str | None) -> ChapterNode | None:
    if not node_id or node_id not in project.nodes:
        return None

    node = project.nodes[node_id]
    while node.parent_id:
        node = project.nodes[node.parent_id]
    return node


def get_node_path(project: ProjectData, node_id: str | None) -> list[ChapterNode]:
    if not node_id or node_id not in project.nodes:
        return []

    path: list[ChapterNode] = []
    current = project.nodes[node_id]
    while True:
        path.append(current)
        if not current.parent_id:
            break
        current = project.nodes[current.parent_id]
    path.reverse()
    return path


def can_add_chapter(project: ProjectData, node_id: str | None) -> bool:
    return _node_type(project, node_id) == NodeType.STORY


def can_add_section(project: ProjectData, node_id: str | None) -> bool:
    return _node_type(project, node_id) == NodeType.CHAPTER


def _node_type(project: ProjectData, node_id: str | None) -> NodeType | None:
    if not node_id or node_id not in project.nodes:
        return None
    return project.nodes[node_id].node_type
