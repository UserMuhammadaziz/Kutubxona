"""Organization application tests: phone is required, Web Push on approval."""
from django.test import TestCase
from rest_framework.test import APIClient


class RegistrationPhoneAndPushTests(TestCase):
    """Org application requires a phone; the owner gets a Web Push on approval."""

    def _payload(self, **extra):
        data = {
            "kutubxona_nomi": "11-maktab",
            "full_name": "Owner One",
            "password": "StrongPass123",
            "password_confirm": "StrongPass123",
            "telefon": "+998901234567",
        }
        data.update(extra)
        return data

    def test_phone_is_required(self):
        data = self._payload()
        data.pop("telefon")
        res = APIClient().post("/api/auth/register/", data, format="json")
        self.assertEqual(res.status_code, 400)

    def test_phone_format_is_validated(self):
        res = APIClient().post(
            "/api/auth/register/", self._payload(telefon="901234567"), format="json"
        )
        self.assertEqual(res.status_code, 400)

    def test_push_sent_on_approval(self):
        from unittest.mock import patch

        from organization.models import Organization, PushSubscription
        from organization.services import set_status

        client = APIClient()
        res = client.post("/api/auth/register/", self._payload(), format="json")
        self.assertEqual(res.status_code, 201, res.data)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")
        sub = client.post(
            "/api/push/subscribe/",
            {"endpoint": "https://push.example/abc", "keys": {"p256dh": "k", "auth": "a"}},
            format="json",
        )
        self.assertEqual(sub.status_code, 201)
        org = Organization.objects.get(nomi="11-maktab")
        self.assertEqual(PushSubscription.objects.filter(organization=org).count(), 1)

        with self.settings(VAPID_PUBLIC_KEY="pub", VAPID_PRIVATE_KEY="priv"), patch(
            "organization.push._send", return_value=True
        ) as send:
            set_status(org, Organization.HOLAT_ACTIVE)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(send.call_args[0][1]["title"], "Arizangiz tasdiqlandi")
