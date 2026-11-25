"""The cross-library competition is not visible to library members."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from organization.models import Membership, Organization

User = get_user_model()
URL = "/api/stats/ratings/competition/"


class CompetitionAccessTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            nomi="a", slug="comp-a", status=Organization.HOLAT_ACTIVE
        )
        Organization.objects.create(nomi="b", slug="comp-b", status=Organization.HOLAT_ACTIVE)

    def get(self, user=None):
        api = APIClient()
        if user:
            api.force_authenticate(user)
        return api.get(URL)

    def test_library_owner_is_refused(self):
        user = User.objects.create_user(username="o", password="parol12345")
        Membership.objects.create(organization=self.org, user=user, rol="egasi")
        self.assertEqual(self.get(user).status_code, 403)

    def test_anonymous_is_refused(self):
        self.assertIn(self.get().status_code, (401, 403))

    def test_platform_admin_sees_every_library(self):
        admin = User.objects.create_superuser(username="p", password="parol12345")
        res = self.get(admin)
        self.assertEqual(res.status_code, 200, res.data)
        self.assertLessEqual({"a", "b"}, {row["nomi"] for row in res.data})
