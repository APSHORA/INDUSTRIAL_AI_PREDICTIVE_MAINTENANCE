# webapp/dashboard.py  (CONFIG-DRIVEN - now machine-agnostic)
import sys, json, time
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd
import requests
from database import get_recent_predictions, DB_PATH

BASE_DIR = Path(__file__).parent.parent

def load_machines():
    with open(BASE_DIR / "machines.json") as f:
        return json.load(f)["machines"]

MACHINES = load_machines()          # ← সব machine এখান থেকেই আসে

def check_backend():
    try:
        return requests.get("http://127.0.0.1:8000/", timeout=1).status_code == 200
    except Exception:
        return False

@st.cache_data(ttl=2)
def load_data(mtype, limit_val):
    return get_recent_predictions(mtype, limit=limit_val)

def status_badge(status):
    if status == "OK": return st.success(f"### ✅ Status: {status}")
    if status == "Warning": return st.warning(f"### ⚠️ Status: {status}")
    return st.error(f"### 🔴 Status: {status}")

def render_machine(machine, preds, limit):
    mtype = machine["type"]
    st.subheader(f"📊 {machine['id']} — Live Status")
    if not preds:
        st.info(f"⏳ No data for '{mtype}' yet. Run: python replay/service.py --machine {mtype}")
        return
    latest = preds[0]
    status_badge(latest["status"])

    # 🔍 Details — GENERIC loop (যেকোনো machine-এর যেকোনো key auto-render)
    st.markdown("#### 🔍 Details")
    cols = st.columns(max(len(latest["details"]), 1))
    for col, (k, v) in zip(cols, latest["details"].items()):
        col.metric(k, v)

    # 📜 History
    st.markdown("#### 📜 Recent Predictions")
    df = pd.DataFrame(preds)[["timestamp", "machine_id", "status", "details"]]
    def color(val):
        return {"OK":"background-color:#90EE90","Warning":"background-color:#FFD700"}.get(val,"background-color:#FF6B6B;color:white")
    st.dataframe(df.style.map(color, subset=["status"]), width="stretch", height=300)
    st.bar_chart(df["status"].value_counts())

# ---------- UI ----------
st.set_page_config(page_title="Health Monitoring Dashboard", page_icon="🏭", layout="wide")
st.title("🏭 Multi-Machine Health Monitoring Dashboard")

backend_ok = check_backend()
with st.sidebar:
    st.header("⚙️ Controls")
    auto = st.checkbox("Auto-refresh (2s)", value=True)
    limit = st.slider("Show last N cycles", 10, 100, 20)
    st.markdown("---")
    st.subheader("System Status (Live)")
    st.success("✅ Backend: Running") if backend_ok else st.error("❌ Backend: DOWN")
    st.info(f"🗄️ DB: {DB_PATH.name}")
    st.info(f"🤖 Machines registered: {len(MACHINES)} → {[m['type'] for m in MACHINES]}")

st.markdown(f"**Active machines:** {' | '.join(m['id'] for m in MACHINES)}")
st.markdown("---")

# 🪪 একটা ট্যাব প্রতি machine-এর জন্য (machines.json থেকে অটো)
tabs = st.tabs([m["type"].upper() for m in MACHINES])
for tab, machine in zip(tabs, MACHINES):
    with tab:
        render_machine(machine, load_data(machine["type"], limit), limit)

if auto:
    time.sleep(2)
    st.rerun()