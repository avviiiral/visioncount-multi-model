"""
utils/csv_logger.py
Thread-safe CSV writer for count records.
"""
import csv
import os
import threading
from datetime import datetime
from config import CSV_PATH

_lock = threading.Lock()
COLUMNS = ["cam_name", "count", "date", "time_hour", "min", "sec"]


def _ensure_file():
    dirpath = os.path.dirname(CSV_PATH)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=COLUMNS).writeheader()


def log_count(cam_name: str, count: int):
    _ensure_file()
    now = datetime.now()
    row = {
        "cam_name":  cam_name,
        "count":     count,
        "date":      now.strftime("%Y-%m-%d"),
        "time_hour": now.hour,
        "min":       now.minute,
        "sec":       now.second,
    }
    with _lock:
        with open(CSV_PATH, "a", newline="") as f:
            csv.DictWriter(f, fieldnames=COLUMNS).writerow(row)


def read_all():
    _ensure_file()
    with _lock:
        with open(CSV_PATH, "r", newline="") as f:
            return list(csv.DictReader(f))
