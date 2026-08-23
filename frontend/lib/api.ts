import {
  MISSING_PERSONS,
  DETECTIONS,
  ALERTS,
  CCTV_JOBS,
  DASHBOARD_STATS,
  ANALYTICS,
  type MissingPerson,
  type Detection,
  type AlertItem,
  type CctvJob,
  type CaseStatus,
} from "./demo-data";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* =========================================================================
   Helpers
   ========================================================================= */

function absoluteUrl(url: string | null | undefined): string | null {
  if (!url) return null;

  if (url.startsWith("http://") || url.startsWith("https://")) {
    return url;
  }

  return `${API_BASE}${url.startsWith("/") ? "" : "/"}${url}`;
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();

    if (typeof data?.detail === "string") {
      return data.detail;
    }

    if (typeof data?.message === "string") {
      return data.message;
    }

    return `Server error ${res.status}`;
  } catch {
    return `Server error ${res.status}`;
  }
}

/* =========================================================================
   Data Mapping
   ========================================================================= */

function mapPerson(raw: any): MissingPerson {
  const missingDate = raw?.missing_since
    ? new Date(raw.missing_since)
    : new Date();

  const now = new Date();

  const diffDays = Math.max(
    0,
    Math.floor(
      (now.getTime() - missingDate.getTime()) /
        (1000 * 60 * 60 * 24)
    )
  );

  const relativeTime =
    diffDays === 0
      ? "Today"
      : diffDays === 1
      ? "Yesterday"
      : `${diffDays} Days Ago`;

  return {
    id: raw?.case_id || raw?.id || "UNKNOWN",
    name: raw?.name || "Unknown",
    photoUrl: absoluteUrl(raw?.photo_url),
    age: raw?.age ?? "Unknown",
    sex:
      raw?.gender === "Female" ||
      raw?.gender === "F"
        ? "F"
        : "M",
    height: raw?.height || "Unknown",
    missingSince: raw?.missing_since || "Recently",
    relativeTime:
      raw?.status === "found_safe"
        ? "Resolved"
        : relativeTime,
    lastKnownLocation:
      raw?.last_known_location || "Unknown",
    status:
      (raw?.status as CaseStatus) || "active_alert",
  };
}

function mapDetection(raw: any): Detection {
  let detectedTime = "Just now";
  let detectedDate = "Today";

  if (raw?.detected_at) {
    const d = new Date(raw.detected_at);

    if (!Number.isNaN(d.getTime())) {
      detectedTime = d.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });

      detectedDate = d.toLocaleDateString([], {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    }
  }

  return {
    id: raw?.detection_code || raw?.id || "UNKNOWN",
    personId: raw?.person_id,
    personName: raw?.person_name || "Unknown Person",
    personPhoto: absoluteUrl(raw?.person_photo),
    frameUrl: absoluteUrl(raw?.frame_url) || "",
    confidence: Number(raw?.confidence ?? 0),
    location: raw?.location || "Unknown",
    cameraId: raw?.camera_id || "Unknown",
    date: detectedDate,
    detectedAt: detectedTime,
    verificationStatus:
      raw?.verification_status || "pending",
  };
}

function mapCctvJob(raw: any): CctvJob {
  let uploaded = "Recently";

  if (raw?.created_at) {
    const d = new Date(raw.created_at);

    if (!Number.isNaN(d.getTime())) {
      uploaded = `${d.toLocaleDateString([], {
        month: "short",
        day: "numeric",
      })} ${d.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      })}`;
    }
  }

  return {
    id: raw?.job_code || raw?.id || "UNKNOWN",
    filename: raw?.filename || "CCTV footage",
    location: raw?.location || "Unknown",
    cameraId: raw?.camera_id || "Unknown",
    uploadedAt: uploaded,
    status: raw?.status || "queued",
    frames: Number(raw?.total_frames ?? 0),
    faces: Number(raw?.faces_detected ?? 0),
    matches: Number(raw?.matches_found ?? 0),
  };
}

function mapAlert(raw: any): AlertItem {
  let timeStr = "Just now";

  if (raw?.created_at) {
    const d = new Date(raw.created_at);

    if (!Number.isNaN(d.getTime())) {
      const diffMin = Math.max(
        0,
        Math.floor(
          (Date.now() - d.getTime()) /
            (1000 * 60)
        )
      );

      timeStr =
        diffMin < 1
          ? "Just now"
          : diffMin < 60
          ? `${diffMin} min ago`
          : `${Math.floor(diffMin / 60)} hr ago`;
    }
  }

  return {
    id: raw?.alert_code || raw?.id || "UNKNOWN",
    title: raw?.title || "LocateMe Alert",
    detail: raw?.detail || "",
    severity: raw?.severity || "critical",
    time: timeStr,
    caseId: raw?.case_id,
  };
}

/* =========================================================================
   1. Missing Persons
   ========================================================================= */

