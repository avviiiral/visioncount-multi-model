"""
pages/camera_dashboard.py
Individual camera: live feed + model info + analytics charts.
"""
import time
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date

from config import CAMERAS
from utils.state import get_workers
from utils.data_helpers import load_df, hourly_counts, camera_daily_series
from utils.model_registry import loaded_models

st.set_page_config(page_title="Camera Dashboard", page_icon="🎥", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; background: #080b12; }
.block-container { padding: 1.5rem 2rem; }
h1, h2, h3 { font-family: 'Space Mono', monospace !important; color: #dde6f0; }
.metric-box {
    background: #0d1829; border: 1px solid #1e3a5f; border-radius: 7px;
    padding: 14px 10px; text-align: center; margin-bottom: 8px;
}
.metric-val { font-family: 'Space Mono'; font-size: 1.7rem; color: #5b8dd9; font-weight: 700; }
.metric-lbl { font-family: 'Space Mono'; font-size: 0.58rem; color: #2d4a6b;
               text-transform: uppercase; letter-spacing: 1.5px; margin-top: 4px; }
.section-title {
    font-family: 'Space Mono'; font-size: 0.62rem; text-transform: uppercase;
    letter-spacing: 2px; color: #2d3f58; border-bottom: 1px solid #141e2e;
    padding-bottom: 7px; margin: 18px 0 12px 0;
}
.model-info-card {
    background: #0a1220; border: 1px solid #1a3050; border-radius: 7px;
    padding: 14px 16px; margin-bottom: 12px;
}
.model-info-row { display: flex; justify-content: space-between; align-items: center;
                  border-bottom: 1px solid #141e2e; padding: 5px 0; }
.model-info-row:last-child { border-bottom: none; }
.model-key   { font-family: 'Space Mono'; font-size: 0.6rem; color: #2d4a6b; }
.model-value { font-family: 'Space Mono'; font-size: 0.62rem; color: #93c5fd; }
.status-dot-ok  { color: #4ade80; }
.status-dot-err { color: #f87171; }
</style>
""", unsafe_allow_html=True)

# ── Guard ────────────────────────────────────────────────────
if "selected_cam" not in st.session_state or not st.session_state["selected_cam"]:
    st.warning("No camera selected.")
    if st.button("← Back"):
        st.switch_page("app.py")
    st.stop()

cam_name = st.session_state["selected_cam"]
cam_cfg  = CAMERAS.get(cam_name, {})

# ── Header ───────────────────────────────────────────────────
c_back, c_title = st.columns([1, 9])
with c_back:
    if st.button("← Back"):
        st.switch_page("app.py")
with c_title:
    st.markdown(f"## 🎥 {cam_name}")

# ── Two-column layout ────────────────────────────────────────
feed_col, info_col = st.columns([2, 3], gap="large")

with feed_col:
    st.markdown('<div class="section-title">Live Feed</div>', unsafe_allow_html=True)
    feed_ph  = st.empty()
    count_ph = st.empty()

    # Model info card
    st.markdown('<div class="section-title">Model Configuration</div>', unsafe_allow_html=True)
    is_loaded = cam_name in loaded_models()
    status_icon = '<span class="status-dot-ok">● LOADED</span>' if is_loaded \
                  else '<span class="status-dot-err">○ NOT YET LOADED</span>'
    st.markdown(f"""
    <div class="model-info-card">
      <div class="model-info-row">
        <span class="model-key">MODEL FILE</span>
        <span class="model-value">{cam_cfg.get("model","—").split("/")[-1]}</span>
      </div>
      <div class="model-info-row">
        <span class="model-key">FULL PATH</span>
        <span class="model-value">{cam_cfg.get("model","—")}</span>
      </div>
      <div class="model-info-row">
        <span class="model-key">CLASS ID</span>
        <span class="model-value">{cam_cfg.get("class_id","—")}</span>
      </div>
      <div class="model-info-row">
        <span class="model-key">CONFIDENCE</span>
        <span class="model-value">{cam_cfg.get("confidence","—")}</span>
      </div>
      <div class="model-info-row">
        <span class="model-key">STATUS</span>
        <span class="model-value">{status_icon}</span>
      </div>
    </div>""", unsafe_allow_html=True)

with info_col:
    st.markdown('<div class="section-title">Today\'s Statistics</div>', unsafe_allow_html=True)

    df    = load_df()
    today = date.today()

    hourly     = hourly_counts(df, today, cam_name)
    today_tot  = int(hourly["count"].sum()) if not hourly.empty else 0
    peak_hour  = int(hourly.loc[hourly["count"].idxmax(), "time_hour"]) if not hourly.empty else 0
    peak_count = int(hourly["count"].max()) if not hourly.empty else 0

    m1, m2, m3 = st.columns(3)
    for col, val, lbl in [
        (m1, f"{today_tot:,}", "Today Total"),
        (m2, f"{peak_hour:02d}:00", "Peak Hour"),
        (m3, f"{peak_count:,}", "Peak Count"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-box">
              <div class="metric-val">{val}</div>
              <div class="metric-lbl">{lbl}</div>
            </div>""", unsafe_allow_html=True)

    # Hourly bar
    st.markdown('<div class="section-title">Count by Hour — Today</div>', unsafe_allow_html=True)
    all_h = pd.DataFrame({"time_hour": range(24)})
    if not hourly.empty:
        h_full = all_h.merge(hourly, on="time_hour", how="left").fillna(0)
    else:
        h_full = all_h.assign(count=0)

    fig = go.Figure(go.Bar(
        x=h_full["time_hour"], y=h_full["count"],
        marker=dict(color="#5b8dd9", opacity=0.85),
    ))
    fig.update_layout(
        paper_bgcolor="#080b12", plot_bgcolor="#0d1829",
        font=dict(family="Space Mono", color="#4a6a8a", size=10),
        xaxis=dict(title="Hour", gridcolor="#141e2e", tickvals=list(range(0,24,2))),
        yaxis=dict(title="Count", gridcolor="#141e2e"),
        margin=dict(l=40, r=10, t=10, b=40), height=210,
    )
    st.plotly_chart(fig, use_container_width=True)

    # 30-day trend
    st.markdown('<div class="section-title">30-Day Trend</div>', unsafe_allow_html=True)
    daily = camera_daily_series(df, cam_name).tail(30)
    if not daily.empty:
        fig2 = go.Figure(go.Scatter(
            x=daily["day"], y=daily["count"],
            mode="lines+markers",
            line=dict(color="#4ade80", width=2),
            marker=dict(size=4),
            fill="tozeroy", fillcolor="rgba(74,222,128,0.07)"
        ))
        fig2.update_layout(
            paper_bgcolor="#080b12", plot_bgcolor="#0d1829",
            font=dict(family="Space Mono", color="#4a6a8a", size=10),
            xaxis=dict(gridcolor="#141e2e"),
            yaxis=dict(title="Count", gridcolor="#141e2e"),
            margin=dict(l=40, r=10, t=10, b=40), height=190,
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No historical data yet.")

# ── Live loop ────────────────────────────────────────────────
workers = get_workers()
worker  = workers.get(cam_name)
while worker:
    fb, count = worker.get_frame()
    if fb:
        feed_ph.image(fb, use_container_width=True)
    count_ph.markdown(f"**Live Count:** `{count}` pieces &nbsp;|&nbsp; "
                      f"**Model:** `{cam_cfg.get('model','').split('/')[-1]}`",
                      unsafe_allow_html=True)
    time.sleep(0.04)
