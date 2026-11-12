import { useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import clsx from 'clsx'
import { Logo } from '../components/Logo'
import { Badge, Button, Card, Field, Input, Label, Select } from '../components/ui'

/*
 * Interactive demo (/demo). Everything lives in React state: no API calls, no storage.
 * Reloading the page resets it. The banner says so.
 */

interface DemoBook {
  id: number
  title: string
  author: string
  copies: number
}
interface DemoReader {
  id: number
  name: string
  grade: string
}
interface DemoLoan {
  id: number
  bookId: number
  readerId: number
  daysLeft: number // negative = overdue
  returned: boolean
}

const FINE_PER_DAY = 5000

const SEED_BOOKS: DemoBook[] = [
  { id: 1, title: 'O‘tkan kunlar', author: 'Abdulla Qodiriy', copies: 3 },
  { id: 2, title: 'Dunyoning ishlari', author: 'O‘tkir Hoshimov', copies: 2 },
]
const SEED_READERS: DemoReader[] = [{ id: 1, name: 'Dilnoza Karimova', grade: '9-A' }]

const STEPS = [
  { title: 'Kitob qo‘shing', hint: 'Nomi va muallifini yozing. Nusxalar sonini ham kiriting.' },
  { title: 'O‘quvchi qo‘shing', hint: 'Ism va sinfni yozing. Karta raqami tizimda o‘zi chiqadi.' },
  { title: 'Kitob bering', hint: 'O‘quvchi va kitobni tanlang. Qaytarish muddati 14 kun.' },
  { title: 'Qaytarib oling', hint: 'Kechikkan kitob uchun jarima o‘zi hisoblanadi.' },
] as const

export function Demo() {
  const [step, setStep] = useState(0)
  const [books, setBooks] = useState(SEED_BOOKS)
  const [readers, setReaders] = useState(SEED_READERS)
  const [loans, setLoans] = useState<DemoLoan[]>([])
  const [nextId, setNextId] = useState(100)

  const [title, setTitle] = useState('')
  const [author, setAuthor] = useState('')
  const [copies, setCopies] = useState('1')
  const [name, setName] = useState('')
  const [grade, setGrade] = useState('')
  const [readerId, setReaderId] = useState('')
  const [bookId, setBookId] = useState('')

  const id = () => {
    setNextId((n) => n + 1)
    return nextId
  }

  const free = (b: DemoBook) => b.copies - loans.filter((l) => l.bookId === b.id && !l.returned).length
  const bookOf = (i: number) => books.find((b) => b.id === i)
  const readerOf = (i: number) => readers.find((r) => r.id === i)

  const totalFine = useMemo(
    () =>
      loans
        .filter((l) => l.returned && l.daysLeft < 0)
        .reduce((sum, l) => sum + -l.daysLeft * FINE_PER_DAY, 0),
    [loans],
  )

  function addBook(e: FormEvent) {
    e.preventDefault()
    if (!title.trim() || !author.trim()) return
    setBooks([...books, { id: id(), title: title.trim(), author: author.trim(), copies: Math.max(1, Number(copies) || 1) }])
    setTitle('')
    setAuthor('')
    setCopies('1')
  }

  function addReader(e: FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    setReaders([...readers, { id: id(), name: name.trim(), grade: grade.trim() || '—' }])
    setName('')
    setGrade('')
  }

  function lend(e: FormEvent) {
    e.preventDefault()
    const b = bookOf(Number(bookId))
    if (!b || !readerOf(Number(readerId)) || free(b) < 1) return
    setLoans([{ id: id(), bookId: b.id, readerId: Number(readerId), daysLeft: 14, returned: false }, ...loans])
    setBookId('')
  }

  // Demo shortcut: pretend 20 days passed for this loan so the fine shows up.
  const skipTime = (loanId: number) =>
    setLoans(loans.map((l) => (l.id === loanId ? { ...l, daysLeft: -6 } : l)))
  const giveBack = (loanId: number) =>
    setLoans(loans.map((l) => (l.id === loanId ? { ...l, returned: true } : l)))

  function reset() {
    setBooks(SEED_BOOKS)
    setReaders(SEED_READERS)
    setLoans([])
    setStep(0)
  }

  const activeLoans = loans.filter((l) => !l.returned)

  return (
    <div className="min-h-dvh bg-canvas dark:bg-slate-900">
      <header className="mx-auto flex h-16 max-w-4xl items-center justify-between px-4">
        <Link to="/welcome" aria-label="Bosh sahifa">
          <Logo />
        </Link>
        <div className="flex items-center gap-2">
          <Link
            to="/login"
            className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-800 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-100 dark:hover:bg-slate-800"
          >
            Tizimga kirish
          </Link>
          <Link
            to="/register"
            className="rounded-full bg-brand-700 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-800"
          >
            Ro‘yxatdan o‘tish
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-4 pb-16">
        <div
          role="status"
          className="mb-5 flex flex-wrap items-center justify-between gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-500/30 dark:bg-amber-950/40 dark:text-amber-200"
        >
          <span>
            <b>Sinov rejimi.</b> Yozganlaringiz serverga yuborilmaydi va saqlanmaydi. Sahifani yangilasangiz, hammasi
            tozalanadi.
          </span>
          <button onClick={reset} className="font-semibold underline underline-offset-2">
            Boshidan boshlash
          </button>
        </div>

        <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl dark:text-slate-100">O‘zingiz sinab ko‘ring</h1>
        <p className="mt-1 text-slate-600 dark:text-slate-400">
          To‘rt qadam: kitob, o‘quvchi, berish, qaytarish. Har birini tugmani bosib bajarasiz.
        </p>

        {/* Steps */}
        <ol className="mt-6 grid grid-cols-4 gap-2" aria-label="Qadamlar">
          {STEPS.map((s, i) => (
            <li key={s.title}>
              <button
                onClick={() => setStep(i)}
                aria-current={i === step ? 'step' : undefined}
                className={clsx(
                  'flex w-full flex-col items-start gap-1 rounded-xl border px-3 py-2 text-left transition',
                  i === step
                    ? 'border-brand-600 bg-brand-50 dark:bg-brand-950/40'
                    : 'border-slate-200 bg-paper hover:border-slate-300 dark:border-slate-700 dark:bg-slate-800',
                )}
              >
                <span
                  className={clsx(
                    'flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold',
                    i <= step ? 'bg-brand-700 text-white' : 'bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-300',
                  )}
                >
                  {i + 1}
                </span>
                <span className="hidden text-sm font-medium text-slate-800 sm:block dark:text-slate-100">{s.title}</span>
              </button>
            </li>
          ))}
        </ol>

        <Card className="mt-4 p-4 sm:p-6">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            {step + 1}. {STEPS[step].title}
          </h2>
          <p className="mb-4 mt-1 text-sm text-slate-600 dark:text-slate-400">{STEPS[step].hint}</p>

          {step === 0 && (
            <>
              <form onSubmit={addBook} className="grid gap-3 sm:grid-cols-[1fr_1fr_6rem_auto] sm:items-end">
                <div>
                  <Label htmlFor="d-title">Nomi</Label>
                  <Input id="d-title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Masalan, Mehrobdan chayon" />
                </div>
                <div>
                  <Label htmlFor="d-author">Muallif</Label>
                  <Input id="d-author" value={author} onChange={(e) => setAuthor(e.target.value)} placeholder="Abdulla Qodiriy" />
                </div>
                <div>
                  <Label htmlFor="d-copies">Nusxa</Label>
                  <Input id="d-copies" type="number" min={1} value={copies} onChange={(e) => setCopies(e.target.value)} />
                </div>
                <Button type="submit" disabled={!title.trim() || !author.trim()}>
                  Qo‘shish
                </Button>
              </form>
              <ul className="mt-5 divide-y divide-slate-100 dark:divide-slate-700">
                {books.map((b) => (
                  <li key={b.id} className="flex items-center justify-between gap-3 py-2.5">
                    <div className="min-w-0">
                      <div className="truncate font-medium text-slate-900 dark:text-slate-100">{b.title}</div>
                      <div className="text-sm text-slate-500">{b.author}</div>
                    </div>
                    <Badge tone={free(b) > 0 ? 'green' : 'red'}>
                      {free(b)}/{b.copies} javonda
                    </Badge>
                  </li>
                ))}
              </ul>
            </>
          )}

          {step === 1 && (
            <>
              <form onSubmit={addReader} className="grid gap-3 sm:grid-cols-[1fr_8rem_auto] sm:items-end">
                <div>
                  <Label htmlFor="d-name">Ism</Label>
                  <Input id="d-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Ism va familiya" />
                </div>
                <div>
                  <Label htmlFor="d-grade">Sinf</Label>
                  <Input id="d-grade" value={grade} onChange={(e) => setGrade(e.target.value)} placeholder="8-B" />
                </div>
                <Button type="submit" disabled={!name.trim()}>
                  Qo‘shish
                </Button>
              </form>
              <ul className="mt-5 divide-y divide-slate-100 dark:divide-slate-700">
                {readers.map((r, i) => (
                  <li key={r.id} className="flex items-center justify-between gap-3 py-2.5">
                    <span className="font-medium text-slate-900 dark:text-slate-100">{r.name}</span>
                    <span className="text-sm text-slate-500">
                      {r.grade} · karta № {String(1000 + i + 1)}
                    </span>
                  </li>
                ))}
              </ul>
            </>
          )}

          {step === 2 && (
            <>
              <form onSubmit={lend} className="grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
                <Field className="mb-0">
                  <Label htmlFor="d-reader">O‘quvchi</Label>
                  <Select id="d-reader" value={readerId} onChange={(e) => setReaderId(e.target.value)}>
                    <option value="">Tanlang</option>
                    {readers.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.name}
                      </option>
                    ))}
                  </Select>
                </Field>
                <Field className="mb-0">
                  <Label htmlFor="d-book">Kitob</Label>
                  <Select id="d-book" value={bookId} onChange={(e) => setBookId(e.target.value)}>
                    <option value="">Tanlang</option>
                    {books.map((b) => (
                      <option key={b.id} value={b.id} disabled={free(b) < 1}>
                        {b.title}
                        {free(b) < 1 ? ' (qolmagan)' : ''}
                      </option>
                    ))}
                  </Select>
                </Field>
                <Button type="submit" disabled={!readerId || !bookId}>
                  Berish
                </Button>
              </form>
              <LoanList
                loans={activeLoans}
                bookOf={bookOf}
                readerOf={readerOf}
                empty="Hali hech kim kitob olmagan."
              />
            </>
          )}

          {step === 3 && (
            <>
              <LoanList
                loans={loans}
                bookOf={bookOf}
                readerOf={readerOf}
                empty="Avval 3-qadamda kitob bering."
                onGiveBack={giveBack}
                onSkip={skipTime}
              />
              {totalFine > 0 && (
                <div className="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-800 dark:bg-red-950/40 dark:text-red-300">
                  Jarima: <b>{totalFine.toLocaleString('uz-UZ')} so‘m</b> ({FINE_PER_DAY.toLocaleString('uz-UZ')} so‘m
                  × kechikkan kun). Haqiqiy tizimda u Jarimalar bo‘limiga tushadi.
                </div>
              )}
            </>
          )}

          <div className="mt-6 flex items-center justify-between">
            <Button variant="secondary" onClick={() => setStep(Math.max(0, step - 1))} disabled={step === 0}>
              Orqaga
            </Button>
            {step < STEPS.length - 1 ? (
              <Button onClick={() => setStep(step + 1)}>Keyingi qadam</Button>
            ) : (
              <Link
                to="/register"
                className="inline-flex items-center rounded-lg bg-brand-700 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-800"
              >
                Kutubxonamni ochish
              </Link>
            )}
          </div>
        </Card>
      </main>
    </div>
  )
}