export async function fetchMissingPersons(
  status?: string,
  search?: string
): Promise<MissingPerson[]> {
  try {
    const params = new URLSearchParams();

    if (status && status !== "all") {
      params.append("status", status);
    }

    if (search) {
      params.append("search", search);
    }

    const query = params.toString();

    const res = await fetch(
      `${API_BASE}/api/persons${query ? `?${query}` : ""}`,
      {
        cache: "no-store",
      }
    );

    if (!res.ok) {
      throw new Error(await parseError(res));
    }

    const data = await res.json();

    const items = Array.isArray(data)
      ? data
      : data?.items || [];

    return items.map(mapPerson);
  } catch (err) {
    console.warn(
      "[API] fetchMissingPersons fallback:",
      err
    );

    return MISSING_PERSONS.filter((person) => {
      const haystack =
        `${person.name} ${person.id} ${person.lastKnownLocation}`.toLowerCase();

      const matchesQuery =
        !search ||
        haystack.includes(search.toLowerCase());

      const matchesStatus =
        !status ||
        status === "all" ||
        person.status === status;

      return matchesQuery && matchesStatus;
    });
  }
}

export async function createMissingPerson(
  formData: FormData
): Promise<{
  success: boolean;
  data?: any;
  error?: string;
}> {
  try {
    const res = await fetch(
      `${API_BASE}/api/persons`,
      {
        method: "POST",
        body: formData,
      }
    );

    if (!res.ok) {
      throw new Error(await parseError(res));
    }

    const data = await res.json();

    return {
      success: true,
      data,
    };
  } catch (err: any) {
    console.warn(
      "[API] createMissingPerson:",
      err
    );

    return {
      success: false,
      error:
        err?.message ||
        "Failed to connect to backend service.",
    };
  }
}

/* =========================================================================
   2. CCTV
   ========================================================================= */

export async function uploadCctvFootage(
  formData: FormData
): Promise<{
  success: boolean;
  data?: any;
  error?: string;
}> {
  try {
    const res = await fetch(
      `${API_BASE}/api/cctv/upload`,
      {
        method: "POST",
        body: formData,
      }
    );

    if (!res.ok) {
      throw new Error(await parseError(res));
    }

    const data = await res.json();

    return {
      success: true,
      data,
    };
  } catch (err: any) {
    console.warn(
      "[API] uploadCctvFootage:",
      err
    );

    return {
      success: false,
      error:
        err?.message ||
        "Failed to upload CCTV footage.",
    };
  }
}

export async function fetchCctvJobs(): Promise<CctvJob[]> {
  try {
    const res = await fetch(
      `${API_BASE}/api/cctv/jobs`,
      {
        cache: "no-store",
      }
    );

    if (!res.ok) {
      throw new Error(await parseError(res));
    }

    const data = await res.json();

    const items = Array.isArray(data)
      ? data
      : data?.items || [];

    return items.map(mapCctvJob);
  } catch (err) {
    console.warn(
      "[API] fetchCctvJobs fallback:",
      err
    );

    return CCTV_JOBS;
  }
}

export async function fetchCctvJob(
  jobId: string
): Promise<CctvJob | null> {
  try {
    const res = await fetch(
      `${API_BASE}/api/cctv/jobs/${jobId}`,
      {
        cache: "no-store",
      }
    );

    if (!res.ok) {
      throw new Error(await parseError(res));
    }

    const data = await res.json();

    return mapCctvJob(data);
  } catch (err) {
    console.warn(
      "[API] fetchCctvJob:",
      err
    );

    return null;
  }
}

/**
 * Poll a CCTV job until it reaches a terminal state.
 */
export async function waitForCctvJob(
  jobId: string,
  onUpdate?: (job: CctvJob) => void,
  intervalMs = 1500,
  timeoutMs = 5 * 60 * 1000
): Promise<CctvJob | null> {
  const start = Date.now();

  while (Date.now() - start < timeoutMs) {
    const job = await fetchCctvJob(jobId);

    if (job) {
      onUpdate?.(job);

      const status = String(
        job.status
      ).toLowerCase();

      if (
        [
          "completed",
          "complete",
          "failed",
          "error",
        ].includes(status)
      ) {
        return job;
      }
    }

    await new Promise((resolve) =>
      setTimeout(resolve, intervalMs)
    );
  }

  return null;
}

/* =========================================================================
   3. Detections
   ========================================================================= */

export async function fetchDetections(
  status?: string
): Promise<Detection[]> {
  try {
    const params = new URLSearchParams();

    if (status && status !== "all") {
      params.append("status", status);
    }

    const query = params.toString();

    const res = await fetch(
      `${API_BASE}/api/detections${query ? `?${query}` : ""}`,
      {
        cache: "no-store",
      }
    );

    if (!res.ok) {
      throw new Error(await parseError(res));
    }

    const data = await res.json();

    const items = Array.isArray(data)
      ? data
      : data?.items || [];

    return items.map(mapDetection);
  } catch (err) {
    console.warn(
      "[API] fetchDetections fallback:",
      err
    );

    return DETECTIONS.filter(
      (d) =>
        !status ||
        status === "all" ||
        d.verificationStatus === status
    );
  }
}

