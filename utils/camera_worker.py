"""
utils/camera_worker.py
One background thread per camera.
Each camera uses its own dedicated YOLOv8 model from model_registry.
"""
import threading
import time
import queue
import cv2
import numpy as np

from config import FRAME_WIDTH, FRAME_HEIGHT, RECONNECT_DELAY, MAX_QUEUE_SIZE, LOG_INTERVAL_SECONDS
from utils.csv_logger import log_count
from utils.model_registry import get_model


class CameraWorker:
    """
    Manages one RTSP camera stream + its own YOLO model in a daemon thread.

    Public API:
        .get_frame()   -> (jpeg_bytes | None, count)
        .stop()
        .status        -> "ok" | "connecting" | "error"
    """

    def __init__(self, cam_name: str, cam_cfg: dict):
        self.cam_name   = cam_name
        self.rtsp_url   = cam_cfg["rtsp"]
        self.model_path = cam_cfg["model"]
        self.class_id   = cam_cfg.get("class_id", 0)
        self.confidence = cam_cfg.get("confidence", 0.5)

        self.count      = 0
        self.status     = "connecting"

        self._q         = queue.Queue(maxsize=MAX_QUEUE_SIZE)
        self._stop_evt  = threading.Event()
        self._last_log  = time.time()

        self._thread = threading.Thread(target=self._run, daemon=True, name=f"cam-{cam_name}")
        self._thread.start()

    # ── Public ────────────────────────────────────────────────
    def get_frame(self):
        """Returns (jpeg_bytes, count). jpeg_bytes=None if no frame yet."""
        try:
            return self._q.get_nowait()
        except queue.Empty:
            return None, self.count

    def stop(self):
        self._stop_evt.set()

    # ── Private ───────────────────────────────────────────────
    def _run(self):
        while not self._stop_evt.is_set():
            self.status = "connecting"
            cap = cv2.VideoCapture(self.rtsp_url)
            if not cap.isOpened():
                self._push_error_frame("Cannot open stream — check RTSP URL")
                time.sleep(RECONNECT_DELAY)
                continue

            self.status = "ok"
            while not self._stop_evt.is_set():
                ret, frame = cap.read()
                if not ret:
                    self.status = "error"
                    self._push_error_frame("Stream lost — reconnecting…")
                    break

                frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
                annotated, count = self._infer(frame)
                self.count = count

                # CSV log at interval
                now = time.time()
                if now - self._last_log >= LOG_INTERVAL_SECONDS:
                    log_count(self.cam_name, count)
                    self._last_log = now

                _, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 75])
                self._push((buf.tobytes(), count))

            cap.release()
            time.sleep(RECONNECT_DELAY)

    def _infer(self, frame):
        try:
            model = get_model(self.cam_name, self.model_path)
            results = model(frame, conf=self.confidence, verbose=False)[0]
            boxes = results.boxes

            if self.class_id is not None:
                boxes = boxes[boxes.cls == self.class_id]
            count = len(boxes)

            annotated = results.plot()
            # Overlay camera name + count
            cv2.rectangle(annotated, (0, 0), (FRAME_WIDTH, 44), (0, 0, 0), -1)
            cv2.putText(annotated, f"{self.cam_name}",
                        (8, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 200, 255), 1)
            cv2.putText(annotated, f"COUNT: {count}",
                        (8, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (80, 220, 120), 2)
            return annotated, count

        except FileNotFoundError:
            self.status = "error"
            cv2.putText(frame, f"Model not found:", (8, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 80, 255), 1)
            cv2.putText(frame, self.model_path, (8, 42),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 80, 255), 1)
            return frame, 0

        except Exception as e:
            cv2.putText(frame, f"Inference error: {str(e)[:50]}", (8, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 60, 255), 1)
            return frame, 0

    def _push(self, item):
        if self._q.full():
            try:
                self._q.get_nowait()
            except queue.Empty:
                pass
        try:
            self._q.put_nowait(item)
        except queue.Full:
            pass

    def _push_error_frame(self, msg: str):
        blank = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
        cv2.putText(blank, self.cam_name, (12, 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 140, 200), 1)
        cv2.putText(blank, msg, (12, FRAME_HEIGHT // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 80, 220), 2)
        _, buf = cv2.imencode(".jpg", blank)
        self._push((buf.tobytes(), 0))
