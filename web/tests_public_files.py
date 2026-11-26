import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase

from web import views


class PublicFileTest(TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dist = Path(tmp.name)
        (self.dist / "landing").mkdir()
        (self.dist / "landing" / "shot.webp").write_bytes(b"RIFF")
        (self.dist / "manifest.json").write_text("{}")
        patcher = patch.object(views, "DIST_DIR", self.dist)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_image_served_with_its_type(self):
        res = self.client.get("/landing/shot.webp")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "image/webp")

    def test_manifest_served_as_json(self):
        self.assertEqual(self.client.get("/manifest.json")["Content-Type"], "application/json")

    def test_missing_file_is_404_not_index(self):
        self.assertEqual(self.client.get("/landing/none.webp").status_code, 404)

    def test_spa_routes_still_render_index(self):
        res = self.client.get("/books")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/html", res["Content-Type"])
