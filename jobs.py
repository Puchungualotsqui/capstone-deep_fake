import threading
import traceback
from face_swap import process_video_swap

JOBS = {}


def create_job(job_id, source_path, target_path, output_path):
    JOBS[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "progress": 0,
        "source_path": source_path,
        "target_path": target_path,
        "output_path": output_path,
        "error": None,
    }


def get_job(job_id):
    return JOBS.get(job_id)


def update_job(job_id, **kwargs):
    if job_id in JOBS:
        JOBS[job_id].update(kwargs)


def _job_runner(job_id):
    job = JOBS[job_id]
    try:
        print(f"[JOB {job_id}] started")

        process_video_swap(
            source_image_path=job["source_path"],
            target_video_path=job["target_path"],
            output_video_path=job["output_path"],
            progress_callback=lambda p: update_job(job_id, progress=p),
        )

        update_job(job_id, status="completed", progress=100)
        print(f"[JOB {job_id}] completed")

    except Exception as e:
        traceback.print_exc()
        update_job(job_id, status="failed", error=str(e))
        print(f"[JOB {job_id}] failed: {e}")


def run_job_in_background(job_id):
    thread = threading.Thread(target=_job_runner, args=(job_id,), daemon=True)
    thread.start()