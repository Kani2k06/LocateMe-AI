# LocateMe

LocateMe is an AI-based missing person identification system.

The original Stitch prototype is kept at the repository root (`code.html`, `DESIGN.md`, `screen.png`) and is the visual reference for the product UI.

## Monorepo

- `frontend` — Next.js command-center UI (Phase 1)
- `backend` — FastAPI + OpenCV + face embeddings (Phase 2, not implemented yet)
- `docs` — architecture and phase notes

## Run the frontend (Phase 1)

Requires Node.js 20+.

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The home route redirects to `/dashboard`.
