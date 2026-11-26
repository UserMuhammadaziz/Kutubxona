import { api } from '../api/client'

/** Web Push is usable only in secure contexts with a registered service worker. */
export function pushSupported(): boolean {
  return (
    typeof window !== 'undefined' &&
    'serviceWorker' in navigator &&
    'PushManager' in window &&
    'Notification' in window
  )
}

function urlBase64ToUint8Array(base64: string): Uint8Array<ArrayBuffer> {
  const padding = '='.repeat((4 - (base64.length % 4)) % 4)
  const raw = atob((base64 + padding).replace(/-/g, '+').replace(/_/g, '/'))
  const out = new Uint8Array(new ArrayBuffer(raw.length))
  for (let i = 0; i < raw.length; i += 1) out[i] = raw.charCodeAt(i)
  return out
}

/**
 * Ask for notification permission. Call it directly from a click/submit handler
 * (browsers require a user gesture). Returns true when granted.
 */
export async function askPushPermission(): Promise<boolean> {
  if (!pushSupported()) return false
  if (Notification.permission === 'granted') return true
  if (Notification.permission === 'denied') return false
  try {
    return (await Notification.requestPermission()) === 'granted'
  } catch {
    return false
  }
}

/** Subscribe this browser and send the subscription to the server. Never throws. */
export async function subscribeToPush(): Promise<boolean> {
  try {
    if (!pushSupported() || Notification.permission !== 'granted') return false
    const { data } = await api.get<{ public_key: string | null }>('/push/public-key/')
    if (!data.public_key) return false
    const reg = await navigator.serviceWorker.getRegistration()
    if (!reg) return false
    const sub =
      (await reg.pushManager.getSubscription()) ??
      (await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(data.public_key),
      }))
    await api.post('/push/subscribe/', sub.toJSON())
    return true
  } catch {
    return false
  }
}
