from datetime import date

import django_filters
from django.db.models import Q

from oquvchi.search import tolerant_q

from .models import Berish


class LoanFilter(django_filters.FilterSet):
    """Loan list filters. Query params are English; model fields are legacy."""

    status = django_filters.CharFilter(field_name="holati")
    reader = django_filters.NumberFilter(field_name="oquvchi")
    grade = django_filters.CharFilter(field_name="oquvchi__sinf")
    issued_from = django_filters.DateFilter(field_name="berilgan_sana", lookup_expr="gte")
    issued_to = django_filters.DateFilter(field_name="berilgan_sana", lookup_expr="lte")
    overdue = django_filters.BooleanFilter(method="filter_overdue")
    q = django_filters.CharFilter(method="filter_q")

    class Meta:
        model = Berish
        # `holati` / `oquvchi` kept for the existing frontend and bot.
        fields = ["holati", "oquvchi"]

    def filter_overdue(self, queryset, name, value):
        overdue = Q(qaytarilgan_sana__isnull=True, qaytarish_muddati__lt=date.today())
        return queryset.filter(overdue) if value else queryset.exclude(overdue)

    def filter_q(self, queryset, name, value):
        value = value.strip()
        if not value:
            return queryset
        return queryset.filter(tolerant_q(["oquvchi__fish", "kitob__nomi"], value))
