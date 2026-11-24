import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { loansApi, telegramApi } from '../api/resources'
import { isAdmin, useAuthStore } from '../store/auth'
import type { DashboardStats } from '../types'
import { SetupChecklist } from './SetupChecklist'
import { Button } from './ui'

/** Setup checklist and the two everyday actions, shared by the overview and the dashboard. */
export function StartActions({ data }: { data: DashboardStats }) {
  const admin = isAdmin(useAuthStore((s) => s.user))
  const bot = useQuery({ queryKey: ['telegram', 'settings'], queryFn: telegramApi.get, enabled: admin })
  const recent = useQuery({ queryKey: ['loans', 'recent'], queryFn: () => loansApi.list({ page: 1 }) })

  return (
    <>
      {admin && !recent.isLoading && !bot.isLoading && (
        <SetupChecklist
          steps={[
            { key: 'book', title: "Kitob qo'shing", hint: 'Kitoblar ro‘yxatiga birinchi kitobni kiriting.', to: '/books', action: "Kitob qo'shish", done: data.jami_kitoblar > 0 },
            { key: 'copy', title: "Nusxalarni qo'shing", hint: 'Berish uchun kitobning jismoniy nusxalari kerak.', to: '/copies', action: "Nusxa qo'shish", done: data.jami_nusxalar > 0 },
            { key: 'reader', title: "O'quvchi qo'shing", hint: 'Yoki o‘quvchilar Telegram bot orqali o‘zlari ariza yuboradi.', to: '/readers', action: "O'quvchi qo'shish", done: (data.oquvchi_soni || 0) > 0 },
            { key: 'bot', title: 'Telegram botni ulang', hint: 'Bot tokenini Kompaniya sahifasida kiriting.', to: '/company', action: 'Ulash', done: !!bot.data?.ulangan },
            { key: 'loan', title: 'Birinchi kitobni bering', hint: 'O‘quvchiga nusxa bering, muddat va jarima avtomatik hisoblanadi.', to: '/loans?berish=1', action: 'Kitob berish', done: (recent.data?.results?.length ?? 0) > 0 },
          ]}
        />
      )}

      <div className="mb-6 grid grid-cols-2 gap-3 sm:max-w-md">
        <Link to="/loans?berish=1">
          <Button className="w-full py-3">Kitob berish</Button>
        </Link>
        <Link to="/loans?holat=faol">
          <Button variant="secondary" className="w-full py-3">
            Qaytarib olish
          </Button>
        </Link>
      </div>
    </>
  )
}
