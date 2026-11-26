"""Everything the platform admin needs to judge one organization (lead) at a glance."""
from django.utils import timezone

from .models import AuditLog, Membership, PushSubscription

VISIT_LIMIT = 50
TIMELINE_LIMIT = 100


def _user(user):
    if user is None:
        return None
    return {
        "id": user.pk,
        "full_name": user.full_name,
        "username": user.username,
        "phone": user.telefon,
        "email": user.email,
        "date_joined": user.date_joined,
        "last_login": user.last_login,
    }


def _touch(source, medium, campaign, **extra):
    return {"source": source, "medium": medium, "campaign": campaign, **extra}


def _attribution(org):
    from marketing.models import SignupAttribution, Visit

    attr = SignupAttribution.objects.filter(organization=org).first()
    if attr is None:
        return None
    visits = []
    if attr.visitor_id:
        visits = [
            {
                "created_at": v.created_at,
                "source": v.source,
                "medium": v.medium,
                "campaign": v.campaign,
                "term": v.term,
                "content": v.content,
                "referrer_host": v.referrer_host,
                "landing_path": v.landing_path,
                "click_id": v.click_id,
            }
            for v in Visit.objects.filter(visitor_id=attr.visitor_id).order_by("created_at")[:VISIT_LIMIT]
        ]
    return {
        "first": _touch(
            attr.source,
            attr.medium,
            attr.campaign,
            term=attr.term,
            content=attr.content,
            referrer_host=attr.referrer_host,
            landing_path=attr.landing_path,
            click_id=attr.click_id,
            at=attr.first_seen_at,
        ),
        "last": _touch(attr.last_source, attr.last_medium, attr.last_campaign),
        "signed_up_at": attr.created_at,
        "visits": visits,
    }


def _usage(org):
    from berish.models import Berish
    from kitob.models import Kitob
    from navbat.models import Navbat
    from nusxa.models import Nusxa
    from oquvchi.models import Ariza, Oquvchi

    open_loans = Berish.objects.filter(organization=org, qaytarilgan_sana__isnull=True)
    return {
        "books": Kitob.objects.filter(organization=org).count(),
        "copies": Nusxa.objects.filter(organization=org).count(),
        "readers": Oquvchi.objects.filter(organization=org).count(),
        "loans": Berish.objects.filter(organization=org).count(),
        "open_loans": open_loans.count(),
        "overdue_loans": open_loans.filter(qaytarish_muddati__lt=timezone.localdate()).count(),
        "pending_applications": Ariza.objects.filter(organization=org, holati="kutmoqda").count(),
        "reservations": Navbat.objects.filter(organization=org, holati="kutmoqda").count(),
    }


def _bot(org):
    bot = getattr(org, "telegram_bot", None)
    if bot is None:
        return None
    return {
        "username": bot.username,
        "status": bot.holati,
        "status_display": bot.get_holati_display(),
        "webhook_set": bot.webhook_ornatilgan,
        "last_checked_at": bot.oxirgi_tekshiruv,
        "last_error": bot.oxirgi_xato,
    }


def organization_details(org, subscription_summary):
    members = (
        Membership.objects.filter(organization=org)
        .select_related("user")
        .order_by("-faol", "qoshilgan")
    )
    timeline = (
        AuditLog.objects.filter(organization=org)
        .select_related("actor")
        .order_by("-yaratilgan", "-id")[:TIMELINE_LIMIT]
    )
    return {
        "organization": {
            "id": org.pk,
            "name": org.nomi,
            "slug": org.slug,
            "type": org.type,
            "status": org.status,
            "status_reason": org.status_reason,
            "status_changed_at": org.status_changed_at,
            "approved_at": org.approved_at,
            "approved_by": org.approved_by.username if org.approved_by_id else "",
            "created_at": org.yaratilgan,
            "phone": org.telefon,
            "email": org.email,
            "address": org.manzil,
            "description": org.tavsif,
            "logo_url": org.logo_url,
        },
        "owner": _user(org.egasi),
        "members": [
            {
                **_user(m.user),
                "role": m.rol,
                "role_display": m.get_rol_display(),
                "active": m.faol,
                "joined_at": m.qoshilgan,
                "telegram_linked": bool(m.telegram_id),
            }
            for m in members
        ],
        "subscription": subscription_summary(org),
        "usage": _usage(org),
        "bot": _bot(org),
        "push_subscriptions": PushSubscription.objects.filter(organization=org).count(),
        "attribution": _attribution(org),
        "timeline": [
            {
                "id": a.pk,
                "action": a.action,
                "actor": (a.actor.full_name or a.actor.username) if a.actor_id else "",
                "metadata": a.metadata,
                "created_at": a.yaratilgan,
            }
            for a in timeline
        ],
    }
