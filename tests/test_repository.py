import json
import os
import tempfile
import unittest

from app.models import NodeType, ProjectData
from app.repository import JsonProjectRepository, ProjectValidationError
from app.services import chapter_service, character_service


class JsonProjectRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.repository = JsonProjectRepository()

    def test_save_and_load_roundtrip(self):
        project = ProjectData()
        story = chapter_service.create_story(project, "Historia")
        chapter = chapter_service.create_chapter(project, story.id, "Capítulo 1")
        chapter_service.create_section(project, chapter.id, "Escena 1")
        character_service.create_character(project, "Luna")

        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "project.json")
            self.repository.save(project, path)
            loaded = self.repository.load(path)

        self.assertEqual(loaded.schema_version, project.schema_version)
        self.assertEqual(loaded.nodes[story.id].node_type, NodeType.STORY)
        self.assertEqual(loaded.nodes[chapter.id].node_type, NodeType.CHAPTER)
        self.assertIn("Luna", loaded.characters)

    def test_load_legacy_json_without_schema_version(self):
        legacy_payload = {
            "next_id": 2,
            "root_ids": ["node_1"],
            "nodes": {
                "node_1": {
                    "id": "node_1",
                    "title": "Historia",
                    "content": "",
                    "notes": "",
                    "children": [],
                    "parent_id": None,
                    "node_type": "story",
                }
            },
            "characters": {},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "legacy.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(legacy_payload, handle)

            loaded = self.repository.load(path)

        self.assertEqual(loaded.nodes["node_1"].node_type, NodeType.STORY)

    def test_invalid_relationships_raise_validation_error(self):
        invalid_payload = {
            "schema_version": 1,
            "next_id": 2,
            "root_ids": ["node_1"],
            "nodes": {
                "node_1": {
                    "id": "node_1",
                    "title": "Historia",
                    "content": "",
                    "notes": "",
                    "children": ["node_2"],
                    "parent_id": None,
                    "node_type": "story",
                },
                "node_2": {
                    "id": "node_2",
                    "title": "Huérfano",
                    "content": "",
                    "notes": "",
                    "children": [],
                    "parent_id": None,
                    "node_type": "chapter",
                },
            },
            "characters": {},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "invalid.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(invalid_payload, handle)

            with self.assertRaises(ProjectValidationError):
                self.repository.load(path)


if __name__ == "__main__":
    unittest.main()