export async function verifyDetection(
  detectionId: string,
  newStatus:
    | "verified"
    | "rejected"
    | "pending"
): Promise<boolean> {
  try {
    const res = await fetch(
      `${API_BASE}/api/detections/${detectionId}/verify`,
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          status: newStatus,
        }),
      }
    );

    if (!res.ok) {
      throw new Error(await parseError(res));
    }

    return true;
  } catch (err) {
    console.warn(
      "[API] verifyDetection:",
      err
    );

    return false;
  }
}

/* =========================================================================
   4. Alerts
   ========================================================================= */

export async function fetchAlerts(): Promise<
  AlertItem[]
> {
  try {
    const res = await fetch(
      `${API_BASE}/api/alerts`,
      {
        cache: "no-store",
      }
    );

    if (!res.ok) {
      throw new Error(await parseError(res));
    }

    const data = await res.json();

    const items = Array.isArray(data)
      ? data
      : data?.items || [];

    return items.map(mapAlert);
  } catch (err) {
    console.warn(
      "[API] fetchAlerts fallback:",
      err
    );

    return ALERTS;
  }
}

/* =========================================================================
   5. Dashboard
   ========================================================================= */

export async function fetchDashboardStats() {
  try {
    const res = await fetch(
      `${API_BASE}/api/stats`,
      {
        cache: "no-store",
      }
    );

    if (!res.ok) {
      throw new Error(await parseError(res));
    }

    return await res.json();
  } catch (err) {
    console.warn(
      "[API] fetchDashboardStats fallback:",
      err
    );

    return {
      stats: DASHBOARD_STATS,
      active_cases: 118,
      matches_today: 7,
      open_alerts: 12,
      cctv_jobs: 4,
    };
  }
}

/* =========================================================================
   6. Analytics
   ========================================================================= */

export async function fetchAnalytics() {
  try {
    const res = await fetch(
      `${API_BASE}/api/analytics`,
      {
        cache: "no-store",
      }
    );

    if (!res.ok) {
      throw new Error(await parseError(res));
    }

    const data = await res.json();

    return {
      ...ANALYTICS,

      // Backend snake_case → frontend camelCase
      matchRate:
        data?.match_rate ?? ANALYTICS.matchRate,

      avgConfidence:
        data?.avg_confidence ?? ANALYTICS.avgConfidence,

      medianTimeToMatch:
        data?.median_time_to_match ??
        ANALYTICS.medianTimeToMatch,

      camerasOnline:
        data?.cameras_online ??
        ANALYTICS.camerasOnline,

      byStatus:
        Array.isArray(data?.by_status)
          ? data.by_status
          : ANALYTICS.byStatus ?? [],

      byLocation:
        Array.isArray(data?.by_location)
          ? data.by_location
          : ANALYTICS.byLocation ?? [],
    };
  } catch (err) {
    console.warn(
      "[API] fetchAnalytics fallback:",
      err
    );

    return ANALYTICS;
  }
}

/* =========================================================================
   7. Settings
   ========================================================================= */

export async function fetchSettings() {
  try {
    const res = await fetch(
      `${API_BASE}/api/settings`,
      {
        cache: "no-store",
      }
    );

    if (!res.ok) {
      throw new Error(await parseError(res));
    }

    return await res.json();
  } catch (err) {
    console.warn(
      "[API] fetchSettings fallback:",
      err
    );

    return {
      similarity_threshold: 0.8,
      alert_threshold: 0.9,
      frame_sample_interval: 1.0,
      supabase_connected: false,
    };
  }
}

export async function updateSettings(
  settingsData: {
    similarity_threshold: number;
    alert_threshold?: number;
    frame_sample_interval?: number;
  }
) {
  try {
    const res = await fetch(
      `${API_BASE}/api/settings`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(settingsData),
      }
    );

    if (!res.ok) {
      throw new Error(await parseError(res));
    }

    return await res.json();
  } catch (err) {
    console.warn(
      "[API] updateSettings:",
      err
    );

    return null;
  }
}

/* =========================================================================
   8. Health Check
   ========================================================================= */

export async function checkApiHealth(): Promise<boolean> {
  try {
    const res = await fetch(
      `${API_BASE}/api/health`,
      {
        cache: "no-store",
      }
    );

    return res.ok;
  } catch {
    return false;
  }
}
// ============================================================
// UPDATE MISSING PERSON STATUS
// ============================================================

export async function updatePersonStatus(
  personId: string,
  status: "active_alert" | "found_safe" | "pending_verification",
): Promise<MissingPerson> {
  const params = new URLSearchParams({
    status,
  });

  const res = await fetch(
    `${API_BASE}/api/persons/${encodeURIComponent(personId)}/status?${params.toString()}`,
    {
      method: "PATCH",
      headers: {
        Accept: "application/json",
      },
    },
  );

  if (!res.ok) {
    throw new Error(await parseError(res));
  }

  return res.json();
}