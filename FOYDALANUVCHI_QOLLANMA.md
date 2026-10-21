# KUTUBXONA SAYTIDAN FOYDALANISH

Bu qo'llanma saytdan **kundalik ishda** foydalanish uchun yozilgan. Texnik tafsilotlar (o'rnatish, API, server) shu yerdа yo'q — ular dasturchilar uchun.

---

## MOQIVJA

1. [Saytga kirish](#1-saytga-kirish)
2. [Saytning umumiy ko'rinishi](#2-saytning-umumiy-ko'rinishi)
3. [Boshqaruv paneli — bir qarashda](#3-boshqaruv-paneli—bir-qarashda)
4. [Kitob qo'shish](#4-kitob-qo'shish)
5. [Jismoniy nusxa qo'shish](#5-jismoniy-nusxa-qo'shish)
6. [O'quvchi yoki o'qituvchi qo'shish](#6-o'quvchi-yoki-o'qituvchi-qo'shish)
7. [Kitob berish](#7-kitob-berish)
8. [Kitobni qaytarib olish](#8-kitobni-qaytarib-olish)
9. [Telegram'dan kelgan arizalarni tasdiqlash](#9-telegramdan-kelgan-arizalarni-tasdiqlash)
10. [Band so'rovlarini boshqarish](#10-band-so'rovlarini-boshqarish)
11. [Navbatlarni boshqarish](#11-navbatlarni-boshqarish)
12. [Jarimani qabul qilish](#12-jarimani-qabul-qilish)
13. [O'quvchini kuzatish](#13-o'quvchini-kuzatish)
14. [Xodim qo'shish (faqat administrator)](#14-xodim-qo'shish-faqat-administrator)
15. [Kunlik ish tartibi](#15-kunlik-ish-tartibi)
16. [Tez-tez so'raladigan savollar](#16-tez-tez-so'raladigan-savollar)

---

## 1. Saytga kirish

1. Brauzerda saytni oching:
   `https://kutubxona.sharqsoft.uz`
2. **Foydalanuvchi nomi** va **parol** ni kiriting
3. **Kirish** tugmasini bosing

> **Parolni unutdingizmi?** Administratordan yoki kutubxona boshlig'idan yangi parol olishingiz kerak — sayt o'z-o'zidan parol tiklamaydi.

**Muhim:**
- Saytga kirish faqat **kutubxonachi** va **administrator** uchun. O'quvchi/o'qituvchilar saytga kirmaydi — ular Telegram botdan foydalanadi.
- Ish tugagach, chap pastdagi **Chiqish** tugmasini bosing — boshqa birov sizning hisobingizga kirmasin.

---

## 2. Saytning umumiy ko'rinishi

### Chap menyu (yoningizdagi ro'yxat)

| Tugma | Nima uchun kerak |
|---|---|
| 📊 Boshqaruv paneli | Umumiy statistika — hamma narsaning bir ko'rinishi |
| 📚 Kitoblar | Kitoblar ro'yxati — qo'shish, tahrirlash |
| 📦 Nusxalar | Jismoniy kitoblar (inventar raqami bilan) |
| 🎓 O'quvchilar | O'quvchilar ro'yxati |
| 👩‍🏫 O'qituvchilar | O'qituvchilar ro'yxati |
| 📋 Arizalar | Telegram'dan kelgan a'rolik arizalari |
| 🔄 Berish / Qaytarish | Kunlik asosiy ish — kitob berish va qaytarish |
| 🔒 Bandlar | O'quvchilarning band so'rovlari |
| ⏳ Navbatlar | Kitob navbatlari |
| 💰 Jarimalar | Kechiktirish uchun jarimalar |
| 🛡️ Xodimlar | Faqat **administrator** ko'radi |
| 📖 Qo'llanma | Shu qo'llanma |

### Yuqori qismdagi tugmalar

- **🌙 / ☯️** — qorong'i va yorug' rejimni almashtiradi
- **☰** — telefonda menyu ochadi

### Umumiy qoidalar (barcha sahifalarda bir xil)

- **Qidiruv maydoni** — kerakli ma'lumotni tez topish uchun. Yozishni boshlaganingizda avtomatik qidiradi.
- **Filtr** (ro'yxat tepasidagi tanlash) — masalan, faqat "Kutmoqda" holatidagi arizalarni ko'rish.
- **Sahifalar** — ro'yxat uzun bo'lsa, pastda sahifa raqamlari chiqadi.
- **O'ng yuqorida xabar** — biror ish muvaffaqiyatli bajarilsa, yashil xabar paydo bo'ladi.
- **Tasdiqlash oynasi** — o'chirish yoki muhim amal bajarishdan oldin "ishonchingiz komilmi?" so'raladi. Xato qilsangiz, **Bekor qilish** tugmasini bosing.

---

## 3. Boshqaruv paneli — bir qarashda

**📊 Boshqaruv paneli** saytga kirganingizda ochiladi. Bu shunchaki ko'rish sahifasi — bu yerda hech narsa o'zgartirilmaydi.

**8 ta ko'rsatkich:**

| Ko'rsatkich | Nimani anglatadi |
|---|---|
| Jami kitoblar | Katalogdagi kitoblar soni |
| Jami nusxalar | Barcha jismoniy kitoblar |
| Mavjud nusxalar | Hozir berishga yaroq kitoblar |
| Berilgan nusxalar | O'quvchi qo'lidagi kitoblar |
| **Muddati o'tgan** (qizil) | Kechiktirilgan kitoblar — shoshilinch |
| Faol navbatlar | Navbatda turganlar |
| **To'lanmagan jarimalar** (sariq) | Qarzdorlar soni |
| **Umumiy qarzdorlik** (sariq) | Jami qarz miqdori |

**Maslahat:** Qizil va sariq kartochkalarni bosishingiz mumkin — tegishli bo'limga darhol o'tasiz.

Pastda **"Eng ko'p o'qilgan kitoblar"** — qaysi kitoblar ko'proq o'qilganini ko'rasiz.

---

## 4. Kitob qo'shish

Kutubxonaga yangi kitob kelganda:

1. Chap menyudan **📚 Kitoblar** ni bosing
2. Yuqoridagi **+ Yangi kitob** tugmasini bosing
3. Formani to'ldiring:

| Maydon | Majburiymi? | Misol |
|---|---|---|
| Nomi | ✅ Ha | "Alpomish" |
| Muallif | ✅ Ha | "Xalq og'zi" |
| ISBN | ❌ Yo'q | 978-605-0000-00-1 (bo'lmasa bo'sh qoldiring) |
| Janr | ✅ Ha | Badiiy / Ilmiy / Darslik / Bolalar / Tarixiy / Boshqa |
| Nashr yili | ✅ Ha | 1980 |
| Til | ❌ Yo'q | O'zbek tili (lotin) |
| Narhi | ❌ Yo'q | 50000 |
| Nashriyot | ❌ Yo'q | "Ma'rifat" |
| Tavsif | ❌ Yo'q | Qisqacha izoh |

4. **Saqlash** tugmasini bosing

> ⚠️ **Kitob qo'shildi, lekin hali berilmaydi!** Yana bir qadam — **5-jadvaldagi nusxa** qo'shish kerak. Nusxasiz kitob o'quvchiga "asli" (nusxasiz nusxa) sifatida beriladi.

**Kitobni tahrirlash:** Ro'yxatdagi **Tahrirlash** tugmasi → o'zgartiring → **Saqlash**.

**Kitobni o'chirish:** **O'chirish** (qizil) → tasdiqlang. Agar kitobda navbat bo'lsa, oldindan ogohlantirish chiqadi.

---

## 5. Jismoniy nusxa qo'shish

Har bir kitobning qo'lidagi jismoniy nusxalari shu yerda. Inventar raqami — kitobning "pasporti".

1. Chap menyudan **📦 Nusxalar** ni bosing
2. **+ Yangi nusxa** tugmasini bosing
3. Formani to'ldiring:

| Maydon | Majburiymi? | Misol |
|---|---|---|
| Kitob | ✅ Ha | Ro'yxatdan kitobni tanlang |
| Inventar raqami | ✅ Ha | INV-000001 |
| Javon | ❌ Yo'q | A-3 |
| Izoh | ❌ Yo'q | "Yangi, birinchi nusxa" |

4. **Saqlash**

**Nusxa holatini o'zgartirish** (ro'yxatdagi tugmalar):

| Tugma | Qachon bosiladi |
|---|---|
| **Ta'mirga berish** | Kitob ta'mirga ketayotganda |
| **Qaytarish** | Ta'mirdan qaytganda |
| **Yo'qolgan deb belgilash** | Kitob yo'qolsa |

> 💡 **Avtomatik:** Nusxa qo'shilsa yoki ta'mirdan qaytsa, navbatdagi birinchi o'quvchi Telegram orqali avtomatik xabar oladi — qo'lda hech narsa qilish shart emas.

---

## 6. O'quvchi yoki o'qituvchi qo'shish

### Usul 1 — Telegram'dan kelgan ariza orqali (asosiy usul)

O'quvchi botda ariza yuboradi → siz faqat **tasdiqlaysiz**. Batafsil — 9-bo'lim.

### Usul 2 — qo'lda

1. **🎓 O'quvchilar** (yoki **👩‍🏫 O'qituvchilar**) ni bosing
2. **+ Yangi o'quvchi** tugmasi
3. To'ldiring:

| Maydon | Majburiymi? | Misol |
|---|---|---|
| To'liq ismi | ✅ Ha | Aliyev Vali |
| Telefon | ✅ Ha | +998901234567 |
| Sinf (fan) | ✅ O'qituvchi uchun | 7-A / Matematika |
| Tug'ilgan sana | ❌ Yo'q | 15.03.2012 |
| Manzil | ❌ Yo'q | Toshkent sh. |

4. **Saqlash**

> 💡 **Karta raqami avtomatik beriladi** — saqlangandan keyin yashil xabarda ko'rinadi (masalan `LIB-2026-0042`). Shu raqamni o'quvchiga bering.

**O'quvchini bloklash** (kutubxonadan foydalanishini taqiqlash): Ro'yxatdagi **Bloklash** tugmasi. Keyin **Faollashtirish** bilan qayta ochiladi.

---

## 7. Kitob berish

Kunlik eng ko'p ishlatiladigan bo'lim.

1. **🔄 Berish / Qaytarish** ni bosing
2. Yuqoridagi **+ Kitob berish** tugmasini bosing
3. **O'quvchini toping:**
   - "Ism, sinf yoki telefon" maydoniga yozing (masalan "Vali")
   - Ro'yxatdan o'quvchini tanlang
4. **Kitobni toping:**
   - "Kitob nomi, muallif yoki ISBN" maydoniga yozing
   - Ro'yxatdan kitobni tanlang
5. **Muhim — rangli xabarni o'qing:**

| Xabar | Nima qilasiz |
|---|---|
| 🟢 "Beriladi: mavjud nusxa (3/5)" | Oddiy berasiz |
| 🟡 "Beriladi: kitob asli (nusxasi yo'q)" | Beriladi, lekin nusxasi yo'q ekan |
| 🟡 "Barcha nusxalar band — o'quvchi navbatga qo'shiladi" | Berish o'rniga o'quvchi navbatga tushadi — xato emas |

6. **Berish** tugmasini bosing

> ✅ Tayyor! O'quvchiga Telegram'dan qaytarish muddati bilan xabar boradi. Muddat — odatda **14 kun** (sozlamaga bog'liq).

**Ixtiyoriy:** aniq qaysi nusxa (inventar raqami) borligini tanlash kerak bo'lsa, **"Aniq nusxani qo'lda tanlash"** belgisini bosing.

---

## 8. Kitobni qaytarib olish

1. **🔄 Berish / Qaytarish** bo'limiga kiring
2. **Holat** filtrida **Faol** ni tanlang — hozir o'quvchi qo'lidagilar chiqadi
3. Kerakli qatorda **Qaytarish** tugmasini bosing
4. Tasdiqlash oynasini o'qing: *"...qaytarasizmi? Muddat o'tganda jarima avtomatik hisoblanadi."*
5. **Qaytarish** tugmasini bosing

**Natija:**
- Muddati o'tgan bo'lsa → xabarda **jarima miqdori** ko'rsatiladi, u avtomatik hisoblanadi
- Kitob navbatda kimsa bo'lsa → navbatdagi odamga avtomatik taklif ketadi
- Muddat ichida bo'lsa → "Jarima yo'q"

> ⚠️ Jarimani **qo'lda hisoblash shart emas** — tizim o'zi hisoblaydi.

**Maslahat:** O'quvchining barcha kitoblari va qarzini bir joyda ko'rish uchun **🎓 O'quvchilar** → o'quvchi ismini bosing (13-bo'lim).

---

## 9. Telegram'dan kelgan arizalarni tasdiqlash

O'quvchi/o'qituvchi botda ariza yuborganda, saytda **📋 Arizalar** bo'limida "Kutmoqda" holatida paydo bo'ladi.

1. **📋 Arizalar** ni bosing — dastlab faqat **kutilayotgan** arizalar chiqadi
2. Arizani o'qing: ism, telefon, sinf/fan, Telegram ID
3. Ikki variant:

### Tasdiqlash ✅
1. **Qabul qilish** tugmasi
2. Tasdiqlash oynasini o'qing: *"...karta raqami avtomatik beriladi va Telegram orqali xabar yuboriladi"*
3. **Qabul qilish** — tizim o'quvchini ro'yxatga oladi, karta raqamini beradi va unga Telegram'dan xabar ketadi

### Rad etish ❌
1. **Rad etish** (qizil) tugmasi
2. Sabab yozing (ixtiyoriy) — masalan: "yosh chegarasi 18"
3. **Rad etish** — sabab o'quvchiga Telegram'dan yuboriladi

> **Qo'shimcha:** Qidiruv, Rol (O'quvchi/O'qituvchi) va Holat filtrlaridan foydalaning. Barcha arizalarni ko'rish uchun Holatni "Barcha holatlar" qiling.

---

## 10. Band so'rovlarini boshqarish

O'quvchi botda mavjud bo'lmagan kitobni **band qilishni** so'rasa, bu bo'limga tushadi.

1. **🔒 Bandlar** ni bosing — dastlab **Kutmoqda** so'rovlar chiqadi
2. So'rovni o'qing: qaysi kitob, kim so'ragan, qachon
3. Ikki variant:

| Tugma | Natija |
|---|---|
| **Tasdiqlash** | Kitob o'quvchiga beriladi, unga muddat bilan xabar ketadi |
| **Rad etish** | Sabab yozasiz, kitob yana hamma uchun ochiq bo'ladi |

4. Ixtiyoriy **izoh** yozing (masalan: "3-sinf darsiga tayyorlanmoqda") → tasdiqlang

> Tasdiqlash = o'quvchiga kitob berish. Shu yerdan qo'shimcha "Berish" bosqichiga o'tish shart emas.

---

## 11. Navbatlarni boshqarish

Kitobning hamma nusxasi band/qilingan bo'lsa, o'quvchilar navbatga turadi. Kitob bo'shaganda tizim **avtomatik taklif** yuboradi — siz faqat o'quvchi kelganda tasdiqlaysiz.

1. **⏳ Navbatlar** ni bosing
2. Holat filtri bilan ishlang:

| Holat | Nimani anglatadi | Sizning harakatingiz |
|---|---|---|
| 🟡 Kutmoqda | Navbatda turibdi | Kuzatib boring |
| 🔵 Taklif qilindi | Nusxa ajratildi, javob kutilmoqda | O'quvchi javobini kuting |
| 🟢 Yakunlandi | Kitob berildi | — |
| 🔴 Bekor | Navbat bekor qilindi | — |

3. O'quvchi "Olaman" deb javob berganda:
   - **Tasdiqlash** → kitob unga beriladi, navbat yakunlanadi
4. O'quvchi kelmasa yoki "Kerak emas" desa:
   - **Bekor qilish** → keyingi navbatdagi odamga taklif ketadi

> ⏳ Taklif **24 soat** amal qiladi. Javob berilmasa, tizim o'zi keyingisiga o'tkazadi (buni siz qo'lda qilishingiz shart emas).

---

## 12. Jarimani qabul qilish

O'quvchi kechiktirib kitob qaytarganda jarima avtomatik hisoblanadi. Naqd pul qabul qilgandan keyin:

1. **💰 Jarimalar** ni bosing (yoki Boshqaruv panelidagi sariq kartochkani bosing)
2. Filtrda **To'lanmagan** ni tanlang
3. Kerakli qatorda **To'landi** tugmasini bosing
4. Tasdiqlash oynasini o'qing → **To'langan deb belgilash**

> ✅ O'quvchiga Telegram'dan to'langani haqida xabar boradi. Qarzdorlik kartochkasi darhol yangilanadi.

**Jarima qanday hisoblanadi?**
`Kechikkan kunlar × kunlik jarima` — masalan 3 kun × 5000 so'm = **15 000 so'm**. Kunlik miqdor sozlamada (5000 so'm) o'zgartirilishi mumkin.

---

## 13. O'quvchini kuzatish

Bitta o'quvchining hamma narsasini bir joyda ko'rish:

1. **🎓 O'quvchilar** → qidiruvdan o'quvchini toping
2. Ismini bosing — **tafsilot sahifasi** ochiladi

**Bu yerda ko'rasiz:**
- Shaxsiy ma'lumotlar (sinf, telefon, karta, Telegram bog'langanmi)
- 📚 **Joriy kitoblar** — qo'lidagi kitoblar, muddat va **qolgan kun** (qizil = muddati o'tgan)
- 💰 **To'lanmagan jarimalar** — qarzi

**Shu yerdan amalga oshirasiz:**
- **Qaytarish** — qo'lidagi kitobni qaytarib olish
- **To'landi deb belgilash** — jarimani yopish

---

## 14. Xodim qo'shish (faqat administrator)

**🛡️ Xodimlar** bo'limi faqat administratorga ko'rinadi.

1. **🛡️ Xodimlar** → **+ Yangi xodim**
2. To'ldiring: To'liq ismi, Foydalanuvchi nomi (login), Parol, Lavozim (Kutubxonachi / Administrator)
3. **Saqlash** → xodimga login va parolni bering

**Xodimni ishdan olish:** **Bloklash** — kirishi o'chadi, lekin ma'lumotlari saqlanadi. Keyin qayta **Faollashtirish** mumkin.

---

## 15. Kunlik ish tartibi

**Kun boshida:**
1. 📊 **Boshqaruv paneli** — qizil/sariq kartochkalarni tekshiring (muddati o'tganlar, qarzdorlar)
2. 📋 **Arizalar** — Telegram'dan kelgan arizalarni tasdiqlang

**Kun davomida:**
3. 🔄 **Berish / Qaytarish** — kelgan o'quvchilarga kitob bering, qaytarib oling
4. 🔒 **Bandlar** — kutilayotgan band so'rovlarini javoblang
5. ⏳ **Navbatlar** — o'quvchi kelgan bo'lsa tasdiqlang

**Kun oxirida:**
6. 💰 **Jarimalar** — naqd pul kelgan bo'lsa yoping

> 🔔 **Eslatma:** Berish, qaytarish, ariza javobi, jarima va navbat takliflari — **hammasi Telegram orqali avtomatik** yuboriladi. Qo'lda xabar yozish shart emas.

---

## 16. Tez-tez so'raladigan savollar

**Savol: Kitob topilmadi (nusxasi yo'q)?**
Javob: Uni 📚 Kitoblar bo'limida qo'shing, keyin 📦 Nusxalar bo'limida kamida bitta nusxa qo'shing. Nusxasiz ham berish mumkin — lekin u "asli" sifatida beriladi.

**Savol: O'quvchi hamma nusxa band bo'lib keldi?**
Javob: "Berish" tugmasini bosing — xato chiqmaydi, o'quvchi avtomatik navbatga qo'shiladi va unga xabar boradi.

**Savol: Xato qilib noto'g'ri o'quvchiga kitob berdim?**
Javob: Derabsiz — 🔄 Berish/Qaytarish'dan kitobni qaytarib oling (o'sha o'quvchidan), keyin to'g'ri o'quvchiga qayta bering.

**Savol: O'quvchi kelmayapti, lekin taklif muddati tugayapti?**
Javob: Hech narsa qilmang — 24 soatdan keyin tizim o'zi bekor qilib, keyingi odamga taklif yuboradi.

**Savol: Parolni unutdim?**
Javob: Administrator parolni o'zgartirib beradi (🛡️ Xodimlar → Tahrirlash).

**Savol: Sayt ochilmayapti?**
Javob: Avval internetni tekshiring. Ishlasa ham ochilmasa — administratorga xabar bering.

**Savol: O'quvchi saytga kirishi kerakmi?**
Javob: Yo'q. O'quvchilar faqat **Telegram bot**dan foydalanadi — sayt faqat kutubxonachilar uchun.

**Savol: Kitob necha kunga beriladi?**
Javob: Odatda **14 kun**. Aniq muddat berish oynasidagi xabarda yoziladi.

**Savol: Jarimani qo'lda hisoblaymanmi?**
Javob: Yo'q — tizim qaytarish paytida o'zi hisoblaydi. Siz faqat naqd pul olgandan keyin "To'landi" deb belgilaysiz.

---

> **Yordam kerakmi?** Shu qo'llanmaning yuqorisidagi 📖 **Qo'llanma** bo'limida saytning barcha imkoniyatlari batafsil yozilgan. Muammo bo'lsa — administratorga murojaat qiling.
