import io
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from organization.models import Membership, Organization

User = get_user_model()
MEDIA = tempfile.mkdtemp()


def image_file(fmt="PNG", size=(900, 600), name="logo.png"):
    buf = io.BytesIO()
    Image.new("RGB", size, (30, 79, 216)).save(buf, format=fmt)
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=MEDIA)
class LogoUploadTest(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.org = Organization.objects.create(nomi="Kutubxona", slug="lib", status=Organization.HOLAT_ACTIVE)

    def api(self, role):
        user = User.objects.create_user(username=f"u-{role}", password="x")
        Membership.objects.create(organization=self.org, user=user, rol=role, faol=True)
        client = APIClient()
        client.force_authenticate(user)
        client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.pk))
        return client

    def url(self):
        return f"/api/organizations/{self.org.pk}/logo/"

    def test_upload_reencodes_to_small_webp_and_serves_it(self):
        res = self.api("egasi").post(self.url(), {"file": image_file()}, format="multipart")
        self.assertEqual(res.status_code, 200, res.data)
        logo_url = res.json()["logo_url"]
        self.assertRegex(logo_url, r"^/media/logos/org\d+-[0-9a-f]{12}\.webp$")
        served = self.client.get(logo_url)
        self.assertEqual(served["Content-Type"], "image/webp")
        with Image.open(io.BytesIO(b"".join(served.streaming_content))) as img:
            self.assertEqual(img.format, "WEBP")
            self.assertLessEqual(max(img.size), 512)

    def test_fake_image_rejected(self):
        fake = SimpleUploadedFile("x.png", b"<svg onload=alert(1)>", content_type="image/png")
        res = self.api("egasi").post(self.url(), {"file": fake}, format="multipart")
        self.assertEqual(res.status_code, 400)
        self.org.refresh_from_db()
        self.assertEqual(self.org.logo_url, "")

    def test_too_big_rejected(self):
        big = SimpleUploadedFile("x.png", b"0" * (2 * 1024 * 1024 + 1), content_type="image/png")
        self.assertEqual(self.api("egasi").post(self.url(), {"file": big}, format="multipart").status_code, 400)

    def test_librarian_cannot_upload(self):
        res = self.api("kutubxonachi").post(self.url(), {"file": image_file()}, format="multipart")
        self.assertEqual(res.status_code, 403)

    def test_delete_removes_logo(self):
        api = self.api("administrator")
        api.post(self.url(), {"file": image_file()}, format="multipart")
        self.assertEqual(api.delete(self.url()).json()["logo_url"], "")

    def test_only_logo_names_are_served(self):
        self.assertEqual(self.client.get("/media/logos/..%2Fsecret.webp").status_code, 404)
        self.assertEqual(self.client.get("/media/logos/evil.webp").status_code, 404)
