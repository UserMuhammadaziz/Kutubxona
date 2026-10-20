# KUTUBXONA — TO'LIQ QO'LLANMA

Tuman kutubxonasi uchun kitob fondi, berish-qaytarish, jarima va navbat tizimi.

**Texnologiyalar:** Django 6.1 · Django REST Framework · Simple JWT · PostgreSQL · Celery + Redis · aiogram 3 (Telegram bot) · React 19 + TypeScript + Vite + Tailwind CSS + Zustand

---

## MOQIVJA

1. [Loyiha haqida](#1-loyiha-haqida)
2. [Tuzilma](#2-tuzilma)
3. [O'rnatish](#3-o'rnatish)
4. [Ishga tushirish](#4-ishga-tushirish)
5. [Admin panel (React) — saytdan foydalanish](#5-admin-panel-react)
6. [Telegram bot](#6-telegram-bot)
7. [API qo'llanmasi](#7-api-qo'llanmasi)
8. [Celery vazifalari](#8-celery-vazifalari)
9. [Boshqaruv buyruqlari (manage.py)](#9-boshqaruv-buyruqlari)
10. [Loyiha qoidalari (sozlamalar)](#10-loyiha-qoidalari)
11. [Biznes qoidalari](#11-biznes-qoidalari)
12. [Muammolarni bartaraf etish](#12-muammolarni-bartaraf-etish)

---

## 1. Loyiha haqida

Kutubxona tizimi quyidagi ish jarayonlarini avtomatlashtiradi:

- **Kitoblar fondi** — kitoblar va ularning jismoniy nusxalari (inventar raqami bilan)
- **O'quvchi/o'qituvchilar** — Telegram bot orqali a'rolik arizasi, karta raqami berish
- **Berish/qaytarish** — kutubxonachi kitob beradi va qaytarib oladi
- **Band qilish** — mavjud bo'lmagan kitobni band qilish
- **Navbat** — hamma nusxasi band/qilingan kitob navbatida turish
- **Jarima** — muddati o'tgan kitob uchun avtomatik hisoblanadigan jarima
- **Eslatmalar** — qaytarish muddati yaqinlashganda Telegram orqali eslatma

### Asosiy oqim

```
Telegram bot ──HTTP──► Django REST API ──► services ──► PostgreSQL
                          ▲                    │
React SPA ───/api─────────┘                    └── commit'dan keyin ──► Telegram Bot API
                          ▲
Celery beat ── 5 vazifa────┘ (jarima, eslatma, navbat)
```

Muhim: **bot va Celery bazaga to'g'ridan-to'g'ri ulanmaydi** — faqat HTTP API orqali ishlaydi. Barcha xatolar yagona formatda: `{"error": kod, "detail": matn}`.

---

## 2. Tuzilma

```
Kutubxona/
├── apps/                    # Django ilovalari
│   ├── user/                # Xodimlar (kutubxonachi, administrator)
│   ├── kitob/               # Kitoblar + band qilish
│   ├── nusxa/               # Jismoniy nusxalar (inventar raqam)
│   ├── oquvchi/             # O'quvchi/o'qituvchi + Telegram arizalari
│   ├── berish/              # Berish/qaytarish
│   ├── jarima/              # Jarimalar
│   ├── navbat/              # Navbat va takliflar
│   └── stats/               # Statistika (dashboard, top kitoblar)
├── bot/                     # Telegram bot (aiogram 3)
│   ├── handlers/            # Tugmalar va buyruqlar
│   ├── api_client.py        # Django API bilan aloqa
│   ├── keyboards.py         # Tugmalar
│   └── main.py              # Ishga tushirish
├── config/                  # Django sozlamalari
│   ├── settings.py          # Asosiy sozlamalar
│   ├── celery.py            # Celery + beat jadvali
│   ├── urls.py              # API routlar
│   └── telegram.py          # Telegram xabar yuborish
├── frontend/                # React admin paneli
│   └── src/
│       ├── api/             # API client (axios)
│       ├── pages/           # Sahifalar (13 ta)
│       ├── components/      # UI komponentlar
│       ├── store/           # Zustand (auth, theme)
│       └── types/           # TypeScript tiplari
├── web/                     # Django SPA hosting
│   ├── templates/web/       # index.html (SPA shell)
│   └── static/web/dist/     # Vite build natijasi
├── logs/                    # Log fayllar
├── .env.example             # Namuna sozlamalar
├── manage.py
├── start_all.ps1            # Hammasini ishga tushirish
├── start_all.bat            # Windows uchun
└── stop_all.ps1             # Hammasini to'xtatish
```

---

## 3. O'rnatish

### 3.1 Talablar

- **Python 3.12+**
- **PostgreSQL 14+**
- **Redis** (Windows'da [Memurai](https://www.memurai.com/) tavsiya etiladi)
- **Node.js 18+** (frontend uchun)
- **Telegram Bot Token** ([@BotFather](https://t.me/BotFather) orqali olinadi)

### 3.2 Python muhiti

```bash
# Repozitoriyani klonlang
git clone <repo_url>
cd Kutubxona

# Virtual muhit yarating
python -m venv venv

# Faollashtirish
venv\Scripts\activate          # Windows
# source venv/bin/activate    # Linux/Mac

# Bog'liqliklarni o'rnatish
pip install -r requirements.txt
```

> **Eslatma:** `requeriments.txt` ham mavjud (eski nom), lekin to'g'ri fayl — `requirements.txt`.

### 3.3 PostgreSQL bazasi

```bash
# PostgreSQL'ga kiring va bazani yarating
psql -U postgres
CREATE DATABASE kutubxona;
\q
```

### 3.4 .env fayli

`.env.example` faylini nusxalab, o'z qiymatlaringizni kiriting:

```bash
cp .env.example .env
```

`.env` fayl mazmuni:

```env
# Django
SECRET_KEY=django-insecure-o-zgartiring-buni   # Almashing!
DEBUG=True                                      # Production'da False qiling
ALLOWED_HOSTS=127.0.0.1,localhost

# PostgreSQL
DB_NAME=kutubxona
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Telegram bot
TELEGRAM_BOT_TOKEN=0000000000:AA...            # BotFather'dan oling
BOT_API_BASE_URL=http://127.0.0.1:8000/api
BOT_SERVICE_USERNAME=bot_service               # Bot uchun maxsus akkaunt
BOT_SERVICE_PASSWORD=kuchli-tasodifiy-parol    # Kuchli parol qo'ying!
BOT_ADMIN_CHAT_IDS=123456789,987654321         # Kutubxonachilar Telegram ID

# Loyiha qoidalari
MUDDAT_KUN=14                                  # Kitob berish muddati (kun)
KUNLIK_JARIMA=5000                             # Kunlik jarima (so'm)
LIMIT_KITOB=3                                  # Bir vaqtda olish mumkin bo'lgan kitoblar soni
TAKLIF_SOAT=24                                 # Navbat taklifi amal qilish muddati (soat)
ESLATMA_KUNLAR_OLDIN=2                         # Qaytarish oldin necha kun eslatma
JARIMA_ESLATMA_TAKROR_SOAT=24                  # Jarima eslatmasi takror oralig'i
```

### 3.5 Migratsiyalar va boshlang'ich ma'lumotlar

```bash
python manage.py migrate
python manage.py createsuperuser               # Admin panel uchun
python manage.py seed_service_account          # Bot uchun xizmat akkaunti
```

### 3.6 (Ixtiyoriy) Demo ma'lumotlar

```bash
python manage.py seed_demo
```

Bu quyidagilarni yaratadi:
- `kutubxonachi_demo` (parol: `demo12345`) — kutubxonachi
- 2 ta kitob + 2 ta nusxa (inventar: INV-000001, INV-000002)
- 4 ta o'quvchi
- 1 ta muddati o'tgan berish
- 2-kitob uchun navbatda 3 kishi

---

## 4. Ishga tushirish

### 4.1 Tez ishga tushirish (tavsiya etiladi)

Redis (Memurai) Windows xizmati sifatida o'rnatilgan bo'lishi kerak — u tizim yuklanganda avtomatik ishlay boshlaydi (port 6379).

Qolgan hammasi **bitta buyruq bilan** avtomatik ishga tushadi:

```bash
# Windows — bir marta bosish
start_all.bat

# yoki terminaldan
powershell -ExecutionPolicy Bypass -File .\start_all.ps1

# Django va botsiz faqat Celery+Redis kerak bo'lsa
powershell -ExecutionPolicy Bypass -File .\start_all.ps1 -SkipBot -SkipDjango

# Faqat Django server
powershell -ExecutionPolicy Bypass -File .\start_all.ps1 -SkipBot
```

### 4.2 To'xtatish

```bash
powershell -ExecutionPolicy Bypass -File .\stop_all.ps1
```

### 4.3 Qo'lda ishga tushirish (har birini alohida terminalda)

```bash
# 1. Redis (agar xizmat sifatida o'rnatilmagan bo'lsa)
redis-server

# 2. Celery worker (jarima, navbat, eslatma vazifalari)
celery -A config worker -l info --pool=solo

# 3. Celery beat (jadval bo'yicha ishlash)
celery -A config beat -l info

# 4. Django server
python manage.py runserver

# 5. Telegram bot
python bot/main.py
```

> **Windows uchun muhim:** Celery'da `--pool=solo` ishlatish tavsiya etiladi.

### 4.4 Log fayllari

| Fayl | Nima yoziladi |
|---|---|
| `logs/django.out.log` | Django server |
| `logs/django.err.log` | Django xatolari |
| `logs/celery_worker.out.log` | Celery worker |
| `logs/celery_worker.err.log` | Celery xatolari |
| `logs/celery_beat.out.log` | Celery beat |
| `logs/bot.out.log` | Telegram bot |
| `logs/bot.err.log` | Bot xatolari |

Muammo bo'lsa, avval shu fayllarni tekshiring:

```bash
# Oxirgi xatolarni ko'rish
Get-Content logs\django.err.log -Tail 50
Get-Content logs\bot.err.log -Tail 50
```

### 4.5 Tekshirish

Ishga tushirishdan keyin tekshiring:

1. **Django:** `http://127.0.0.1:8000/` — admin panel ochilishi kerak
2. **Admin:** `http://127.0.0.1:8000/admin/` — Django admin
3. **Bot:** Telegram'da botni oching, `/start` yozing — javob kelishi kerak
4. **Redis:** `redis-cli ping` — `POTONG` javobi kelishi kerak

---

## 5. Admin panel (React)

### 5.1 Ishlab chiqish rejimi

Django serverini alohida ishga tushirgan holda (`python manage.py runserver`):

```bash
cd frontend
npm install
npm run dev
```

Bu `http://localhost:5173` da ochiladi va `/api` so'rovlarini Vite dev serveri orqali `http://127.0.0.1:8000` ga proksi qiladi (CORS sozlash shart emas).

### 5.2 Production build

```bash
cd frontend
npm run build
```

Bu buyruq:
1. TypeScript'ni tekshiradi
2. `web/static/web/dist/` ga build qiladi
3. `index.html`'ni `web/templates/web/index.html` ga ko'chiradi

Shundan so'ng `python manage.py runserver` orqali `http://127.0.0.1:8000/` da to'liq ishlaydigan panelni ko'rasiz.

> **Muhim:** Build natijalari `.gitignore`'da — repozitoriyani klon qilganidan keyin frontend'ni ishlatish uchun **kamida bir marta** `npm run build` bajarish kerak.

### 5.3 Sahifalar

| Sahifa | Yo'l | Vazifasi |
|---|---|---|
| **Kirish** | `/login` | JWT orqali kirish |
| **Boshqaruv paneli** | `/` | Umumiy statistika, top kitoblar |
| **Kitoblar** | `/books` | Kitoblar qo'shish/tahrirlash/o'chirish |
| **Kitob tafsiloti** | `/books/:id` | Bitta kitob, nusxalar, navbat |
| **Nusxalar** | `/copies` | Jismoniy nusxalar (inventar raqam) |
| **O'quvchilar** | `/readers` | O'quvchilar ro'yxati |
| **O'quvchi tafsiloti** | `/readers/:id` | O'quvchi + kitoblari + jarimalari |
| **O'qituvchilar** | `/teachers` | O'qituvchilar ro'yxati |
| **Arizalar** | `/applications` | Telegram arizalarni tasdiqlash/rad etish |
| **Berish/Qaytarish** | `/loans` | Kitob berish va qaytarish |
| **Bandlar** | `/bandlar` | Band so'rovlarini boshqarish |
| **Navbatlar** | `/reservations` | Navbatlar ro'yxati |
| **Jarimalar** | `/fines` | Jarimalarni ko'rish/to'lash |
| **Xodimlar** | `/staff` | Xodimlar CRUD (faqat admin) |

### 5.4 Saytdan foydalanish — bosqichma-bosqich to'liq qo'llanma

#### 5.4.1 Tizimga kirish

1. Saytni oching (`http://127.0.0.1:8000/` yoki `https://kutubxona.sharqsoft.uz`)
2. Avtomatik ravishda **/login** sahifasiga tashlanadi
3. **Foydalanuvchi nomi** va **Parol** ni kiriting
4. **Kirish** tugmasini bosing

> Agar login/parol noto'g'ri bo'lsa, qizil xatolik banneri paydo bo'ladi. Birinchi marta kirish uchun `python manage.py createsuperuser` bilan yaratilgan hisobdan foydalaning.

**Chiqish:** Chap paneldagi pastki qismdagi **"Chiqish"** tugmasi.

**Mavzu almashtirish:** Yuqori qismdagi 🌙 (qorong'i) / ☯️ (yorug') tugmasi bilan rejimni almashtirasiz.

---

#### 5.4.2 Boshqaruv paneli (Dashboard) — `/`

Saytga kirganingizda birinchi ochiladigan sahifa. Bu **ko'rish** sahifasi — o'zgartirish mumkin emas.

**8 ta ko'rsatkich kartasi:**

| Kartacha | Nima ko'rsatadi | Rangi |
|---|---|---|
| Jami kitoblar | Katalogdagi kitoblar soni | Ko'k |
| Jami nusxalar | Barcha jismoniy nusxalar | Ko'k |
| Mavjud nusxalar | Hozir berishga yaroqli nusxalar | Yashil |
| Berilgan nusxalar | O'quvchi qo'lidagi nusxalar | Ko'k |
| Muddati o'tgan berishlar | Kechiktirilgan kitoblar | **Qizil** |
| Faol navbatlar | Navbatda turganlar | Ko'k |
| To'lanmagan jarimalar | Qarzdorlar soni | **Sariq** |
| Umumiy qarzdorlik | Jami qarz (so'mda) | **Sariq** |

> **Maslahat:** Muddati o'tgan, navbat yoki jarima kartochkalarini bosishingiz mumkin — tegishli bo'limga tez o'tasiz.

**"Eng ko'p o'qilgan kitoblar"** — 10 tagacha kitob nomi, muallifi va necha marta berilgani ko'rsatiladi. Qaysi kitoblar ommalashganini shu yerdan bilasiz.

**Kunlik tartib:**
1. Dashboard'ni oching — umumiy holatni ko'ring
2. Qizil/sariq kartochkalarni bosib, muammolarni ko'ring
3. Arizalarni tekshiring
4. Berish/Qaytarish bilan ishlashni boshlang

---

#### 5.4.3 Kirish (Login) — `/login`

**Maydonlar:**
- **Foydalanuvchi nomi** — majburiy
- **Parol** — majburiy

**Tugma:** **Kirish** (yuklanayotganda "Kirilmoqda..." deb ko'rinadi)

Xatolik: Login/parol noto'g'ri bo'lsa, forma tepasida qizil banner chiqadi.

---

#### 5.4.4 Kitoblar — `/books`

Katalogdagi barcha kitoblarni ko'rish, qo'shish, tahrirlash va o'chirish.

**Filtr / qidiruv:**
- **Qidiruv maydoni** — "Nomi, muallif yoki ISBN bo'yicha qidirish..." (yozishni boshlaganingizda avtomatik qidiradi)
- **Janr select** — "Barcha janrlar" / Badiiy / Ilmiy / Darslik / Bolalar / Tarixiy / Boshqa

> Qidiruv faol bo'lganda janr filtri o'chiriladi — avval nom bo'yicha qidirasiz, keyin natijani janr bo'yicha saralaysiz.

**Jadval ustunlari:** Nomi (ISBN ostida) · Muallif · Janr · Til · Nashriyot · Yil · Narhi · Buyurtma · Holati · Nusxalar (`mavjud/jami`) · Band · Harakatlar

**Holat badge'lari:**
- 🟢 **Mavjud** — kamida bitta nusxa bor
- 🔵 **Berilgan** — hamma nusxa hozir o'quvchi qo'lidа
- 🔴 **Yo'qolgan**

**Nusxalar soni:** 0 bo'lsa qizil, 0 dan katta bo'lsa yashil. Faol navbat bo'lsa sariq "N ta navbat" chiqadi.

**Yangi kitob qo'shish:**
1. **"+ Yangi kitob"** tugmasini bosing
2. Maydonlarni to'ldiring:

| Maydon | Majburiy | Izoh |
|---|---|---|
| Nomi | ✅ | Kitob nomi |
| Muallif | ✅ | Muallif ismi |
| ISBN | ❌ | Mavjud bo'lmasa bo'sh qoldiring |
| Janr | ✅ | Standart: Badiiy |
| Nashr yili | ✅ | 1400–joriy yil |
| Til | ❌ | O'zbek (lotin), Kirill, Rus, Ingliz, Boshqa |
| Narhi (so'm) | ❌ | 0 dan katta |
| Holati | ✅ | Mavjud / Yo'qolgan (Berilgan tizim avtomatik boshqaradi) |
| Buyurtma soni | ❌ | 0 dan katta |
| Nashriyot | ❌ | Matn |
| Tavsif | ❌ | 3 qatorli |

3. **Saqlash** → "Kitob qo'shildi." xabari

> ⚠️ **Muhim:** Kitob qo'shgandan keyin **Nusxalar** bo'limida kamida bitta nusxa qo'shishingiz kerak — aks holda u "asli" sifatida beriladi.

**Kitobni tahrirlash:** Har bir qatordagi **Tahrirlash** tugmasi → forma avval joriy qiymatlar bilan to'ldiriladi → o'zgartirib **Saqlash**.

**Kitobni o'chirish:** **O'chirish** (qizil) → tasdiqlash oynasi:
- "**[kitob nomi]** kitobini ro'yxatdan o'chiramoqchimisiz?"
- Agar faol navbat bo'lsa: "Bu kitobga **N ta faol navbat** bor — ular ham bekor qilinadi."
- **O'chirish** / **Bekor qilish**

**Navbatni boshqarish:** Faol navbat bo'lsa qatordagi **Navbat** tugmasi → modali ochiladi:
- O'quvchi · Navbat sanasi · Holati · Harakatlar
- Har bir qatorda **Bekor qilish** — tasdiqlanganda keyingi o'quvchiga taklif yuboriladi

---

#### 5.4.5 Kitob tafsiloti — `/books/:id`

Bitta kitob haqida to'liq ma'lumot. **Ko'rish** sahifasi — o'zgartirish yo'q.

**Tugmalar:** ← Orqaga · Nusxalarni boshqarish (→ `/copies`)

**Chapdagi ma'lumot karta:** ISBN · Janr · Til · Holati · Narhi · Buyurtma · Nashriyot · Qo'shilgan sana · Tavsif

**Uchta jadval:**
1. **Nusxalar** — Inventar № · Holati · Javon
2. **Navbat** — O'quvchi · Holati · Sana (faqat navbat bo'lsa)
3. **Band qilingan so'rovlar** — O'quvchi · Holati · Sana · Izoh (faqat bo'lsa)

---

#### 5.4.6 Nusxalar — `/copies`

Har bir kitobning **jismoniy nusxalarini** (inventar raqam bilan) boshqarish.

**Filtr:** Holat bo'yicha — "Barcha holatlar" / Mavjud / Berilgan / Band / Ta'mirda / Yo'qolgan

**Jadval ustunlari:** Kitob · Inventar № · Javon · Holati · Harakatlar

**Holat badge'lari:** 🟢 Mavjud · 🔵 Berilgan · 🟡 Band / Ta'mirda · 🔴 Yo'qolgan

**Harakat tugmalari (holatga bog'liq):**

| Tugma | Qachon chiqadi | Nima qiladi |
|---|---|---|
| **Ta'mirga berish** | Faqat "Mavjud" bo'lsa | Holat → "Ta'mirda" |
| **Qaytarish** | Faqat "Ta'mirda" bo'lsa | Holat → "Mavjud" |
| **Yo'qolgan deb belgilash** | Faqat "Mavjud" bo'lsa | Holat → "Yo'qolgan" |
| **O'chirish** | Faqat "Mavjud" bo'lsa | Butunlay ro'yxatdan o'chirish |

**Yangi nusxa qo'shish:**
1. **"+ Yangi nusxa"** tugmasi
2. Maydonlar:

| Maydon | Majburiy | Izoh |
|---|---|---|
| Kitob | ✅ | "Kitobni tanlang" — ro'yxatdan tanlang |
| Inventar raqami | ✅ | Masalan: `INV-000001` |
| Javon | ❌ | Masalan: `A-3` |
| Izoh | ❌ | Matn |

3. **Saqlash**

> ⚠️ **Muhim:** Nusxa qo'shilsa yoki ta'mirdan chiqsa, avtomatik ravishda navbatdagi birinchi odamga Telegram orqali taklif yuboriladi.

---

#### 5.4.7 O'quvchilar / O'qituvchilar — `/readers` va `/teachers`

Kutubxona a'zolarini boshqarish. Ikkala sahifa bir xil, faqat roli boshqacha.

**Qidiruv:** "Ism, telefon yoki karta raqami bo'yicha qidirish..."

**Jadval ustunlari:** F.I.Sh. (bosilganda tafsilotga o'tadi) · Sinf (o'qituvchilar uchun "Fan") · Telefon · Karta raqami · Holati · Harakat

**Holat:** 🟢 Faol · 🔴 Bloklangan

**Yangi o'quvchi qo'shish:**
1. **"+ Yangi o'quvchi"** tugmasi
2. Maydonlar:

| Maydon | Majburiy | Izoh |
|---|---|---|
| To'liq ismi (F.I.Sh.) | ✅ | Masalan: Aliyev Vali |
| Telefon raqami | ✅ | `+998` bilan oldindan to'ldirilgan |
| Sinf (yoki Fan) | ✅ (o'qituvchi uchun) | Masalan: `7-A` / `Matematika` |
| Tug'ilgan sana | ❌ | Sana tanlash |
| Manzil | ❌ | Matn |

3. **Saqlash** → toast xabar: "Ism ro'yxatga qo'shildi. Karta: **LIB-2026-0001**"

> 💡 **Karta raqami avtomatik beriladi** — qo'lda yozish shart emas. Toast xabarda ko'rsatiladi, o'quvchiga bering.

**Bloklash/Faollashtirish:** Har bir qatordagi **Bloklash** / **Faollashtirish** tugmasi — bir bosishda amalga oshadi.

---

#### 5.4.8 O'quvchi tafsiloti — `/readers/:id`

Bitta o'quvchi haqida to'liq ma'lumot. **Kitob qaytarish va jarima to'lash shu yerdan.**

**Sarlavha yonida:** O'qituvchi bo'lsa ko'k badge + Faol/Faol emas badge

**Chapdagi shaxsiy ma'lumotlar karta:**
- Sinf (yoki Fan)
- Ro'yxatdan o'tgan sana
- Tug'ilgan sana
- Manzil
- Telegram (`#telegram_id` yoki "Bog'lanmagan")

**Joriy kitoblar jadvali:**

| Ustun | Nima ko'rsatadi |
|---|---|
| Kitob | Kitob nomi |
| Berilgan | Berilgan sana |
| Muddat | Qaytarish muddati |
| Qolgan kun | 🔴 Manfiy = muddati o'tgan · 🟡 2 kundan kam · 🟢 Xavfsiz |
| Harakat | **Qaytarish** tugmasi |

**To'lanmagan jarimalar jadvali:**

| Ustun | Nima ko'rsatadi |
|---|---|
| Kitob | Jarima sabab bo'lgan kitob |
| Kechikkan kun | Necha kun kechiktirilgan |
| Summa | Qarz miqdori (qizil) |
| Harakat | **To'landi deb belgilash** tugmasi |

**Kitob qaytarish:**
1. **Qaytarish** tugmasini bosing
2. Tasdiqlash oynasi: "**[kitob]** kitobini **[o'quvchi]** dan qaytarasizmi? Muddat o'tganda jarima avtomatik hisoblanadi."
3. **Qaytarish** → toast: "Kitob qaytarildi. Jarima: N so'm" yoki "Jarima yo'q"
4. Agar kitob band bo'lsa: "Kitob band bo'lgani uchun navbatdagi o'quvchiga taklif yuborildi."

**Jarimani to'lash:**
1. **To'landi deb belgilash** tugmasi
2. Tasdiqlash: "**[summa]** jarimani to'langan deb belgilaysizmi?"
3. **To'langan deb belgilash** → o'quvchiga Telegram xabar yuboriladi

---

#### 5.4.9 Arizalar — `/applications`

Telegram bot orqali kelgan a'zolik arizalarini ko'rib chiqish.

**Filtr / qidiruv (3 ta maydon):**
1. **Qidiruv** — "Ism, telefon yoki Telegram ID bo'yicha qidirish..."
2. **Rol** — "Barcha rollar" / O'quvchi / O'qituvchi
3. **Holat** — "Barcha holatlar" / Kutmoqda / Tasdiqlandi / Bekor

> **Standart holat: "Kutmoqda"** — dastlab faqat kutilayotgan arizalar chiqadi.

**Jadval ustunlari:** F.I.Sh. (Telegram ID ostida) · Rol · Sinf/Kasb · Telefon · Holati · Sana · Harakatlar

**Arizani qabul qilish:**
1. Ariza ma'lumotlarini o'qing (Ism, telefon, sinf/kasb, Telegram ID)
2. **Qabul qilish** tugmasini bosing
3. Tasdiqlash oynasi: "[Ism] arizasini qabul qilib, **ro'yxatga** qo'shasizmi? Karta raqami avtomatik beriladi va Telegram orqali tasdiqlash xabari yuboriladi."
4. **Qabul qilish** → o'quvchi yaratiladi, karta raqami beriladi, Telegram'ga xabar ketadi

**Arizani rad etish:**
1. **Rad etish** (qizil) tugmasi
2. Alohida modal oyna ochiladi
3. **Sabab** yozing (ixtiyoriy, 255 belgi) — "Sabab o'quvchiga Telegram orqali yuboriladi" izohi bilan
4. **Rad etish** → sabab Telegram'ga yuboriladi

---

#### 5.4.10 Berish / Qaytarish — `/loans`

**Asosiy ish o'rni** — kunlik eng ko'p ishlatiladigan bo'lim.

**Filtr:** "Barcha holatlar" / Faol / Qaytarilgan / Yo'qolgan

**Jadval ustunlari:** Kitob (inventar № yoki "Asli kitob") · O'quvchi · Berilgan · Muddat · Holati · Harakat

**Kitob berish (bosqichma-bosqich):**
1. **"+ Kitob berish"** tugmasi
2. **O'quvchini qidirish** maydoni — "Ism, sinf yoki telefon..." yozing
3. **O'quvchi select** — natijadan tanlang ("Ism — 7-sinf — +99890...")
4. **Kitobni qidirish** maydoni — "Kitob nomi, muallif yoki ISBN..." yozing
5. **Kitob select** — variantda nusxa holati ko'rsatiladi:
   - `(2/5 nusxa)` — 5 tadan 2 tasi mavjud
   - `(asli)` — nusxasi yo'q, asli beriladi
   - `(barcha nusxalar band)` — hozircha berilmaydi
6. **Ma'lumot bannerini** o'qing:
   - 🟢 "Beriladi: mavjud nusxa (N ta mavjud / jami M)"
   - 🟡 "Beriladi: kitob asli (bu kitobning umuman nusxasi yo'q)"
   - 🟡 "Hozircha barcha nusxalar band (N ta). O'quvchi navbatga qo'shiladi."
7. **Ixtiyoriy:** "Aniq nusxani qo'lda tanlash" ni belgilang → inventar raqamini tanlash mumkin
8. **Berish** tugmasi

**Muhim xatti-harakatlar:**
- Barcha nusxalar band bo'lib berishga urinilsa, **bu xato emas** — o'quvchi avtomatik navbatga qo'shiladi
- Muvaffaqiyatli berishdan keyin toast: "Kitob berildi (inventar №). O'quvchiga Telegram orqali xabar yuborildi."

**Kitob qaytarish:**
1. Faol qatordagi **Qaytarish** tugmasi
2. Tasdiqlash oynasi: "**[kitob]** kitobini **[o'quvchi]** dan qaytarasizmi? Muddat o'tganda jarima avtomatik hisoblanadi."
3. **Qaytarish** → toast: "Jarima: N so'm" yoki "Jarima yo'q"
4. Navbatdagi o'quvchi bo'lsa qo'shimcha: "navbatdagi o'quvchiga taklif yuborildi"

---

#### 5.4.11 Bandlar — `/bandlar`

O'quvchi tomonidan kitob **band qilish** so'rovlarini boshqarish.

**Filtr / qidiruv:**
1. **Qidiruv** — "Kitob ID bo'yicha..." (faqat raqam)
2. **Holat** — "Barcha holatlar" / Kutmoqda / Tasdiqlandi / Rad etildi / Bekor qilindi
3. O'ngda: "Jami: N ta so'rov"

> **Standart holat: "Kutmoqda"**

**Jadval ustunlari:** So'rov (ID) · Kitob (nomi + muallif) · So'ragan o'quvchi (rol + sinf) · Holati · So'rov sanasi · Tasdiqlovchi · Harakat

**Bandni tasdiqlash:**
1. **Tasdiqlash** (ko'k) tugmasi
2. Tasdiqlash oynasi ochiladi:
   - Kitob, so'ragan o'quvchi, holat, sana ko'rsatiladi
   - Eslatma: "Tasdiqlanganda kitob so'rov qilgan o'quvchiga beriladi va unga qaytarish muddati bilan xabar yuboriladi."
   - O'quvchining sababi (izoh) ko'rinadi
3. **Izoh** yozing (ixtiyoriy) — masalan: "3-sinf darsiga tayyorlanmoqda..."
4. **Tasdiqlash** → kitob avtomatik o'quvchiga beriladi, Telegram'ga xabar ketadi

**Bandni rad etish:**
1. **Rad etish** (qizil) tugmasi
2. Alohida oyna: sabab izohi yozing — masalan: "hozircha bitta nusxa bor, keyinroq taklif qilamiz..."
3. **Rad etish** → kitob yana berishga ochiq bo'ladi

---

#### 5.4.12 Navbatlar — `/reservations`

Kitob mavjud bo'lmaganda o'quvchilarning navbatini kuzatish.

**Filtr:** "Barcha holatlar" / Kutmoqda / Taklif qilindi / Yakunlandi / Bekor

**Jadval ustunlari:** Kitob · O'quvchi · Navbat sanasi · Holati · Taklif javobi · Harakat

**Holat badge'lari:**
- 🟡 **Kutmoqda** — navbatda turibdi
- 🔵 **Taklif qilindi** — nusxa ajratildi, javob kutilmoqda
- 🟢 **Yakunlandi** — kitob berildi
- 🔴 **Bekor** — navbat bekor qilindi

**Taklif javobi ustuni:** O'quvchi javob bergandan keyin ko'rinadi:
- 🟢 "Olaman" — taklif muddati bilan
- 🔴 "Kerak emas" — keyingisiga o'tadi

**Navbatni tasdiqlash (kitobni berish):**
1. "Taklif qilindi" holatini tanlab, javobni ko'ring
2. O'quvchi kelib olganda **Tasdiqlash** tugmasi
3. Tasdiqlash: "**[kitob]** kitobini **[o'quvchi]** ga berdingizmi? Navbat yakunlanadi va ajratilgan nusxa «mavjud» holatiga qaytariladi."
4. **Tasdiqlash** → kitob beriladi, navbat yakunlanadi

**Navbatni bekor qilish:**
1. **Bekor qilish** (qizil) tugmasi
2. Tasdiqlash: "Keyingi navbatdagi o'quvchiga taklif yuboriladi."
3. Agar o'quvchi "olaman" deb javob bergan bo'lsa, qo'shimcha ogohlantirish chiqadi

---

#### 5.4.13 Jarimalar — `/fines`

Kechiktirib qaytarilgan kitoblar uchun jarimalarni boshqarish.

**Filtr:** "Barchasi" / "To'lanmagan" / "To'langan"

**Jadval ustunlari:** O'quvchi · Kitob · Kechikkan kun · Summa · Holati · Harakat

**Holat:** 🟢 To'langan · 🔴 To'lanmagan

**Jarimani to'lash:**
1. Filtrda "To'lanmagan" ni tanlab qarzdorlarni ko'ring
2. **To'landi** tugmasini bosing
3. Tasdiqlash: "**[o'quvchi]** uchun **[summa]** jarimani to'langan deb belgilaysizmi? O'quvchiga Telegram orqali tasdiqlash xabari yuboriladi."
4. **To'langan deb belgilash** → Telegram'ga xabar ketadi

> Dashboard'dagi "To'lanmagan jarimalar" kartochkasini bosib shu yerga to'g'ridan-to'g'ri o'tasiz.

---

#### 5.4.14 Xodimlar — `/staff` (faqat administrator)

Kutubxonachi va administrator hisoblarini boshqarish. **Faqat administrator** ko'ra oladi.

**Filtr yo'q** — barcha xodimlar bitta ro'yxatda.

**Jadval ustunlari:** F.I.Sh. · Foydalanuvchi nomi (@username) · Lavozim · Telefon · Holati · Harakat

**Lavozim badge'lari:** 🔵 Administrator · ⚪ Kutubxonachi

**Yangi xodim qo'shish:**
1. **"+ Yangi xodim"** tugmasi
2. Maydonlar:

| Maydon | Majburiy | Izoh |
|---|---|---|
| To'liq ismi | ✅ | F.I.Sh. |
| Foydalanuvchi nomi | ✅ | Login (unique) |
| Parol | ✅ | Xodimga bering |
| Lavozim | ✅ | Kutubxonachi / Administrator (standart: Kutubxonachi) |
| Telefon | ❌ | `+998 ...` |

3. **Saqlash** → xodimga login/parolni bering

**Xodimni bloklash:** **Bloklash** tugmasi → tasdiqlash: "Kirishidan mahrum qilinsinmi?" → ma'lumotlar saqlanadi, faqat kirish o'chadi.

---

#### 5.4.15 Umumiy qoidalar (barcha sahifalarga tegishli)

| Xususiyat | Tushuntirish |
|---|---|
| **Yuklanish** | Har bir sahifa ochilayotganda skelet (skeleton) ko'rinadi |
| **Xatolik** | "Qayta urinish" (retry) tugmasi chiqadi |
| **Bo'sh holat** | "Ma'lumot yo'q" kartochkasi chiqadi |
| **Muvaffaqiyat** | O'ng yuqori burchakda toast (habar) paydo bo'ladi |
| **Sahifalash** | Ro'yxatlar pastda sahifa raqamlari bilan (20 tadan) |
| **Keng/kiyin ekran** | Keng ekranda jadval, kichik ekranda karta ko'rinishi |
| **Qidiruv** | Har harfda so'rov yuborilmaydi — biroz kutiladi (debounce) |
| **O'chirish/Tasdiqlash** | Har doim tasdiqlash oynasi chiqadi |
| **Mavzu** | 🌙 qorong'i / ☯️ yorug' rejim |

#### 5.4.16 Kunlik ish tartibi (tavsiya etiladi)

1. **Dashboard** oching — umumiy holatni ko'ring (qizil/sariq kartochkalar)
2. **Arizalar** — Telegram'dan kelgan arizalarni tasdiqlang
3. **Berish/Qaytarish** — kunlik asosiy ish
4. **Bandlar** — kutilayotgan band so'rovlarini tasdiqlang/rad eting
5. **Navbatlar** — takliflarni kuzating, o'quvchi kelganda tasdiqlang
6. **Jarimalar** — naqd pul kelgan bo'lsa yoping

> **Eslatma:** Berish, qaytarish, ariza tasdiqlash, jarima to'lash va navbat takliflari — barchasi **Telegram orqali avtomatik** xabar yuboradi. Qo'lda xabar yuborish shart emas.

---

## 6. Telegram bot

### 6.1 Bot yaratish

1. Telegram'da [@BotFather](https://t.me/BotFather) ga kiring
2. `/newbot` buyrug'ini yuboring
3. Bot nomini kiriting
4. Username kiriting (masalan `kutubxona_bot`)
5. **Token** olasiz — uni `.env` faylidagi `TELEGRAM_BOT_TOKEN` ga qo'ying

### 6.2 Botni ishga tushirish

```bash
python bot/main.py
```

yoki `start_all.bat` orqali avtomatik.

### 6.3 Bot buyruqlari

| Buyruq | Vazifasi |
|---|---|
| `/start` | Ro'yxatdan o'tish yoki asosiy menyu |
| `/menu` | Asosiy menyu |
| `/qidiruv` | Kitob qidirish |
| `/kategoriyalar` | Janrlar bo'yicha qidirish |
| `/kitoblarim` | Mening kitoblarim |
| `/navbatlarim` | Mening navbatlarim |
| `/bandlarim` | Mening bandlarim |
| `/jarimalarim` | Mening jarimalarim |
| `/yordam` | Yordam |
| `/bekor` | Joriy amalni bekor qilish |
| `/bandlar` | (Kutubxonachi) Band so'rovlarini ko'rish |
| `/qaytar` | (Kutubxonachi) Kitob qaytarish |

### 6.4 Botdan foydalanish oqimi

#### Birinchi marta foydalanuvchi (aro'lik arizasi)

1. Botga `/start` yuboring
2. Rolni tanlang: **O'quvchi** yoki **O'qituvchi**
3. Ma'lumotlarni kiriting:
   - **O'quvchi** → Ism-familiya → Telefon → Sinf
   - **O'qituvchi** → Ism-familiya → Telefon → Kasb (o'qitayotgan fan)
4. Ariza yuboriladi — kutubxonachidan tasdiq kutiladi
5. Tasdiqlangandan keyin karta raqami beriladi

#### Asosiy menyu tugmalari

- 🔍 **Kitob qidirish** — matn orqali qidirish
- 📚 **Kategoriyalar** — janrlar bo'yicha
- 📚 **Mening kitoblarim** — joriy berilgan kitoblar
- ⏳ **Navbatlarim** — navbatdagi kitoblar
- 🔖 **Bandlarim** — band qilingan kitoblar
- 💰 **Jarimalarim** — to'lanmagan jarimalar
- ❓ **Yordam** — bot haqida ma'lumot

#### Kitob qidirish va band qilish

1. **Kitob qidirish** tugmasi bosing yoki `/qidiruv` yozing
2. Kitob nomini yozing
3. Natijalardan kitobni tanlang
4. Agar mavjud nusxa bo'lsa → **Berish** mumkin
5. Agar hammasi band/qilingan bo'lsa → **Navbatga turish** yoki **Band qilish**

#### Navbat taklifiga javob berish

Kutubxona nusxa qaytarganda bot xabar yuboradi:
- **Olaman** — kitob ajratiladi
- **Kerak emas** — keyingi odamga o'tadi

> Taklif 24 soat amal qiladi. Javob berilmasa, keyingi odamga o'tadi.

### 6.5 Kutubxonachi uchun bot

`BOT_ADMIN_CHAT_IDS` ga Telegram ID'si kiritilgan xodimlar quyidagi qo'shimcha imkoniyatlarga ega:

- `/bandlar` — band so'rovlarini tasdiqlash/rad etish
- `/qaytar` — inventar raqam orqali kitob qaytarish

Telegram ID'ni olish: [@userinfobot](https://t.me/userinfobot) ga yozing.

---

## 7. API qo'llanmasi

Barcha API endpointlari `/api/` prefiksi ostida. Autentifikatsiya — JWT (Bearer token).

### 7.1 Autentifikatsiya

| Metod | Yo'l | Tavsif |
|---|---|---|
| POST | `/api/auth/token/` | JWT token olish (username + password) |
| POST | `/api/auth/token/refresh/` | Tokenni yangilash |
| GET | `/api/auth/me/` | Joriy foydalanuvchi |

**Misol:**
```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "kutubxonachi_demo", "password": "demo12345"}'
```

Javob:
```json
{
  "access": "eyJ0eXAiOi...",
  "refresh": "eyJ0eXAiOi..."
}
```

So'rovlarda ishlatish:
```bash
curl http://127.0.0.1:8000/api/books/ \
  -H "Authorization: Bearer eyJ0eXAiOi..."
```

### 7.2 Kitoblar

| Metod | Yo'l | Tavsif |
|---|---|---|
| GET | `/api/books/` | Kitoblar ro'yxati (sahifalangan) |
| POST | `/api/books/` | Yangi kitob qo'shish |
| GET | `/api/books/{id}/` | Bitta kitob (nusxalar bilan) |
| PATCH | `/api/books/{id}/` | Kitobni tahrirlash |
| DELETE | `/api/books/{id}/` | Kitobni o'chirish |
| GET | `/api/books/search/?q=matn` | Qidiruv |
| GET | `/api/books/genres/` | Janrlar ro'yxati |
| GET | `/api/books/{id}/queue/` | Kitob navbati |
| POST | `/api/books/{id}/hold/` | Band qilish (kutubxonachi) |

### 7.3 Nusxalar

| Metod | Yo'l | Tavsif |
|---|---|---|
| GET | `/api/copies/` | Nusxalar ro'yxati |
| POST | `/api/copies/` | Yangi nusxa qo'shish |
| GET | `/api/copies/{id}/` | Bitta nusxa (berish tarixi bilan) |
| PATCH | `/api/copies/{id}/` | Nusxani tahrirlash |
| DELETE | `/api/copies/{id}/` | Nusxani o'chirish |

### 7.4 O'quvchilar

| Metod | Yo'l | Tavsif |
|---|---|---|
| GET | `/api/readers/` | O'quvchilar ro'yxati |
| POST | `/api/readers/` | Yangi o'quvchi qo'shish |
| GET | `/api/readers/{id}/` | Bitta o'quvchi (kitoblari, jarimalari) |
| PATCH | `/api/readers/{id}/` | O'quvchini tahrirlash |
| POST | `/api/readers/bind/` | Bot: telegram_id bog'lash |

### 7.5 Arizalar

| Metod | Yo'l | Tavsif |
|---|---|---|
| GET | `/api/applications/` | Arizalar ro'yxati |
| POST | `/api/applications/` | Bot: yangi ariza |
| GET | `/api/applications/status/?telegram_id=` | Bot: ariza holati |
| POST | `/api/applications/{id}/approve/` | Arizani tasdiqlash |
| POST | `/api/applications/{id}/reject/` | Arizani rad etish |

### 7.6 Berish/Qaytarish

| Metod | Yo'l | Tavsif |
|---|---|---|
| GET | `/api/loans/` | Berishlar ro'yxati |
| POST | `/api/loans/` | Kitob berish |
| POST | `/api/loans/{id}/return/` | Kitob qaytarish |
| GET | `/api/loans/my/?telegram_id=` | O'quvchining kitoblari |
| GET | `/api/loans/overdue/` | Muddati o'tganlar |

### 7.7 Jarimalar

| Metod | Yo'l | Tavsif |
|---|---|---|
| GET | `/api/fines/` | Jarimalar ro'yxati |
| GET | `/api/fines/my/?telegram_id=` | O'quvchining jarimalari (+umumiy qarz) |
| POST | `/api/fines/{id}/pay/` | Jarimani to'langan qilish |

### 7.8 Navbat

| Metod | Yo'l | Tavsif |
|---|---|---|
| GET | `/api/reservations/` | Navbatlar ro'yxati |
| POST | `/api/reservations/` | Navbatga turish |
| GET | `/api/reservations/my/?telegram_id=` | O'quvchining navbatlari (+o'rni) |
| POST | `/api/reservations/{id}/respond/` | Taklifga javob (olaman/kerak emas) |
| POST | `/api/reservations/{id}/confirm/` | Navbatni tasdiqlash (kutubxonachi) |
| DELETE | `/api/reservations/{id}/` | Navbatdan chiqish |

### 7.9 Band qilish

| Metod | Yo'l | Tavsif |
|---|---|---|
| GET | `/api/holds/` | Band so'rovlar (kutubxonachi uchun) |
| POST | `/api/holds/` | Band qilish |
| GET | `/api/holds/my/?telegram_id=` | O'quvchining bandlari |
| POST | `/api/holds/{id}/approve/` | Bandni tasdiqlash |
| POST | `/api/holds/{id}/reject/` | Bandni rad etish |
| POST | `/api/holds/{id}/cancel/` | Bandni bekor qilish |

### 7.10 Statistika

| Metod | Yo'l | Tavsif |
|---|---|---|
| GET | `/api/stats/top-books/?limit=10` | Eng ko'p o'qilgan kitoblar |
| GET | `/api/stats/dashboard/` | Umumiy statistika (8 KPI) |

### 7.11 Xodimlar (faqat admin)

| Metod | Yo'l | Tavsif |
|---|---|---|
| GET | `/api/staff/` | Xodimlar ro'yxati |
| POST | `/api/staff/` | Yangi xodim qo'shish |
| PATCH | `/api/staff/{id}/` | Xodimni tahrirlash |
| DELETE | `/api/staff/{id}/` | Xodimni o'chirish |

---

## 8. Celery vazifalari

Celery beat quyidagi vazifalarni avtomatik bajaradi:

| Vazifa | Jadval | Nima qiladi |
|---|---|---|
| `jarimalarni_hisobla` | Har kuni 00:30 | Muddati o'tgan berishlar uchun jarima hisoblaydi |
| `jarima_eslatma_yubor` | Har 3 soatda | To'lanmagan jarimalarga xabar yuboradi |
| `takliflarni_tekshir` | Har 10 daqiqada | Muddati o'tgan navbat takliflarini bekor qiladi |
| `ochiq_navbatlarni_tekshir` | Har 10 daqiqada | Yangi nusxa qo'shilsa navbatga taklif yuboradi |
| `eslatma_yuborish` | Har kuni 09:00 | Qaytarish muddati yaqinlashganlarga eslatma |

### Vazifalarni qo'lda ishga tushirish (testing uchun)

```bash
# Barcha vazifalarni bir marta bajarish
celery -A config call apps.jarima.tasks.jarimalarni_hisobla
celery -A config call apps.berish.tasks.eslatma_yuborish
```

---

## 9. Boshqaruv buyruqlari

```bash
# Django server
python manage.py runserver

# Migratsiyalar
python manage.py migrate

# Yangi migratsiya yaratish
python manage.py makemigrations

# Admin yaratish
python manage.py createsuperuser

# Demo ma'lumotlar
python manage.py seed_demo

# Bot uchun xizmat akkaunti
python manage.py seed_service_account

# CSV dan kitoblar import qilish
python manage.py import_books_csv --file kitoblar.csv
python manage.py import_books_csv --file kitoblar.csv --dry-run  # sinov

# Tozalash: o'quvchisiz/nofaol o'quvchining jarimalari
python manage.py tozalash_jarimalar
python manage.py tozalash_jarimalar --o'chirish           # o'chirish
python manage.py tozalash_jarimalar --faqat-nofaol        # faqat nofaollarni
```

### Testlar

```bash
python manage.py test
```

---

## 10. Loyiha qoidalari (sozlamalar)

`.env` faylida o'zgartirish mumkin bo'lgan qoidalar:

| O'zgaruvchi | Standart | Tavsif |
|---|---|---|
| `MUDDAT_KUN` | 14 | Kitob berish muddati (kun) |
| `KUNLIK_JARIMA` | 5000 | Kunlik jarima (so'm) |
| `LIMIT_KITOB` | 3 | Bir vaqtda olish mumkin bo'lgan kitoblar soni |
| `TAKLIF_SOAT` | 24 | Navbat taklifi amal qilish muddati (soat) |
| `ESLATMA_KUNLAR_OLDIN` | 2 | Qaytarish oldin necha kun eslatma yuboriladi |
| `JARIMA_ESLATMA_TAKROR_SOAT` | 24 | Jarima eslatmasi takror oralig'i |

---

## 11. Biznes qoidalari

### Kitob berish
- O'quvchi faqat **o'ziga** kitob oladi (LIMIT_KITOB = 3 tagacha)
- Qarzi bo'lsa — yangi kitob berilmaydi
- Band qilingan kitob — faqat band egasiga beriladi
- Nusxa bo'lmasa — "asli" berish (nusxa'siz) amalga oshiriladi

### Kitob qaytarish
- Muddati o'tgan bo'lsa — jarima avtomatik hisoblanadi
- Qaytargandan keyin — navbatdagi birinchi odamga taklif yuboriladi
- Erta qaytarish — qabul qilinadi, xabar yuboriladi

### Jarima
- **Idempotent** — bir necha marta hisoblansa ham natija o'zgarmaydi
- OneToOne maydon orqali bir berishga bitta jarima
- To'langan jarimaga tegilmaydi
- Kunlik stavka: 5000 so'm/kun (o'zgartirish mumkin)

### Navbat
- Bir kitobga bir kishi faol navbatda turadi
- Nusxa qo'shilsa/ta'mirdan chiqsa/qaytarilsa — taklif yuboriladi
- Taklif 24 soat — javob berilmasa keyingi odamga o'tadi
- O'quvchi navbatdan chiqishi mumkin

### Band qilish
- Bir kitobga bitta faol band
- Kutubxonachi tasdiqlaydi/rad etadi
- Tasdiqlanganda — avtomatik berish amalga oshiriladi

### Telegram bildirishnomalar
- Kitob berilganda
- Qaytarish muddati yaqinlashganda (2 kun oldin)
- Jarima hisoblanganda
- Navbat taklifi kelganda
- Ariza tasdiqlanganda/rad etilganda
- Jarima to'langanda

---

## 12. Muammolarni bartaraf etish

### Dastur ishga tushmayapti

**Muammo:** `ModuleNotFoundError`

```bash
# Virtual muhit faolmi tekshiring
venv\Scripts\activate
pip install -r requirements.txt
```

**Muammo:** PostgreSQL'ga ulanish xatosi

```bash
# PostgreSQL xizmati ishlayaptimi?
Get-Service postgresql*
# .env faylda DB_* qiymatlarini tekshiring
```

**Muammo:** Redis/Memurai ishlamayapti

```bash
# Xizmat holati
Get-Service Memurai*
# Ishga tushirish
Start-Service Memurai
# Portni tekshirish
Get-NetTCPConnection -LocalPort 6379 -State Listen
```

### Bot ishlamayapti

1. `.env` faylda `TELEGRAM_BOT_TOKEN` to'g'ri ekanini tekshiring
2. `logs/bot.err.log` faylini o'qing
3. Bot allaqachon ishlayotgan bo'lishi mumkin — qayta ishga tushiring:

```bash
# Eski bot jarayonini to'xtatish
Get-Process python* | Where-Object {$_.Path -like "*Kutubxona*"} | Stop-Process -Force
# Qayta ishga tushirish
python bot/main.py
```

### Celery vazifalari ishlamayapti

1. Redis ishlayotganini tekshiring
2. `logs/celery_worker.err.log` va `logs/celery_beat.err.log` ni o'qing
3. Celery qayta ishga tushiring:

```bash
# Eski Celery'ni to'xtatish
Get-Process celery* | Stop-Process -Force
# Qayta ishga tushirish
celery -A config worker -l info --pool=solo
celery -A config beat -l info
```

### Frontend build xatosi

```bash
cd frontend
# Node modullarni yangilash
rm -rf node_modules
npm install
# Build
npm run build
```

### 401 Unauthorized xatosi

Token muddati tugagan. Frontend avtomatik yangilaydi, lekin qo'lda:

```bash
# Yangi token olish
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "kutubxonachi_demo", "password": "demo12345"}'
```

### Portlar band

```bash
# 8000 portni kim egallaganini ko'rish
netstat -ano | findstr :8000
# Jarayonni to'xtatish (PID raqamni kiriting)
taskkill /PID <PID> /F
```

### Barchasini noldan qayta ishga tushirish

```powershell
# 1. Hammasini to'xtatish
.\stop_all.ps1

# 2. Eski jarayonlarni majburiy to'xtatish
Get-Process celery* -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process python* | Where-Object {$_.Path -like "*Kutubxona*"} | Stop-Process -Force

# 3. Redis'ni tekshirish
Start-Service Memurai

# 4. Qayta ishga tushirish
.\start_all.ps1
```

---

## Qo'shimcha ma'lumot

- **Django admin:** `http://127.0.0.1:8000/admin/`
- **API browsable:** `http://127.0.0.1:8000/api/books/` (JWT talab qiladi)
- **Frontend (dev):** `http://localhost:5173`
- **Frontend (prod):** `http://127.0.0.1:8000/`

### CSV import formati

`import_books_csv` buyrug'i quyidagi ustunlarni kutadi:

```csv
nomi,muallif,isbn,janr,til,nashr_yili,nashriyot,narh,tavsif
"Alpomish","Xalq og'zi","978-0-00-000000-1","epik","o'zbek",1980,"Ma'rifat",5000,"Milliy doston"
```

- `janr` — `JANR_MAP` dagi qiymatlardan biri
- `til` — `TIL_MAP` dagi qiymatlardan biri
- ISBN takrorlansa — avtomatik tozalanadi
- Yaroqsiz yil kiritilsa — 2000 yil qo'yiladi

---

**Tayyor!** Loyiha ishlatishga tayyor. Muammo bo'lsa, log fayllarini tekshiring yoki GitHub'da issue oching.
