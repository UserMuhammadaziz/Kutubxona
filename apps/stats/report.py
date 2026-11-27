"""Period statistics for a library: who had to return books, who did, who did not.

Used by the statistics page, its Excel download and the daily Telegram report.
"""

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from io import BytesIO
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db.models import Avg, Count, Max, Q, Sum
from django.utils import timezone

from berish.models import Berish
from jarima.models import Jarima
from kitob.models import Kitob
from navbat.models import Navbat
from organization.tenancy import scope
from oquvchi.models import Ariza, Oquvchi
from oquvchi.utils import sinf_normal

from reviews.models import Review

from .models import ReminderLog

PRESETS = ("today", "yesterday", "tomorrow", "week", "month", "custom")
MAX_PERIOD_DAYS = 366
LIST_LIMIT = 1000


def local_tz():
    return ZoneInfo(getattr(settings, "CELERY_TIMEZONE", "Asia/Tashkent"))


def local_today():
    return timezone.localtime(timezone.now(), local_tz()).date()


def resolve_period(preset, start=None, end=None, today=None):
    """Return (start, end) dates for a filter button; raises ValueError on bad input."""
    today = today or local_today()
    if preset in (None, "", "today"):
        return today, today
    if preset == "yesterday":
        day = today - timedelta(days=1)
        return day, day
    if preset == "tomorrow":
        day = today + timedelta(days=1)
        return day, day
    if preset == "week":
        monday = today - timedelta(days=today.weekday())
        return monday, monday + timedelta(days=6)
    if preset == "month":
        first = today.replace(day=1)
        next_month = (first + timedelta(days=32)).replace(day=1)
        return first, next_month - timedelta(days=1)
    if preset == "custom":
        try:
            start_date = date.fromisoformat(start)
            end_date = date.fromisoformat(end)
        except (TypeError, ValueError):
            raise ValueError("Sanalar YYYY-MM-DD ko'rinishida bo'lishi kerak.")
        if end_date < start_date:
            raise ValueError("Tugash sanasi boshlanish sanasidan oldin bo'lmasin.")
        if (end_date - start_date).days >= MAX_PERIOD_DAYS:
            raise ValueError("Davr bir yildan oshmasin.")
        return start_date, end_date
    raise ValueError("Noma'lum davr.")


def _datetime_range(start, end):
    tz = local_tz()
    return (
        datetime.combine(start, time.min, tzinfo=tz),
        datetime.combine(end + timedelta(days=1), time.min, tzinfo=tz),
    )


def _staff_name(user):
    if user is None:
        return ""
    return user.full_name or user.username


def _latest_reminders(loan_ids):
    latest = {}
    for log in ReminderLog.objects.filter(loan_id__in=loan_ids).order_by("loan_id", "-sent_at"):
        latest.setdefault(log.loan_id, log)
    return latest


def _loan_row(loan, today, reminders):
    reader = loan.oquvchi
    log = reminders.get(loan.pk)
    if log is not None:
        reminder = {
            "sent_at": timezone.localtime(log.sent_at, local_tz()).isoformat(),
            "delivered": log.delivered,
            "kind": log.kind,
        }
    elif loan.eslatma_yuborilgan:
        # Sent before reminder history existed: only the flag is known.
        reminder = {"sent_at": None, "delivered": True, "kind": ReminderLog.KIND_DUE_SOON}
    else:
        reminder = None
    if loan.qaytarilgan_sana:
        status = "on_time" if loan.qaytarilgan_sana <= loan.qaytarish_muddati else "late"
        late_days = max(0, (loan.qaytarilgan_sana - loan.qaytarish_muddati).days)
    else:
        status = "not_returned"
        late_days = max(0, (today - loan.qaytarish_muddati).days)
    return {
        "id": loan.pk,
        "reader_id": reader.pk,
        "reader": reader.fish,
        "role": reader.rol,
        "class_name": reader.sinf or "",
        "phone": reader.telefon or "",
        "telegram_linked": bool(reader.telegram_id),
        "book": loan.kitob.nomi,
        "inventory_number": loan.nusxa.inventar_raqami if loan.nusxa_id else "",
        "issued_at": loan.berilgan_sana.isoformat(),
        "due_date": loan.qaytarish_muddati.isoformat(),
        "returned_at": loan.qaytarilgan_sana.isoformat() if loan.qaytarilgan_sana else None,
        "status": status,
        "late_days": late_days,
        "issued_by": _staff_name(loan.bergan_xodim),
        "received_by": _staff_name(loan.olgan_xodim),
        "reminder": reminder,
    }


