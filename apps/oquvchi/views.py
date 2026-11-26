from datetime import date

from django.db import transaction
from django.db.models import F, Q, Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from berish.models import Berish
from berish.serializers import BerishMeniSerializer
from config.telegram import telegram_escape
from telegrambot.services import organizatsiya_xabari
from jarima.models import Jarima
from jarima.serializers import JarimaMeniSerializer
from organization.tenancy import (
    TenantViewSetMixin,
    joriy_kutubxonani_aniqla,
    legacy_rejimmi,
    scope,
)
from user.permissions import IsLibrarian
from . import services
from .filters import ReaderFilter
from .models import Ariza, Fan, Oquvchi
from .search import ChidamliQidiruvFilter
from .serializers import (
    ArizaSerializer,
    ArizaStatusSerializer,
    ArizaYaratishSerializer,
    FanSerializer,
    OquvchiSerializer,
    OquvchiYaratishSerializer,
    OquvchiBindSerializer,
    OquvchilarniOchirishSerializer,
    ariza_kutubxonasi,
)


def trust_score(*, late_days, overdue_loans, lost, unpaid_fines, paid_fines):
    """Reader reliability in percent (0-100).

    Everyone starts at 100 and loses points gradually:
    0.5 per day a loan was late (max 10 per loan), 2 per late return, 3 more per loan still overdue,
    5 per unpaid fine, 2 per paid fine, 25 per lost book.
    `late_days` is a list with the number of late days of each late loan (returned or still overdue).
    """
    penalty = sum(min(d * 0.5, 10) for d in late_days) + 2 * len(late_days)
    penalty += 3 * overdue_loans + 5 * unpaid_fines + 2 * paid_fines + 25 * lost
    return max(0, round(100 - penalty))


def trust_level(score, total_loans=1):
    if not total_loans:
        return "new"
    return "high" if score >= 80 else "medium" if score >= 50 else "low"


def _reader_stats(reader):
    """Aggregate numbers for the reader profile header."""
    today = date.today()
    loans = Berish.objects.filter(oquvchi=reader)
    fines = Jarima.objects.filter(berish__oquvchi=reader)
    unpaid = fines.filter(tolandimi=False).aggregate(s=Sum("summa"))["s"] or 0
    paid = fines.filter(tolandimi=True).aggregate(s=Sum("summa"))["s"] or 0
    total = loans.count()
    overdue = loans.filter(qaytarilgan_sana__isnull=True, qaytarish_muddati__lt=today).count()
    returned_late = loans.filter(qaytarilgan_sana__gt=F("qaytarish_muddati")).count()
    late_days = [
        ((returned or today) - due).days
        for returned, due in loans.values_list("qaytarilgan_sana", "qaytarish_muddati")
        if (returned or today) > due
    ]
    score = trust_score(
        late_days=late_days,
        overdue_loans=overdue,
        lost=loans.filter(holati="yoqolgan").count(),
        unpaid_fines=fines.filter(tolandimi=False).count(),
        paid_fines=fines.filter(tolandimi=True).count(),
    )
    return {
        "total_loans": total,
        "active_loans": loans.filter(qaytarilgan_sana__isnull=True).count(),
        "overdue_loans": overdue,
        "returned_late": returned_late,
        "unpaid_fines_total": unpaid,
        "paid_fines_total": paid,
        "trust_score": score,
        "trust_level": trust_level(score, total),
    }


def _reader_history(reader, limit=30):
    """Latest loans (active and returned), newest first."""
    today = date.today()
    loans = (
        Berish.objects.filter(oquvchi=reader)
        .select_related("kitob", "nusxa")
        .prefetch_related("jarima")
        .order_by("-berilgan_sana", "-id")[:limit]
    )
    rows = []
    for loan in loans:
        returned = loan.qaytarilgan_sana
        if returned:
            status_ = "returned"
        elif loan.qaytarish_muddati < today:
            status_ = "overdue"
        else:
            status_ = "active"
        fine = getattr(loan, "jarima", None)
        rows.append(
            {
                "id": loan.id,
                "book_title": loan.kitob.nomi,
                "issued_at": loan.berilgan_sana,
                "due_date": loan.qaytarish_muddati,
                "returned_at": returned,
                "status": status_,
                "fine_amount": fine.summa if fine else None,
                "fine_paid": fine.tolandimi if fine else None,
            }
        )
    return rows


class OquvchiViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """
    GET   /api/readers/       -> ro'yxat (qidiruv: fish, telefon, karta_raqami)
    GET   /api/readers/?rol=oqituvchi -> faqat o'qituvchilar ("O'qituvchilar" bo'limi)
    POST  /api/readers/       -> yangi o'quvchi ro'yxatga olish (karta_raqami avtomatik)
    GET   /api/readers/{id}/  -> o'quvchi kartochkasi: joriy kitoblari va jarimalari
    PATCH /api/readers/{id}/  -> tahrirlash
    POST  /api/readers/ochirish/ -> tanlangan kitobxonlarni o'chirish
    POST  /api/readers/bind/  -> bot: telefon + karta_raqami bo'yicha telegram_id ni bog'lash
    """

    permission_classes = [IsLibrarian]
    queryset = Oquvchi.objects.all().order_by("-royxat_sanasi", "-id")
    search_fields = ["fish", "telefon", "karta_raqami", "sinf", "kasb"]
    # Typed apostrophe must match typographic ones stored in names.
    filter_backends = [DjangoFilterBackend, ChidamliQidiruvFilter]
    filterset_class = ReaderFilter
    http_method_names = ["get", "post", "patch"]

    def get_serializer_class(self):
        if self.action == "create":
            return OquvchiYaratishSerializer
        return OquvchiSerializer

    def get_permissions(self):
        # `bind` ochiq emas: telefon + karta raqamini bilgan har kim
        # internet orqali o'quvchi akkauntini o'z telegram_id'siga qayta
        # bog'lashi (akkount egallash) mumkin edi. Endi so'rov
        # autentifikatsiyalangan bo'lishi shart — bot o'z xizmat
        # akkaunti JWT'si bilan chaqiradi.
        return [IsLibrarian()]

    def retrieve(self, request, *args, **kwargs):
        oquvchi = self.get_object()
        data = OquvchiSerializer(oquvchi).data

        joriy = oquvchi.berish_set.filter(qaytarilgan_sana__isnull=True)
        data["joriy_kitoblari"] = BerishMeniSerializer(joriy, many=True).data

        jarimalar = Jarima.objects.filter(berish__oquvchi=oquvchi, tolandimi=False)
        data["jarimalari"] = JarimaMeniSerializer(jarimalar, many=True).data

        # New English keys (profile page): statistics + loan history.
        data["stats"] = _reader_stats(oquvchi)
        data["history"] = _reader_history(oquvchi)

        return Response(data)

    @action(detail=True, methods=["post"], url_path="message")
    def message(self, request, pk=None):
        """POST /api/readers/{id}/message/ {"text": "..."} -> Telegram message to this reader."""
        reader = self.get_object()
        text = str(request.data.get("text", "")).strip()
        if not text:
            raise ValidationError({"text": "Xabar matni bo‘sh bo‘lmasligi kerak."})
        if len(text) > 1000:
            raise ValidationError({"text": "Xabar 1000 belgidan oshmasligi kerak."})
        if not reader.telegram_id:
            raise ValidationError({"detail": "O‘quvchi Telegram botga ulanmagan."})
        sent = organizatsiya_xabari(reader.organization, reader.telegram_id, telegram_escape(text))
        if not sent:
            raise ValidationError({"detail": "Xabar yuborilmadi. Bot ulanganini tekshiring."})
        return Response({"sent": True})

    @action(detail=False, methods=["post"], url_path="bind")
    def bind(self, request):
        # Serializer kutubxonani aynan shu so'rov kontekstidan aniqlaydi
        # (xizmat akkauntining a'zoligi bo'yicha). Kontekstsiz u barcha
        # kutubxonalarni ko'rmaydi va bog'lash ishlamay qoladi.
        serializer = OquvchiBindSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        oquvchi = serializer.save()
        return Response(OquvchiSerializer(oquvchi).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="ochirish")
    def ochirish(self, request):
        """POST /api/readers/ochirish/ — tanlangan kitobxonlarni o'chirish.

        Faqat **joriy** kitob (qaytarilmagan Berish) yoki **kutilayotgan**
        band so'rovi (`kutmoqda`) o'chirishga to'sqinlik qiladi — bular
        Bandlar/Berishlar bo'limida ko'rinadi va avval yakunlanishi kerak.

        Tugallangan tarix (qaytarilgan berishlar, rad etilgan/tasdiqlangan/
        bekor qilingan bandlar) endi to'siq bo'lmaydi: ular PROTECT bog'lanish
        tufayli oldin o'chirishni bloklagan, lekin hech qayerda ko'rinmagan.
        Bunday yozuvlar bir tranzaksiyada tozalanadi, so'ngra kitobxon
        o'chiriladi. Sabab natijada qaytariladi.
        """
        serializer = OquvchilarniOchirishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        org = joriy_kutubxonani_aniqla(request, required=False)
        # Fail closed: without a resolved library nothing is deleted (outside legacy mode).
        qs = scope(Oquvchi.objects.filter(pk__in=serializer.validated_data["ids"]), org)

        ochirildi = 0
        ochirilmadi = []
        with transaction.atomic():
            for oquvchi in qs.select_for_update():
                sabablar = []
                if oquvchi.berish_set.filter(qaytarilgan_sana__isnull=True).exists():
                    sabablar.append("kitob berish tarixi bor (kitob hali qaytarilmagan)")
                if oquvchi.band_qilishlar.filter(holati="kutmoqda").exists():
                    sabablar.append("kutilayotgan band so'rovi bor (Bandlar bo'limida)")
                if sabablar:
                    ochirilmadi.append(
                        {
                            "id": oquvchi.pk,
                            "fish": oquvchi.fish,
                            "sabab": ", ".join(sabablar),
                        }
                    )
                    continue

                # O'chirishdan oldin xabar oluvchini saqlab qolamiz: Django
                # `delete()` dan keyin instansiyaning PK sini bo'shatadi.
                telegram_id = oquvchi.telegram_id
                organization = oquvchi.organization

                # Eski arizani ham tozalaymiz: aks holda bot `/start` da
                # "arizangiz kutmoqda" deb qayta ariza berishni bloklaydi.
                # Shundan keyin foydalanuvchi yangi ariza yubora oladi.
                if telegram_id:
                    eski_arizalar = Ariza.objects.filter(telegram_id=telegram_id)
                    if oquvchi.organization_id:
                        eski_arizalar = eski_arizalar.filter(organization=organization)
                    eski_arizalar.delete()

                # Faqat yakunlangan yozuvlarni tozalaymiz: ular hech qanday
                # faol jarayonga ta'sir qilmaydi, lekin PROTECT tufayli
                # kitobxonnini o'chirishga xalaqit berardi.
                oquvchi.berish_set.filter(qaytarilgan_sana__isnull=False).delete()
                oquvchi.band_qilishlar.all().delete()
                oquvchi.delete()
                # Xabar faqat o'chirish muvaffaqiyatli commit bo'lgach ketadi;
                # telegram_id si yo'qlarga xabar yuborilmaydi (False qaytadi).
                services.ochirilish_xabarini_yubor(telegram_id, organization)
                ochirildi += 1

        return Response({"ochirildi": ochirildi, "ochirilmadi": ochirilmadi})


