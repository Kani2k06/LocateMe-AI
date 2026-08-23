# LocateMe — Phase 2 Implementation Plan

## Executive Summary
This document defines the complete end-to-end architecture and implementation plan for Phase 2 of **LocateMe** (AI-based Missing Person Identification System). It connects the existing Next.js command-center UI with a Python FastAPI vision backend, OpenCV frame extraction, face embedding extraction, similarity matching, and Supabase PostgreSQL/Storage persistence, with built-in demo-friendly local fallbacks.

---

## 1. Database Schema (Supabase PostgreSQL)

```sql
-- Enable UUID and pgvector extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 1. Missing Persons Table
CREATE TABLE IF NOT EXISTS missing_persons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id VARCHAR(50) UNIQUE NOT NULL,             -- e.g. "MP-24-0891"
    name VARCHAR(255) NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(10) NOT NULL,                    -- "M", "F", "Other"
    height VARCHAR(20),                             -- e.g. "5'9\""
    missing_since DATE NOT NULL,
    last_known_location TEXT NOT NULL,
    notes TEXT,
    photo_url TEXT,
    status VARCHAR(30) DEFAULT 'active_alert',      -- 'active_alert', 'found_safe', 'pending_verification'
    embedding VECTOR(512),                          -- 512-d normalized face embedding (or float array)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. CCTV Processing Jobs Table
CREATE TABLE IF NOT EXISTS cctv_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_code VARCHAR(50) UNIQUE NOT NULL,           -- e.g. "JOB-441"
    filename VARCHAR(255) NOT NULL,
    video_url TEXT,
    location VARCHAR(255) NOT NULL,
    camera_id VARCHAR(50) NOT NULL,                 -- e.g. "CAM-04-DT-12"
    capture_time TIMESTAMPTZ NOT NULL,
    status VARCHAR(30) DEFAULT 'queued',            -- 'queued', 'extracting', 'matching', 'complete', 'failed'
    total_frames INT DEFAULT 0,
    processed_frames INT DEFAULT 0,
    faces_detected INT DEFAULT 0,
    matches_found INT DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Detection Results Table
CREATE TABLE IF NOT EXISTS detections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    detection_code VARCHAR(50) UNIQUE NOT NULL,     -- e.g. "DET-88421"
    person_id UUID NOT NULL REFERENCES missing_persons(id) ON DELETE CASCADE,
    cctv_job_id UUID REFERENCES cctv_jobs(id) ON DELETE SET NULL,
    confidence FLOAT NOT NULL,                      -- e.g. 0.94 (0.0 to 1.0)
    frame_url TEXT NOT NULL,                        -- URL/path to matched CCTV frame
    location VARCHAR(255) NOT NULL,
    camera_id VARCHAR(50) NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL,
    verification_status VARCHAR(30) DEFAULT 'pending', -- 'pending', 'verified', 'rejected'
    bounding_box JSONB,                             -- {"x": 120, "y": 80, "w": 64, "h": 64}
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_code VARCHAR(50) UNIQUE NOT NULL,         -- e.g. "AL-1022"
    detection_id UUID REFERENCES detections(id) ON DELETE CASCADE,
    case_id VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    detail TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'critical',        -- 'critical', 'high', 'info'
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. System Settings Table
CREATE TABLE IF NOT EXISTS system_settings (
    key VARCHAR(50) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Default system settings
INSERT INTO system_settings (key, value) VALUES
('recognition', '{"similarity_threshold": 0.80, "alert_threshold": 0.90}')
ON CONFLICT (key) DO NOTHING;
```

---

## 2. Supabase Storage Structure

We configure 3 primary buckets with public read policies for the web console:

| Bucket Name | Access | Purpose | File Key Pattern |
| :--- | :--- | :--- | :--- |
| `photos` | Public | Reference missing-person photographs | `persons/{case_id}/{timestamp}_{filename}` |
| `cctv-videos` | Authenticated | Uploaded CCTV video footage | `videos/{job_code}/{filename}` |
| `cctv-frames` | Public | Extracted CCTV frames and match crops | `frames/{job_code}/frame_{idx}_{face_idx}.jpg` |

> **Demo & Offline Fallback**: The backend will support a local directory fallback (`backend/storage/`) when Supabase credentials are not provided, serving files via FastAPI static mount (`/static/...`).

---

