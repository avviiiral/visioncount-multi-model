"""
utils/model_registry.py
Loads and caches a separate YOLOv8 model for each camera.
Models are loaded lazily on first inference call and kept in memory.
"""
import threading
from typing import Dict

_models: Dict[str, object] = {}
_locks: Dict[str, threading.Lock] = {}
_global_lock = threading.Lock()


def _get_lock(cam_name: str) -> threading.Lock:
    with _global_lock:
        if cam_name not in _locks:
            _locks[cam_name] = threading.Lock()
        return _locks[cam_name]


def get_model(cam_name: str, model_path: str):
    """
    Return the YOLO model for this camera, loading it if not yet cached.
    Thread-safe: two threads for the same camera won't double-load.
    """
    if cam_name not in _models:
        lock = _get_lock(cam_name)
        with lock:
            if cam_name not in _models:   # double-checked locking
                from ultralytics import YOLO
                print(f"[ModelRegistry] Loading model for '{cam_name}': {model_path}")
                _models[cam_name] = YOLO(model_path)
    return _models[cam_name]


def loaded_models() -> Dict[str, str]:
    """Return dict of cam_name -> model path for status display."""
    return {k: type(v).__name__ for k, v in _models.items()}
