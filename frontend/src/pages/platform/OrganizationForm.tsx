import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { platformApi, type PlatformOrgForm } from '../../api/resources'
import { useToast } from '../../components/Toast'
import { Button, ErrorBanner, Field, Input, Label, PhoneInput, Select, Textarea } from '../../components/ui'
import { formError } from './shared'

const ORG_TYPES: [string, string][] = [
  ['library', 'Kutubxona'],
  ['school', "Maktab / ta'lim muassasasi"],
  ['university', 'Universitet / kollej'],
  ['office', 'Ofis / tashkilot'],
  ['other', 'Boshqa'],
]

export const emptyOrgForm = (): PlatformOrgForm => ({
  nomi: '',
  slug: '',
  turi: 'library',
  tavsif: '',
  telefon: '',
  email: '',
  manzil: '',
  logo_url: '',
  muddat_kun: 14,
  kunlik_jarima: 5000,
  limit_kitob: 3,
  owner: { telefon: '+998', full_name: '', password: '' },
})

const legendClass = 'mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100'
const sectionClass = 'border-t border-slate-200 pt-4 dark:border-slate-700'
const grid = 'grid gap-x-4 sm:grid-cols-2'

export function OrganizationForm({ id, initial, onClose }: { id: number | null; initial: PlatformOrgForm; onClose: () => void }) {
  const qc = useQueryClient()
  const toast = useToast()
  const [form, setForm] = useState(initial)
  const set = <K extends keyof PlatformOrgForm>(key: K, value: PlatformOrgForm[K]) => setForm((f) => ({ ...f, [key]: value }))
  const setOwner = (patch: Partial<NonNullable<PlatformOrgForm['owner']>>) =>
    setForm((f) => ({ ...f, owner: { ...f.owner!, ...patch } }))

  const save = useMutation({
    mutationFn: () => {
      const { owner, slug, ...rest } = form
      return id
        ? platformApi.update(id, { ...rest, slug: slug || undefined })
        : platformApi.create({ ...rest, slug: slug || undefined, owner })
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['platform'] })
      toast.success(id ? `«${form.nomi}» saqlandi.` : `«${form.nomi}» yaratildi va faol.`)
      onClose()
    },
  })

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        save.mutate()
      }}
    >
      <ErrorBanner message={formError(save.error)} />
      <div className={grid}>
        <Field>
          <Label htmlFor="o-nomi">Nomi</Label>
          <Input id="o-nomi" required autoFocus value={form.nomi} onChange={(e) => set('nomi', e.target.value)} />
        </Field>
        <Field>
          <Label htmlFor="o-turi">Turi</Label>
          <Select id="o-turi" value={form.turi} onChange={(e) => set('turi', e.target.value)}>
            {ORG_TYPES.map(([v, l]) => (
              <option key={v} value={v}>{l}</option>
            ))}
          </Select>
        </Field>
        <Field>
          <Label htmlFor="o-tel">Telefon</Label>
          <PhoneInput id="o-tel" value={form.telefon} onValueChange={(v) => set('telefon', v)} />
        </Field>
        <Field>
          <Label htmlFor="o-email">Email</Label>
          <Input id="o-email" type="email" value={form.email} onChange={(e) => set('email', e.target.value)} />
        </Field>
        <Field>
          <Label htmlFor="o-manzil">Manzil</Label>
          <Input id="o-manzil" value={form.manzil} onChange={(e) => set('manzil', e.target.value)} />
        </Field>
        <Field>
          <Label htmlFor="o-slug">Slug (ixtiyoriy)</Label>
          <Input id="o-slug" value={form.slug ?? ''} onChange={(e) => set('slug', e.target.value)} placeholder="Bo'sh qolsa, nomidan olinadi" />
        </Field>
      </div>
      <Field>
        <Label htmlFor="o-tavsif">Tavsif</Label>
        <Textarea id="o-tavsif" rows={2} value={form.tavsif} onChange={(e) => set('tavsif', e.target.value)} />
      </Field>

      <fieldset className={sectionClass}>
        <legend className="sr-only">Kitob berish qoidalari</legend>
        <p aria-hidden className={legendClass}>Kitob berish qoidalari</p>
        <div className="grid gap-x-4 sm:grid-cols-3">
          <Field>
            <Label htmlFor="o-muddat">Muddat, kun</Label>
            <Input id="o-muddat" type="number" inputMode="numeric" min={1} max={365} value={form.muddat_kun} onChange={(e) => set('muddat_kun', Number(e.target.value))} />
          </Field>
          <Field>
            <Label htmlFor="o-jarima">Kunlik jarima, so'm</Label>
            <Input id="o-jarima" type="number" inputMode="numeric" min={0} value={form.kunlik_jarima} onChange={(e) => set('kunlik_jarima', Number(e.target.value))} />
          </Field>
          <Field>
            <Label htmlFor="o-limit">Bir kitobxonga, kitob</Label>
            <Input id="o-limit" type="number" inputMode="numeric" min={1} max={100} value={form.limit_kitob} onChange={(e) => set('limit_kitob', Number(e.target.value))} />
          </Field>
        </div>
      </fieldset>

      {!id && form.owner && (
        <fieldset className={sectionClass}>
          <legend className="sr-only">Egasi</legend>
          <p aria-hidden className={legendClass}>Egasi</p>
          <div className={grid}>
            <Field>
              <Label htmlFor="ow-tel">Telefon (login)</Label>
              <PhoneInput id="ow-tel" required value={form.owner.telefon} onValueChange={(telefon) => setOwner({ telefon })} />
            </Field>
            <Field>
              <Label htmlFor="ow-name">To'liq ism</Label>
              <Input id="ow-name" value={form.owner.full_name} onChange={(e) => setOwner({ full_name: e.target.value })} />
            </Field>
            <Field>
              <Label htmlFor="ow-pass">Parol (kamida 8 belgi)</Label>
              <Input id="ow-pass" type="password" autoComplete="new-password" aria-describedby="ow-hint" value={form.owner.password} onChange={(e) => setOwner({ password: e.target.value })} />
            </Field>
          </div>
          <p id="ow-hint" className="text-xs text-slate-600 dark:text-slate-300">Bu telefon bilan foydalanuvchi bor bo'lsa, o'sha hisob egasi bo'ladi.</p>
        </fieldset>
      )}
      <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button type="button" variant="secondary" onClick={onClose}>Bekor qilish</Button>
        <Button type="submit" loading={save.isPending}>{id ? 'Saqlash' : 'Tashkilot yaratish'}</Button>
      </div>
    </form>
  )
}
