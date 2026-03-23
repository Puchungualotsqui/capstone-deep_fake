import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from jobs import create_job, get_job, update_job, run_job_in_background

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 300 * 1024 * 1024  # 300 MB example

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv"}


def allowed_file(filename, allowed_extensions):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )


@app.route("/api/v1/swap", methods=["POST"])
def swap():
    if "source_image" not in request.files or "target_video" not in request.files:
        return jsonify({"error": "source_image and target_video are required"}), 400

    source_image = request.files["source_image"]
    target_video = request.files["target_video"]

    if source_image.filename == "" or target_video.filename == "":
        return jsonify({"error": "Both files must have a filename"}), 400

    if not allowed_file(source_image.filename, ALLOWED_IMAGE_EXTENSIONS):
        return jsonify({"error": "Invalid source image format"}), 400

    if not allowed_file(target_video.filename, ALLOWED_VIDEO_EXTENSIONS):
        return jsonify({"error": "Invalid target video format"}), 400

    job_id = str(uuid.uuid4())

    source_filename = f"{job_id}_source_{secure_filename(source_image.filename)}"
    target_filename = f"{job_id}_target_{secure_filename(target_video.filename)}"

    source_path = os.path.join(UPLOAD_DIR, source_filename)
    target_path = os.path.join(UPLOAD_DIR, target_filename)
    output_filename = f"{job_id}.mp4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    source_image.save(source_path)
    target_video.save(target_path)

    create_job(
        job_id=job_id,
        source_path=source_path,
        target_path=target_path,
        output_path=output_path,
    )

    run_job_in_background(job_id)

    return jsonify({
        "status": "processing",
        "job_id": job_id
    }), 202


@app.route("/api/v1/status/<job_id>", methods=["GET"])
def status(job_id):
    job = get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    response = {
        "status": job["status"],
        "progress": job["progress"]
    }

    if job["status"] == "completed":
        response["result_url"] = f"/media/{os.path.basename(job['output_path'])}"

    if job["status"] == "failed":
        response["error"] = job.get("error", "Unknown error")

    return jsonify(response), 200


@app.route("/media/<filename>", methods=["GET"])
def media(filename):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    app.run(debug=False)