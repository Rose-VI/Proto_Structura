import unittest

from app.models import NodeType, ProjectData
from app.services import chapter_service, character_service
from app.services.chapter_service import ChapterStructureError


class ChapterServiceTests(unittest.TestCase):
    def test_story_only_accepts_chapters(self):
        project = ProjectData()
        story = chapter_service.create_story(project, "Historia")

        chapter = chapter_service.create_chapter(project, story.id, "Capítulo 1")

        self.assertEqual(chapter.node_type, NodeType.CHAPTER)
        self.assertEqual(project.nodes[story.id].children, [chapter.id])

        with self.assertRaises(ChapterStructureError):
            chapter_service.create_chapter(project, chapter.id, "Capítulo inválido")

    def test_chapter_only_accepts_sections(self):
        project = ProjectData()
        story = chapter_service.create_story(project, "Historia")
        chapter = chapter_service.create_chapter(project, story.id, "Capítulo 1")

        section = chapter_service.create_section(project, chapter.id, "Escena 1")

        self.assertEqual(section.node_type, NodeType.SECTION)
        self.assertEqual(project.nodes[chapter.id].children, [section.id])

        with self.assertRaises(ChapterStructureError):
            chapter_service.create_section(project, story.id, "Escena inválida")

    def test_delete_node_recursive_removes_branch(self):
        project = ProjectData()
        story = chapter_service.create_story(project, "Historia")
        chapter = chapter_service.create_chapter(project, story.id, "Capítulo 1")
        section = chapter_service.create_section(project, chapter.id, "Escena 1")

        deleted_ids = chapter_service.delete_node_recursive(project, chapter.id)

        self.assertCountEqual(deleted_ids, [chapter.id, section.id])
        self.assertEqual(project.nodes[story.id].children, [])


class CharacterServiceTests(unittest.TestCase):
    def test_character_lifecycle(self):
        project = ProjectData()
        character_service.create_character(project, "Luna")
        character_service.update_character_description(project, "Luna", "Guardiana lunar")
        character_service.rename_character(project, "Luna", "Selene")

        self.assertIn("Selene", project.characters)
        self.assertEqual(project.characters["Selene"].description, "Guardiana lunar")

        character_service.delete_character(project, "Selene")
        self.assertEqual(project.characters, {})


if __name__ == "__main__":
    unittest.main()
