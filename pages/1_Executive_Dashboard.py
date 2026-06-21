"""
Page 1: Executive Dashboard — CXO Scorecard with Traffic Lights
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from data.sample_data import generate_opportunities
from utils.traffic_light import traffic_light_badge, get_status, correlation_badge
from utils.metrics import format_currency, calculate_cohort_delta

st.set_page_config(page_title="Executive Dashboard", page_icon="\U0001F4CA", layout="wide")

@st.cache_data
def load_data():
    return generate_opportunities(n=150)

df = load_data()
regions = st.session_state.get("selected_regions", df["region"].unique().tolist())
df = df[df["region"].isin(regions)]
active = df[~df["stage"].isin(["Closed Won", "Closed Lost"])]

st.markdown("# Executive Dashboard")
st.markdown("**Pipeline:** {} | **Active Deals:** {}".format(
    format_currency(active["deal_value_usd"].sum()), len(active)))

if len(df) > 5:
    r_val, _ = stats.pearsonr(df["enablement_score"], df["win_probability"])
    st.markdown(correlation_badge(r_val, "Enablement to Win Rate"), unsafe_allow_html=True)
st.markdown("---")

# --- TRAFFIC LIGHT REGIONAL MATRIX ---
st.markdown("## Regional Health Matrix")

unique_regions = sorted(df["region"].unique())
for region in unique_regions:
    rdf = df[df["region"] == region]
    if len(rdf) == 0:
        continue
    statuses = {
        "Win Rate": get_status(rdf["win_probability"].mean(), "win_rate"),
        "Enablement": get_status(rdf["enablement_score"].mean(), "enablement_score"),
        "GenAI": get_status(rdf["genai_readiness"].mean(), "genai_readiness"),
        "MEDDPICC": get_status(rdf["meddpicc_avg"].mean(), "meddpicc_score"),
    }
    cols = st.columns([1.5, 1, 1, 1, 1])
    cols[0].markdown("**{}**".format(region))
    for i, (metric_name, status_val) in enumerate(statuses.items()):
        cols[i + 1].markdown(
            traffic_light_badge(status_val, metric_name), unsafe_allow_html=True)

st.markdown("---")

# --- PIPELINE FUNNEL ---
st.markdown("## Pipeline Funnel")
stage_order = ["Prospect", "Qualification", "Technical Validation",
               "Business Validation", "Negotiation", "Closed Won", "Closed Lost"]
funnel_stages = [s for s in stage_order if s in df["stage"].values]
funnel_counts = [len(df[df["stage"] == s]) for s in funnel_stages]

if funnel_counts:
    fig = go.Figure(go.Funnel(
        y=funnel_stages, x=funnel_counts,
        textinfo="value+percent initial",
        marker={"color": ["#FF9900", "#FFB300", "#58A6FF",
                          "#69F0AE", "#9C27B0", "#00C851", "#FF3D00"][:len(funnel_stages)]}
    ))
    fig.update_layout(
        paper_bgcolor="#0D1117", plot_bgcolor="#0D1117",
        font=dict(color="#F0F6FC"), height=350, margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --- DEAL VELOCITY SCATTER ---
st.markdown("## Deal Velocity vs Enablement")
if len(active) > 0:
    fig2 = px.scatter(
        active, x="enablement_score", y="velocity_weekly_usd",
        size="deal_value_usd", color="region",
        hover_data=["opportunity_id", "stage", "win_probability"],
        color_discrete_sequence=["#FF9900", "#58A6FF", "#69F0AE", "#9C27B0", "#FFD54F", "#FF6B6B"]
    )
    fig2.update_layout(
        paper_bgcolor="#0D1117", plot_bgcolor="#161B22",
        font=dict(color="#F0F6FC"), height=400,
        xaxis=dict(title="Enablement Score", gridcolor="#30363D"),
        yaxis=dict(title="Weekly Velocity ($)", gridcolor="#30363D"),
        showlegend=True
    )
    st.plotly_chart(fig2, use_container_width=True)
