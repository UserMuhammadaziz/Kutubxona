from datetime import timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from organization.models import Organization
from organization.permissions import IsPlatformAdmin

from .attribution import UTM_FIELDS, normalise
from .models import SignupAttribution, Visit

# A repeat hit from the same browser and source inside this window is the same visit.
SAME_VISIT = timedelta(minutes=30)


class VisitThrottle(AnonRateThrottle):
    scope = "marketing_visit"
    rate = "60/hour"


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([VisitThrottle])
def track_visit(request):
    data = normalise(request.data, request.get_host().split(":")[0])
    if not data["visitor_id"]:
        return Response({"detail": "visitor_id kerak."}, status=status.HTTP_400_BAD_REQUEST)
    duplicate = Visit.objects.filter(
        visitor_id=data["visitor_id"],
        source=data["source"],
        medium=data["medium"],
        campaign=data["campaign"],
        created_at__gte=timezone.now() - SAME_VISIT,
    ).exists()
    if not duplicate:
        Visit.objects.create(**data)
    return Response(status=status.HTTP_204_NO_CONTENT)


def _days(request):
    try:
        return min(max(int(request.query_params.get("days", 30)), 1), 365)
    except (TypeError, ValueError):
        return 30


def _rate(part, whole):
    return round(part * 100 / whole, 1) if whole else 0.0


@api_view(["GET"])
@permission_classes([IsPlatformAdmin])
def marketing_report(request):
    days = _days(request)
    since = timezone.now() - timedelta(days=days)
    visits = Visit.objects.filter(created_at__gte=since)
    signups = SignupAttribution.objects.filter(organization__yaratilgan__gte=since)
    active = Q(organization__status=Organization.HOLAT_ACTIVE)
    orgs_total = Organization.objects.filter(yaratilgan__gte=since).count()

    rows = {}
    for row in visits.values("source", "medium").annotate(
        visits=Count("id"), visitors=Count("visitor_id", distinct=True)
    ):
        rows[(row["source"], row["medium"])] = {**row, "signups": 0, "approved": 0}
    for row in signups.values("source", "medium").annotate(
        signups=Count("id"), approved=Count("id", filter=active)
    ):
        key = (row["source"], row["medium"])
        rows.setdefault(key, {"source": key[0], "medium": key[1], "visits": 0, "visitors": 0})
        rows[key].update(signups=row["signups"], approved=row["approved"])
    # Organizations registered before tracking (or by platform staff) have no attribution.
    unknown = orgs_total - signups.count()
    if unknown > 0:
        rows[("unknown", "")] = {"source": "unknown", "medium": "", "visits": 0, "visitors": 0, "signups": unknown, "approved": 0}
    sources = sorted(rows.values(), key=lambda r: (-r["signups"], -r["visitors"], r["source"]))
    for row in sources:
        row["conversion"] = _rate(row["signups"], row["visitors"])

    campaigns = {}
    for row in visits.exclude(campaign="").values("source", "medium", "campaign").annotate(
        visits=Count("id"), visitors=Count("visitor_id", distinct=True)
    ):
        campaigns[(row["source"], row["medium"], row["campaign"])] = {**row, "signups": 0}
    for row in signups.exclude(campaign="").values("source", "medium", "campaign").annotate(signups=Count("id")):
        key = (row["source"], row["medium"], row["campaign"])
        campaigns.setdefault(key, {"source": key[0], "medium": key[1], "campaign": key[2], "visits": 0, "visitors": 0})
        campaigns[key]["signups"] = row["signups"]
    campaign_rows = sorted(campaigns.values(), key=lambda r: (-r["signups"], -r["visitors"]))
    for row in campaign_rows:
        row["conversion"] = _rate(row["signups"], row["visitors"])

    daily = {}
    for row in visits.annotate(day=TruncDate("created_at")).values("day").annotate(
        visits=Count("id"), visitors=Count("visitor_id", distinct=True)
    ):
        daily[row["day"]] = {"date": row["day"].isoformat(), "visits": row["visits"], "visitors": row["visitors"], "signups": 0}
    for row in Organization.objects.filter(yaratilgan__gte=since).annotate(day=TruncDate("yaratilgan")).values("day").annotate(n=Count("id")):
        daily.setdefault(row["day"], {"date": row["day"].isoformat(), "visits": 0, "visitors": 0, "signups": 0})
        daily[row["day"]]["signups"] = row["n"]

    recent = [
        {
            "organization_id": a.organization_id,
            "organization_name": a.organization.nomi,
            "status": a.organization.status,
            "created_at": a.organization.yaratilgan,
            "first_seen_at": a.first_seen_at,
            **{f: getattr(a, f) for f in (*UTM_FIELDS, "referrer_host", "landing_path")},
            "last_source": a.last_source,
            "last_medium": a.last_medium,
        }
        for a in signups.select_related("organization").order_by("-organization__yaratilgan")[:25]
    ]

    visitors_total = visits.values("visitor_id").distinct().count()
    return Response(
        {
            "days": days,
            "totals": {
                "visits": visits.count(),
                "visitors": visitors_total,
                "signups": orgs_total,
                "approved": Organization.objects.filter(yaratilgan__gte=since, status=Organization.HOLAT_ACTIVE).count(),
                "conversion": _rate(orgs_total, visitors_total),
            },
            "sources": sources,
            "campaigns": campaign_rows[:50],
            "daily": [daily[d] for d in sorted(daily)],
            "recent_signups": recent,
        }
    )
