# Phase 1 implementation plan

## Inspected

- `code.html` is a single Stitch screen: **Missing Persons Registry** with sidebar, header search, filters, data table, pagination.
- `DESIGN.md` defines navy/slate tokens, Inter + JetBrains Mono, high-density command-center layout, status badges, and breakpoints.
- `screen.png` matches that Missing Persons view.

## Approach

1. Keep Stitch files at the repo root.
2. Scaffold Next.js (App Router, TypeScript, Tailwind v4) under `/frontend`.
3. Encode Stitch color/type/spacing tokens in `app/globals.css`.
4. Shared shell: sidebar + header + mobile overlay.
5. Additional routes use the same visual language and demo data.

## Environment notes

- This machine originally had **Python 3.13** but **no Node.js on PATH**. Node.js LTS was installed via winget so the frontend can run.
- Nested `frontend/.git` from `create-next-app` should be removed so the monorepo can use a single git root.
- Stitch photos/logo are remote `lh3.googleusercontent.com` URLs; they may expire. Phase 2 should store files in Supabase Storage.
- Material Symbols load from Google Fonts (needs network in the browser).
- InsightFace/OpenCV on Python 3.13 can be a Phase 2 deployment risk (wheel availability). Prefer a pinned 3.11/3.12 runtime later.
- Next.js 16 + React 19 is what `create-next-app` installed; deploy on a host that supports Node 20+.