class ArizaViewSet(viewsets.ModelViewSet):
    """
    POST   /api/applications/            -> yangi a'zolik arizasi (bot, ochiq)
    GET    /api/applications/            -> arizalar ro'yxati (kutubxonachi)
    GET    /api/applications/status/?telegram_id= -> ariza holati (bot, ochiq)
    POST   /api/applications/{id}/approve/ -> tasdiqlash: Oquvchi yaratib, telegram_id bog'laydi
    POST   /api/applications/{id}/reject/ -> rad etish
    """

    queryset = Ariza.objects.all()
    serializer_class = ArizaSerializer
    filterset_fields = ["holati", "sinf", "rol"]
    search_fields = ["fish", "telefon", "telegram_id", "kasb"]
    filter_backends = [DjangoFilterBackend, ChidamliQidiruvFilter]
    http_method_names = ["get", "post"]

    def get_permissions(self):
        if self.action in ("create", "holat"):
            return []
        return [IsLibrarian()]

    def get_serializer_class(self):
        if self.action == "create":
            return ArizaYaratishSerializer
        return ArizaSerializer

    def _org(self):
        # Arizalar ro'yxati/tasdiqlash — kutubxonachi endpoint'lari.
        return joriy_kutubxonani_aniqla(self.request, required=False)

    def get_queryset(self):
        # `list`, `approve`, `reject` faqat joriy kutubxonaning arizalarini
        # ko'radi. Bot chaqiradigan ochiq `create`/`holat` bu metodga
        # tayanmaydi — ular `ariza_kutubxonasi()` orqali aniqlanadi.
        org = self._org()
        qs = scope(super().get_queryset(), org)
        if org is not None:
            from organization.models import Organization

            # Eski bot arizalarida organization bo'sh qolgan: bitta kutubxona
            # bo'lgan ular ham ko'rinishi va tasdiqlanishi kerak.
            if Organization.objects.filter(status=Organization.HOLAT_ACTIVE).count() <= 1:
                qs = super().get_queryset().filter(Q(organization=org) | Q(organization__isnull=True))
        return qs

    def create(self, request, *args, **kwargs):
        # An application without a library is invisible to every librarian, so
        # it is refused instead of being stored as an orphan.
        organization = ariza_kutubxonasi(request)
        if organization is None and not legacy_rejimmi():
            raise ValidationError(
                {
                    "error": "kutubxona_aniqlanmadi",
                    "detail": "Kutubxona aniqlanmadi. Kutubxonangiz botidan foydalaning.",
                }
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ariza = serializer.save(organization=organization)
        return Response(ArizaSerializer(ariza).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="status")
    def holat(self, request):
        telegram_id = request.query_params.get("telegram_id")
        if not telegram_id:
            raise ValidationError(
                {"error": "telegram_id_kerak", "detail": "telegram_id parametri kiritilishi shart"}
            )
        org = ariza_kutubxonasi(request)
        ariza = scope(Ariza.objects, org).filter(telegram_id=telegram_id).first()
        # Qabul qilinganlar ham eski formatdagi ariza sababli qayta yuborishi
        # kerak — bayroq Oquvchi yoki Ariza ustida turishi mumkin.
        # Ammo yangi (to'g'ri formatdagi) ariza allaqachon yuborilgan bo'lsa,
        # foydalanuvchini yana qayta yuborishga majbur qilmaymiz: ariza
        # "kutmoqda" holatida ko'rinadi va tasdiqlanishini kutadi.
        yangi_ariza_yuborildi = bool(
            ariza and ariza.holati == "kutmoqda" and not ariza.qayta_ariza_kerak
        )
        qayta_ariza_kerak = not yangi_ariza_yuborildi and (
            scope(Oquvchi.objects, org).filter(
                telegram_id=telegram_id, qayta_ariza_kerak=True
            ).exists()
            or bool(ariza and ariza.qayta_ariza_kerak)
        )
        if ariza:
            data = {
                "holati": ariza.holati,
                "izoh": ariza.izoh or "",
                "qayta_ariza_kerak": qayta_ariza_kerak,
            }
        else:
            data = {
                "holati": None,
                "izoh": "",
                "qayta_ariza_kerak": qayta_ariza_kerak,
            }
        serializer = ArizaStatusSerializer(data)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        ariza = self.get_object()
        if ariza.holati != "kutmoqda":
            raise ValidationError(
                {"error": "holat_notogri", "detail": "Faqat 'kutmoqda' holatidagi ariza tasdiqlanadi"}
            )
        # Faqat eski formatda qayta ariza yuborgan foydalanuvchigina mavjud
        # o'quvchi ustiga tasdiqlanishi mumkin.
        if scope(Oquvchi.objects, ariza.organization or self._org()).filter(
            telegram_id=ariza.telegram_id
        ).exclude(qayta_ariza_kerak=True).exists():
            raise ValidationError(
                {"error": "telegram_band", "detail": "Bu telegram akkaunt allaqachon o'quvchiga bog'langan"}
            )

        try:
            with transaction.atomic():
                # Bot arizasida kutubxona bo'sh bo'ladi — tasdiqlovchi xodimning
                # kutubxonasi o'quvchiga bog'lanadi (tenant doirasida ko'rinadi).
                org = joriy_kutubxonani_aniqla(request, required=False)
                ariza, oquvchi, yangi_karta = services.arizani_tasdiqla(
                    ariza, organization=org
                )
                services.ariza_holatini_yubor(
                    ariza, services.tasdiqlash_xabari(ariza, oquvchi, yangi_karta)
                )
        except services.ArizaTelegramBandi as xato:
            raise ValidationError({"error": "telefon_band", "detail": str(xato)})

        return Response(ArizaSerializer(ariza).data)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        ariza = self.get_object()
        if ariza.holati != "kutmoqda":
            raise ValidationError(
                {"error": "holat_notogri", "detail": "Faqat 'kutmoqda' holatidagi ariza rad etiladi"}
            )

        with transaction.atomic():
            services.arizani_rad_et(ariza, request.data.get("izoh", ""))
            services.ariza_holatini_yubor(ariza, services.rad_etilgan_xabari(ariza, ariza.izoh))

        return Response(ArizaSerializer(ariza).data)


class FanViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/subjects/ — o'qituvchi ariza berayotganda tanlaydigan fanlar ro'yxati."""

    serializer_class = FanSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    queryset = Fan.objects.filter(faol=True)
