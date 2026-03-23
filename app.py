"""
app.py  –  Main page: 10-camera live grid + model status + monthly calendar
Run:  streamlit run app.py
"""
import time
import calendar
from datetime import date
import streamlit as st

from config import CAMERAS
from utils.state import get_workers
from utils.data_helpers import load_df, monthly_totals
from utils.model_registry import loaded_models

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="VisionCount Multi-Model",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.main { background: #080b12; }
.block-container { padding: 1.2rem 2rem; max-width: 100%; }
h1, h2, h3 { font-family: 'Space Mono', monospace !important; color: #dde6f0; }

.cam-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    color: #5b8dd9;
    margin-bottom: 3px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
}
.cam-model-tag {
    font-family: 'Space Mono', monospace;
    font-size: 0.58rem;
    color: #3d5a82;
    margin-bottom: 4px;
}
.count-badge {
    background: #0d1829;
    color: #5b8dd9;
    border: 1px solid #1e3a5f;
    border-radius: 3px;
    padding: 2px 10px;
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
    display: inline-block;
    margin-top: 3px;
}
.model-status-ok   { color: #4ade80; font-family: 'Space Mono'; font-size: 0.6rem; }
.model-status-wait { color: #facc15; font-family: 'Space Mono'; font-size: 0.6rem; }
.model-status-err  { color: #f87171; font-family: 'Space Mono'; font-size: 0.6rem; }

.section-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 2.5px;
    color: #2d3f58;
    border-bottom: 1px solid #141e2e;
    padding-bottom: 8px;
    margin: 20px 0 14px 0;
}
.stButton>button {
    background: #0d1829 !important;
    border: 1px solid #1e3a5f !important;
    color: #5b8dd9 !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.65rem !important;
    border-radius: 5px !important;
    width: 100% !important;
    min-height: 52px !important;
    letter-spacing: 0.5px !important;
    transition: all 0.15s !important;
}
.stButton>button:hover {
    border-color: #5b8dd9 !important;
    background: #0f2040 !important;
    color: #93c5fd !important;
}

/* Calendar */
.cal-header {
    font-family: 'Space Mono', monospace;
    color: #2d3f58;
    font-size: 0.6rem;
    text-align: center;
    padding: 4px 0;
    letter-spacing: 2px;
}
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────
st.markdown("## 🔬 VisionCount — 10-Camera / 10-Model Monitor")

# ── Model status bar ─────────────────────────────────────────
with st.expander("⚙️ Model Load Status", expanded=False):
    loaded = loaded_models()
    cols = st.columns(5)
    for i, (name, cfg) in enumerate(CAMERAS.items()):
        with cols[i % 5]:
            short = name.split("–")[-1].strip() if "–" in name else name
            is_loaded = name in loaded
            tag  = "● LOADED" if is_loaded else "○ PENDING"
            cls  = "model-status-ok" if is_loaded else "model-status-wait"
            st.markdown(f"""
            <div style='background:#0d1829;border:1px solid #1e3a5f;border-radius:5px;padding:8px;margin-bottom:6px;'>
              <div style='font-family:Space Mono;font-size:0.62rem;color:#93c5fd;'>{short}</div>
              <div style='font-family:Space Mono;font-size:0.55rem;color:#2d4a6b;margin:2px 0;'>{cfg["model"]}</div>
              <div class='{cls}'>{tag}</div>
            </div>""", unsafe_allow_html=True)

# ── Camera grid (5 × 2) ──────────────────────────────────────
st.markdown('<div class="section-title">Live Feeds — All Cameras</div>', unsafe_allow_html=True)
workers = get_workers()
cam_names = list(CAMERAS.keys())

COLS = 5
placeholders       = {}
count_placeholders = {}

for row_start in range(0, len(cam_names), COLS):
    row_cams = cam_names[row_start:row_start + COLS]
    cols = st.columns(COLS)
    for col, name in zip(cols, row_cams):
        with col:
            short_model = CAMERAS[name]["model"].split("/")[-1]
            st.markdown(f'<div class="cam-label">{name}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="cam-model-tag">model: {short_model}</div>', unsafe_allow_html=True)
            placeholders[name]       = st.empty()
            count_placeholders[name] = st.empty()

# ── Open Camera buttons ──────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-title">Open Individual Dashboard</div>', unsafe_allow_html=True)
btn_cols = st.columns(COLS)
for i, name in enumerate(cam_names):
    with btn_cols[i % COLS]:
        short = name.split("–")[-1].strip() if "–" in name else name
        if st.button(f"🎥 {short}", key=f"btn_{name}"):
            st.session_state["selected_cam"] = name
            st.switch_page("pages/camera_dashboard.py")

# ── Calendar ─────────────────────────────────────────────────
st.markdown("---")
today = date.today()
st.markdown(f'<div class="section-title">Monthly Overview — {today.strftime("%B %Y")}</div>',
            unsafe_allow_html=True)

df = load_df()
month_data = monthly_totals(df, today.year, today.month)
day_totals = {int(r["day"]): int(r["total"]) for _, r in month_data.iterrows()}

day_names = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
h_cols = st.columns(7)
for i, d in enumerate(day_names):
    with h_cols[i]:
        st.markdown(f'<div class="cal-header">{d}</div>', unsafe_allow_html=True)

for week in calendar.monthcalendar(today.year, today.month):
    w_cols = st.columns(7)
    for i, day in enumerate(week):
        with w_cols[i]:
            if day == 0:
                st.markdown('<div style="min-height:50px"></div>', unsafe_allow_html=True)
            else:
                total = day_totals.get(day, 0)
                is_today = (day == today.day)
                label = f"**{day}**\n{'📦 ' + str(total) if total else ''}"
                key = f"cal_{today.year}_{today.month}_{day}"
                if st.button(label, key=key,
                             help=f"{date(today.year, today.month, day).strftime('%b %d')} — {total} pieces"):
                    st.session_state["dashboard_date"] = date(today.year, today.month, day)
                    st.session_state["selected_cam"] = None
                    st.switch_page("pages/day_dashboard.py")

# ── Live update loop ─────────────────────────────────────────
while True:
    for name, worker in workers.items():
        frame_bytes, count = worker.get_frame()
        if frame_bytes:
            placeholders[name].image(frame_bytes, use_container_width=True)
        count_placeholders[name].markdown(
            f'<div class="count-badge">COUNT: {count}</div>', unsafe_allow_html=True
        )
    time.sleep(0.04)