def _loans(org):
    return scope(Berish.objects, org).select_related(
        "oquvchi", "kitob", "nusxa", "bergan_xodim", "olgan_xodim"
    )


def _fine_row(fine):
    loan = fine.berish
    return {
        "id": fine.pk,
        "reader": loan.oquvchi.fish,
        "class_name": loan.oquvchi.sinf or "",
        "book": loan.kitob.nomi,
        "late_days": fine.kechikkan_kunlar,
        "amount": str(fine.summa),
        "paid": fine.tolandimi,
        "paid_at": timezone.localtime(fine.tolangan_sana, local_tz()).isoformat() if fine.tolangan_sana else None,
        "received_by": _staff_name(fine.qabul_qilgan),
    }


def _book_row(book, ratings, **extra):
    avg, count = ratings.get(book.pk, (None, 0))
    return {
        "id": book.pk,
        "title": book.nomi,
        "author": book.muallif,
        "added_at": book.qoshilgan_sana.isoformat() if book.qoshilgan_sana else None,
        "rating": round(avg, 1) if avg is not None else None,
        "rating_count": count,
        **extra,
    }


def build_book_usage(org, start, end, today):
    """Which books are read in the period, which sit on loan now, which nobody reads."""
    books = scope(Kitob.objects, org).exclude(holati="yoqolgan")
    loans = scope(Berish.objects, org)
    ratings = {
        row["book"]: (row["avg"], row["count"])
        for row in Review.objects.filter(organization=org, is_hidden=False)
        .values("book").annotate(avg=Avg("rating"), count=Count("id"))
    }

    period_counts = dict(
        loans.filter(berilgan_sana__range=(start, end)).values("kitob").annotate(n=Count("id")).values_list("kitob", "n")
    )
    last_loan = dict(loans.values("kitob").annotate(last=Max("berilgan_sana")).values_list("kitob", "last"))

    popular_books = books.filter(pk__in=period_counts)
    popular = sorted(
        (_book_row(b, ratings, loans=period_counts[b.pk]) for b in popular_books),
        key=lambda row: (-row["loans"], row["title"]),
    )[:LIST_LIMIT]

    on_loan = [
        {
            "book_id": loan.kitob_id,
            "title": loan.kitob.nomi,
            "reader": loan.oquvchi.fish,
            "class_name": loan.oquvchi.sinf or "",
            "issued_at": loan.berilgan_sana.isoformat(),
            "due_date": loan.qaytarish_muddati.isoformat(),
            "late_days": max((today - loan.qaytarish_muddati).days, 0),
        }
        for loan in loans.filter(qaytarilgan_sana__isnull=True)
        .exclude(holati="yoqolgan")
        .select_related("kitob", "oquvchi")
        .order_by("qaytarish_muddati", "kitob__nomi")[:LIST_LIMIT]
    ]

    # Books that existed during the period but were not issued in it.
    unread_qs = books.exclude(pk__in=period_counts).filter(qoshilgan_sana__lte=end).order_by("nomi")
    unread = [
        _book_row(b, ratings, last_loan=last_loan[b.pk].isoformat() if b.pk in last_loan else None)
        for b in unread_qs[:LIST_LIMIT]
    ]
    never_qs = books.exclude(pk__in=last_loan).order_by("qoshilgan_sana", "nomi")
    never = [_book_row(b, ratings) for b in never_qs[:LIST_LIMIT]]

    return {
        "summary": {
            "total": books.count(),
            "read_in_period": len(period_counts),
            "unread_in_period": unread_qs.count(),
            "never_read": never_qs.count(),
            "on_loan": len(on_loan),
        },
        "popular": popular,
        "on_loan": on_loan,
        "unread": unread,
        "never_read": never,
    }


