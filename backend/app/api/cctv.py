from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from app.core.database import db
from app.core.storage import storage
from app.services.video_processor import video_processor
from app.schemas.cctv import CCTVJobResponse, CCTVJobListResponse

router = APIRouter(prefix="/cctv", tags=["CCTV Ingestion & Processing"])


@router.post("/upload", response_model=CCTVJobResponse)
async def upload_cctv(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    location: str = Form("Downtown Transit Center, Sector 4"),
    camera_id: str = Form("CAM-04-DT-12"),
    capture_time: Optional[str] = Form(None),
):
    """
    Uploads CCTV footage with camera metadata and dispatches async background worker
    to extract frames, detect faces, and run similarity matching.
    """
    if not video.filename:
        raise HTTPException(status_code=400, detail="A video file must be provided.")

    video_bytes = await video.read()
    if len(video_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded video file is empty.")

    # 1. Create job record
    job_record = db.create_cctv_job({
        "filename": video.filename,
        "location": location,
        "camera_id": camera_id,
        "capture_time": capture_time,
    })

    # 2. Save video locally
    video_url, local_path = storage.save_video(video_bytes, video.filename, job_record["job_code"])
    db.update_cctv_job(job_record["id"], {"video_url": video_url})
    job_record["video_url"] = video_url

    # 3. Dispatch background video processing worker
    background_tasks.add_task(
        video_processor.process_cctv_video,
        job_id=job_record["id"],
        video_path=local_path,
        location=location,
        camera_id=camera_id,
        capture_time_str=job_record["capture_time"]
    )

    return job_record


@router.get("/jobs", response_model=CCTVJobListResponse)
def list_cctv_jobs():
    """Lists all CCTV processing jobs and their current status."""
    jobs = db.get_cctv_jobs()
    return {
        "total": len(jobs),
        "items": jobs
    }


@router.get("/jobs/{job_id}", response_model=CCTVJobResponse)
def get_cctv_job(job_id: str):
    """Gets details and live processing status for a single CCTV job."""
    job = db.get_cctv_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="CCTV job not found.")
    return job
