# Kutubxona boshqaruvi

Tuman kutubxonasi uchun kitob fondi, berish-qaytarish, jarima va navbat tizimi.
Django REST Framework + PostgreSQL + Celery/Redis + aiogram 3 (Telegram bot).

## O'rnatish

1. Repozitoriyani klonlang va virtual muhit yarating:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requeriments.txt
   ```

2. PostgreSQL bazasini yarating:
   ```bash
   createdb kutubxona
   ```

3. `.env.example` faylini nusxalab, o'z qiymatlaringizni kiriting:
   ```bash
   cp .env.example .env
   ```

4. Migratsiyalarni bajaring va admin foydalanuvchi yarating:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. (Ixtiyoriy) Sinov uchun demo ma'lumot yarating:
   ```bash
   python manage.py seed_demo
   ```

## Ishga tushirish

Loyiha to'liq ishlashi uchun **4 ta jarayon** parallel ishlashi kerak (har biri alohida terminalda):

```bash
# 1) Django server
python manage.py runserver

# 2) Redis (agar mahalliy o'rnatilmagan bo'lsa, Docker orqali)
redis-server
# yoki: docker run -p 6379:6379 redis

# 3) Celery worker — jarima hisoblash va navbat vazifalarini bajaradi
celery -A config worker -l info

# 4) Celery beat — vazifalarni jadval bo'yicha ishga tushiradi
celery -A config beat -l info

# 5) Telegram bot
python bot/main.py
```

## Muhim: jarima hisoblash idempotent

`jarima.tasks.jarimalarni_hisobla` vazifasi bir necha marta ketma-ket ishga
tushirilsa ham natija o'zgarmaydi — `Jarima` OneToOne maydon orqali bazada,
`update_or_create` esa kod darajasida ikki marta yozilishning oldini oladi,
va allaqachon to'langan jarimaga tegilmaydi.

## API endpointlar

| Metod | Yo'l | Tavsif |
|---|---|---|
| POST | `/api/auth/token/` | JWT token olish |
| POST | `/api/auth/token/refresh/` | Tokenni yangilash |
| GET/POST | `/api/books/` | Kitoblar ro'yxati / qo'shish |
| GET/PATCH/DELETE | `/api/books/{id}/` | Bitta kitob |
| GET | `/api/books/search/?q=` | Qidiruv |
| GET | `/api/books/{id}/queue/` | Kitob navbati |
| GET/POST | `/api/copies/` | Nusxalar |
| GET/PATCH/DELETE | `/api/copies/{id}/` | Bitta nusxa |
| GET/POST | `/api/readers/` | O'quvchilar |
| GET/PATCH | `/api/readers/{id}/` | Bitta o'quvchi |
| POST | `/api/readers/bind/` | Bot: telegram_id bog'lash |
| GET/POST | `/api/loans/` | Berishlar |
| POST | `/api/loans/{id}/return/` | Qaytarish |
| GET | `/api/loans/my/?telegram_id=` | O'quvchining kitoblari |
| GET | `/api/loans/overdue/` | Muddati o'tganlar |
| GET/POST | `/api/reservations/` | Navbat |
| GET | `/api/reservations/my/?telegram_id=` | O'quvchining navbatlari |
| POST | `/api/reservations/{id}/respond/` | Taklifga javob |
| DELETE | `/api/reservations/{id}/` | Navbatdan chiqish |
| GET | `/api/fines/` | Jarimalar |
| GET | `/api/fines/my/?telegram_id=` | O'quvchining jarimalari |
| POST | `/api/fines/{id}/pay/` | Jarimani to'langan qilish |
| GET | `/api/stats/top-books/?limit=10` | Top kitoblar |
| GET | `/api/stats/dashboard/` | Umumiy statistika |

## Bot buyruqlari

- `/start` — kartani bog'lash (FSM)
- «Kitob qidirish», «Mening kitoblarim», «Navbatlarim», «Jarimalarim» — asosiy menyu tugmalari

## Texnologiyalar

PostgreSQL · Django REST Framework · Simple JWT · Celery + Redis · aiogram 3
