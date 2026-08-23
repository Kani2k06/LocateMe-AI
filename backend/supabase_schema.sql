-- =============================================================================
-- LocateMe: Supabase PostgreSQL Schema & pgvector Setup
-- =============================================================================

-- 1. Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- Enable pgvector for facial embedding vector similarity search
CREATE EXTENSION IF NOT EXISTS "vector";

-- =============================================================================
-- 2. Tables Definition
-- =============================================================================

-- 2.1 Missing Persons Table
CREATE TABLE IF NOT EXISTS public.missing_persons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id VARCHAR(50) UNIQUE NOT NULL,                       -- e.g. "MP-24-0891"
    name VARCHAR(255) NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(20) NOT NULL,                              -- "M", "F", "Other", "Unknown"
    height VARCHAR(50),                                       -- e.g. "5'9\""
    missing_since DATE NOT NULL,
    last_known_location TEXT NOT NULL,
    notes TEXT,
    photo_url TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'active_alert',        -- 'active_alert', 'found_safe', 'pending_verification'
    embedding VECTOR(512),                                    -- 512-dimensional face embedding vector
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2.2 CCTV Processing Jobs Table
CREATE TABLE IF NOT EXISTS public.cctv_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_code VARCHAR(50) UNIQUE NOT NULL,                     -- e.g. "JOB-441"
    filename VARCHAR(255) NOT NULL,
    video_url TEXT,
    location VARCHAR(255) NOT NULL,
    camera_id VARCHAR(100) NOT NULL,                          -- e.g. "CAM-04-DT-12"
    capture_time TIMESTAMPTZ NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'queued',              -- 'queued', 'extracting', 'matching', 'complete', 'failed'
    total_frames INT NOT NULL DEFAULT 0,
    processed_frames INT NOT NULL DEFAULT 0,
    faces_detected INT NOT NULL DEFAULT 0,
    matches_found INT NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2.3 Detection Results Table
CREATE TABLE IF NOT EXISTS public.detections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    detection_code VARCHAR(50) UNIQUE NOT NULL,               -- e.g. "DET-88421"
    person_id UUID NOT NULL REFERENCES public.missing_persons(id) ON DELETE CASCADE,
    cctv_job_id UUID REFERENCES public.cctv_jobs(id) ON DELETE SET NULL,
    confidence FLOAT NOT NULL,                                -- Range 0.0 to 1.0 (e.g. 0.94)
    frame_url TEXT NOT NULL,
    location VARCHAR(255) NOT NULL,
    camera_id VARCHAR(100) NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL,
    verification_status VARCHAR(30) NOT NULL DEFAULT 'pending', -- 'pending', 'verified', 'rejected'
    bounding_box JSONB,                                       -- Bounding box {"x": 100, "y": 80, "w": 60, "h": 60}
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2.4 Operator Alerts Table
CREATE TABLE IF NOT EXISTS public.alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_code VARCHAR(50) UNIQUE NOT NULL,                   -- e.g. "AL-1022"
    detection_id UUID REFERENCES public.detections(id) ON DELETE CASCADE,
    case_id VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    detail TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'critical',          -- 'critical', 'high', 'info'
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2.5 System Settings Table
CREATE TABLE IF NOT EXISTS public.system_settings (
    key VARCHAR(50) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Default settings seed
INSERT INTO public.system_settings (key, value)
VALUES ('recognition', '{"similarity_threshold": 0.80, "alert_threshold": 0.90}')
ON CONFLICT (key) DO NOTHING;

-- =============================================================================
-- 3. Indexes
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_missing_persons_case_id ON public.missing_persons(case_id);
CREATE INDEX IF NOT EXISTS idx_missing_persons_status ON public.missing_persons(status);
CREATE INDEX IF NOT EXISTS idx_cctv_jobs_status ON public.cctv_jobs(status);
CREATE INDEX IF NOT EXISTS idx_detections_person_id ON public.detections(person_id);
CREATE INDEX IF NOT EXISTS idx_detections_verification_status ON public.detections(verification_status);
CREATE INDEX IF NOT EXISTS idx_detections_detected_at ON public.detections(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON public.alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_is_read ON public.alerts(is_read);

-- Vector Cosine Similarity Index (HNSW)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'vector'
    ) THEN
        BEGIN
            CREATE INDEX IF NOT EXISTS idx_missing_persons_embedding_hnsw 
            ON public.missing_persons 
            USING hnsw (embedding vector_cosine_ops);
        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE 'Vector index note: %', SQLERRM;
        END;
    END IF;
END $$;
