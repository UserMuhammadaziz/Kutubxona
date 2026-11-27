import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { reviewsApi } from '../api/resources'
import { errorMessage } from '../api/client'
import { formatDateTime } from '../lib/format'
import { useToast } from './Toast'
import { Badge, Button, Card } from './ui'

function Stars({ value }: { value: number }) {
  return (
    <span className="text-amber-500" aria-label={`${value} / 5`}>
      {'★'.repeat(value)}
      <span className="text-slate-300 dark:text-slate-600">{'★'.repeat(5 - value)}</span>
    </span>
  )
}

/** Readers' ratings of a book. Librarians can hide a review from the bot. */
export function BookReviews({ bookId }: { bookId: number }) {
  const qc = useQueryClient()
  const toast = useToast()
  const key = ['books', bookId, 'reviews']
  const { data } = useQuery({ queryKey: key, queryFn: () => reviewsApi.list(bookId) })

  const toggle = useMutation({
    mutationFn: ({ id, hidden }: { id: number; hidden: boolean }) => reviewsApi.setHidden(id, hidden),
    onSuccess: (review) => {
      void qc.invalidateQueries({ queryKey: key })
      toast.success(review.is_hidden ? 'Fikr yashirildi.' : "Fikr qayta ko'rsatildi.")
    },
    onError: (err) => toast.error(errorMessage(err)),
  })

  if (!data) return null
  const { summary, results } = data

  return (
    <Card className="mt-6 p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-semibold text-slate-900 dark:text-slate-100">Kitobxonlar fikri</h2>
        {summary.count > 0 && (
          <span className="text-sm text-slate-600 dark:text-slate-300">
            <b className="text-slate-900 dark:text-slate-100">{summary.avg}</b> / 5 · {summary.count} ta baho
          </span>
        )}
      </div>
      {results.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          Hali fikr yo'q. Kitobxon kitobni qaytargach, bot undan baho va fikr so'raydi.
        </p>
      ) : (
        <ul className="mt-3 divide-y divide-slate-100 dark:divide-slate-700">
          {results.map((r) => (
            <li key={r.id} className={`flex gap-3 py-3 ${r.is_hidden ? 'opacity-60' : ''}`}>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <Stars value={r.rating} />
                  <span className="font-medium text-slate-900 dark:text-slate-100">{r.reader_name}</span>
                  <span className="text-xs text-slate-500">{formatDateTime(r.updated_at)}</span>
                  {r.is_hidden && <Badge tone="slate">Yashirilgan</Badge>}
                </div>
                {r.text && <p className="mt-1 whitespace-pre-line text-sm text-slate-700 dark:text-slate-200">{r.text}</p>}
              </div>
              <Button
                size="sm"
                variant="secondary"
                loading={toggle.isPending && toggle.variables?.id === r.id}
                onClick={() => toggle.mutate({ id: r.id, hidden: !r.is_hidden })}
              >
                {r.is_hidden ? "Ko'rsatish" : 'Yashirish'}
              </Button>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}
