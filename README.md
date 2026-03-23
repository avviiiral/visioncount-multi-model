# VisionCount Multi-Model — 10 Cameras × 10 Models

Each camera runs its **own dedicated YOLOv8 model** in a separate background thread.
Models are loaded lazily (on first frame) and cached in memory for the session.

---

## Project Structure

```
vision_counter_multi/
├── app.py                        Main page: 5×2 live grid + model status + calendar
├── config.py                     EDIT THIS — RTSP links, model paths, settings
├── requirements.txt
├── data/
│   └── counts.csv                Auto-generated count log
├── models/
│   ├── cam01_best.pt             Put your model files here
│   ├── cam02_best.pt
│   └── ...  (cam03 – cam10)
├── pages/
│   ├── camera_dashboard.py       Per-camera: live feed + model info + charts
│   └── day_dashboard.py          Calendar-date: all cameras, heatmap, table
└── utils/
    ├── model_registry.py         Lazy per-camera model loader + cache
    ├── camera_worker.py          RTSP thread — uses model_registry
    ├── csv_logger.py             Thread-safe CSV writer
    ├── data_helpers.py           Pandas analytics
    └── state.py                  Streamlit session state manager
```

---

## Setup

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Edit `config.py`

For each camera, fill in:
```python
"Camera 01 - Gate A": {
    "rtsp":       "rtsp://admin:yourpass@192.168.1.101:554/stream1",
    "model":      "models/cam01_best.pt",   # path to THIS camera's .pt file
    "class_id":   0,                         # which class to count (None = all)
    "confidence": 0.5,                       # detection threshold
},
```

You have **10 entries** — one per camera with its own model path.

### 3. Place models
Copy your `.pt` files into the `models/` folder.
Names must match the `"model"` values in `config.py`.

### 4. Run
```bash
streamlit run app.py
```

Open: http://localhost:8501

---

## How Multi-Model Loading Works

`utils/model_registry.py` maintains a global dict `{cam_name -> YOLO model}`.

- Models are **not loaded at startup** — they load on the first frame from that camera.
- Each camera's thread calls `get_model(cam_name, model_path)` which uses
  double-checked locking so two threads never double-load the same model.
- The **Model Load Status** expander on the home page shows which models are loaded.

**Memory note:** 10 YOLOv8-nano models ≈ 600 MB RAM. YOLOv8-large × 10 ≈ 5 GB.
Plan GPU/RAM accordingly or stagger camera startup if needed.

---

## CSV Format

`data/counts.csv` — one row per camera per `LOG_INTERVAL_SECONDS` (default 60s):

| cam_name | count | date | time_hour | min | sec |
|---|---|---|---|---|---|
| Camera 01 - Gate A | 14 | 2024-12-01 | 9 | 30 | 0 |

---

## Pages

| Page | Description |
|---|---|
| `app.py` | 5×2 live grid, model status panel, monthly calendar |
| `pages/camera_dashboard.py` | Live feed + model config card + hourly chart + 30d trend |
| `pages/day_dashboard.py` | KPIs, per-camera bar (hover shows model), heatmap, line chart, table |

---

## Config Reference

| Key | Default | Description |
|---|---|---|
| `LOG_INTERVAL_SECONDS` | 60 | Seconds between CSV writes per camera |
| `FRAME_WIDTH/HEIGHT` | 640×360 | Resize resolution |
| `RECONNECT_DELAY` | 5 | Seconds before retrying broken stream |
| per-camera `confidence` | 0.5 | YOLO detection threshold |
| per-camera `class_id` | 0 | Class index to count; `None` = all classes |

---

## Troubleshooting

**"Model not found"** shown on feed
→ The `.pt` file path in `config.py` doesn't match the actual file.
→ Check `models/README.txt` for expected filenames.

**High RAM usage**
→ Use YOLOv8n (nano) models where possible: `yolo export model=best.pt format=onnx`
→ Or reduce `MAX_QUEUE_SIZE` in config to limit buffering.

**Camera shows "Cannot open stream"**
→ Test RTSP URL in VLC: Media → Open Network Stream.
→ Common path variants: `/stream1`, `/h264/ch01/main/av_stream`, `/cam/realmonitor`
