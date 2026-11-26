import django_filters
from django.db.models import Exists, OuterRef

from berish.models import Berish
from jarima.models import Jarima

from .models import Oquvchi


class ReaderFilter(django_filters.FilterSet):
    """Reader list filters. New params are English; legacy ones kept."""

    has_telegram = django_filters.BooleanFilter(method="filter_has_telegram")
    has_debt = django_filters.BooleanFilter(method="filter_has_debt")
    has_active_loans = django_filters.BooleanFilter(method="filter_has_active_loans")

    class Meta:
        model = Oquvchi
        fields = ["rol", "faol", "sinf"]

    def filter_has_telegram(self, queryset, name, value):
        return queryset.filter(telegram_id__isnull=not value)

    def filter_has_debt(self, queryset, name, value):
        debt = Exists(Jarima.objects.filter(berish__oquvchi=OuterRef("pk"), tolandimi=False))
        return queryset.filter(debt) if value else queryset.exclude(debt)

    def filter_has_active_loans(self, queryset, name, value):
        active = Exists(Berish.objects.filter(oquvchi=OuterRef("pk"), qaytarilgan_sana__isnull=True))
        return queryset.filter(active) if value else queryset.exclude(active)
