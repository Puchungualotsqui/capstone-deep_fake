
---

# FaceSwap Backend

This repository contains the backend service for the FaceSwap application.
It provides a REST API that accepts a source face image and a target video, performs face swapping using InsightFace, and returns a processed video.

The backend is implemented in Python using Flask and performs video processing with OpenCV, InsightFace, ONNX Runtime, and FFmpeg.

---

# Features

* REST API for submitting face swap jobs
* Asynchronous background processing
* Real-time progress polling
* GPU acceleration using ONNX Runtime (optional)
* Browser-compatible video output (H.264 + AAC)
* Automatic audio preservation from the original video
* Compatible with web browsers and messaging platforms

---

# Project Structure

```
backend/
├── app.py
├── jobs.py
├── face_swap.py
├── uploads/
├── outputs/
├── models/
│   └── inswapper_128.onnx
├── requirements.txt
└── README.md
```

---

# Requirements

* Python 3.12 recommended
* FFmpeg installed and available in PATH
* NVIDIA GPU recommended for faster processing (optional)

Python packages are listed in `requirements.txt`.

---

# Setup

## 1. Clone the repository

```
git clone <repository-url>
cd backend
```

## 2. Create a virtual environment

```
python3.12 -m venv .venv
source .venv/bin/activate
```

For Fish shell:

```
source .venv/bin/activate.fish
```

## 3. Install dependencies

```
pip install -r requirements.txt
```

---

# Model Setup

Download the InsightFace swap model:

```
inswapper_128.onnx
```

Place it in:

```
models/inswapper_128.onnx
```

---

# Running the Server

Start the Flask server:

```
python app.py
```

The server runs at:

```
http://127.0.0.1:5000
```

---

# API Endpoints

## POST `/api/v1/swap`

Upload a source face image and target video.

Request type:

```
multipart/form-data
```

Fields:

```
source_image  image file (jpg or png)
target_video  video file (mp4)
```

Example:

```
curl -X POST http://127.0.0.1:5000/api/v1/swap \
  -F "source_image=@face.jpg" \
  -F "target_video=@video.mp4"
```

Response:

```
{
  "status": "processing",
  "job_id": "uuid"
}
```

---

## GET `/api/v1/status/{job_id}`

Check the progress of a submitted job.

Example:

```
curl http://127.0.0.1:5000/api/v1/status/<job_id>
```

Possible responses during processing:

```
{
  "status": "processing",
  "progress": 45
}
```

Completed job:

```
{
  "status": "completed",
  "progress": 100,
  "result_url": "/media/<job_id>.mp4"
}
```

Failed job:

```
{
  "status": "failed",
  "error": "error message"
}
```

---

## GET `/media/<filename>`

Download the generated video file.

Example:

```
http://127.0.0.1:5000/media/<job_id>.mp4
```

---

# Frontend Integration

Frontend applications should follow this workflow:

1. Upload files using `POST /api/v1/swap`
2. Store the returned `job_id`
3. Poll `GET /api/v1/status/{job_id}` every 2–3 seconds
4. Update the UI progress bar from `progress`
5. When `status = completed`, load the video from `result_url`
6. When `status = failed`, display the error message

---

# Video Encoding

The processing pipeline:

1. Frames are processed using OpenCV and InsightFace
2. A temporary video is generated
3. FFmpeg re-encodes the video to ensure compatibility

Final encoding settings:

* Video codec: H.264
* Audio codec: AAC
* Pixel format: yuv420p
* Container: MP4

This ensures compatibility with browsers and messaging platforms.

---

# Troubleshooting

## GPU not used

Verify ONNX Runtime providers:

```
python -c "import onnxruntime as ort; print(ort.get_available_providers())"
```

Expected output should include:

```
CUDAExecutionProvider
```

If not, install GPU runtime:

```
pip install "onnxruntime-gpu[cuda,cudnn]"
```

---

## Video cannot be played in browser

Ensure FFmpeg is installed:

```
ffmpeg -version
```

The backend automatically converts output to a browser-compatible format.

---

# Development Notes

This backend is designed to run locally during development.
The Flask development server should not be used in production.

For production deployment, consider using:

* Gunicorn
* Nginx
* Docker
* A job queue such as Celery or Redis

---

# License

This project is intended for educational and research purposes.