## 3. FastAPI Backend Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # App factory, CORS, static mounts, route registration
│   ├── config.py                   # Pydantic Settings (.env loader)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── persons.py              # Person registration & search
│   │   ├── cctv.py                 # Video upload & job queue
│   │   ├── detections.py           # Match results & status updates
│   │   ├── alerts.py               # Active alert stream
│   │   ├── stats.py                # Dashboard statistics & KPIs
│   │   └── settings.py             # Thresholds configuration
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py             # Supabase / SQLite / in-memory repository adapter
│   │   └── storage.py              # Supabase Storage / Local filesystem storage adapter
│   ├── services/
│   │   ├── __init__.py
│   │   ├── face_engine.py          # Face detection & 512-d/128-d embedding extraction
│   │   ├── video_processor.py      # OpenCV/FFmpeg frame sampling & worker
│   │   └── matcher.py              # Vector cosine similarity calculation & threshold evaluation
│   └── schemas/
│       ├── __init__.py
│       ├── person.py               # PersonCreate, PersonResponse
│       ├── cctv.py                 # CCTVUploadRequest, CCTVJobResponse
│       ├── detection.py            # DetectionResponse, VerificationUpdate
│       └── alert.py                # AlertResponse
├── storage/                        # Local fallback file storage
├── tests/
├── .env.example
├── requirements.txt
└── Dockerfile
```

---

## 4. Face Embedding Workflow

```
[Operator Uploads Photo]
          │
          ▼
[Validate & Decode Image] (OpenCV / PIL)
          │
          ▼
[Face Detection & Landmark Alignment] (OpenCV YuNet / InsightFace / ONNX)
          │
      ┌───┴───────────────────────────────┐
  (No face found)                 (Face detected)
      │                                   │
  Raise 400 Error                [Crop & Normalize] (112x112 / 160x160)
  "No face detected"                      │
                                 [Embedding Extraction] (512-d ArcFace / SFace ONNX)
                                          │
                                 [L2 Normalization] (||v|| = 1.0)
                                          │
                                 [Store Vector & Image URL in Database]
```

* **Model Engine**: OpenCV DNN FaceRecognizerSF (SFace) / InsightFace ArcFace ONNX.
  * Extremely fast CPU inference (10–25ms per face on modern standard CPUs).
  * No heavy CUDA requirement for local demo.
  * Produces standardized L2-normalized float vectors.

---

## 5. CCTV Frame Processing Workflow

```
[CCTV Video Ingest] (MP4/MKV/AVI + Location + Camera ID + Timestamp)
          │
          ▼
[Create Job Record (Status: 'extracting')]
          │
          ▼
[Frame Extraction Pipeline] (OpenCV VideoCapture / FFmpeg)
          ├─ Sampling rate: e.g. 1 frame every 1.0s (configurable)
          ├─ Resolution normalization (720p / 1080p)
          │
          ▼
[Batch Face Detection on Sampled Frame]
          ├─ For each detected face bounding box:
          │     ├─ Extract aligned face crop
          │     ├─ Compute 512-d embedding vector
          │     └─ Pass to Matcher Service
          │
          ▼
[Update Job Progress: processed_frames, faces_detected]
          │
          ▼
[Finalize Job (Status: 'complete')]
```

---

## 6. Matching Workflow

```
[CCTV Face Embedding (u)] vs [Registered Active Missing Person Embeddings (V)]
                                   │
                                   ▼
          [Cosine Similarity Calculation: score = dot(u, v_i)]
                                   │
                                   ▼
                 [Find Best Match (max_score, person_i)]
                                   │
                     ┌─────────────┴─────────────┐
        (score < threshold)             (score >= threshold)
             [Skip]                              │
                                     [Save Frame & Face Crop]
                                                 │
                                     [Create Detection Record]
                                     (confidence = score, status = 'pending')
                                                 │
                                     ┌───────────┴───────────┐
                          (score < alert_threshold)   (score >= alert_threshold)
                                     │                           │
                                  [Done]             [Create Critical Alert]
                                                     [Push to Active Alerts]
