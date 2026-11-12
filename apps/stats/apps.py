from django.apps import AppConfig


class StatsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "stats"

    def ready(self):
        from django.db.models.signals import post_delete, post_save

        from config.cache import stats_keshini_tozala
        from berish.models import Berish
        from jarima.models import Jarima
        from kitob.models import Kitob
        from navbat.models import Navbat
        from nusxa.models import Nusxa

        for model in (Berish, Jarima, Kitob, Navbat, Nusxa):
            post_save.connect(lambda **kw: stats_keshini_tozala(), sender=model, weak=False, dispatch_uid=f"stats-{model.__name__}-s")
            post_delete.connect(lambda **kw: stats_keshini_tozala(), sender=model, weak=False, dispatch_uid=f"stats-{model.__name__}-d")
