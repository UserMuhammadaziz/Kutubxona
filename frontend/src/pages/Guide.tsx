import { Link } from 'react-router-dom'
import { useState, type ReactNode, type SVGProps } from 'react'
import clsx from 'clsx'
import { Icons } from '../components/icons'
import { PageHeader } from '../components/ui'

/* ------------------------------------------------------------------ */
/*  Yordamchi komponentlar (markdown o'rniga — to'liq React/JSX)      */
/* ------------------------------------------------------------------ */

function P({ children }: { children: ReactNode }) {
  return <p className="leading-relaxed text-slate-700 dark:text-slate-300">{children}</p>
}

function H3({ children }: { children: ReactNode }) {
  return (
    <h3 className="mt-5 text-base font-semibold text-slate-900 dark:text-slate-100">{children}</h3>
  )
}

function UL({ items }: { items: ReactNode[] }) {
  return (
    <ul className="space-y-1.5 pl-5 text-slate-700 marker:text-slate-400 dark:text-slate-300">
      {items.map((item, i) => (
        <li key={i} className="list-disc leading-relaxed">
          {item}
        </li>
      ))}
    </ul>
  )
}

function OL({ items }: { items: ReactNode[] }) {
  return (
    <ol className="space-y-1.5 pl-5 text-slate-700 marker:font-medium marker:text-slate-500 dark:text-slate-300">
      {items.map((item, i) => (
        <li key={i} className="list-decimal leading-relaxed">
          {item}
        </li>
      ))}
    </ol>
  )
}

/** E'tibor berish uchun blok (markdown'dagi ">" bloklari). */
function Note({
  tone = 'info',
  children,
}: {
  tone?: 'info' | 'alert' | 'success' | 'bell'
  children: ReactNode
}) {
  const tones = {
    info: {
      wrap: 'border-blue-200 bg-blue-50 dark:border-blue-500/30 dark:bg-blue-950/40',
      icon: 'text-blue-600 dark:text-blue-400',
      Icon: Icons.info,
    },
    alert: {
      wrap: 'border-amber-200 bg-amber-50 dark:border-amber-500/30 dark:bg-amber-950/40',
      icon: 'text-amber-600 dark:text-amber-400',
      Icon: Icons.alert,
    },
    success: {
      wrap: 'border-emerald-200 bg-emerald-50 dark:border-emerald-500/30 dark:bg-emerald-950/40',
      icon: 'text-emerald-600 dark:text-emerald-400',
      Icon: Icons.checkCircle,
    },
    bell: {
      wrap: 'border-brand-200 bg-brand-50 dark:border-brand-500/30 dark:bg-brand-950/40',
      icon: 'text-brand-600 dark:text-brand-400',
      Icon: Icons.bell,
    },
  }[tone]
  const { Icon } = tones
  return (
    <div className={clsx('flex items-start gap-2.5 rounded-lg border px-3.5 py-3', tones.wrap)}>
      <Icon className={clsx('mt-0.5 h-4.5 w-4.5 shrink-0', tones.icon)} />
      <div className="text-sm leading-relaxed text-slate-700 dark:text-slate-200">{children}</div>
    </div>
  )
}

/** Holat/rang belgisi (markdown'dagi yashil/sariq/qizil doirachalari). */
function Dot({ color }: { color: 'green' | 'amber' | 'blue' | 'red' }) {
  const colors = {
    green: 'bg-emerald-500',
    amber: 'bg-amber-400',
    blue: 'bg-blue-500',
    red: 'bg-red-500',
  }[color]
  return <span className={clsx('inline-block h-2.5 w-2.5 shrink-0 rounded-full', colors)} aria-hidden />
}

