"""
Page 2: Opportunity Pipeline — Deal-Level Analysis with MEDDPICC
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from data.sample_data import generate_opportunities
from utils.traffic_light import traffic_light_badge, get_status, meddpicc_traffic_light
from utils.metrics import format_currency

st.set_page_config(page_title="Opportunity Pipeline", page_icon="\U0001F4B0", layout="wide")

@st.cache_data
def load_data():
    return generate_opportunities(n=150)

df = load_data()
regions = st.session_state.get("selected_regions", df["region"].unique().tolist())
df = df[df["region"].isin(regions)]
active = df[~df["stage"].isin(["Closed Won", "Closed Lost"])]

st.markdown("# Opportunity Pipeline")
st.markdown("**Active Deals:** {} | **Pipeline:** {}".format(
    len(active), format_currency(active["deal_value_usd"].sum())))
st.markdown("---")

# --- FILTERS ---
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    stage_filter = st.multiselect("Stage:", active["stage"].unique().tolist(),
                                   default=active["stage"].unique().tolist())
with col_f2:
    risk_filter = st.multiselect("Risk Flag:", ["High", "Medium", "Low"],
                                  default=["High", "Medium", "Low"])
with col_f3:
    min_deal = st.number_input("Min Deal Value ($K):", 0, 1000, 0, step=50)

filtered = active[
    (active["stage"].isin(stage_filter)) &
    (active["risk_flag"].isin(risk_filter)) &
    (active["deal_value_usd"] >= min_deal * 1000)
]

# --- PIPELINE BY STAGE ---
st.markdown("## Pipeline by Stage")
if len(filtered) > 0:
    stage_summary = filtered.groupby("stage").agg(
        deals=("opportunity_id", "count"),
        pipeline=("deal_value_usd", "sum"),
        avg_win=("win_probability", "mean"),
        avg_enablement=("enablement_score", "mean")
    ).reset_index()

    fig = px.bar(
        stage_summary, x="stage", y="pipeline", color="avg_enablement",
        text="deals", color_continuous_scale=["#FF3D00", "#FFB300", "#69F0AE"],
        hover_data=["avg_win"]
    )
    fig.update_layout(
        paper_bgcolor="#0D1117", plot_bgcolor="#161B22",
        font=dict(color="#F0F6FC"), height=350,
        xaxis=dict(title="", gridcolor="#30363D"),
        yaxis=dict(title="Pipeline Value ($)", gridcolor="#30363D")
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- MEDDPICC HEATMAP ---
st.markdown("## MEDDPICC Scorecard")
meddpicc_cols = ["meddpicc_metrics", "meddpicc_econ_buyer", "meddpicc_decision_criteria",
                 "meddpicc_decision_process", "meddpicc_paper_process",
                 "meddpicc_pain", "meddpicc_champion", "meddpicc_competition"]
meddpicc_labels = ["Metrics", "Econ Buyer", "Decision Criteria", "Decision Process",
                   "Paper Process", "Pain", "Champion", "Competition"]

if len(filtered) > 0:
    region_meddpicc = filtered.groupby("region")[meddpicc_cols].mean()

    header_html = "<table style='width:100%;border-collapse:collapse;'><tr><th style='color:#8B949E;padding:8px;'>Region</th>"
    for label in meddpicc_labels:
        header_html += "<th style='color:#8B949E;padding:8px;text-align:center;'>{}</th>".format(label)
    header_html += "</tr>"

    for region_name in region_meddpicc.index:
        header_html += "<tr><td style='color:#F0F6FC;padding:8px;font-weight:600;'>{}</td>".format(region_name)
        for col in meddpicc_cols:
            score = region_meddpicc.loc[region_name, col]
            header_html += "<td style='padding:4px;text-align:center;'>{}</td>".format(
                meddpicc_traffic_light(score))
        header_html += "</tr>"
    header_html += "</table>"
    st.markdown(header_html, unsafe_allow_html=True)

st.markdown("---")

# --- DEAL TABLE ---
st.markdown("## Deal Details")
if len(filtered) > 0:
    display_cols = ["opportunity_id", "region", "stage", "deal_value_usd",
                    "win_probability", "enablement_score", "meddpicc_avg",
                    "days_in_current_stage", "risk_flag", "aging_status"]
    st.dataframe(
        filtered[display_cols].sort_values("deal_value_usd", ascending=False),
        use_container_width=True, height=400,
        column_config={
            "deal_value_usd": st.column_config.NumberColumn("Deal Value", format="$%d"),
            "win_probability": st.column_config.ProgressColumn("Win %", min_value=0, max_value=100),
            "enablement_score": st.column_config.ProgressColumn("Enablement", min_value=0, max_value=100),
            "meddpicc_avg": st.column_config.ProgressColumn("MEDDPICC", min_value=0, max_value=100),
        }
    )
else:
    st.warning("No deals match the current filters.")
