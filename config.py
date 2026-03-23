# ============================================================
#  config.py  –  EDIT THIS FILE TO SET YOUR CAMERAS & MODELS
# ============================================================
#
#  Each camera has its OWN dedicated YOLOv8 model.
#  Format per entry:
#    "Camera Display Name": {
#        "rtsp":       "rtsp://user:pass@ip:port/stream",
#        "model":      "models/cam01_best.pt",   <- path to THIS camera's model
#        "class_id":   0,                         <- class index to count (None = all)
#        "confidence": 0.5,                       <- detection threshold
#    }
# ============================================================

CAMERAS = {
    "Camera 01 - Gate A": {
        "rtsp":       "rtsp://admin:password@192.168.1.101:554/stream1",
        "model":      "models/cam01_best.pt",
        "class_id":   0,
        "confidence": 0.5,
    },
    "Camera 02 - Gate B": {
        "rtsp":       "rtsp://admin:password@192.168.1.102:554/stream1",
        "model":      "models/cam02_best.pt",
        "class_id":   0,
        "confidence": 0.5,
    },
    "Camera 03 - Warehouse": {
        "rtsp":       "rtsp://admin:password@192.168.1.103:554/stream1",
        "model":      "models/cam03_best.pt",
        "class_id":   0,
        "confidence": 0.5,
    },
    "Camera 04 - Loading Bay": {
        "rtsp":       "rtsp://admin:password@192.168.1.104:554/stream1",
        "model":      "models/cam04_best.pt",
        "class_id":   0,
        "confidence": 0.5,
    },
    "Camera 05 - Conveyor 1": {
        "rtsp":       "rtsp://admin:password@192.168.1.105:554/stream1",
        "model":      "models/cam05_best.pt",
        "class_id":   0,
        "confidence": 0.5,
    },
    "Camera 06 - Conveyor 2": {
        "rtsp":       "rtsp://admin:password@192.168.1.106:554/stream1",
        "model":      "models/cam06_best.pt",
        "class_id":   0,
        "confidence": 0.5,
    },
    "Camera 07 - Packing A": {
        "rtsp":       "rtsp://admin:password@192.168.1.107:554/stream1",
        "model":      "models/cam07_best.pt",
        "class_id":   0,
        "confidence": 0.5,
    },
    "Camera 08 - Packing B": {
        "rtsp":       "rtsp://admin:password@192.168.1.108:554/stream1",
        "model":      "models/cam08_best.pt",
        "class_id":   0,
        "confidence": 0.5,
    },
    "Camera 09 - QC Station": {
        "rtsp":       "rtsp://admin:password@192.168.1.109:554/stream1",
        "model":      "models/cam09_best.pt",
        "class_id":   0,
        "confidence": 0.5,
    },
    "Camera 10 - Exit": {
        "rtsp":       "rtsp://admin:password@192.168.1.110:554/stream1",
        "model":      "models/cam10_best.pt",
        "class_id":   0,
        "confidence": 0.5,
    },
}

# ── CSV OUTPUT ───────────────────────────────────────────────
CSV_PATH              = "data/counts.csv"
LOG_INTERVAL_SECONDS  = 60        # seconds between each count row written

# ── STREAM SETTINGS ─────────────────────────────────────────
FRAME_WIDTH      = 640
FRAME_HEIGHT     = 360
RECONNECT_DELAY  = 5              # seconds before retrying a broken stream
MAX_QUEUE_SIZE   = 2              # per-camera frame buffer
