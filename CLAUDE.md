# Kutubxona

Multi-tenant library SaaS. Django + DRF backend (`apps/`), React 19 + Vite + TypeScript + Tailwind v4 frontend (`frontend/`), aiogram Telegram bot. Every tenant row carries an `organization` FK.

## Naming rules (mandatory for all new code)

- **All identifiers are English**: model and class names, fields, variables, functions, serializers, URL route names, API JSON keys, TypeScript types and props, test names, DB columns, branch names.
  - Good: `Book`, `Copy`, `Reader`, `Loan`, `Fine`, `Reservation`, `due_date`, `returned_at`, `overdue_days`.
  - Bad: `Kitob`, `Nusxa`, `Oquvchi`, `qaytarish_muddati`, `jarima_summasi`.
- **User-facing text stays Uzbek**: UI labels, toasts, error messages, bot messages, docs shown to librarians. Keep them in string literals (no Uzbek in identifiers).
- Code comments and commit messages: English preferred. Uzbek comments in old code can stay until the file is touched.
- Do not mix: never add a new Uzbek-named field or API key next to existing ones, even if neighbours are Uzbek. Use the English name and, if the old name must keep working, map it explicitly (serializer `source=`, `db_column=`, `db_table=`), with a short comment.
- Touching an old file: new identifiers you add are English. Rename old ones only when the task is the rename (see below), not as a side effect inside an unrelated change.

## Legacy Uzbek names (being migrated)

Existing apps/models/fields are Uzbek (`kitob`, `nusxa`, `oquvchi`, `berish`, `jarima`, `navbat`, plus fields like `qaytarish_muddati`). Migrate one app per PR, in this order of safety: Python names first, then API keys with the frontend types, then DB names via migrations (`RenameModel`/`RenameField`, or keep `db_table`/`db_column`). Never rename DB objects on production without a backup and a dev-server dry run.

## Frontend design tokens

Tokens live in `frontend/src/index.css` (`@theme`): green `brand-*`, warm neutral `slate-*`, `canvas`, `paper`, radii, IBM Plex Sans. Use tokens and `components/ui.tsx`; do not hard-code hex colors in pages. The public landing (`/welcome`, `pages/Home.tsx`) uses the same palette.

## Working agreements

- Assistant replies to the user in Uzbek; code, commits and PRs in English.
- Add features incrementally; do not degrade existing screens. Compare before/after screenshots for UI changes.
- Run only the tests related to the change; full suite at the end.
- Deploy only to the dev server unless the user explicitly asks for production.

## Environments

| | URL | Rules |
|---|---|---|
| **Dev** | https://kutubxona-dev.orgtrace.uz/ | Sandbox with demo/test data. Change anything here without asking: deploy, migrations, test records, demo accounts, screenshots. |
| **Prod** | https://kutubxona.sharqsoft.uz/ | Real library data. **Never touch without the user's explicit permission in chat**: no deploy, SSH, DB/shell commands, migrations, config changes, or state-changing browser actions. Permission is per action and does not carry over. |

- SSH access details for either server: ask the user; never guess keys/users.
- When unsure which environment a URL, host, or database belongs to, treat it as prod and ask.
