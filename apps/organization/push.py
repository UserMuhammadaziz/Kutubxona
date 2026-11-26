"""Web Push helpers: notify an organization's owner when the application is decided."""
import json
import logging

from django.conf import settings

from .models import Organization, PushSubscription

logger = logging.getLogger(__name__)

STATUS_MESSAGES = {
    Organization.HOLAT_ACTIVE: (
        "Arizangiz tasdiqlandi",
        "Kutubxonangiz faollashtirildi. Tizimga kirib ishlashingiz mumkin.",
    ),
    Organization.HOLAT_REJECTED: (
        "Arizangiz rad etildi",
        "Ariza rad etildi. Sababini ilovada ko'ring.",
    ),
}


def push_enabled() -> bool:
    return bool(settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY)


def _send(subscription: PushSubscription, payload: dict) -> bool:
    """Send one push. Returns False when the subscription is gone (404/410)."""
    from pywebpush import WebPushException, webpush

    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            data=json.dumps(payload),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": f"mailto:{settings.VAPID_CLAIMS_EMAIL}"},
            ttl=86400,
        )
        return True
    except WebPushException as exc:
        code = getattr(getattr(exc, "response", None), "status_code", None)
        if code in (404, 410):
            return False
        logger.warning("web push failed: %s", exc)
        return True


def notify_organization_status(organization: Organization) -> int:
    """Push the new status to the owner's browsers. Never raises."""
    message = STATUS_MESSAGES.get(organization.status)
    if not message or not push_enabled():
        return 0
    title, body = message
    payload = {"title": title, "body": body, "url": "/", "tag": "organization-status"}
    sent = 0
    try:
        for sub in PushSubscription.objects.filter(organization=organization):
            if _send(sub, payload):
                sent += 1
            else:
                sub.delete()
    except Exception:  # noqa: BLE001 - push must never break the approval flow
        logger.exception("organization status push failed")
    return sent
