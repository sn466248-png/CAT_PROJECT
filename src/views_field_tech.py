import pandas as pd
import os
import json
import streamlit as st
from datetime import datetime

FIELD_LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "field_observations.json")

def load_field_observations():
    if not os.path.exists(FIELD_LOG_FILE):
        return []
    try:
        with open(FIELD_LOG_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def save_field_observations(observations):
    os.makedirs(os.path.dirname(FIELD_LOG_FILE), exist_ok=True)
    with open(FIELD_LOG_FILE, 'w') as f:
        json.dump(observations, f, indent=2)

def render_field_tech_view(df, quality_info):
    """
    Renders mobile-optimized field inspection tool with offline observation capture and deferred queue synchronization.
    """
    st.title("📱 Field Technician Inspection Workflow")
    st.caption("Simplified mobile-friendly logger for equipment observations with offline queue support.")

    observations = load_field_observations()

    # Network Connection Simulator Toggle
    col_net1, col_net2 = st.columns([2, 1])
    with col_net1:
        st.subheader("📶 Connectivity Status")
    with col_net2:
        is_online = st.toggle("Network Connected", value=True, help="Toggle OFF to simulate offline local storage mode")

    if is_online:
        st.success("🟢 Connected to Enterprise Network. Observations auto-sync to central database.")
    else:
        st.warning("🟠 Offline Mode Active. Observations will be saved locally to device storage and queued for sync.")

    st.markdown("---")

    # Form to capture field observation
    st.subheader("📝 New Field Inspection Record")

    with st.form("field_observation_form", clear_on_submit=True):
        equip_name = st.selectbox(
            "Equipment Name / ID:",
            ["HVAC Chiller #1 (East Bay)", "HVAC AHU #3 (Office)", "Process Line 2 Main Compressor", "Warehouse Bay 4 Lighting Panel", "Substation Transformer #2"]
        )

        op_status = st.radio(
            "Operating Status:",
            ["NORMAL", "DEGRADED / VIBRATION", "OFF-SCHEDULE OPERATION", "CRITICAL FAULT"]
        )

        fault_obs = st.multiselect(
            "Observed Issues:",
            ["Unexpected Heat", "Audible Air Leak", "BMS Schedule Override Switch Engaged", "Sensor Calibration Drift", "Manual Bypass Activated"]
        )

        notes = st.text_area("Technician Notes / Remediation Action:", placeholder="e.g. Cleaned condenser coils, reset manual override to BMS auto mode.")

        submitted = st.form_submit_button("💾 Save Observation Record")

        if submitted:
            new_record = {
                "id": len(observations) + 1,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "equipment": equip_name,
                "status": op_status,
                "faults": fault_obs,
                "notes": notes,
                "synced": is_online
            }
            observations.append(new_record)
            save_field_observations(observations)

            if is_online:
                st.success("✅ Inspection record saved and SYNCHRONIZED to central energy management server!")
            else:
                st.info("📦 Inspection record saved to LOCAL QUEUE (Offline). Sync pending network restoration.")

    st.markdown("---")

    # Pending Sync Queue & Inspection History
    st.subheader("📋 Inspection History & Pending Sync Queue")

    pending_records = [r for r in observations if not r.get("synced", True)]
    synced_records = [r for r in observations if r.get("synced", True)]

    if pending_records:
        st.warning(f"⚠️ **{len(pending_records)} Pending Record(s) Queued for Synchronization**")
        if is_online:
            if st.button("🔄 Synchronize Pending Local Records Now"):
                for r in observations:
                    r["synced"] = True
                save_field_observations(observations)
                st.success("🎉 All pending field observation records synchronized successfully!")
                st.rerun()
    else:
        st.info("✅ All local field records are fully synchronized.")

    if observations:
        history_df = pd.DataFrame(observations)
        st.dataframe(history_df[['id', 'timestamp', 'equipment', 'status', 'synced', 'notes']], use_container_width=True)
    else:
        st.text("No inspection records logged yet.")
