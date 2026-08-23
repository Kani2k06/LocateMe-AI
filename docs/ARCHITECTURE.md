# Architecture

```
Frontend (Next.js)
   ↓
FastAPI API
   ↓
OpenCV + Face Recognition
   ↓
Supabase (Auth, PostgreSQL, Storage)
```

## Phase 1 (current)

The Next.js app reproduces the Stitch command-center UI with demo data. There is no live recognition pipeline.

## Phase 2 (planned)

- FastAPI endpoints for person registration, video ingest, and detections
- Embedding generation on photograph upload
- Frame extraction from CCTV
- Configurable similarity threshold
- Persist matches with location, camera ID, timestamps, verification status
