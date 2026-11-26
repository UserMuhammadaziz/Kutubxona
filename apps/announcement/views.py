from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from organization.tenancy import joriy_kutubxonani_aniqla, scope
from user.permissions import IsLibrarian

from . import services
from .models import Announcement


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = [
            "id", "text", "audience", "grade", "created_at",
            "recipients_count", "sent_count", "failed_count",
        ]
        read_only_fields = fields


class AnnouncementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET  /api/announcements/          -> send log
    POST /api/announcements/preview/  -> {audience, grade} -> recipients count + daily limit
    POST /api/announcements/send/     -> {text, audience, grade} -> send now
    """

    permission_classes = [IsLibrarian]
    serializer_class = AnnouncementSerializer
    queryset = Announcement.objects.all()
    filterset_fields = []

    def get_organization(self):
        return joriy_kutubxonani_aniqla(self.request, required=True)

    def get_queryset(self):
        return scope(Announcement.objects.all(), self.get_organization())

    def _audience(self, request):
        audience = request.data.get("audience", "")
        if audience not in dict(Announcement.AUDIENCE_CHOICES):
            raise ValidationError({"audience": "Auditoriyani tanlang."})
        return audience, str(request.data.get("grade", "")).strip()

    @action(detail=False, methods=["post"])
    def preview(self, request):
        org = self.get_organization()
        audience, grade = self._audience(request)
        return Response(
            {
                "recipients": services.audience_queryset(org, audience, grade).count(),
                "sent_today": services.sent_today(org),
                "daily_limit": services.DAILY_LIMIT,
            }
        )

    @action(detail=False, methods=["post"])
    def send(self, request):
        org = self.get_organization()
        audience, grade = self._audience(request)
        text = str(request.data.get("text", "")).strip()
        if not text:
            raise ValidationError({"text": "Xabar matni bo‘sh bo‘lmasligi kerak."})
        if len(text) > 1000:
            raise ValidationError({"text": "Xabar 1000 belgidan oshmasligi kerak."})
        if services.sent_today(org) >= services.DAILY_LIMIT:
            raise ValidationError(
                {"detail": f"Kunlik limit ({services.DAILY_LIMIT} ta e’lon) tugadi. Ertaga urinib ko‘ring."}
            )
        if not services.audience_queryset(org, audience, grade).exists():
            raise ValidationError({"detail": "Tanlangan guruhda Telegramga ulangan o‘quvchi yo‘q."})
        item = services.send_announcement(org, request.user, text, audience, grade)
        return Response(AnnouncementSerializer(item).data, status=201)
