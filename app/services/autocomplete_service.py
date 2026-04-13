import re

from app.models import ProjectData


WORD_PATTERN = re.compile(r"([A-Za-zÁÉÍÓÚáéíóúÑñ0-9_]+)$")


def get_current_prefix(text_before_cursor: str) -> str | None:
    match = WORD_PATTERN.search(text_before_cursor)
    if not match:
        return None
    return match.group(1)


def find_character_matches(project: ProjectData, prefix: str) -> list[str]:
    if not prefix or len(prefix) < 2:
        return []

    lowered_prefix = prefix.lower()
    return [
        name
        for name in sorted(project.characters.keys(), key=str.lower)
        if name.lower().startswith(lowered_prefix)
    ]


def build_highlight_spans(project: ProjectData, content: str) -> dict[str, dict[str, object]]:
    spans: dict[str, dict[str, object]] = {}
    for character in project.characters.values():
        if not character.highlight_enabled:
            continue

        pattern = rf"\b{re.escape(character.name)}\b"
        matches = [
            (match.start(), match.end())
            for match in re.finditer(pattern, content, flags=re.IGNORECASE)
        ]
        if not matches:
            continue

        spans[f"char_{character.name.replace(' ', '_')}"] = {
            "color": character.highlight_color,
            "ranges": matches,
        }
    return spans
