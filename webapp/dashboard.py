# webapp/dashboard.py

import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime, timezone
from database import get_recent_predictions, DB_PATH

st.set_page_config(
    page_title="Health Monitoring Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏭 Multi-Machine Health Monitoring Dashboard")
st.markdown("---")

# ---------- REAL STATUS CHECKS ----------
def check_backend():
    try:
        r = requests.get("http://127.0.0.1:8000/", timeout=1)
        return r.status_code == 200
    except Exception:
        return False

def check_replay_active(predictions):
    """সর্বশেষ prediction ৫ সেকেন্ডের মধ্যে হলে replay active ধরা হবে"""
    if not predictions:
        return False, None
    try:
        last_ts = datetime.fromisoformat(predictions[0]["timestamp"])
        if last_ts.tzinfo is None:
            last_ts = last_ts.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = (now - last_ts).total_seconds()
        return delta < 5, delta
    except Exception:
        return False, None

backend_ok = check_backend()

with st.sidebar:
    st.header("⚙️ Controls")
    auto_refresh = st.checkbox("Auto-refresh (every 2s)", value=True)
    limit = st.slider("Show last N cycles", 10, 100, 20)

    st.markdown("---")
    st.subheader("System Status (Live)")
    if backend_ok:
        st.success("✅ Backend: Running")
    else:
        st.error("❌ Backend: DOWN — run `python webapp/main.py`")

    st.info(f"🗄️ DB file: {DB_PATH.name}")

# ---------- LOAD DATA ----------
@st.cache_data(ttl=2)
def load_data(limit_val):
    return get_recent_predictions("hydraulic", limit=limit_val)

predictions = load_data(limit)
replay_ok, age = check_replay_active(predictions)

with st.sidebar:
    if replay_ok:
        st.success(f"🔄 Replay: Active ({age:.1f}s ago)")
    else:
        st.warning("🔄 Replay: Idle — run `python replay/service.py`")

# ---------- LIVE STATUS CARD ----------
st.subheader("📊 Live Machine Status")

if predictions:
    latest = predictions[0]
    status = latest["status"]
    if status == "OK":
        st.success(f"### ✅ Hydraulic Rig 1 — Status: {status}")
    elif status == "Warning":
        st.warning(f"### ⚠️ Hydraulic Rig 1 — Status: {status}")
    else:
        st.error(f"### 🔴 Hydraulic Rig 1 — Status: {status}")

    st.markdown("#### 🔍 Component Conditions")
    col1, col2, col3, col4 = st.columns(4)
    d = latest["details"]
    col1.metric("Cooler Condition", d.get("cooler_condition", "N/A"))
    col2.metric("Valve Condition", d.get("valve_condition", "N/A"))
    col3.metric("Pump Leakage", d.get("pump_leakage", "N/A"))
    col4.metric("Accumulator Pressure", d.get("accumulator_pressure", "N/A"))
else:
    if backend_ok:
        st.info("⏳ Backend is up but DB is empty. Start the replay service to see live data.")
    else:
        st.error("Backend is not running. Start it first.")

st.markdown("---")

# ---------- HISTORY TABLE ----------
st.subheader("📜 Recent Predictions History")
if predictions:
    df = pd.DataFrame(predictions)
    df = df[["timestamp", "machine_id", "status", "details"]]
    def color_status(val):
        if val == "OK": return "background-color:#90EE90;color:black"
        if val == "Warning": return "background-color:#FFD700;color:black"
        return "background-color:#FF6B6B;color:white"
    st.dataframe(df.style.map(color_status, subset=["status"]),
                 use_container_width=True, height=400)

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.bar_chart(df["status"].value_counts())
    with col_chart2:
        st.write("**Latest Alert Details:**")
        st.json(predictions[0]["details"])
else:
    st.warning("No data available yet.")

if auto_refresh:
    time.sleep(2)
    st.rerun()