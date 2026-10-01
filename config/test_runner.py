"""Test runner.

Standart `manage.py test` bu loyihada 0 ta test topadi: ilovalar `apps/`
ichida, `apps/` esa Python paketi emas (ilova nomlari `oquvchi`, `navbat`
... shaklida `sys.path` orqali import qilinadi). Shu sababli top-level
`test*.py` qidiruvi `apps/` ichiga kira olmaydi.

Bu runner topgan bo'sh bo'lganda barcha INSTALLED_APPS ilovalarini
o'zi test label sifatida ishlatadi — shunda `manage.py test` barcha
testlarni topib, ishga tushiradi.
"""
from django.apps import apps
from django.test.runner import DiscoverRunner


class AppTestRunner(DiscoverRunner):
    def build_suite(self, test_labels=None, **kwargs):
        if not test_labels:
            # Faqat loyihaning o'z ilovalari: django.contrib ilovalari
            # ushbu yerda test modullari yo'q va ularni import qilish
            # xato beradi (ular paket sifatida import qilinmaydi).
            test_labels = [
                config.label
                for config in apps.get_app_configs()
                if not config.name.startswith("django.")
            ]
        return super().build_suite(test_labels, **kwargs)