def build_period_report(org, start, end, today=None):
    today = today or local_today()
    start_dt, end_dt = _datetime_range(start, end)
    loans = _loans(org)

    due = list(
        loans.filter(qaytarish_muddati__range=(start, end))
        .exclude(holati="yoqolgan")
        .order_by("qaytarish_muddati", "oquvchi__fish")[:LIST_LIMIT]
    )
    overdue = list(
        loans.filter(qaytarilgan_sana__isnull=True, qaytarish_muddati__lt=today)
        .exclude(holati="yoqolgan")
        .order_by("qaytarish_muddati", "oquvchi__fish")[:LIST_LIMIT]
    )
    issued = list(loans.filter(berilgan_sana__range=(start, end)).order_by("-berilgan_sana", "-pk")[:LIST_LIMIT])
    returned = list(loans.filter(qaytarilgan_sana__range=(start, end)).order_by("-qaytarilgan_sana", "-pk")[:LIST_LIMIT])

    reminders = _latest_reminders({loan.pk for loan in due + overdue})
    due_rows = [_loan_row(loan, today, reminders) for loan in due]
    overdue_rows = [_loan_row(loan, today, reminders) for loan in overdue]
    issued_rows = [_loan_row(loan, today, {}) for loan in issued]
    returned_rows = [_loan_row(loan, today, {}) for loan in returned]

    not_returned = [row for row in due_rows if row["status"] == "not_returned"]

    fines = scope(Jarima.objects, org).select_related("berish__oquvchi", "berish__kitob", "qabul_qilgan")
    new_fines = list(fines.filter(created_at__gte=start_dt, created_at__lt=end_dt)[:LIST_LIMIT])
    paid_fines = list(
        fines.filter(tolandimi=True, tolangan_sana__gte=start_dt, tolangan_sana__lt=end_dt)[:LIST_LIMIT]
    )
    unpaid = fines.filter(tolandimi=False).aggregate(total=Sum("summa"))["total"] or Decimal("0")

    queue = scope(Navbat.objects, org).filter(navbat_sanasi__gte=start_dt, navbat_sanasi__lt=end_dt)
    applications = Ariza.objects.filter(organization=org, ariza_sanasi__gte=start_dt, ariza_sanasi__lt=end_dt)
    reminder_logs = ReminderLog.objects.filter(organization=org, sent_at__gte=start_dt, sent_at__lt=end_dt)

    by_staff = defaultdict(lambda: {"issued": 0, "received": 0})
    for row in issued_rows:
        if row["issued_by"]:
            by_staff[row["issued_by"]]["issued"] += 1
    for row in returned_rows:
        if row["received_by"]:
            by_staff[row["received_by"]]["received"] += 1

    by_class = defaultdict(int)
    for row in overdue_rows:
        if row["role"] == "oquvchi":
            by_class[sinf_normal(row["class_name"]) or "—"] += 1

    return {
        "period": {"start": start.isoformat(), "end": end.isoformat(), "today": today.isoformat()},
        "summary": {
            "due": len(due_rows),
            "returned_on_time": sum(1 for row in due_rows if row["status"] == "on_time"),
            "returned_late": sum(1 for row in due_rows if row["status"] == "late"),
            "not_returned": len(not_returned),
            "overdue_total": len(overdue_rows),
            "issued": len(issued_rows),
            "returned": len(returned_rows),
            "fines_new_count": len(new_fines),
            "fines_new_amount": str(sum((f.summa for f in new_fines), Decimal("0"))),
            "fines_paid_count": len(paid_fines),
            "fines_paid_amount": str(sum((f.summa for f in paid_fines), Decimal("0"))),
            "fines_unpaid_amount": str(unpaid),
            "reservations_new": queue.count(),
            "reservations_fulfilled": queue.filter(holati="yakunlandi").count(),
            "applications_new": applications.count(),
            "applications_approved": applications.filter(holati="tasdiqlandi").count(),
            "new_readers": Oquvchi.objects.filter(organization=org, royxat_sanasi__range=(start, end)).count(),
            "reminders_sent": reminder_logs.count(),
            "reminders_delivered": reminder_logs.filter(delivered=True).count(),
        },
        "due": due_rows,
        "not_returned": not_returned,
        "overdue": overdue_rows,
        "issued": issued_rows,
        "returned": returned_rows,
        "fines_new": [_fine_row(f) for f in new_fines],
        "fines_paid": [_fine_row(f) for f in paid_fines],
        "by_staff": [
            {"name": name, **counts} for name, counts in sorted(by_staff.items(), key=lambda item: item[0])
        ],
        "by_class": [
            {"class_name": name, "overdue": count}
            for name, count in sorted(by_class.items(), key=lambda item: (-item[1], item[0]))
        ],
        "books": build_book_usage(org, start, end, today),
    }


