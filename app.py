import streamlit as st
import pandas as pd
from src.data_loader import load_dataset
from src.edge_cases import evaluate_data_quality, render_edge_case_banner
from src.low_bandwidth import render_low_bandwidth_view
from src.views_executive import render_executive_view
from src.views_energy_manager import render_energy_manager_view
from src.views_facilities import render_facilities_view
from src.views_field_tech import render_field_tech_view
from src.views_ml_mv import render_ml_mv_view
from src.documentation import render_documentation_view

def main():
    st.set_page_config(
        page_title="Actionable Energy Disaggregation & M&V Platform",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Sidebar Navigation & Persona Switcher
    st.sidebar.image("https://img.icons8.com/color/96/lightning-bolt.png", width=60)
    st.sidebar.title("Energy Intelligence")
    st.sidebar.caption("Actionable NILM Disaggregation & ASHRAE 14 M&V Hub")

    st.sidebar.markdown("---")

    # Role / Section Selector
    st.sidebar.subheader("👤 Select Navigation View")
    role_view = st.sidebar.radio(
        "Platform Perspective:",
        [
            "Energy Manager View",
            "ML/NILM & ASHRAE 14 M&V Hub",
            "Executive View",
            "Facilities Operator View",
            "Field Technician View",
            "System Analysis & Documentation"
        ],
        index=0
    )

    st.sidebar.markdown("---")

    # Low Bandwidth Mode Toggle
    st.sidebar.subheader("⚡ Display Mode")
    low_bandwidth_mode = st.sidebar.toggle("Low-Bandwidth / Text Mode", value=False, help="Enable simplified text/table view for poor network environments.")

    st.sidebar.markdown("---")

    # Edge Case Simulation Controls (5 Failure Cases)
    st.sidebar.subheader("🧪 Edge Case & Fault Simulator")
    edge_case_selection = st.sidebar.selectbox(
        "Inject Data Quality Scenario:",
        [
            "NONE (Clean Real-Time Telemetry)",
            "MISSING_METER_VALUES (Case 1: Missing Meter Intervals)",
            "STALE_DATA (Case 2: Delayed/Frozen Meter Feed)",
            "MISSING_OCCUPANCY (Case 3: Occupancy Sensor Offline)",
            "SCHEDULE_MISMATCH (Case 4: Off-Schedule HVAC/Light Draw)",
            "EXTREME_OUTLIER (Case 5: Unphysical Electrical Surge)",
            "MISSING_TIMESTAMPS (Corrupted Telemetry Dates)"
        ]
    )

    edge_case_code = "NONE"
    if "MISSING_METER_VALUES" in edge_case_selection:
        edge_case_code = "MISSING_METER_VALUES"
    elif "STALE_DATA" in edge_case_selection:
        edge_case_code = "STALE_DATA"
    elif "MISSING_OCCUPANCY" in edge_case_selection:
        edge_case_code = "MISSING_OCCUPANCY"
    elif "SCHEDULE_MISMATCH" in edge_case_selection:
        edge_case_code = "SCHEDULE_MISMATCH"
    elif "EXTREME_OUTLIER" in edge_case_selection:
        edge_case_code = "EXTREME_OUTLIER"
    elif "MISSING_TIMESTAMPS" in edge_case_selection:
        edge_case_code = "MISSING_TIMESTAMPS"

    # Load Data and evaluate quality
    df = load_dataset(edge_case_type=edge_case_code)
    quality_info = evaluate_data_quality(df, edge_case_type=edge_case_code)

    # Main Header & Quality Indicators
    st.markdown(f"### 🏭 Industrial Facility Energy Disaggregation & M&V Platform")
    
    # Render Data Quality Indicator Banner
    render_edge_case_banner(st, quality_info)

    st.markdown("---")

    # Render requested view
    if low_bandwidth_mode and role_view != "System Analysis & Documentation":
        render_low_bandwidth_view(df, quality_info)
    elif role_view == "ML/NILM & ASHRAE 14 M&V Hub":
        render_ml_mv_view(df, quality_info)
    elif role_view == "Executive View":
        render_executive_view(df, quality_info)
    elif role_view == "Energy Manager View":
        render_energy_manager_view(df, quality_info)
    elif role_view == "Facilities Operator View":
        render_facilities_view(df, quality_info)
    elif role_view == "Field Technician View":
        render_field_tech_view(df, quality_info)
    elif role_view == "System Analysis & Documentation":
        render_documentation_view()

    # Footer
    st.markdown("---")
    st.caption("Actionable Energy-Use Disaggregation & M&V Platform (70% Milestone) | ASHRAE Guideline 14 & IPMVP Option C Compliant | Built with Streamlit, Plotly, Scikit-Learn & Python")

if __name__ == "__main__":
    main()
