"""
pages/day_dashboard.py
Full analytics for a calendar-selected date across all 10 cameras.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date

from config import CAMERAS
from utils.data_helpers import load_df, daily_totals, hourly_counts, monthly_totals

st.set_page_config(page_title="Day Dashboard", page_icon="📅", layout="wide")

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
.metric-val { font-family: 'Space Mono'; font-size: 1.6rem; color: #5b8dd9; font-weight: 700; }
.metric-lbl { font-family: 'Space Mono'; font-size: 0.58rem; color: #2d4a6b;
               text-transform: uppercase; letter-spacing: 1.5px; margin-top: 4px; }
.section-title {
    font-family: 'Space Mono'; font-size: 0.62rem; text-transform: uppercase;
    letter-spacing: 2px; color: #2d3f58; border-bottom: 1px solid #141e2e;
    padding-bottom: 7px; margin: 20px 0 14px 0;
}
.model-chip {
    display: inline-block;
    background: #0a1220; border: 1px solid #1a3050;
    border-radius: 3px; padding: 2px 7px;
    font-family: 'Space Mono'; font-size: 0.55rem; color: #3d6a9f;
    margin-left: 6px;
}
</style>
""", unsafe_allow_html=True)

# ── Date guard ───────────────────────────────────────────────
sel_date = st.session_state.get("dashboard_date", date.today())

c_back, c_title = st.columns([1, 9])
with c_back:
    if st.button("← Back"):
        st.switch_page("app.py")
with c_title:
    st.markdown(f"## 📅 Day Dashboard — {sel_date.strftime('%A, %d %B %Y')}")

df = load_df()

# ── KPI row ──────────────────────────────────────────────────
day_df    = daily_totals(df, sel_date)
all_count = int(day_df["total"].sum())   if not day_df.empty else 0
active    = int((day_df["total"] > 0).sum()) if not day_df.empty else 0
top_cam   = day_df.loc[day_df["total"].idxmax(), "cam_name"] if not day_df.empty else "—"
top_val   = int(day_df["total"].max()) if not day_df.empty else 0
avg_val   = round(all_count / max(active, 1))

m1, m2, m3, m4, m5 = st.columns(5)
for col, val, lbl in [
    (m1, f"{all_count:,}", "Total Pieces"),
    (m2, active, "Active Cameras"),
    (m3, avg_val, "Avg per Camera"),
    (m4, (top_cam.split("–")[-1].strip()[:11] if "–" in top_cam else top_cam[:11]), "Top Camera"),
    (m5, f"{top_val:,}", "Top Camera Count"),
]:
    with col:
        st.markdown(f"""
        <div class="metric-box">
          <div class="metric-val">{val}</div>
          <div class="metric-lbl">{lbl}</div>
        </div>""", unsafe_allow_html=True)

