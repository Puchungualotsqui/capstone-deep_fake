```md
# FaceSwap Backend (Flask)

This is the backend service for the FaceSwap project. It provides an API to upload a source face image and a target video, performs face swapping using InsightFace, and returns a processed video.

---

## Features

- Upload image and video via API
- Asynchronous processing using background threads
- Real-time progress tracking
- GPU acceleration support (ONNX Runtime)
- Outputs browser-compatible and WhatsApp-compatible MP4 videos (H.264 + AAC)
- Simple REST API for frontend integration

---

## Project Structure

```

.
├── app.py                # Flask app and routes
├── jobs.py               # Background job management
├── face_swap.py          # Face swap processing logic
├── models/               # ONNX model files (not tracked)
├── uploads/              # Uploaded files (runtime)
├── outputs/              # Generated videos (runtime)
├── requirements.txt
└── README.md

````

---

## Requirements

- Python 3.12 recommended
- ffmpeg installed on system
- NVIDIA GPU (optional, for acceleration)

---

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd <repo-folder>
````

### 2. Create virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate.fish   # for fish shell
# or
source .venv/bin/activate        # for bash/zsh
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install ffmpeg

```bash
sudo pacman -S ffmpeg     # Arch Linux
# or
sudo apt install ffmpeg   # Ubuntu/Debian
```

### 5. Add model file

Download `inswapper_128.onnx` and place it in:

```
models/inswapper_128.onnx
```

---

## Running the Server

```bash
python app.py
```

Server will run at:

```
http://127.0.0.1:5000
```

---

## API Endpoints

### POST `/api/v1/swap`

Upload files and start processing.

**Request:**

* Content-Type: `multipart/form-data`
* Fields:

  * `source_image` (image file)
  * `target_video` (mp4 file)

**Response:**

```json
{
  "status": "processing",
  "job_id": "uuid"
}
```

---

### GET `/api/v1/status/{job_id}`

Check job progress.

**Processing:**

```json
{
  "status": "processing",
  "progress": 45
}
```

**Completed:**

```json
{
  "status": "completed",
  "progress": 100,
  "result_url": "/media/<file>.mp4"
}
```

**Failed:**

```json
{
  "status": "failed",
  "progress": 10,
  "error": "error message"
}
```

---

### GET `/media/<filename>`

Serves generated video file.

---

## Testing with curl

### Upload

```bash
curl -X POST http://127.0.0.1:5000/api/v1/swap \
  -F "source_image=@face.jpg" \
  -F "target_video=@video.mp4"
```

### Check status

```bash
curl http://127.0.0.1:5000/api/v1/status/<job_id>
```

### Download result

```bash
curl -L -o result.mp4 http://127.0.0.1:5000/media/<filename>.mp4
```

---

## Notes on Video Output

The backend:

1. Processes frames using OpenCV
2. Generates a temporary video
3. Re-encodes using ffmpeg to ensure compatibility:

* Video codec: H.264
* Audio codec: AAC
* Pixel format: yuv420p

This ensures compatibility with browsers and messaging platforms such as WhatsApp.

---

## GPU Support

To enable GPU acceleration:

```bash
pip install "onnxruntime-gpu[cuda,cudnn]"
```

Verify:

```bash
python -c "import onnxruntime as ort; print(ort.get_available_providers())"
```

Expected:

```
['CUDAExecutionProvider', 'CPUExecutionProvider']
```

---

## Troubleshooting

### CORS issues

Install and enable CORS:

```bash
pip install flask-cors
```

In `app.py`:

```python
from flask_cors import CORS
CORS(app)
```

---

### Video not playing in browser

Ensure ffmpeg step is working and output is encoded with:

* libx264
* yuv420p
* aac

---

### Model not found

Ensure file exists:

```
models/inswapper_128.onnx
```

---

### GPU not used

Check:

```bash
nvidia-smi
```

and:

```bash
python -c "import onnxruntime as ort; print(ort.get_available_providers())"
```

---

## Development Notes

* Background jobs are handled with threads (not production-ready)
* Jobs are stored in memory (lost on restart)
* Suitable for prototypes and demos

---

## License

This project is for educational purposes.

```
```
