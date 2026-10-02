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

**Redis (Memurai) Windows xizmati sifatida o'rnatilgan bo'lishi kerak** — u
tizim yuklanganda avtomatik ishlay boshlaydi (port 6379).

Qolgan hammasi (Celery worker, Celery beat, Telegram bot, Django server)
**bitta buyruq bilan avtomatik** ishga tushadi:

```bash
# Windows — bir marta bosish (yaoki ikkimarta bosish):
start_all.bat

# yoki terminaldan:
powershell -ExecutionPolicy Bypass -File .\start_all.ps1

# Django va boptisiz faqat Celery+Redis kerak bo'lsa:
powershell -ExecutionPolicy Bypass -File .\start_all.ps1 -SkipBot -SkipDjango
```

Ishlashni to'xtatish:

```bash
powershell -ExecutionPolicy Bypass -File .\stop_all.ps1
```

Qo'shimcha ma'lumot:

- Jurnal fayllari: `logs/celery_worker.out.log`, `logs/celery_beat.out.log`,
  `logs/bot.out.log`, `logs/django.out.log`
- `--pool=solo` ishlatiladi (Windows uchun tavsiya etiladi)
- Redis/Memurai xizmati o'zi alohida ishlaydi, uni to'xtatish shart emas

Agar qo'lda alohida terminalda ishga tushirish kerak bo'lsa:

```bash
redis-server                                          # Redis
celery -A config worker -l info --pool=solo           # Celery worker
celery -A config beat -l info                         # Celery beat
python manage.py runserver                            # Django
python bot/main.py                                    # Telegram bot
```

## Frontend (React admin paneli)

Admin paneli `frontend/` papkasida React + TypeScript + Vite + Tailwind CSS
bilan qurilgan (avvalgi vanilla-JS `web/static/web/js` panelining o'rnini
bosadi). JWT autentifikatsiya, kitoblar/nusxalar/o'quvchilar/berish-
qaytarish/navbat/jarima/xodimlar bo'yicha to'liq CRUD interfeysini o'z
ichiga oladi.

**Ishlab chiqish rejimi** (Django serverini alohida, `python manage.py
runserver` bilan ishga tushirgan holda):

```bash
cd frontend
npm install
npm run dev
```

Bu `http://localhost:5173` da ochiladi va `/api` so'rovlarini Vite dev
serveri orqali `http://127.0.0.1:8000` ga proksi qiladi (CORS sozlash shart
emas).

**Production build** — Django shu build'ni to'g'ridan-to'g'ri xizmat
ko'rsatadi (alohida frontend server kerak emas):

```bash
cd frontend
npm run build
```

Bu buyruq: TypeScript'ni tekshiradi → `web/static/web/dist/` ga build
qiladi → chiqarilgan `index.html`'ni `web/templates/web/index.html` ga
ko'chiradi (Django'ning `IndexView` shu shablonni beradi). Shundan so'ng
`python manage.py runserver` orqali `http://127.0.0.1:8000/` da to'liq
ishlaydigan panelni ko'rasiz — React Router client-side routing uchun
`web/urls.py` `admin/` va `api/` dan boshqa barcha yo'llarni shu SPA
shell'ga yo'naltiradi.

Build natijalari (`web/static/web/dist/`, `web/templates/web/index.html`)
`.gitignore`'da — reponi klon qilganidan keyin frontend'ni ishlatish uchun
kamida bir marta `npm run build` bajarish kerak.

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
| POST | `/api/applications/` | Bot: a'rolik arizasi (o'quvchi/o'qituvchi) |
| GET | `/api/applications/status/?telegram_id=` | Bot: ariza holati |
| POST | `/api/applications/{id}/approve/` | Arizani qabul qilish (karta ochiladi) |
| POST | `/api/applications/{id}/reject/` | Arizani rad etish |
| GET | `/api/stats/top-books/?limit=10` | Top kitoblar |
| GET | `/api/stats/dashboard/` | Umumiy statistika |

## Bot buyruqlari

- `/start` — ro'yxatga olingan bo'lsa asosiy menyu; aks holda a'riza yuborish
  uchun inline tugmalar: «🎓 Oquvchi sifatida a'riza yuborish» va
  «👨‍🏫 O'qituvchi sifatida a'riza yuborish».
  Tanlangan rolga qarab so'raladigan ma'lumotlar:
  - **Oquvchi** → ism-familiya → telefon → sinf
  - **O'qituvchi** → ism-familiya → telefon → kasb (o'qitayotgan fan,
    masalan Matematika, Ona tili)
- «Kitob qidirish», «Mening kitoblarim», «Navbatlarim», «Jarimalarim» — asosiy menyu tugmalari

## Texnologiyalar

PostgreSQL · Django REST Framework · Simple JWT · Celery + Redis · aiogram 3
