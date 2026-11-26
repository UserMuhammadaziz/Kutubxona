import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { announcementsApi } from '../api/resources'
import { errorMessage } from '../api/client'
import { Icons } from '../components/icons'
import { useToast } from '../components/Toast'
import {
  Badge,
  Button,
  Card,
  ConfirmDialog,
  EmptyState,
  Input,
  PageHeader,
  Select,
  ListSkeleton,
  Textarea,
} from '../components/ui'
import { ANNOUNCEMENT_AUDIENCE_LABELS, type AnnouncementAudience } from '../types'
import { formatDateTime } from '../lib/format'

const MAX_LEN = 1000

export function Announcements() {
  const qc = useQueryClient()
  const toast = useToast()
  const [audience, setAudience] = useState<AnnouncementAudience>('all')
  const [grade, setGrade] = useState('')
  const [text, setText] = useState('')
  const [confirmOpen, setConfirmOpen] = useState(false)

  const preview = useQuery({
    queryKey: ['announcements', 'preview', audience, grade],
    queryFn: () => announcementsApi.preview(audience, grade.trim()),
  })
  const log = useQuery({ queryKey: ['announcements', 'log'], queryFn: () => announcementsApi.list() })

  const sendMut = useMutation({
    mutationFn: () => announcementsApi.send({ text: text.trim(), audience, grade: grade.trim() }),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['announcements'] })
      setConfirmOpen(false)
      setText('')
      toast.success(`Yuborildi: ${res.sent_count} ta, xato: ${res.failed_count} ta.`)
    },
    onError: (err) => {
      setConfirmOpen(false)
      toast.error(errorMessage(err))
    },
  })

  const recipients = preview.data?.recipients ?? 0
  const limitReached = !!preview.data && preview.data.sent_today >= preview.data.daily_limit
  const canSend = !!text.trim() && recipients > 0 && !limitReached

  return (
    <div>
      <PageHeader
        title="E‘lonlar"
        subtitle="Telegramga ulangan o‘quvchilarga ommaviy xabar: chegirma, yangi kitoblar, ish vaqti"
      />

      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="p-4 sm:p-5 lg:col-span-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">Kimga</label>
              <Select value={audience} onChange={(e) => setAudience(e.target.value as AnnouncementAudience)}>
                {Object.entries(ANNOUNCEMENT_AUDIENCE_LABELS).map(([v, l]) => (
                  <option key={v} value={v}>
                    {l}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
                Sinf (ixtiyoriy)
              </label>
              <Input value={grade} onChange={(e) => setGrade(e.target.value)} placeholder="Masalan: 6-B" />
            </div>
          </div>

          <div className="mt-4">
            <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">Xabar matni</label>
            <Textarea
              rows={6}
              maxLength={MAX_LEN}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Masalan: Bu hafta barcha darsliklarga 20% chegirma."
            />
            <div className="mt-1 text-right text-xs text-slate-500 dark:text-slate-400">
              {text.length} / {MAX_LEN}
            </div>
          </div>

          <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
            <div className="text-sm text-slate-600 dark:text-slate-300">
              {preview.isLoading ? (
                'Hisoblanmoqda...'
              ) : (
                <>
                  Oluvchilar: <b>{recipients}</b> ta · Bugun yuborilgan: {preview.data?.sent_today}/
                  {preview.data?.daily_limit}
                </>
              )}
            </div>
            <Button disabled={!canSend} onClick={() => setConfirmOpen(true)}>
              Yuborish
            </Button>
          </div>
          {limitReached && (
            <p className="mt-2 text-sm text-amber-700 dark:text-amber-400">
              Bugungi limit tugadi. Ertaga yana yuborishingiz mumkin.
            </p>
          )}
          {!preview.isLoading && recipients === 0 && (
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              Bu guruhda Telegramga ulangan o‘quvchi yo‘q. Faqat botga ulangan o‘quvchilar xabar oladi.
            </p>
          )}
        </Card>

        <div className="lg:col-span-2">
          <h2 className="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">Yuborilganlar</h2>
          {log.isLoading ? (
            <ListSkeleton rows={4} />
          ) : !log.data?.results.length ? (
            <EmptyState
              icon={<Icons.bell className="h-10 w-10" />}
              title="Hali e‘lon yuborilmagan"
              description="Birinchi xabarni chap tomondagi shakldan yuboring."
            />
          ) : (
            <Card className="divide-y divide-slate-100 dark:divide-slate-700">
              {log.data.results.map((a) => (
                <div key={a.id} className="px-4 py-3 text-sm">
                  <div className="line-clamp-2 font-medium text-slate-900 dark:text-slate-100">{a.text}</div>
                  <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                    <span>{formatDateTime(a.created_at)}</span>
                    <span>· {ANNOUNCEMENT_AUDIENCE_LABELS[a.audience]}</span>
                    <Badge tone="green">{a.sent_count} yuborildi</Badge>
                    {a.failed_count > 0 && <Badge tone="red">{a.failed_count} xato</Badge>}
                  </div>
                </div>
              ))}
            </Card>
          )}
        </div>
      </div>

      <ConfirmDialog
        open={confirmOpen}
        title="E‘lonni yuborish"
        confirmLabel="Yuborish"
        loading={sendMut.isPending}
        message={
          <>
            <b>{recipients}</b> ta o‘quvchiga ({ANNOUNCEMENT_AUDIENCE_LABELS[audience]}
            {grade.trim() ? `, ${grade.trim()}` : ''}) quyidagi xabar yuboriladi. Yuborilgach qaytarib bo‘lmaydi.
            <br />
            <br />
            <span className="whitespace-pre-wrap">{text.trim()}</span>
          </>
        }
        onConfirm={() => sendMut.mutate()}
        onCancel={() => setConfirmOpen(false)}
      />
    </div>
  )
}
