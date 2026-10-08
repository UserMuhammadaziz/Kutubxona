// PWA ikonkalarini `public/logo-icon.svg` dan generatsiya qiladi.
// `logo-icon.svg` to'liq kvadrat (fonsiz, burchaksiz) — undan ikonka
// aynan o'sha hajmda tushadi, qo'shimcha fon kerak emas.
// Ishga tushirish: node scripts/generate-icons.mjs
import { mkdir } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import sharp from 'sharp'

const __dirname = dirname(fileURLToPath(import.meta.url))
const publicDir = resolve(__dirname, '../public')
const iconsDir = resolve(publicDir, 'icons')
const iconSvg = resolve(publicDir, 'logo-icon.svg')

async function generate(name, size) {
  await sharp(iconSvg, { density: (size / 64) * 72 })
    .resize(size, size, { fit: 'fill' })
    .png()
    .toFile(resolve(iconsDir, name))
  console.log(`${name} (${size}x${size})`)
}

await mkdir(iconsDir, { recursive: true })
await generate('icon-192.png', 192)
await generate('icon-512.png', 512)
// Maskable: `logo-icon.svg` ichidagi belgi maxsus kichraytirilgan (85%),
// shuning uchun xavfsiz zona buzilmaydi.
await generate('icon-maskable-512.png', 512)
await generate('apple-touch-icon.png', 180)
