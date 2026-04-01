import os
import subprocess

import cv2
import insightface
import onnxruntime as ort
from insightface.app import FaceAnalysis

ort.preload_dlls(directory="")
ort.print_debug_info()

face_app = None
swapper = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "inswapper_128.onnx")


def load_models(progress_callback=None):
    global face_app, swapper

    print("ORT available providers:", ort.get_available_providers())

    if progress_callback:
        progress_callback(5)

    if face_app is None:
        face_app = FaceAnalysis(
            name="buffalo_l",
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        )
        face_app.prepare(ctx_id=0, det_size=(640, 640))

    if progress_callback:
        progress_callback(15)

    if swapper is None:
        swapper = insightface.model_zoo.get_model(
            MODEL_PATH,
            download=False,
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        )

    if progress_callback:
        progress_callback(25)


def reencode_to_browser_safe_mp4(
    temp_video_path,
    original_video_path,
    final_output_path,
):
    """
    Re-encode the processed temp video to H.264/AAC MP4.
    Tries to preserve audio from the original target video if present.
    """

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        temp_video_path,
        "-i",
        original_video_path,
        "-map",
        "0:v:0",
        "-map",
        "1:a:0?",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-shortest",
        final_output_path,
    ]

    print("Running ffmpeg:", " ".join(cmd))
    subprocess.run(cmd, check=True)


def process_video_swap(
    source_image_path, target_video_path, output_video_path, progress_callback=None
):
    load_models(progress_callback)

    source_img = cv2.imread(source_image_path)
    if source_img is None:
        raise ValueError("Could not read source image")

    if progress_callback:
        progress_callback(30)

    source_faces = face_app.get(source_img)
    if not source_faces:
        raise ValueError("No face found in source image")

    source_face = source_faces[0]

    if progress_callback:
        progress_callback(35)

    cap = cv2.VideoCapture(target_video_path)
    if not cap.isOpened():
        raise ValueError("Could not open target video")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 25.0

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        total_frames = 1

    temp_output_path = output_video_path.replace(".mp4", "_temp.mp4")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(temp_output_path, fourcc, fps, (width, height))
    if not out.isOpened():
        cap.release()
        raise ValueError("Could not create temporary output video")

    if progress_callback:
        progress_callback(40)

    frame_idx = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            faces = face_app.get(frame)
            result_frame = frame.copy()

            for target_face in faces:
                result_frame = swapper.get(
                    result_frame, target_face, source_face, paste_back=True
                )

            out.write(result_frame)
            frame_idx += 1

            progress = 40 + int((frame_idx / total_frames) * 50)
            if progress_callback:
                progress_callback(min(progress, 90))

    finally:
        cap.release()
        out.release()

    if progress_callback:
        progress_callback(95)

    reencode_to_browser_safe_mp4(
        temp_video_path=temp_output_path,
        original_video_path=target_video_path,
        final_output_path=output_video_path,
    )

    if os.path.exists(temp_output_path):
        os.remove(temp_output_path)

    if progress_callback:
        progress_callback(100)
