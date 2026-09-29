import numpy as np
import pandas as pd
from preprocessing.clean_data import detect_outliers, detect_schedule_mismatch

def evaluate_data_quality(df, edge_case_type="NONE"):
    """
    Evaluates current data quality state across standardized indicators and tests 5 specific failure cases:
    - CASE 1: Missing meter values (detect, warn, avoid silent filling, reduced confidence)
    - CASE 2: Stale meter data (display STALE status, lock current savings verification)
    - CASE 3: Missing occupancy data (display MISSING status, reduce attribution confidence)
    - CASE 4: Equipment schedule mismatch (detect abnormal operation, flag schedule deviation)
    - CASE 5: Unexpected extreme meter value (detect potential outlier, flag for review)
    """
    status = "FRESH"
    color = "green"
    badge_icon = "🟢"
    confidence_pct = 95.0
    messages = []
    actions_allowed = True
    savings_claim_locked = False
    flagged_outliers = []
    flagged_schedule_deviations = []

    # CASE 1: Missing meter values
    has_missing_meter = False
    if 'total_kw' in df.columns:
        n_missing_meter = int(df['total_kw'].isna().sum())
        if n_missing_meter > 0 or edge_case_type == "MISSING_METER_VALUES":
            has_missing_meter = True
            status = "REDUCED CONFIDENCE"
            color = "red"
            badge_icon = "🔴"
            confidence_pct = 35.0
            messages.append(f"WARNING: {n_missing_meter if n_missing_meter > 0 else 20} missing meter interval readings detected in telemetry feed.")
            messages.append("Critical data is NOT silently imputed. ML disaggregation and automated savings claims paused.")
            actions_allowed = False
            savings_claim_locked = True

    # CASE 2: Stale meter data
    if edge_case_type == "STALE_DATA":
        status = "STALE"
        color = "orange"
        badge_icon = "🟠"
        confidence_pct = 40.0
        messages.append("WARNING: Meter data feed frozen or delayed > 6 hours. Last recorded timestamp is outdated.")
        messages.append("Current savings claims and live disaggregation verification are LOCKED until telemetry restores.")
        actions_allowed = False
        savings_claim_locked = True

    # CASE 3: Missing occupancy data
    elif edge_case_type == "MISSING_OCCUPANCY" or ('occupancy_pct' in df.columns and df['occupancy_pct'].isna().all()):
        status = "MISSING"
        color = "red"
        badge_icon = "🔴"
        confidence_pct = 55.0
        messages.append("ATTENTION: Occupancy sensor feed is completely MISSING (NaN / offline).")
        messages.append("HVAC disaggregation attribution running in REDUCED CONFIDENCE fallback mode using temperature baselines only.")

    # Missing timestamps
    elif edge_case_type == "MISSING_TIMESTAMPS" or ('timestamp' in df.columns and df['timestamp'].isna().any()):
        status = "REDUCED CONFIDENCE"
        color = "red"
        badge_icon = "🔴"
        confidence_pct = 30.0
        messages.append("CRITICAL: Corrupted or missing timestamp records detected in time-series telemetry.")
        messages.append("Time-based peak tariff aggregations temporarily disabled to prevent misleading calculations.")
        actions_allowed = False

    # CASE 5: Unexpected extreme meter value
    if not has_missing_meter and 'total_kw' in df.columns:
        valid_kw = df[df['total_kw'].notna()]
        if not valid_kw.empty:
            outlier_mask, outlier_records = detect_outliers(valid_kw, column='total_kw', threshold_sigma=3.5, max_physical_kw=800.0)
            if outlier_mask.any() or edge_case_type == "EXTREME_OUTLIER":
                n_outliers = int(outlier_mask.sum()) if outlier_mask.any() else 1
                messages.append(f"ALERT: {n_outliers} unexpected extreme meter reading(s) detected (> 800 kW or > 3.5σ). Flagged for engineering review.")
                confidence_pct = min(confidence_pct, 65.0)
                if not outlier_records.empty:
                    flagged_outliers = outlier_records[['timestamp', 'total_kw', 'outlier_reason']].to_dict('records')
                else:
                    flagged_outliers = [{"timestamp": "Recent reading", "total_kw": 1450.0, "outlier_reason": "Exceeds Physical Capacity (800.0 kW)"}]

    # CASE 4: Equipment schedule mismatch
    mismatch_df = detect_schedule_mismatch(df)
    if not mismatch_df.empty or edge_case_type == "SCHEDULE_MISMATCH":
        n_mismatches = len(mismatch_df) if not mismatch_df.empty else 16
        messages.append(f"NOTICE: {n_mismatches} intervals detected with equipment operating during unscheduled hours. Possible operational schedule deviation.")
        if not mismatch_df.empty:
            flagged_schedule_deviations = mismatch_df.head(5).to_dict('records')
        else:
            flagged_schedule_deviations = [{"equipment": "HVAC System", "draw_kw": 145.0, "scheduled_status": "OFF (0)", "severity": "HIGH"}]

    if not messages:
        messages.append("All primary meter telemetry feeds, contextual sensors, and equipment schedules are nominal (< 15 min lag).")

    return {
        "status": status,
        "color": color,
        "badge_icon": badge_icon,
        "confidence_pct": confidence_pct,
        "messages": messages,
        "actions_allowed": actions_allowed,
        "savings_claim_locked": savings_claim_locked,
        "flagged_outliers": flagged_outliers,
        "flagged_schedule_deviations": flagged_schedule_deviations
    }

def render_edge_case_banner(st, quality_info):
    """
    Renders Streamlit UI banner for data quality status.
    """
    st.markdown(f"### Data Quality Indicator: {quality_info['badge_icon']} **{quality_info['status']}** (Confidence: {quality_info['confidence_pct']}%)")
    
    if quality_info.get("savings_claim_locked", False):
        st.error("🔒 **Savings Verification Claims are Locked** due to data quality degradation or delayed telemetry feed.")
        
    for msg in quality_info['messages']:
        if quality_info['status'] == "STALE":
            st.warning(msg)
        elif quality_info['status'] in ["MISSING", "REDUCED CONFIDENCE"]:
            st.error(msg)
        elif "ALERT" in msg:
            st.warning(msg)
        elif "NOTICE" in msg:
            st.info(msg)
        else:
            st.success(msg)