# ── Per-camera bar with model labels ─────────────────────────
st.markdown('<div class="section-title">Count per Camera (with Model)</div>', unsafe_allow_html=True)
if not day_df.empty:
    model_map = {name: cfg["model"].split("/")[-1] for name, cfg in CAMERAS.items()}
    day_df["model"] = day_df["cam_name"].map(model_map).fillna("unknown")
    day_df["label"] = day_df.apply(
        lambda r: r["cam_name"].split("–")[-1].strip() if "–" in r["cam_name"] else r["cam_name"],
        axis=1
    )
    day_df["hover"] = day_df.apply(
        lambda r: f"{r['cam_name']}<br>Model: {r['model']}<br>Count: {r['total']}", axis=1
    )

    fig = go.Figure(go.Bar(
        x=day_df["label"],
        y=day_df["total"],
        text=day_df["total"],
        textposition="outside",
        customdata=day_df["model"],
        hovertemplate="%{x}<br>Model: %{customdata}<br>Count: %{y}<extra></extra>",
        marker=dict(
            color=day_df["total"],
            colorscale=[[0,"#0d1829"],[0.5,"#1e4080"],[1.0,"#5b8dd9"]],
            showscale=False,
            line=dict(color="#1e3a5f", width=1),
        ),
        textfont=dict(family="Space Mono", size=9, color="#7aafd4"),
    ))
    fig.update_layout(
        paper_bgcolor="#080b12", plot_bgcolor="#0d1829",
        font=dict(family="Space Mono", color="#4a6a8a", size=10),
        xaxis=dict(gridcolor="#141e2e", tickangle=-25),
        yaxis=dict(title="Count", gridcolor="#141e2e"),
        margin=dict(l=40, r=10, t=30, b=80), height=290,
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Hourly heatmap ───────────────────────────────────────────
st.markdown('<div class="section-title">Hourly Heatmap — All Cameras</div>', unsafe_allow_html=True)
day_sub = df[df["date"].dt.normalize() == pd.Timestamp(sel_date).normalize()]
if not day_sub.empty:
    cam_list = list(CAMERAS.keys())
    heat = pd.pivot_table(
        day_sub, values="count", index="cam_name", columns="time_hour",
        aggfunc="sum", fill_value=0
    ).reindex(index=cam_list, columns=range(24), fill_value=0)

    short_y = [c.split("–")[-1].strip() if "–" in c else c for c in heat.index]
    fig2 = go.Figure(go.Heatmap(
        z=heat.values,
        x=[f"{h:02d}:00" for h in range(24)],
        y=short_y,
        colorscale=[[0,"#080b12"],[0.3,"#0d2040"],[0.7,"#1e4080"],[1.0,"#5b8dd9"]],
        showscale=True,
    ))
    fig2.update_layout(
        paper_bgcolor="#080b12", plot_bgcolor="#0d1829",
        font=dict(family="Space Mono", color="#4a6a8a", size=10),
        margin=dict(l=130, r=20, t=10, b=50), height=320,
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Multi-camera hourly line chart ───────────────────────────
st.markdown('<div class="section-title">Hourly Breakdown per Camera</div>', unsafe_allow_html=True)
if not day_sub.empty:
    fig3 = go.Figure()
    palette = px.colors.qualitative.Pastel
    for i, cam in enumerate(list(CAMERAS.keys())):
        h = hourly_counts(df, sel_date, cam)
        if h.empty:
            continue
        h_full = pd.DataFrame({"time_hour": range(24)}).merge(h, on="time_hour", how="left").fillna(0)
        short  = cam.split("–")[-1].strip() if "–" in cam else cam
        fig3.add_trace(go.Scatter(
            x=h_full["time_hour"], y=h_full["count"],
            mode="lines", name=short,
            line=dict(color=palette[i % len(palette)], width=1.5),
        ))
    fig3.update_layout(
        paper_bgcolor="#080b12", plot_bgcolor="#0d1829",
        font=dict(family="Space Mono", color="#4a6a8a", size=10),
        xaxis=dict(title="Hour", gridcolor="#141e2e", tickvals=list(range(0,24,2))),
        yaxis=dict(title="Count", gridcolor="#141e2e"),
        legend=dict(bgcolor="#0d1829", bordercolor="#1e3a5f", font=dict(size=8)),
        margin=dict(l=40, r=10, t=10, b=40), height=280,
    )
    st.plotly_chart(fig3, use_container_width=True)

# ── Data table + download ─────────────────────────────────────
st.markdown('<div class="section-title">Detailed Log — All Records This Day</div>',
            unsafe_allow_html=True)
if not day_sub.empty:
    display = day_sub[["cam_name","count","date","time_hour","min","sec"]].copy()
    display["date"] = display["date"].dt.strftime("%Y-%m-%d")
    display.columns = ["Camera","Count","Date","Hour","Min","Sec"]
    st.dataframe(display, use_container_width=True, height=260)
    st.download_button(
        "⬇ Download CSV for this day",
        data=day_sub.to_csv(index=False).encode(),
        file_name=f"counts_{sel_date}.csv",
        mime="text/csv",
    )
else:
    st.info("No data recorded for this date.")
