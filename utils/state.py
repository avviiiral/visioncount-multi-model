"""
utils/state.py
Keeps CameraWorker instances alive across Streamlit reruns via session_state.
"""
import streamlit as st
from config import CAMERAS
from utils.camera_worker import CameraWorker


def get_workers() -> dict:
    """Return {cam_name: CameraWorker}, initialising on first call."""
    if "workers" not in st.session_state:
        st.session_state["workers"] = {
            name: CameraWorker(name, cfg)
            for name, cfg in CAMERAS.items()
        }
    return st.session_state["workers"]