function LoanList({
  loans,
  bookOf,
  readerOf,
  empty,
  onGiveBack,
  onSkip,
}: {
  loans: DemoLoan[]
  bookOf: (id: number) => DemoBook | undefined
  readerOf: (id: number) => DemoReader | undefined
  empty: string
  onGiveBack?: (id: number) => void
  onSkip?: (id: number) => void
}) {
  if (loans.length === 0) return <p className="mt-5 text-sm text-slate-500">{empty}</p>
  return (
    <ul className="mt-5 divide-y divide-slate-100 dark:divide-slate-700">
      {loans.map((l) => {
        const overdue = l.daysLeft < 0
        return (
          <li key={l.id} className="flex flex-wrap items-center justify-between gap-2 py-2.5">
            <div className="min-w-0">
              <div className="truncate font-medium text-slate-900 dark:text-slate-100">{bookOf(l.bookId)?.title}</div>
              <div className="text-sm text-slate-500">{readerOf(l.readerId)?.name}</div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {l.returned ? (
                <Badge tone="slate">Qaytarilgan</Badge>
              ) : overdue ? (
                <Badge tone="red">{-l.daysLeft} kun kechikkan</Badge>
              ) : (
                <Badge tone="green">{l.daysLeft} kun qoldi</Badge>
              )}
              {!l.returned && onSkip && !overdue && (
                <Button size="sm" variant="ghost" onClick={() => onSkip(l.id)}>
                  20 kun o‘tdi deb ko‘rish
                </Button>
              )}
              {!l.returned && onGiveBack && (
                <Button size="sm" onClick={() => onGiveBack(l.id)}>
                  Qaytarish
                </Button>
              )}
            </div>
          </li>
        )
      })}
    </ul>
  )
}