def period_label(report):
    start, end = report["period"]["start"], report["period"]["end"]
    return start if start == end else f"{start} — {end}"


def _money(value):
    return f"{Decimal(value):,.0f}".replace(",", " ")


def _reminder_text(row):
    reminder = row["reminder"]
    if not row["telegram_linked"]:
        return "Telegram ulanmagan"
    if reminder is None:
        return "Yuborilmagan"
    return "Yuborildi" if reminder["delivered"] else "Yetib bormadi"


STATUS_LABELS = {"on_time": "Vaqtida qaytardi", "late": "Kechikib qaytardi", "not_returned": "Qaytarmadi"}


def build_report_xlsx(report, organization_name=""):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="2F6B4F")
    workbook = Workbook()

    def sheet(title, headers, rows, widths):
        ws = workbook.create_sheet(title)
        ws.append(headers)
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(vertical="center")
        for row in rows:
            ws.append(row)
        for index, width in enumerate(widths, start=1):
            ws.column_dimensions[ws.cell(row=1, column=index).column_letter].width = width
        ws.freeze_panes = "A2"
        return ws

    summary = report["summary"]
    ws = workbook.active
    ws.title = "Xulosa"
    ws.append([organization_name or "Kutubxona", f"Hisobot: {period_label(report)}"])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append([])
    lines = [
        ("Qaytarilishi kerak edi", summary["due"]),
        ("Vaqtida qaytardi", summary["returned_on_time"]),
        ("Kechikib qaytardi", summary["returned_late"]),
        ("Qaytarmadi", summary["not_returned"]),
        ("Hozir muddati o'tganlar (jami)", summary["overdue_total"]),
        ("Berilgan kitoblar", summary["issued"]),
        ("Qaytgan kitoblar", summary["returned"]),
        ("Yangi jarimalar", f"{summary['fines_new_count']} ta, {_money(summary['fines_new_amount'])} so'm"),
        ("To'langan jarimalar", f"{summary['fines_paid_count']} ta, {_money(summary['fines_paid_amount'])} so'm"),
        ("To'lanmagan jarimalar (jami)", f"{_money(summary['fines_unpaid_amount'])} so'm"),
        ("Yangi navbatlar", summary["reservations_new"]),
        ("Yangi arizalar", summary["applications_new"]),
        ("Tasdiqlangan arizalar", summary["applications_approved"]),
        ("Yangi kitobxonlar", summary["new_readers"]),
        ("Yuborilgan eslatmalar", f"{summary['reminders_sent']} ta ({summary['reminders_delivered']} tasi yetib bordi)"),
    ]
    for label, value in lines:
        ws.append([label, value])
        ws.cell(row=ws.max_row, column=1).font = Font(bold=True)
    books = report["books"]
    for label, value in [
        ("Kitoblar (jami)", books["summary"]["total"]),
        ("Davrda o'qilgan kitoblar", books["summary"]["read_in_period"]),
        ("Davrda o'qilmagan kitoblar", books["summary"]["unread_in_period"]),
        ("Hech qachon o'qilmagan", books["summary"]["never_read"]),
        ("Hozir kitobxonlar qo'lida", books["summary"]["on_loan"]),
    ]:
        ws.append([label, value])
        ws.cell(row=ws.max_row, column=1).font = Font(bold=True)
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 40

    loan_headers = ["F.I.Sh.", "Sinf", "Telefon", "Kitob", "Inventar", "Berilgan", "Muddat", "Qaytgan", "Holat", "Kechikish (kun)", "Eslatma"]
    loan_widths = [30, 8, 16, 36, 12, 12, 12, 12, 18, 14, 18]

    def loan_values(row):
        return [
            row["reader"], row["class_name"], row["phone"], row["book"], row["inventory_number"],
            row["issued_at"], row["due_date"], row["returned_at"] or "",
            STATUS_LABELS[row["status"]], row["late_days"], _reminder_text(row),
        ]

    sheet("Qaytarmaganlar", loan_headers, [loan_values(r) for r in report["not_returned"]], loan_widths)
    sheet("Muddati o'tganlar", loan_headers, [loan_values(r) for r in report["overdue"]], loan_widths)
    sheet("Qaytarilishi kerak edi", loan_headers, [loan_values(r) for r in report["due"]], loan_widths)
    sheet(
        "Berilgan",
        ["F.I.Sh.", "Sinf", "Kitob", "Inventar", "Berilgan", "Muddat", "Bergan xodim"],
        [[r["reader"], r["class_name"], r["book"], r["inventory_number"], r["issued_at"], r["due_date"], r["issued_by"]] for r in report["issued"]],
        [30, 8, 36, 12, 12, 12, 24],
    )
    sheet(
        "Qaytgan",
        ["F.I.Sh.", "Sinf", "Kitob", "Inventar", "Muddat", "Qaytgan", "Holat", "Qabul qilgan xodim"],
        [[r["reader"], r["class_name"], r["book"], r["inventory_number"], r["due_date"], r["returned_at"], STATUS_LABELS[r["status"]], r["received_by"]] for r in report["returned"]],
        [30, 8, 36, 12, 12, 12, 18, 24],
    )
    fine_rows = [
        ["Yangi", f["reader"], f["class_name"], f["book"], f["late_days"], float(f["amount"]), "Ha" if f["paid"] else "Yo'q", f["received_by"]]
        for f in report["fines_new"]
    ] + [
        ["To'landi", f["reader"], f["class_name"], f["book"], f["late_days"], float(f["amount"]), "Ha", f["received_by"]]
        for f in report["fines_paid"]
    ]
    sheet("Jarimalar", ["Tur", "F.I.Sh.", "Sinf", "Kitob", "Kechikish (kun)", "Summa (so'm)", "To'langan", "Qabul qilgan"], fine_rows, [10, 30, 8, 36, 14, 14, 10, 24])
    sheet(
        "Xodimlar",
        ["Xodim", "Bergan", "Qabul qilgan"],
        [[s["name"], s["issued"], s["received"]] for s in report["by_staff"]],
        [30, 10, 14],
    )

    def rating(row):
        return f"{row['rating']} ({row['rating_count']})" if row["rating"] is not None else ""

    sheet(
        "Ko'p o'qilgan",
        ["Kitob", "Muallif", "Berildi (marta)", "Baho"],
        [[r["title"], r["author"], r["loans"], rating(r)] for r in books["popular"]],
        [40, 28, 16, 12],
    )
    sheet(
        "Kitobxonlar qo'lida",
        ["Kitob", "F.I.Sh.", "Sinf", "Berilgan", "Muddat", "Kechikish (kun)"],
        [[r["title"], r["reader"], r["class_name"], r["issued_at"], r["due_date"], r["late_days"]] for r in books["on_loan"]],
        [40, 30, 8, 12, 12, 14],
    )
    sheet(
        "Davrda o'qilmagan",
        ["Kitob", "Muallif", "Oxirgi berilgan", "Baho"],
        [[r["title"], r["author"], r["last_loan"] or "Hech qachon", rating(r)] for r in books["unread"]],
        [40, 28, 16, 12],
    )
    sheet(
        "Hech o'qilmagan",
        ["Kitob", "Muallif", "Qo'shilgan sana"],
        [[r["title"], r["author"], r["added_at"] or ""] for r in books["never_read"]],
        [40, 28, 16],
    )

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def report_filename(report):
    start, end = report["period"]["start"], report["period"]["end"]
    suffix = start if start == end else f"{start}_{end}"
    return f"hisobot_{suffix}.xlsx"


def report_caption(report, organization_name=""):
    from config.telegram import telegram_escape

    s = report["summary"]
    return (
        f"📊 <b>{telegram_escape(organization_name)}</b> — kunlik hisobot ({period_label(report)})\n\n"
        f"📚 Berildi: <b>{s['issued']}</b> · Qaytdi: <b>{s['returned']}</b>\n"
        f"📅 Bugun qaytarilishi kerak edi: <b>{s['due']}</b>\n"
        f"   ✅ Olib keldi: {s['returned_on_time'] + s['returned_late']} · ❌ Olib kelmadi: {s['not_returned']}\n"
        f"⏰ Muddati o'tganlar (jami): <b>{s['overdue_total']}</b>\n"
        f"💰 Jarima: yangi {_money(s['fines_new_amount'])} so'm · to'landi {_money(s['fines_paid_amount'])} so'm\n"
        f"🔔 Eslatmalar: {s['reminders_sent']} ta yuborildi\n\n"
        "Batafsil ro'yxat ilova qilingan Excel faylda."
    )
