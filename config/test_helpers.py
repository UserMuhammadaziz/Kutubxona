"""Tenancy (ko'p kutubxonali) modeliga mos test yordamchilari.

Eski testlar `Organization`/`Membership` qo'shilishidan oldin yozilgan: ular
faqat global `user.rol` ga tayanib API chaqiradi va yangi obyektlarni
`organization`siz yaratadi. Migration bitta kutubxona yaratgani uchun
`legacy_rejimmi()` endi False — bunday testlar `403` oladi yoki `scope()`
tufayli o'z yozuvlarini ko'rmaydi.

`TenantTestMixin` shu farqni bitta joyda bartaraf etadi:

* har test uchun faol `Organization` yaratadi;
* `TenantModel.save` ni vaqtincha o'zgartirib, `organization` berilmagan
  barcha yozuvlarga shu kutubxonani qo'yadi (test kodidagi yuzlab
  `objects.create()` chaqiruvlarini o'zgartirish shart emas);
* `azolik()` metodi bilan foydalanuvchiga kutubxonachi rolini beradi —
  shunda `IsLibrarian`/`IsAdmin` va `joriy_kutubxonani_aniqla()` ishlaydi.
"""
from unittest.mock import patch

from django.contrib.auth import get_user_model

from organization.models import Membership, Organization, TenantModel

User = get_user_model()


class TenantTestMixin:
    """Legacy test sinflarini tenancy bilan ishlashga moslashtiradi."""

    def setUp(self):
        # Avval kutubxona yaratiladi: keyingi setUp'da yaratiladigan barcha
        # tenant obyektlari shu kutubxonaga bog'lanadi.
        self.org = Organization.objects.create(
            nomi="Test kutubxona",
            status=Organization.HOLAT_ACTIVE,
        )

        asosiy_save = TenantModel.save
        org = self.org

        def save_bilan_organization(instance, *args, **kwargs):
            if instance.organization_id is None:
                instance.organization = org
            return asosiy_save(instance, *args, **kwargs)

        patcher = patch.object(TenantModel, "save", save_bilan_organization)
        patcher.start()
        self.addCleanup(patcher.stop)

        super().setUp()

    def azolik(self, user, rol="kutubxonachi"):
        """Foydalanuvchiga test kutubxonasida a'zolik beradi."""
        return Membership.objects.get_or_create(
            organization=self.org,
            user=user,
            defaults={"rol": rol, "faol": True},
        )[0]
