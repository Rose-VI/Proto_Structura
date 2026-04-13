from app.models import Character, ProjectData


def create_character(project: ProjectData, name: str) -> Character:
    name = name.strip()
    if not name:
        raise ValueError("El nombre no puede estar vacío.")
    if name in project.characters:
        raise ValueError("Ese personaje ya existe.")

    character = Character(name=name)
    project.characters[name] = character
    return character


def rename_character(project: ProjectData, old_name: str, new_name: str) -> None:
    new_name = new_name.strip()
    if not new_name:
        raise ValueError("El nombre no puede estar vacío.")
    if new_name != old_name and new_name in project.characters:
        raise ValueError("Ya existe un personaje con ese nombre.")

    character = project.characters.pop(old_name)
    character.name = new_name
    project.characters[new_name] = character


def delete_character(project: ProjectData, name: str) -> None:
    if name in project.characters:
        del project.characters[name]


def update_character_description(project: ProjectData, name: str, description: str) -> None:
    if name in project.characters:
        project.characters[name].description = description.rstrip()


def get_sorted_character_names(project: ProjectData) -> list[str]:
    return sorted(project.characters.keys(), key=str.lower)


def set_character_highlight_enabled(project: ProjectData, name: str, enabled: bool) -> None:
    if name in project.characters:
        project.characters[name].highlight_enabled = enabled


def set_character_highlight_color(project: ProjectData, name: str, color: str) -> None:
    if name in project.characters:
        project.characters[name].highlight_color = color
