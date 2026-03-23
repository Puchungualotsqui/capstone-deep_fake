import os
import cv2
import insightface
from insightface.app import FaceAnalysis
import onnxruntime as ort

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


def process_video_swap(source_image_path, target_video_path, output_video_path, progress_callback=None):
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

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    if progress_callback:
        progress_callback(40)

    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        faces = face_app.get(frame)
        result_frame = frame.copy()

        for target_face in faces:
            result_frame = swapper.get(
                result_frame,
                target_face,
                source_face,
                paste_back=True
            )

        out.write(result_frame)
        frame_idx += 1

        # Map frame progress into 40..99 range
        progress = 40 + int((frame_idx / total_frames) * 59)
        if progress_callback:
            progress_callback(min(progress, 99))

    cap.release()
    out.release()

    if progress_callback:
        progress_callback(100)