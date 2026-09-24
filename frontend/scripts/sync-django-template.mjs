// Copies the built index.html into the Django template location and removes
// it from the static dist folder (static assets stay in web/static/web/dist,
// but the HTML shell is served by Django's IndexView via a template so it
// can participate in Django's template loading / context in the future).
import { copyFileSync, rmSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const distIndex = resolve(__dirname, '../../web/static/web/dist/index.html')
const templateIndex = resolve(__dirname, '../../web/templates/web/index.html')

copyFileSync(distIndex, templateIndex)
rmSync(distIndex)

console.log(`Synced ${distIndex} -> ${templateIndex}`)