```

---

## 7. API Endpoints

### 7.1 Missing Persons
* `POST /api/persons` — Register person (multipart form: metadata + photo). Generates embedding automatically.
* `GET /api/persons` — List registered persons (filter by `status`, search query).
* `GET /api/persons/{id}` — Get single person record details.
* `PATCH /api/persons/{id}/status` — Update case status (`active_alert`, `found_safe`, `pending_verification`).

### 7.2 CCTV Ingestion
* `POST /api/cctv/upload` — Upload video file + metadata (`location`, `camera_id`, `capture_time`). Dispatches async worker.
* `GET /api/cctv/jobs` — List all CCTV processing jobs.
* `GET /api/cctv/jobs/{id}` — Get status and real-time progress for a specific job.

### 7.3 Detections & Alerts
* `GET /api/detections` — List detection results (filters: `verification_status`, `person_id`, `min_confidence`).
* `PATCH /api/detections/{id}/verify` — Update verification status (`verified`, `rejected`, `pending`).
* `GET /api/alerts` — Fetch active operator alerts.

### 7.4 Dashboard & Settings
* `GET /api/stats` — Dashboard key metric counts (`active_cases`, `matches_today`, `open_alerts`, `cctv_jobs`).
* `GET /api/analytics` — KPI summaries & distribution breakdowns.
* `GET /api/settings` — Get current threshold settings (`similarity_threshold`, `alert_threshold`).
* `PUT /api/settings` — Update similarity and alert thresholds.

---

## 8. Frontend-Backend Integration

### 8.1 API Client (`frontend/lib/api.ts`)
* Centralized typed client interacting with `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).
* If the API server is unreachable, automatically fall back to mock data in [frontend/lib/demo-data.ts](file:///D:/locate_me/frontend/lib/demo-data.ts) for uninterrupted offline demo presentations.

### 8.2 Route Connections (Preserving 100% of UI)
* `/register-person`: Submits multipart form directly to `POST /api/persons`. On success, redirects to `/missing-persons`.
* `/missing-persons`: Fetches live records from `GET /api/persons`, preserves search, filter, and pagination UI.
* `/cctv-analysis`: Submits video upload to `POST /api/cctv/upload`, polls job status from `GET /api/cctv/jobs`.
* `/detections`: Fetches live match cards from `GET /api/detections`. Action buttons call `PATCH /api/detections/{id}/verify`.
* `/alerts`: Fetches alerts from `GET /api/alerts`.
* `/dashboard`: Fetches live summary counters from `GET /api/stats`.
* `/settings`: Controls `similarity_threshold` via `PUT /api/settings`.

---

## 9. Local Setup & Verification

### 9.1 Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Install dependencies:
pip install -r requirements.txt
# Copy environment:
cp .env.example .env
# Run FastAPI server:
uvicorn app.main:app --reload --port 8000
```

### 9.2 Frontend Setup
```bash
cd frontend
# Install dependencies:
npm install
# Set environment:
# (NEXT_PUBLIC_API_URL=http://localhost:8000)
npm run dev
```

### 9.3 Environment Variables (`backend/.env.example`)
```ini
# Server
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:3000

# Supabase (Optional for local offline demo)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_BUCKET_PHOTOS=photos
SUPABASE_BUCKET_VIDEOS=cctv-videos
SUPABASE_BUCKET_FRAMES=cctv-frames

# Recognition Defaults
DEFAULT_SIMILARITY_THRESHOLD=0.80
DEFAULT_ALERT_THRESHOLD=0.90
FRAME_SAMPLE_INTERVAL_SECONDS=1.0
```

---

## 10. Deployment Plan

```
                   ┌───────────────────────────────────────┐
                   │               User / Browser          │
                   └──────────────────┬────────────────────┘
                                      │
               ┌──────────────────────┴──────────────────────┐
               ▼                                             ▼
  ┌─────────────────────────┐                   ┌─────────────────────────┐
  │   Frontend (Vercel)     │                   │  Backend (Fly.io/Render)│
  │   Next.js 16 App Router │ ──── API Calls ──▶│  FastAPI + OpenCV/ONNX  │
  └─────────────────────────┘                   └────────────┬────────────┘
                                                             │
                                        ┌────────────────────┴────────────────────┐
                                        ▼                                         ▼
                          ┌───────────────────────────┐             ┌───────────────────────────┐
                          │   Supabase PostgreSQL     │             │     Supabase Storage      │
                          │   (Persons, Jobs, Vector) │             │    (Photos, Videos, Frames)│
                          └───────────────────────────┘             └───────────────────────────┘
```

1. **Frontend (Vercel / Docker)**: Deploy Next.js App Router repository with `NEXT_PUBLIC_API_URL` pointing to the FastAPI backend domain.
2. **Backend (Render / Fly.io / Railway / GCP Cloud Run)**: Containerized with Docker, lightweight OpenCV + ONNX runtime image.
3. **Database & Storage (Supabase)**: Managed PostgreSQL instance with `vector` extension and public storage buckets.
