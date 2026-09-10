import pandas as pd
import numpy as np

def evaluate_data_quality(df, edge_case_type="NONE"):
    """
    Evaluates current data quality state across four standardized indicators:
    - FRESH: Meter feed active and recent (< 15 min lag), all metadata present.
    - STALE: Data feed delayed (> 30 min lag or frozen timestamps).
    - MISSING: Crucial contextual data (occupancy or schedules) unavailable.
    - REDUCED CONFIDENCE: Core meter present, but missing context reduces AI disaggregation accuracy.
    """
    status = "FRESH"
    color = "green"
    badge_icon = "🟢"
    confidence_pct = 95.0
    messages = []
    actions_allowed = True

    if edge_case_type == "STALE_DATA":
        status = "STALE"
        color = "orange"
        badge_icon = "🟠"
        confidence_pct = 40.0
        messages.append("WARNING: Meter data feed frozen or delayed > 6 hours. Last recorded timestamp is outdated.")
        messages.append("Savings claims and live disaggregation updates are locked until telemetry restores.")
        actions_allowed = False

    elif edge_case_type == "MISSING_OCCUPANCY":
        status = "MISSING"
        color = "red"
        badge_icon = "🔴"
        confidence_pct = 55.0
        messages.append("ATTENTION: Occupancy sensor feed is MISSING (NaN / offline).")
        messages.append("HVAC disaggregation attribution running on REDUCED CONFIDENCE mode using temperature baselines only.")

    elif edge_case_type == "MISSING_TIMESTAMPS":
        status = "REDUCED CONFIDENCE"
        color = "red"
        badge_icon = "🔴"
        confidence_pct = 30.0
        messages.append("CRITICAL: Corrupted or missing timestamp records detected in time-series telemetry.")
        messages.append("Time-based peak tariff aggregations temporarily disabled to prevent misleading calculations.")
        actions_allowed = False

    elif df['occupancy_pct'].isnull().any():
        status = "MISSING"
        color = "red"
        badge_icon = "🔴"
        confidence_pct = 60.0
        messages.append("Partial occupancy data missing across some time intervals.")

    return {
        "status": status,
        "color": color,
        "badge_icon": badge_icon,
        "confidence_pct": confidence_pct,
        "messages": messages,
        "actions_allowed": actions_allowed
    }

def render_edge_case_banner(st, quality_info):
    """
    Renders Streamlit UI banner for data quality status.
    """
    st.markdown(f"### Data Quality Indicator: {quality_info['badge_icon']} **{quality_info['status']}** (Confidence: {quality_info['confidence_pct']}%)")
    
    for msg in quality_info['messages']:
        if quality_info['status'] == "STALE":
            st.warning(msg)
        elif quality_info['status'] in ["MISSING", "REDUCED CONFIDENCE"]:
            st.error(msg)
        else:
            st.info(msg)