function Tbl({ head, rows }: { head: string[]; rows: ReactNode[][] }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700">
      <table className="w-full min-w-[32rem] text-left text-sm">
        <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-700/60 dark:text-slate-300">
          <tr>
            {head.map((h) => (
              <th key={h} className="px-3 py-2.5 font-medium">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 text-slate-700 dark:divide-slate-700/60 dark:text-slate-300">
          {rows.map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => (
                <td key={j} className="px-3 py-2.5 align-top leading-relaxed">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Code({ children }: { children: ReactNode }) {
  return (
    <code className="rounded bg-slate-100 px-1.5 py-0.5 text-[0.85em] text-slate-800 dark:bg-slate-700 dark:text-slate-100">
      {children}
    </code>
  )
}

function B({ children }: { children: ReactNode }) {
  return <strong className="font-semibold text-slate-900 dark:text-slate-100">{children}</strong>
}

/* ------------------------------------------------------------------ */
/*  Bo'limlar ma'lumotlari                                              */
/* ------------------------------------------------------------------ */

type IconComponent = (p: SVGProps<SVGSVGElement>) => ReactNode

type Section = {
  id: string
  num: string
  title: string
  icon: IconComponent
  blocks: ReactNode[]
}

const sections: Section[] = [
  {
    id: 'kirish',
    num: '1',
    title: 'Saytga kirish',
    icon: Icons.user,
    blocks: [
      <P key="0">
        Bu qo‘llanma saytdan <B>kundalik ishda</B> foydalanish uchun yozilgan. Texnik tafsilotlar
        (o‘rnatish, API, server) shu yerda yo‘q — ular dasturchilar uchun.
      </P>,
      <OL
        key="1"
        items={[
          <>
            Brauzerda saytni oching: <Code>https://kutubxona.sharqsoft.uz</Code>
          </>,
          <>
            <B>Foydalanuvchi nomi</B> va <B>parol</B> ni kiriting
          </>,
          <>
            <B>Kirish</B> tugmasini bosing
          </>,
        ]}
      />,
      <Note key="2" tone="alert">
        <B>Parolni unutdingizmi?</B> Administratordan yoki kutubxona boshlig‘idan yangi parol
        olishingiz kerak — sayt o‘z-o‘zidan parol tiklamaydi.
      </Note>,
      <P key="3">
        <B>Muhim:</B>
      </P>,
      <UL
        key="4"
        items={[
          <>
            Saytga kirish faqat <B>kutubxonachi</B> va <B>administrator</B> uchun.
            O‘quvchi/o‘qituvchilar saytga kirmaydi — ular Telegram botdan foydalanadi.
          </>,
          <>
            Ish tugagach, chap pastdagi <B>Chiqish</B> tugmasini bosing — boshqa birov sizning
            hisobingizga kirmasin.
          </>,
        ]}
      />,
    ],
  },
  {
    id: 'ko-rinish',
    num: '2',
    title: 'Saytning umumiy ko‘rinishi',
    icon: Icons.menu,
    blocks: [
      <H3 key="0">Chap menyu (yoningizdagi ro‘yxat)</H3>,
      <Tbl
        key="1"
        head={['Tugma', 'Nima uchun kerak']}
        rows={[
          [
            <span key="a" className="flex items-center gap-2">
              <Icons.dashboard className="h-4 w-4 shrink-0 text-slate-400" />
              <B>Boshqaruv paneli</B>
            </span>,
            'Umumiy statistika — hamma narsaning bir ko‘rinishi',
          ],
          [
            <span key="a" className="flex items-center gap-2">
              <Icons.books className="h-4 w-4 shrink-0 text-slate-400" />
              <B>Kitoblar</B>
            </span>,
            'Kitoblar ro‘yxati — qo‘shish, tahrirlash',
          ],
          [
            <span key="a" className="flex items-center gap-2">
              <Icons.package className="h-4 w-4 shrink-0 text-slate-400" />
              <B>Nusxalar</B>
            </span>,
            'Jismoniy kitoblar (inventar raqami bilan)',
          ],
          [
            <span key="a" className="flex items-center gap-2">
              <Icons.graduationCap className="h-4 w-4 shrink-0 text-slate-400" />
              <B>O‘quvchilar</B>
            </span>,
            'O‘quvchilar ro‘yxati',
          ],
          [
            <span key="a" className="flex items-center gap-2">
              <Icons.user className="h-4 w-4 shrink-0 text-slate-400" />
              <B>O‘qituvchilar</B>
            </span>,
            'O‘qituvchilar ro‘yxati',
          ],
          [
            <span key="a" className="flex items-center gap-2">
              <Icons.clipboardList className="h-4 w-4 shrink-0 text-slate-400" />
              <B>Arizalar</B>
            </span>,
            'Telegram’dan kelgan arizalar',
          ],
          [
            <span key="a" className="flex items-center gap-2">
              <Icons.arrowsRightLeft className="h-4 w-4 shrink-0 text-slate-400" />
              <B>Berish / Qaytarish</B>
            </span>,
            'Kunlik asosiy ish — kitob berish va qaytarish',
          ],
          [
            <span key="a" className="flex items-center gap-2">
              <Icons.lock className="h-4 w-4 shrink-0 text-slate-400" />
              <B>Bandlar</B>
            </span>,
            'O‘quvchilarning band so‘rovlari',
          ],
          [
            <span key="a" className="flex items-center gap-2">
              <Icons.clock className="h-4 w-4 shrink-0 text-slate-400" />
              <B>Navbatlar</B>
            </span>,
            'Kitob navbatlari',
          ],
          [
            <span key="a" className="flex items-center gap-2">
              <Icons.money className="h-4 w-4 shrink-0 text-slate-400" />
              <B>Jarimalar</B>
            </span>,
            'Kechiktirish uchun jarimalar',
          ],
          [
            <span key="a" className="flex items-center gap-2">
              <Icons.shield className="h-4 w-4 shrink-0 text-slate-400" />
              <B>Xodimlar</B>
            </span>,
            'Faqat administrator ko‘radi',
          ],
          [
            <span key="a" className="flex items-center gap-2">
              <Icons.bookOpen className="h-4 w-4 shrink-0 text-slate-400" />
              <B>Qo‘llanma</B>
            </span>,
            'Shu qo‘llanma',
          ],
        ]}
      />,
      <Note key="2" tone="info">
        Saytdagi ikonkalar sizga bo‘limlarni tez topishga yordam beradi.
      </Note>,
      <H3 key="3">Yuqori qismdagi tugmalar</H3>,
      <UL
        key="4"
        items={[
          <span key="a" className="flex items-center gap-2">
            <Icons.moon className="h-4 w-4 shrink-0 text-slate-400" />
            <Icons.sun className="h-4 w-4 shrink-0 text-slate-400" />
            qorong‘i (tungi) va yorug‘ (kunduzgi) rejimni almashtiradi
          </span>,
          <span key="b" className="flex items-center gap-2">
            <Icons.menu className="h-4 w-4 shrink-0 text-slate-400" />
            telefonda chap menyuni ochadi/yopadi
          </span>,
        ]}
      />,
      <H3 key="5">Umumiy qoidalar (barcha sahifalarda bir xil)</H3>,
      <UL
        key="6"
        items={[
          <>
            <B>Qidiruv maydoni</B> — kerakli ma’lumotni tez topish uchun. Yozishni boshlaganingizda
            avtomatik qidiradi.
          </>,
          <>
            <B>Filtr</B> (ro‘yxat tepasidagi tanlash) — masalan, faqat “Kutmoqda” holatidagi
            arizalarni ko‘rish.
          </>,
          <>
            <B>Sahifalar</B> — ro‘yxat uzun bo‘lsa, pastda sahifa raqamlari chiqadi.
          </>,
          <>
            <B>O‘ng yuqorida xabar</B> — biror ish muvaffaqiyatli bajarilsa, yashil xabar paydo
            bo‘ladi.
          </>,
          <>
            <B>Tasdiqlash oynasi</B> — o‘chirish yoki muhim amal bajarishdan oldin “ishonchingiz
            komilmi?” so‘raladi. Xato qilsangiz, <B>Bekor qilish</B> tugmasini bosing.
          </>,
        ]}
      />,
    ],
  },
  {
    id: 'boshqaruv-paneli',
    num: '3',
    title: 'Boshqaruv paneli — bir qarashda',
    icon: Icons.dashboard,
    blocks: [
      <P key="0">
        <B>Boshqaruv paneli</B> saytga kirganingizda ochiladi. Bu shunchaki ko‘rish sahifasi — bu
        yerda hech narsa o‘zgartirilmaydi.
      </P>,
      <P key="1">
        <B>8 ta ko‘rsatkich:</B>
      </P>,
      <Tbl
        key="2"
        head={['Ko‘rsatkich', 'Nimani anglatadi']}
        rows={[
          ['Jami kitoblar', 'Katalogdagi kitoblar soni'],
          ['Jami nusxalar', 'Barcha jismoniy kitoblar'],
          ['Mavjud nusxalar', 'Hozir berishga yaroq kitoblar'],
          ['Berilgan nusxalar', 'O‘quvchi qo‘lidagi kitoblar'],
          [
            <span key="a" className="flex items-center gap-2">
              <Dot color="red" />
              <B>Muddati o‘tgan</B>
            </span>,
            'Kechiktirilgan kitoblar — shoshilinch ekanligini bildiradi',
          ],
          ['Faol navbatlar', 'Navbatda turganlar soni'],
          [
            <span key="a" className="flex items-center gap-2">
              <Dot color="amber" />
              <B>To‘lanmagan jarimalar</B>
            </span>,
            'Qarzdorlar soni',
          ],
          [
            <span key="a" className="flex items-center gap-2">
              <Dot color="amber" />
              <B>Umumiy qarzdorlik</B>
            </span>,
            'Jami qarz miqdori (so‘mda)',
          ],
        ]}
      />,
      <Note key="3" tone="info">
        <B>Maslahat:</B> Qizil va sariq kartochkalarni bosishingiz mumkin — tegishli bo‘limga
        darhol o‘tasiz.
      </Note>,
      <P key="4">
        Pastda <B>“Eng ko‘p o‘qilgan kitoblar”</B> — qaysi kitoblar ko‘proq o‘qilganini ko‘rasiz.
      </P>,
    ],
  },
  {
    id: 'kitob-qoshish',
    num: '4',
    title: 'Kitob qo‘shish',
    icon: Icons.books,
    blocks: [
      <P key="0">Kutubxonaga yangi kitob kelganda:</P>,
      <OL
        key="1"
        items={[
          <>
            Chap menyudan <B>Kitoblar</B> ni bosing
          </>,
          <>
            Yuqoridagi <B>+ Yangi kitob</B> tugmasini bosing
          </>,
          <>Formani to‘ldiring:</>,
        ]}
      />,
      <Tbl
        key="2"
        head={['Maydon', 'Majburiymi?', 'Misol']}
        rows={[
          ['Nomi', <B key="a">Ha</B>, '“Alpomish”'],
          ['Muallif', <B key="a">Ha</B>, '“Xalq og‘zi”'],
          ['ISBN', <>Yo‘q</>, '978-605-0000-00-1 (bo‘lmasa bo‘sh qoldiring)'],
          ['Janr', <B key="a">Ha</B>, 'Badiiy / Ilmiy / Darslik / Bolalar / Tarixiy / Boshqa'],
          ['Nashr yili', <B key="a">Ha</B>, '1980'],
          ['Til', <>Yo‘q</>, 'O‘zbek tili (lotin)'],
          ['Narhi', <>Yo‘q</>, '50000'],
          ['Nashriyot', <>Yo‘q</>, '“Ma‘rifat”'],
          ['Tavsif', <>Yo‘q</>, 'Qisqacha izoh'],
        ]}
      />,
      <OL key="3" items={[<>Saqlash tugmasini bosing</>]} />,
      <Note key="4" tone="alert">
        <B>Diqqat:</B> Kitob qo‘shildi, lekin hali berilmaydi! Yana bir qadam — 5-bo‘limda
        <B> nusxa</B> qo‘shish kerak. Nusxasiz kitob o‘quvchiga “asli” (nusxasiz nusxa) sifatida
        beriladi.
      </Note>,
      <P key="5">
        <B>Kitobni tahrirlash:</B> Ro‘yxatdagi <B>Tahrirlash</B> tugmasi → o‘zgartiring →{' '}
        <B>Saqlash</B>.
      </P>,
      <P key="6">
        <B>Kitobni o‘chirish:</B> <B>O‘chirish</B> (qizil tugma) → tasdiqlang. Agar kitobda navbat
        bo‘lsa, oldindan ogohlantirish chiqadi.
      </P>,
    ],
  },
  {
    id: 'nusxa-qoshish',
    num: '5',
    title: 'Jismoniy nusxa qo‘shish',
    icon: Icons.package,
    blocks: [
      <P key="0">
        Har bir kitobning qo‘lidagi jismoniy nusxalari shu yerda. <B>Inventar raqami</B> — kitobning
        “pasporti” (har bir nusxa uchun noyob raqam).
      </P>,
      <OL
        key="1"
        items={[
          <>
            Chap menyudan <B>Nusxalar</B> ni bosing
          </>,
          <>
            <B>+ Yangi nusxa</B> tugmasini bosing
          </>,
          <>Formani to‘ldiring:</>,
        ]}
      />,
      <Tbl
        key="2"
        head={['Maydon', 'Majburiymi?', 'Misol']}
        rows={[
          ['Kitob', <B key="a">Ha</B>, 'Ro‘yxatdan kitobni tanlang'],
          ['Inventar raqami', <B key="a">Ha</B>, 'INV-000001'],
          ['Javon', <>Yo‘q</>, 'A-3'],
          ['Izoh', <>Yo‘q</>, '“Yangi, birinchi nusxa”'],
        ]}
      />,
      <OL key="3" items={[<>Saqlash</>]} />,
      <P key="4">
        <B>Nusxa holatini o‘zgartirish</B> (ro‘yxatdagi tugmalar):
      </P>,
      <Tbl
        key="5"
        head={['Tugma', 'Qachon bosiladi']}
        rows={[
          [<B key="a">Ta‘mirga berish</B>, 'Kitob ta‘mirga ketayotganda'],
          [<B key="a">Qaytarish</B>, 'Ta‘mirdan qaytganda'],
          [<B key="a">Yo‘qolgan deb belgilash</B>, 'Kitob yo‘qolsa'],
        ]}
      />,
      <Note key="6" tone="info">
        <B>Avtomatik:</B> Nusxa qo‘shilsa yoki ta‘mirdan qaytsa, navbatdagi birinchi o‘quvchi
        Telegram orqali avtomatik xabar oladi — qo‘lda hech narsa qilish shart emas.
      </Note>,
    ],
  },
  {
    id: 'oquvchi-qoshish',
    num: '6',
    title: 'O‘quvchi yoki o‘qituvchi qo‘shish',
    icon: Icons.graduationCap,
    blocks: [
      <H3 key="0">Usul 1 — Telegram’dan kelgan ariza orqali (asosiy usul)</H3>,
      <P key="1">
        O‘quvchi botda ariza yuboradi → siz faqat <B>tasdiqlaysiz</B>. Batafsil — 9-bo‘lim.
      </P>,
      <H3 key="2">Usul 2 — qo‘lda</H3>,
      <OL
        key="3"
        items={[
          <>
            <B>O‘quvchilar</B> (yoki <B>O‘qituvchilar</B>) ni bosing
          </>,
          <>
            <B>+ Yangi o‘quvchi</B> tugmasi
          </>,
          <>To‘ldiring:</>,
        ]}
      />,
      <Tbl
        key="4"
        head={['Maydon', 'Majburiymi?', 'Misol']}
        rows={[
          ['To‘liq ismi', <B key="a">Ha</B>, 'Aliyev Vali'],
          ['Telefon', <B key="a">Ha</B>, '+998901234567'],
          [
            'Sinf (fan)',
            <span key="a">
              <B>Ha</B> (o‘qituvchi uchun)
            </span>,
            '7-A / Matematika',
          ],
          ['Tug‘ilgan sana', <>Yo‘q</>, '15.03.2012'],
          ['Manzil', <>Yo‘q</>, 'Toshkent sh.'],
        ]}
      />,
      <OL key="5" items={[<>Saqlash</>]} />,
      <Note key="6" tone="info">
        <B>Karta raqami avtomatik beriladi</B> — saqlangandan keyin yashil xabarda ko‘rinadi
        (masalan <Code>LIB-2026-0042</Code>). Shu raqamni o‘quvchiga bering.
      </Note>,
      <P key="7">
        <B>O‘quvchini bloklash</B> (kutubxonadan foydalanishini taqiqlash): Ro‘yxatdagi{' '}
        <B>Bloklash</B> tugmasi. Keyin <B>Faollashtirish</B> bilan qayta ochiladi.
      </P>,
    ],
  },
  {
    id: 'kitob-berish',
    num: '7',
    title: 'Kitob berish',
    icon: Icons.send,
    blocks: [
      <P key="0">Kunlik eng ko‘p ishlatiladigan bo‘lim.</P>,
      <OL
        key="1"
        items={[
          <>
            <B>Berish / Qaytarish</B> ni bosing
          </>,
          <>
            Yuqoridagi <B>+ Kitob berish</B> tugmasini bosing
          </>,
          <>
            <B>O‘quvchini toping:</B>
            <UL
              items={[
                <>
                  “Ism, sinf yoki telefon” maydoniga yozing (masalan “Vali”)
                </>,
                <>Ro‘yxatdan o‘quvchini tanlang</>,
              ]}
            />
          </>,
          <>
            <B>Kitobni toping:</B>
            <UL
              items={[
                <>
                  “Kitob nomi, muallif yoki ISBN” maydoniga yozing
                </>,
                <>Ro‘yxatdan kitobni tanlang</>,
              ]}
            />
          </>,
          <>
            <B>Muhim — rangli xabarni o‘qing:</B>
          </>,
        ]}
      />,
      <Tbl
        key="2"
        head={['Xabar rangi', 'Ma’nosi', 'Nima qilasiz']}
        rows={[
          [
            <span key="a" className="flex items-center gap-2">
              <Dot color="green" />
              <B>Yashil</B> “Beriladi: mavjud nusxa (3/5)”
            </span>,
            'Nusxalar bor',
            'Oddiy berasiz',
          ],
          [
            <span key="a" className="flex items-center gap-2">
              <Dot color="amber" />
              <B>Sariq</B> “Beriladi: kitob asli (nusxasi yo‘q)”
            </span>,
            'Faqat 1 nusxa (asli)',
            'Beriladi, lekin nusxasi yo‘q ekan',
          ],
          [
            <span key="a" className="flex items-center gap-2">
              <Dot color="amber" />
              <B>Sariq</B> “Barcha nusxalar band — o‘quvchi navbatga qo‘shiladi”
            </span>,
            'Hech qanday nusxa yo‘q',
            'Berish o‘rniga o‘quvchi navbatga tushadi — xato emas',
          ],
        ]}
      />,
      <OL key="3" items={[<>Berish tugmasini bosing</>]} />,
      <Note key="4" tone="success">
        <B>Tayyor!</B> O‘quvchiga Telegram’da qaytarish muddati bilan xabar boradi. Muddat — odatda{' '}
        <B>14 kun</B> (sozlamaga bog‘liq).
      </Note>,
      <P key="5">
        <B>Ixtiyoriy:</B> aniq qaysi nusxa (inventar raqami) borligini tanlash kerak bo‘lsa,{' '}
        <B>“Aniq nusxani qo‘lda tanlash”</B> belgisini bosing.
      </P>,
    ],
  },
  {
    id: 'kitob-qaytarish',
    num: '8',
    title: 'Kitobni qaytarib olish',
    icon: Icons.arrowsRightLeft,
    blocks: [
      <OL
        key="0"
        items={[
          <>
            <B>Berish / Qaytarish</B> bo‘limiga kiring
          </>,
          <>
            <B>Holat</B> filtrida <B>Faol</B> ni tanlang — hozir o‘quvchi qo‘lidagilar chiqadi
          </>,
          <>
            Kerakli qatorda <B>Qaytarish</B> tugmasini bosing
          </>,
          <>
            Tasdiqlash oynasini o‘qing: <i>“…qaytarasizmi? Muddat o‘tganda jarima avtomatik
            hisoblanadi.”</i>
          </>,
          <>
            <B>Qaytarish</B> tugmasini bosing
          </>,
        ]}
      />,
      <P key="1">
        <B>Natija:</B>
      </P>,
      <UL
        key="2"
        items={[
          <>
            Muddati o‘tgan bo‘lsa → xabarda <B>jarima miqdori</B> ko‘rsatiladi, u avtomatik
            hisoblanadi
          </>,
          <>
            Kitob navbatda kimsa bo‘lsa → navbatdagi odamga avtomatik taklif ketadi
          </>,
          <>
            Muddat ichida bo‘lsa → “Jarima yo‘q”
          </>,
        ]}
      />,
      <Note key="3" tone="alert">
        Jarimani <B>qo‘lda hisoblash shart emas</B> — tizim o‘zi hisoblaydi.
      </Note>,
      <P key="4">
        <B>Maslahat:</B> O‘quvchining barcha kitoblari va qarzini bir joyda ko‘rish uchun{' '}
        <B>O‘quvchilar</B> → o‘quvchi ismini bosing (13-bo‘lim).
      </P>,
    ],
  },
  {
    id: 'arizalarni-tasdiqlash',
    num: '9',
    title: 'Telegram’dan kelgan arizalarni tasdiqlash',
    icon: Icons.clipboardList,
    blocks: [
      <P key="0">
        O‘quvchi/o‘qituvchi botda ariza yuborganda, saytda <B>Arizalar</B> bo‘limida “Kutmoqda”
        holatida paydo bo‘ladi.
      </P>,
      <OL
        key="1"
        items={[
          <>
            <B>Arizalar</B> ni bosing — dastlab faqat <B>kutilayotgan</B> arizalar chiqadi
          </>,
          <>
            Arizani o‘qing: ism, telefon, sinf/fan (o‘qituvchi ikkitagacha fan tanlaydi, jumladan{' '}
            <B>Boshlang‘ich</B>), Telegram ID
          </>,
          <>Ikki variant:</>,
        ]}
      />,
      <H3 key="2">
        <span className="flex items-center gap-2">
          <Icons.checkCircle className="h-4.5 w-4.5 shrink-0 text-emerald-500" />
          Tasdiqlash (Qabul qilish)
        </span>
      </H3>,
      <OL
        key="3"
        items={[
          <>
            <B>Qabul qilish</B> tugmasini bosing
          </>,
          <>
            Tasdiqlash oynasini o‘qing: <i>“…karta raqami avtomatik beriladi va Telegram orqali
            xabar yuboriladi”</i>
          </>,
          <>
            <B>Qabul qilish</B> — tizim o‘quvchini ro‘yxatga oladi, karta raqamini beradi va unga
            Telegram’da xabar ketadi
          </>,
        ]}
      />,
      <H3 key="4">
        <span className="flex items-center gap-2">
          <Icons.xCircle className="h-4.5 w-4.5 shrink-0 text-red-500" />
          Rad etish
        </span>
      </H3>,
      <OL
        key="5"
        items={[
          <>
            <B>Rad etish</B> (qizil tugma) ni bosing
          </>,
          <>Sabab yozing (ixtiyoriy) — masalan: “yosh chegarasi 18”</>,
          <>
            <B>Rad etish</B> — sabab o‘quvchiga Telegram’da yuboriladi
          </>,
        ]}
      />,
      <Note key="6" tone="info">
        <B>Qo‘shimcha:</B> Qidiruv, Rol (O‘quvchi/O‘qituvchi) va Holat filtrlaridan foydalaning.
        Barcha arizalarni ko‘rish uchun Holatni “Barcha holatlar” qiling.
      </Note>,
      <Note key="7" tone="alert">
        <B>Noto‘g‘ri formatdagi arizalar.</B> Ism, telefon, sinf yoki fan noto‘g‘ri yozilgan
        arizalar (qabul qilinganlari ham) qaytadan yuborilishi shart — ular “qayta ariza kerak”
        deb belgilanadi. Foydalanuvchi to‘g‘ri formatda qayta yuborgach, ariza yana “Kutmoqda”
        holatida ko‘rinadi va uni tasdiqlash mumkin.
      </Note>,
    ],
  },
  {
    id: 'bandlar',
    num: '10',
    title: 'Band so‘rovlarini boshqarish',
    icon: Icons.lock,
    blocks: [
      <P key="0">
        O‘quvchi botda mavjud bo‘lmagan kitobni <B>band qilishni</B> so‘rasa, bu bo‘limga tushadi.
      </P>,
      <OL
        key="1"
        items={[
          <>
            <B>Bandlar</B> ni bosing — dastlab <B>Kutmoqda</B> so‘rovlar chiqadi
          </>,
          <>So‘rovni o‘qing: qaysi kitob, kim so‘ragan, qachon</>,
          <>Ikki variant:</>,
        ]}
      />,
      <Tbl
        key="2"
        head={['Tugma', 'Natija']}
        rows={[
          [<B key="a">Tasdiqlash</B>, 'Kitob o‘quvchiga beriladi, unga muddat bilan xabar ketadi'],
          [<B key="a">Rad etish</B>, 'Sabab yozasiz, kitob yana hamma uchun ochiq bo‘ladi'],
        ]}
      />,
      <OL
        key="3"
        items={[
          <>
            Ixtiyoriy <B>izoh</B> yozing (masalan: “3-sinf darsiga tayyorlanmoqda”) → tasdiqlang
          </>,
        ]}
      />,
      <Note key="4" tone="info">
        Tasdiqlash = o‘quvchiga kitob berish. Shu yerdan qo‘shimcha “Berish” bosqichiga o‘tish
        shart emas.
      </Note>,
    ],
  },
  {
    id: 'navbatlar',
    num: '11',
    title: 'Navbatlarni boshqarish',
    icon: Icons.clock,
    blocks: [
      <P key="0">
        Kitobning hamma nusxasi band/qilingan bo‘lsa, o‘quvchilar navbatga turadi. Kitob
        bo‘shaganda tizim <B>avtomatik taklif</B> yuboradi — siz faqat o‘quvchi kelganda
        tasdiqlaysiz.
      </P>,
      <OL key="1" items={[<><B>Navbatlar</B> ni bosing</>, <>Holat filtri bilan ishlang:</>]} />,
      <Tbl
        key="2"
        head={['Holat', 'Nimani anglatadi', 'Sizning harakatingiz']}
        rows={[
          [
            <span key="a" className="flex items-center gap-2">
              <Dot color="amber" />
              <B>Kutmoqda</B>
            </span>,
            'Navbatda turibdi',
            'Kuzatib boring',
          ],
          [
            <span key="a" className="flex items-center gap-2">
              <Dot color="blue" />
              <B>Taklif qilindi</B>
            </span>,
            'Nusxa ajratildi, javob kutilmoqda',
            'O‘quvchi javobini kuting',
          ],
          [
            <span key="a" className="flex items-center gap-2">
              <Dot color="green" />
              <B>Yakunlandi</B>
            </span>,
            'Kitob berildi',
            '—',
          ],
          [
            <span key="a" className="flex items-center gap-2">
              <Dot color="red" />
              <B>Bekor</B>
            </span>,
            'Navbat bekor qilindi',
            '—',
          ],
        ]}
      />,
      <OL
        key="3"
        items={[
          <>
            O‘quvchi “Olaman” deb javob berganda:
            <UL items={[<>Tasdiqlash → kitob unga beriladi, navbat yakunlanadi</>]} />
          </>,
          <>
            O‘quvchi kelmasa yoki “Kerak emas” desa:
            <UL items={[<>Bekor qilish → keyingi navbatdagi odamga taklif ketadi</>]} />
          </>,
        ]}
      />,
      <Note key="4" tone="info">
        Taklif <B>24 soat</B> amal qiladi. Javob berilmasa, tizim o‘zi keyingisiga o‘tkazadi (buni
        siz qo‘lda qilishingiz shart emas).
      </Note>,
    ],
  },
  {
    id: 'jarimalar',
    num: '12',
    title: 'Jarimani qabul qilish',
    icon: Icons.money,
    blocks: [
      <P key="0">
        O‘quvchi kechiktirib kitob qaytarganda jarima avtomatik hisoblanadi. Naqd pul qabul
        qilgandan keyin:
      </P>,
      <OL
        key="1"
        items={[
          <>
            <B>Jarimalar</B> ni bosing (yoki Boshqaruv panelidagi sariq kartochkani bosing)
          </>,
          <>
            Filtrda <B>To‘lanmagan</B> ni tanlang
          </>,
          <>
            Kerakli qatorda <B>To‘landi</B> tugmasini bosing
          </>,
          <>
            Tasdiqlash oynasini o‘qing → <B>To‘langan deb belgilash</B>
          </>,
        ]}
      />,
      <Note key="2" tone="success">
        O‘quvchiga Telegram’da to‘langani haqida xabar boradi. Qarzdorlik kartochkasi darhol
        yangilanadi.
      </Note>,
      <P key="3">
        <B>Jarima qanday hisoblanadi?</B>
      </P>,
      <P key="4">
        <Code>Kechikkan kunlar × kunlik jarima</Code> — masalan 3 kun × 5000 so‘m ={' '}
        <B>15 000 so‘m</B>. Kunlik miqdor sozlamada (5000 so‘m) o‘zgartirilishi mumkin.
      </P>,
    ],
  },
  {
    id: 'oquvchini-kuzatish',
    num: '13',
    title: 'O‘quvchini kuzatish',
    icon: Icons.idCard,
    blocks: [
      <P key="0">Bitta o‘quvchining hamma narsasini bir joyda ko‘rish:</P>,
      <OL
        key="1"
        items={[
          <>
            <B>O‘quvchilar</B> → qidiruvdan o‘quvchini toping
          </>,
          <>
            Ismini bosing — <B>tafsilot sahifasi</B> ochiladi
          </>,
        ]}
      />,
      <P key="2">
        <B>Bu yerda ko‘rasiz:</B>
      </P>,
      <UL
        key="3"
        items={[
          <>Shaxsiy ma’lumotlar (sinf, telefon, karta raqami, Telegram bog‘langanmi)</>,
          <>
            <B>Joriy kitoblar</B> — qo‘lidagi kitoblar, muddat va <B>qolgan kun</B> (qizil =
            muddati o‘tgan)
          </>,
          <>
            <B>To‘lanmagan jarimalar</B> — qarzi
          </>,
        ]}
      />,
      <P key="4">
        <B>Shu yerdan amalga oshirasiz:</B>
      </P>,
      <UL
        key="5"
        items={[
          <>
            <B>Qaytarish</B> — qo‘lidagi kitobni qaytarib olish
          </>,
          <>
            <B>To‘landi deb belgilash</B> — jarimani yopish
          </>,
        ]}
      />,
    ],
  },
  {
    id: 'xodim-qoshish',
    num: '14',
    title: 'Xodim qo‘shish (faqat administrator)',
    icon: Icons.shield,
    blocks: [
      <P key="0">
        <B>Xodimlar</B> bo‘limi faqat administratorga ko‘rinadi.
      </P>,
      <OL
        key="1"
        items={[
          <>
            <B>Xodimlar</B> → <B>+ Yangi xodim</B>
          </>,
          <>
            To‘ldiring: To‘liq ismi, Foydalanuvchi nomi (login), Parol, Lavozim (Kutubxonachi /
            Administrator)
          </>,
          <>
            <B>Saqlash</B> → xodimga login va parolni bering
          </>,
        ]}
      />,
      <P key="2">
        <B>Xodimni ishdan olish:</B> <B>Bloklash</B> — kirishi o‘chadi, lekin ma’lumotlari
        saqlanadi. Keyin qayta <B>Faollashtirish</B> mumkin.
      </P>,
    ],
  },
  {
    id: 'profil',
    num: '15',
    title: 'Profil, xabar yuborish va o‘chirish',
    icon: Icons.idCard,
    blocks: [
      <P key="0">
        Chap menyudagi <B>Profil</B> tugmasi orqali hisobingizni boshqarasiz. U <B>Chiqish</B>
        tugmasi ustida joylashgan.
      </P>,
      <H3 key="1">Shaxsiy ma’lumotlarni o‘zgartirish</H3>,
      <OL
        key="2"
        items={[
          <>
            <B>Profil</B> → <B>Shaxsiy ma’lumotlar</B> → <B>Tahrirlash</B>
          </>,
          <>
            To‘liq ism, foydalanuvchi nomi (login) va telefon raqamini o‘zgartiring
          </>,
          <>
            <B>Saqlash</B> — yangi ma’lumotlar darhol saqlanadi; parol o‘zgarmaydi
          </>,
        ]}
      />,
      <Note key="3" tone="info">
        Login allaqachon boshqa xodimda bor bo‘lsa, saqlanmaydi — boshqa login tanlang.
      </Note>,
      <H3 key="4">Parol almashtirish</H3>,
      <P key="5">
        <B>Profil</B> → <B>Parol almashtirish</B>: avval eski parolni, keyin yangi parolni ikki marta
        kiriting. Eski parol noto‘g‘ri bo‘lsa, parol o‘zgarmaydi.
      </P>,
      <H3 key="8">Kitobxonlarga xabar yuborish</H3>,
      <P key="9">
        <B>Profil</B> → <B>Kitobxonlarga xabar yuborish</B> orqali Telegram orqali xabar yuborasiz:
      </P>,
      <Tbl
        key="10"
        head={['Yuborish usuli', 'Qachon ishlatiladi']}
        rows={[
          [<>Bitta o‘quvchi/o‘qituvchi</>, <>Bir kishiga shaxsiy xabar</>],
          [<>Sinf bo‘yicha</>, <>Masalan, 7-A dagi barcha o‘quvchilarga</>],
          [<>Barcha sinflarga</>, <>Tanlangan roldagi hamma faol kitobxonlarga</>],
        ]}
      />,
      <Note key="11" tone="bell">
        Telegram ID si bo‘lmagan kitobxonlar hisobga olinadi, lekin ularga xabar bormaydi — natijada
        “Telegram yo‘q” deb ko‘rsatiladi. Xabar yuborish uchun kutubxonaning Telegram boti ulangan
        bo‘lishi shart.
      </Note>,
      <H3 key="11a">Xatolik haqida xabar berish</H3>,
      <P key="11b">
        <B>Profil</B> → <B>Xatolik haqida xabar berish</B> bo‘limida saytdagi nosozlikni yozib
        yuboring. Xabar saqlanadi va kutubxona egasi/administratorlarining Telegram‘iga yetkaziladi.
        <B> «Xatolik yuz berganda avtomatik yuborish»</B> standart yoqilgan: ushlanmagan xatolar
        va server xatolari ham o‘z-o‘zidan yuboriladi (istamasangiz katakchani o‘chiring).
      </P>,
      <H3 key="12">O‘quvchi va o‘qituvchilarni o‘chirish</H3>,
      <OL
        key="13"
        items={[
          <>
            <B>Profil</B> → <B>Kitobxonlarni o‘chirish</B> → rol tanlang → qidirib, belgilang →{' '}
            <B>O‘chirish</B>
          </>,
          <>
            Faqat <B>qo‘lidagi kitob qaytarilmagan</B> yoki <B>kutilayotgan band so‘rovi</B> borlar
            o‘chirilmaydi — ular <B>Berishlar</B> / <B>Bandlar</B> bo‘limida ko‘rinadi
          </>,
          <>
            Qaytarilgan kitoblar va yakunlangan band so‘rovlari tarixi endi to‘sqinlik qilmaydi —
            bunday kitobxonlar ham o‘chiriladi
          </>,
          <>
            O‘chirilgan kitobxonga Telegram orqali xabar ketadi: <B>/start</B> buyrug‘i bilan
            qaytadan a‘riza topshirishi so‘raladi. Eski arizasi o‘chiriladi, shuning uchun bot
            uni “arizangiz kutmoqda” deb bloklamaydi
          </>,
        ]}
      />,
      <Note key="14" tone="alert">
        O‘chirib bo‘lmaganlar ro‘yxami va sababi natija oynasida ko‘rsatiladi. Avval kitobni
        qaytarib oling yoki band so‘rovini tasdiqlang/rad eting, keyin qayta urinib ko‘ring.
      </Note>,
    ],
  },
  {
    id: 'kunlik-tartib',
    num: '16',
    title: 'Kunlik ish tartibi',
    icon: Icons.calendar,
    blocks: [
      <P key="0">
        <B>Kun boshida:</B>
      </P>,
      <OL
        key="1"
        items={[
          <>
            <B>Boshqaruv paneli</B> — qizil/sariq kartochkalarni tekshiring (muddati o‘tganlar,
            qarzdorlar)
          </>,
          <>
            <B>Arizalar</B> — Telegram’dan kelgan arizalarni tasdiqlang
          </>,
        ]}
      />,
      <P key="2">
        <B>Kun davomida:</B>
      </P>,
      <OL
        key="3"
        items={[
          <>
            <B>Berish / Qaytarish</B> — kelgan o‘quvchilarga kitob bering, qaytarib oling
          </>,
          <>
            <B>Bandlar</B> — kutilayotgan band so‘rovlarini javoblang
          </>,
          <>
            <B>Navbatlar</B> — o‘quvchi kelgan bo‘lsa tasdiqlang
          </>,
        ]}
      />,
      <P key="4">
        <B>Kun oxirida:</B>
      </P>,
      <OL key="5" items={[<>Jarimalar — naqd pul kelgan bo‘lsa yoping</>]} />,
      <Note key="6" tone="bell">
        <B>Eslatma:</B> Berish, qaytarish, ariza javobi, jarima va navbat takliflari — <B>hammasi
        Telegram orqali avtomatik</B> yuboriladi. Qo‘lda xabar yozish shart emas.
      </Note>,
    ],
  },
  {
    id: 'faq',
    num: '17',
    title: 'Tez-tez so‘raladigan savollar',
    icon: Icons.chat,
    blocks: [
      <H3 key="0">Kitob topilmadi (nusxasi yo‘q)?</H3>,
      <P key="1">
        Uni <B>Kitoblar</B> bo‘limida qo‘shing, keyin <B>Nusxalar</B> bo‘limida kamida bitta nusxa
        qo‘shing. Nusxasiz ham berish mumkin — lekin u “asli” sifatida beriladi.
      </P>,
      <H3 key="2">O‘quvchi hamma nusxa band bo‘lib keldi?</H3>,
      <P key="3">
        “Berish” tugmasini bosing — xato chiqmaydi, o‘quvchi avtomatik navbatga qo‘shiladi va unga
        xabar boradi.
      </P>,
      <H3 key="4">Xato qilib noto‘g‘ri o‘quvchiga kitob berdim?</H3>,
      <P key="5">
        Derabsiz — <B>Berish/Qaytarish</B> bo‘limidan kitobni qaytarib oling (o‘sha o‘quvchidan),
        keyin to‘g‘ri o‘quvchiga qayta bering.
      </P>,
      <H3 key="6">O‘quvchi kelmayapti, lekin taklif muddati tugayapti?</H3>,
      <P key="7">
        Hech narsa qilmang — 24 soatdan keyin tizim o‘zi bekor qilib, keyingi odamga taklif
        yuboradi.
      </P>,
      <H3 key="8">Parolni unutdim?</H3>,
      <P key="9">
        Eski parolni bilsangiz, <B>Profil</B> → <B>Parol almashtirish</B> orqali o‘zingiz
        o‘zgartirishingiz mumkin. Unutgan bo‘lsangiz — administrator yangi parol beradi (
        <B>Xodimlar</B> → <B>Tahrirlash</B>).
      </P>,
      <H3 key="8a">Band qilgan o‘quvchini o‘chira olmayapman, lekin Bandlar bo‘limida yo‘q?</H3>,
      <P key="9a">
        Bu tarixiy band so‘rovi (tasdiqlangan, rad etilgan yoki bekor qilingan) bo‘lib, endi to‘sqinlik
        qilmaydi. Sahifani yangilab, qayta o‘chirib ko‘ring. Agar <B>kutmoqda</B> holatidagi so‘rov
        bo‘lsa — u Bandlar bo‘limida ko‘rinadi, avval uni tasdiqlang yoki rad eting.
      </P>,
      <H3 key="10">Sayt ochilmayapti?</H3>,
      <P key="11">
        Avval internetni tekshiring. Ishlasa ham ochilmasa — administratorga xabar bering.
      </P>,
      <H3 key="12">O‘quvchi saytga kirishi kerakmi?</H3>,
      <P key="13">
        Yo‘q. O‘quvchilar faqat <B>Telegram bot</B>dan foydalanadi — sayt faqat kutubxonachilar
        uchun.
      </P>,
      <H3 key="14">Kitob necha kunga beriladi?</H3>,
      <P key="15">
        Odatda <B>14 kun</B>. Aniq muddat berish oynasidagi xabarda yoziladi.
      </P>,
      <H3 key="16">Jarimani qo‘lda hisoblaymanmi?</H3>,
      <P key="17">
        Yo‘q — tizim qaytarish paytida o‘zi hisoblaydi. Siz faqat naqd pul olgandan keyin
        “To‘landi” deb belgilaysiz.
      </P>,
    ],
  },
]

/* ------------------------------------------------------------------ */
/*  Kitob animatsiyalari                                                */
/* ------------------------------------------------------------------ */

const kitobAnimatsiyasi = `
@keyframes qollanma-flip-next {
  from { opacity: 0; transform: perspective(1400px) rotateY(-16deg) translateX(18px); }
  to   { opacity: 1; transform: perspective(1400px) rotateY(0deg) translateX(0); }
}
@keyframes qollanma-flip-prev {
  from { opacity: 0; transform: perspective(1400px) rotateY(16deg) translateX(-18px); }
  to   { opacity: 1; transform: perspective(1400px) rotateY(0deg) translateX(0); }
}
@keyframes qollanma-open {
  from { opacity: 0; transform: perspective(1400px) rotateY(-26deg) scale(0.95); }
  to   { opacity: 1; transform: perspective(1400px) rotateY(0deg) scale(1); }
}
`

/* ------------------------------------------------------------------ */
/*  Sahifa — kitob ko'rinishida                                        */
/* ------------------------------------------------------------------ */

export function Guide() {
  const [ochilgan, setOchilgan] = useState(false)
  const [keng, setKeng] = useState(true)
  const [activeId, setActiveId] = useState(sections[0].id)
  const [yornalish, setYornalish] = useState<'next' | 'prev'>('next')

  const index = sections.findIndex((s) => s.id === activeId)
  const active = sections[index]
  const prev = sections[index - 1]
  const next = sections[index + 1]

  /** Varaqlash — sahifani kengaytirib, yo'nalish bo'yicha animatsiya qiladi. */
  const varoq = (id: string, yonalish: 'next' | 'prev') => {
    setYornalish(yonalish)
    setActiveId(id)
    setKeng(true)
  }

  const umumiySarlavha = (
    <PageHeader
      title={
        <>
          <Icons.bookOpen className="h-6 w-6 shrink-0 text-slate-400" />
          Qo‘llanma
        </>
      }
      subtitle="Saytdan foydalanish bo‘icha qo‘llanma — kitobni ochib varaqlang"
    />
  )

  /* ----------------------- Yopiq kitob (muqova) ---------------------- */
  if (!ochilgan) {
    return (
      <div>
        <style>{kitobAnimatsiyasi}</style>
        {umumiySarlavha}

        <div className="flex min-h-[65dvh] items-center justify-center px-4 py-10">
          <button
            type="button"
            onClick={() => setOchilgan(true)}
            aria-label="Qo‘llanma kitobini ochish"
            className="group relative block w-[19rem] max-w-full text-left focus:outline-none"
          >
            {/* Orqadagi sahifalar */}
            <div className="absolute -right-1.5 top-1.5 h-full w-full rounded-r-2xl border border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-700/70" />
            <div className="absolute -right-0.5 top-0.5 h-full w-full rounded-r-2xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800" />

            {/* Muqova */}
            <div className="relative flex h-[min(26rem,52dvh)] min-h-[17rem] flex-col justify-between overflow-hidden rounded-2xl rounded-l-md bg-gradient-to-br from-brand-500 via-brand-700 to-brand-900 p-7 text-white shadow-2xl ring-1 ring-black/10 transition-all duration-300 group-hover:-translate-y-2 group-hover:shadow-[0_25px_50px_-12px_rgba(0,0,0,0.35)] group-focus-visible:ring-4 group-focus-visible:ring-brand-400">
              {/* Umurtqa */}
              <div className="absolute inset-y-0 left-0 w-3.5 bg-black/25" />
              <div className="absolute inset-y-0 left-3.5 w-px bg-white/25" />
              <div className="absolute -right-16 -top-16 h-48 w-48 rounded-full bg-white/10 blur-2xl" />
              <div className="absolute -bottom-20 -left-10 h-52 w-52 rounded-full bg-black/20 blur-2xl" />

              <div className="relative">
                <Icons.bookClosed className="h-11 w-11 text-white/85" />
              </div>

              <div className="relative">
                <div className="text-[2rem] font-bold leading-tight">Qo‘llanma</div>
                <div className="mt-2 text-sm text-white/75">Saytdan foydalanish bo‘yicha</div>
                <div className="mt-5 h-px w-16 bg-white/40" />
              </div>

              <div className="relative flex items-center justify-between">
                <span className="rounded-full bg-white/15 px-3 py-1 text-xs font-medium">
                  {sections.length} bob
                </span>
                <span className="flex items-center gap-1.5 text-sm font-semibold">
                  Ochish <Icons.arrowLeft className="h-4 w-4 rotate-180" />
                </span>
              </div>
            </div>
          </button>
        </div>
      </div>
    )
  }

  /* -------------------------- Ochiq kitob ---------------------------- */
  return (
    <div>
      <style>{kitobAnimatsiyasi}</style>
      {umumiySarlavha}

      {/* Boshqaruv paneli */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-paper px-4 py-2.5 shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <button
          type="button"
          onClick={() => setOchilgan(false)}
          className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700"
        >
          <Icons.close className="h-4 w-4" /> Kitobni yopish
        </button>

        <div className="flex items-center gap-3">
          <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
            {index + 1} / {sections.length} — {active.title}
          </span>
          <button
            type="button"
            onClick={() => setKeng(!keng)}
            className={clsx(
              'rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors',
              keng
                ? 'border-brand-200 bg-brand-50 text-brand-700 dark:border-brand-500/30 dark:bg-brand-900/30 dark:text-brand-300'
                : 'border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-700',
            )}
          >
            {keng ? 'Keng ko‘rinish' : 'Tor ko‘rinish'}
          </button>
        </div>
      </div>

      {/* Kitob */}
      <div
        className={clsx(
          'relative mx-auto w-full transition-[max-width] duration-700 ease-out',
          keng ? 'max-w-none' : 'max-w-3xl',
        )}
        style={{ animation: 'qollanma-open 0.5s ease-out both' }}
      >
        <div className="overflow-hidden rounded-2xl border border-slate-300 bg-[#fffdf8] shadow-2xl ring-1 ring-black/5 dark:border-slate-700 dark:bg-slate-900 dark:ring-white/5">
          {/* Kitob ustki qismi */}
          <div className="flex items-center justify-between border-b border-slate-200/80 bg-slate-50/80 px-4 py-2.5 dark:border-slate-700 dark:bg-slate-800/60">
            <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-slate-400">
              <Icons.bookOpen className="h-4 w-4" /> Qo‘llanma
            </div>
            <div className="text-xs text-slate-400">Bob {active.num}</div>
          </div>

          <div className={clsx('relative grid', keng && 'lg:grid-cols-2')}>
            {/* Chap sahifa — mundarija (faqat keng ko'rinishda) */}
            {keng && (
              <div className="relative border-b border-slate-200 bg-slate-50/60 p-5 lg:border-b-0 lg:border-r dark:border-slate-700 dark:bg-slate-800/30 lg:p-7">
                <div className="mb-4 flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-slate-400">
                  <Icons.note className="h-4 w-4" /> Mundarija
                </div>
                <ul className="grid grid-cols-1 gap-0.5 sm:grid-cols-2 lg:grid-cols-1">
                  {sections.map((s) => {
                    const faol = s.id === activeId
                    const sIndex = sections.findIndex((x) => x.id === s.id)
                    return (
                      <li key={s.id}>
                        <button
                          type="button"
                          onClick={() => varoq(s.id, sIndex > index ? 'next' : 'prev')}
                          aria-current={faol ? 'true' : undefined}
                          className={clsx(
                            'flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-sm transition-colors',
                            faol
                              ? 'bg-brand-50 font-medium text-brand-700 dark:bg-brand-900/30 dark:text-brand-300'
                              : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700/50',
                          )}
                        >
                          <span
                            className={clsx(
                              'flex h-6 w-6 shrink-0 items-center justify-center rounded text-xs',
                              faol
                                ? 'bg-brand-100 text-brand-700 dark:bg-brand-900/50 dark:text-brand-300'
                                : 'bg-slate-100 text-slate-500 dark:bg-slate-700 dark:text-slate-300',
                            )}
                          >
                            {s.num}
                          </span>
                          <span className="min-w-0 truncate">{s.title}</span>
                        </button>
                      </li>
                    )
                  })}
                </ul>
              </div>
            )}

            {/* O'ng sahifa — bob mazmuni */}
            <div
              key={`${activeId}-${yornalish}`}
              className="p-5 sm:p-8 lg:p-10"
              style={{
                animation: `qollanma-flip-${yornalish} 0.38s ease-out both`,
                transformOrigin: yornalish === 'next' ? 'left center' : 'right center',
              }}
            >
              <div className="mb-6 flex items-start gap-3 border-b border-slate-200 pb-4 dark:border-slate-700">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-900/40 dark:text-brand-300">
                  {active.icon({ className: 'h-5 w-5' })}
                </span>
                <div className="min-w-0">
                  <div className="text-xs font-medium uppercase tracking-wider text-slate-400">
                    {active.num}-bob
                  </div>
                  <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
                    {active.title}
                  </h2>
                </div>
              </div>

              <div className="space-y-4">{active.blocks}</div>

              {/* Oldingi / Keyingi varaqlar */}
              <div className="mt-10 flex flex-col gap-3 border-t border-slate-200 pt-5 sm:flex-row sm:items-center sm:justify-between dark:border-slate-700">
                {prev ? (
                  <button
                    type="button"
                    onClick={() => varoq(prev.id, 'prev')}
                    className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-left text-sm text-slate-600 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-700/50"
                  >
                    <Icons.arrowLeft className="h-4 w-4 shrink-0" />
                    <span className="min-w-0">
                      <span className="block text-xs text-slate-400">Oldingi varaqlar</span>
                      <span className="block truncate font-medium">
                        {prev.num}. {prev.title}
                      </span>
                    </span>
                  </button>
                ) : (
                  <span />
                )}

                {next ? (
                  <button
                    type="button"
                    onClick={() => varoq(next.id, 'next')}
                    className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-right text-sm text-slate-600 transition-colors hover:bg-slate-50 sm:ml-auto dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-700/50"
                  >
                    <span className="min-w-0">
                      <span className="block text-xs text-slate-400">Keyingi varaqlar</span>
                      <span className="block truncate font-medium">
                        {next.num}. {next.title}
                      </span>
                    </span>
                    <Icons.arrowLeft className="h-4 w-4 shrink-0 rotate-180" />
                  </button>
                ) : null}
              </div>
            </div>
          </div>

          {/* Kitob umurtqasi (keng ko'rinishda o'rtada) */}
          {keng && (
            <div className="pointer-events-none absolute inset-y-0 left-1/2 hidden w-10 -translate-x-1/2 bg-gradient-to-r from-transparent via-slate-900/[0.06] to-transparent lg:block dark:via-black/30" />
          )}
        </div>

        <p className="mt-3 text-center text-xs text-slate-400">
          Varaqlar almashganda kitob kengayadi · Tarkib bo‘limiga bosib istalgan bobga o‘ting
        </p>
      </div>
    </div>
  )
}

/** Login'dan oldin ham ochiladigan qo'llanma (kirish talab qilinmaydi). */
export function PublicGuide() {
  return (
    <div className="min-h-dvh bg-canvas px-4 py-6 dark:bg-slate-900">
      <div className="mx-auto max-w-6xl">
        <Link
          to="/login"
          className="mb-4 inline-flex items-center gap-1 text-sm font-medium text-brand-700 hover:underline dark:text-brand-300"
        >
          ← Kirish sahifasiga qaytish
        </Link>
        <Guide />
      </div>
    </div>
  )
}
